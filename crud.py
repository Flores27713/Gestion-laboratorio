from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

import models
import schemas

def get_items(db: Session, search: str = "", category: str = "", location: str = "", cost_center: str = ""):
    query = db.query(models.Item)
    if search:
        search_pattern = f"%{search.lower()}%"
        query = query.filter(
            func.lower(models.Item.name).like(search_pattern) |
            func.lower(models.Item.location).like(search_pattern) |
            models.Item.id.cast(models.String).like(search_pattern)
        )
    if category and category != "TODAS":
        query = query.filter(models.Item.category == category)
    if location and location != "TODAS":
        query = query.filter(models.Item.location.like(f"%{location}%"))
    if cost_center and cost_center != "TODOS":
        query = query.filter(models.Item.cost_center.like(f"%{cost_center}%"))
    return query.order_by(models.Item.id).all()

def get_item_by_id(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()

def create_requisition(db: Session, req_data: schemas.RequisitionCreate):
    if not req_data.items:
        raise HTTPException(status_code=400, detail="Debe incluir al menos un material en la solicitud.")

    # Validate stock for all items
    for item_input in req_data.items:
        item = get_item_by_id(db, item_input.item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"Artículo ID #{item_input.item_id} no encontrado.")
        if item.avail < item_input.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para '{item.name}'. Disponible actual: {item.avail}, solicitado: {item_input.quantity}."
            )

    # Generate unique code SOL-2026-XXX
    total_reqs = db.query(models.Requisition).count() + 1
    code = f"SOL-2026-{str(total_reqs).zfill(3)}"

    new_req = models.Requisition(
        code=code,
        applicant=req_data.applicant,
        rut=req_data.rut,
        career=req_data.career,
        course=req_data.course,
        professor=req_data.professor,
        return_date=req_data.return_date,
        status="ACTIVO"
    )
    db.add(new_req)
    db.flush() # get new_req.id

    # Add items and update inventory stock
    for item_input in req_data.items:
        item = get_item_by_id(db, item_input.item_id)
        
        # Deduct stock
        item.avail -= item_input.quantity
        item.in_use += item_input.quantity

        req_item = models.RequisitionItem(
            requisition_id=new_req.id,
            item_id=item.id,
            item_name=item.name,
            quantity=item_input.quantity
        )
        db.add(req_item)

    db.commit()
    db.refresh(new_req)
    return new_req

def return_requisition(db: Session, requisition_id: int):
    req = db.query(models.Requisition).filter(models.Requisition.id == requisition_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")

    if req.status == "DEVUELTO":
        raise HTTPException(status_code=400, detail="Esta solicitud ya fue devuelta anteriormente.")

    # Reincorporate stock
    for req_item in req.items:
        item = get_item_by_id(db, req_item.item_id)
        if item:
            item.in_use = max(0, item.in_use - req_item.quantity)
            item.avail += req_item.quantity

    req.status = "DEVUELTO"
    db.commit()
    db.refresh(req)
    return req

def get_dashboard_metrics(db: Session):
    items = db.query(models.Item).all()
    total_items = len(items)
    total_units = sum(i.stock for i in items)
    total_avail = sum(i.avail for i in items)
    total_in_use = sum(i.in_use for i in items)
    total_damaged = sum(i.damaged for i in items)

    active_reqs = db.query(models.Requisition).filter(models.Requisition.status == "ACTIVO").count()
    low_stock = db.query(models.Item).filter(models.Item.avail <= 2).order_by(models.Item.avail).limit(6).all()
    recent_reqs = db.query(models.Requisition).order_by(models.Requisition.id.desc()).limit(5).all()

    return {
        "total_items": total_items,
        "total_units": total_units,
        "total_avail": total_avail,
        "total_in_use": total_in_use,
        "total_damaged": total_damaged,
        "active_reqs": active_reqs,
        "low_stock": [i.to_dict() for i in low_stock],
        "recent_reqs": [r.to_dict() for r in recent_reqs]
    }

def get_semester_stats(db: Session):
    # Top items by requested quantity in requisitions
    top_items_query = db.query(
        models.RequisitionItem.item_name,
        func.sum(models.RequisitionItem.quantity).label("total_qty")
    ).group_by(models.RequisitionItem.item_name).order_by(func.sum(models.RequisitionItem.quantity).desc()).limit(10).all()

    top_items = [{"name": row[0], "count": row[1]} for row in top_items_query]

    # Cost center counts
    items = db.query(models.Item).all()
    cost_breakdown = {
        "Informática": sum(1 for i in items if "Informática" in i.cost_center),
        "Industrial": sum(1 for i in items if "Industrial" in i.cost_center),
        "Ambas Carreras": sum(1 for i in items if "Ambas" in i.cost_center or "Caja" in i.cost_center)
    }

    return {
        "top_items": top_items,
        "cost_breakdown": cost_breakdown
    }

def _parse_file_to_rows(file_bytes: bytes, filename: str):
    """Parse CSV or Excel file into a clean list of rows (each row is a list of strings).
    Handles Excel files with decorative header rows and empty leading/trailing columns."""
    import csv
    import io

    raw_rows = []
    filename_lower = filename.lower()

    if filename_lower.endswith(('.xlsx', '.xls')):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(filename=io.BytesIO(file_bytes), data_only=True)
            sheet = wb.active
            for row in sheet.iter_rows(values_only=True):
                raw_rows.append([str(c).strip() if c is not None else "" for c in row])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo Excel: {str(e)}")
    else:
        try:
            try:
                text = file_bytes.decode('utf-8-sig')
            except Exception:
                text = file_bytes.decode('latin-1')

            delimiter = ';' if ';' in text else (',' if ',' in text else '\t')
            f = io.StringIO(text.strip())
            reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                raw_rows.append([c.strip() for c in row])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo CSV: {str(e)}")

    if not raw_rows:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")

    # Find the header row by looking for keywords like "nombre", "articulo", "stock", "id"
    header_keywords = ["nombre", "artículo", "articulo", "stock", "ubicaci", "bodega", "id"]
    header_row_idx = None
    for idx, row in enumerate(raw_rows):
        row_text = " ".join(str(c).lower() for c in row)
        matches = sum(1 for kw in header_keywords if kw in row_text)
        if matches >= 2:  # at least 2 keywords found = this is the header row
            header_row_idx = idx
            break

    # If no header found, use first non-empty row
    if header_row_idx is None:
        for idx, row in enumerate(raw_rows):
            if any(c for c in row):
                header_row_idx = idx
                break
        if header_row_idx is None:
            raise HTTPException(status_code=400, detail="No se encontraron datos válidos en el archivo.")

    # Take rows from header onwards
    relevant_rows = raw_rows[header_row_idx:]

    # Detect and strip empty leading/trailing columns
    # Find the first and last column that have data across all rows
    if relevant_rows:
        num_cols = max(len(r) for r in relevant_rows)
        first_data_col = 0
        last_data_col = num_cols - 1

        for col in range(num_cols):
            col_values = [r[col] if col < len(r) else "" for r in relevant_rows]
            if any(v for v in col_values):
                first_data_col = col
                break

        for col in range(num_cols - 1, -1, -1):
            col_values = [r[col] if col < len(r) else "" for r in relevant_rows]
            if any(v for v in col_values):
                last_data_col = col
                break

        # Trim columns
        rows = []
        for row in relevant_rows:
            trimmed = [row[c] if c < len(row) else "" for c in range(first_data_col, last_data_col + 1)]
            if any(v for v in trimmed):
                rows.append(trimmed)
    else:
        rows = relevant_rows

    if not rows:
        raise HTTPException(status_code=400, detail="El archivo no contiene datos después de procesar.")

    return rows


def _detect_column_mapping(headers):
    """Detect column indices by matching header names intelligently."""
    col_map = {"id": None, "name": None, "location": None, "stock": None,
               "in_use": None, "damaged": None, "avail": None, "cost_center": None}

    # First pass: detect specific/long matches first to avoid conflicts
    for idx, h in enumerate(headers):
        hl = str(h).strip().lower()
        if hl in ("id", "#", "n°", "nro", "numero", "número"):
            col_map["id"] = idx
        elif any(k in hl for k in ["nombre", "artículo", "articulo", "descripcion", "descripción", "material", "item"]):
            col_map["name"] = idx
        elif any(k in hl for k in ["ubicacion", "ubicación", "bodega", "estante", "location"]):
            col_map["location"] = idx
        elif any(k in hl for k in ["en uso", "prestado", "uso/prestado", "prestamo", "préstamo"]):
            col_map["in_use"] = idx
        elif any(k in hl for k in ["mal estado", "dañado", "dañados", "damaged", "defectuoso", "malo"]):
            col_map["damaged"] = idx
        elif any(k in hl for k in ["stock disponible", "disponible", "disp", "available"]):
            col_map["avail"] = idx
        elif any(k in hl for k in ["centro", "costo", "carrera", "cost"]):
            col_map["cost_center"] = idx

    # Second pass: detect "stock" column (must NOT be the "stock disponible" column)
    for idx, h in enumerate(headers):
        hl = str(h).strip().lower()
        if idx == col_map["avail"]:
            continue  # skip the "stock disponible" column
        if "stock" in hl or "cantidad" in hl or hl == "total":
            col_map["stock"] = idx
            break

    return col_map


def _safe_int(val, default=0):
    """Safely convert a value to int, handling empty strings, None, floats."""
    s = str(val).strip()
    if not s:
        return default
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return default


def preview_file_data(file_bytes: bytes, filename: str):
    """Parse a file and return diagnostic info about how it would be imported."""
    rows = _parse_file_to_rows(file_bytes, filename)

    headers = [str(h).strip() for h in rows[0]]
    headers_lower = [h.lower() for h in headers]
    has_header = any("nombre" in h or "id" == h or "articulo" in h or "artículo" in h for h in headers_lower)

    col_map = _detect_column_mapping(headers) if has_header else None

    preview_rows = []
    data_start = 1 if has_header else 0
    for row in rows[data_start:data_start + 5]:  # first 5 data rows
        preview_rows.append([str(c) for c in row])

    return {
        "filename": filename,
        "total_rows": len(rows),
        "data_rows": len(rows) - (1 if has_header else 0),
        "headers_detected": has_header,
        "raw_headers": headers if has_header else None,
        "column_mapping": {k: (v if v is not None else "NO DETECTADA") for k, v in col_map.items()} if col_map else "Sin encabezados - usando posición fija",
        "preview_data": preview_rows,
        "total_columns": len(rows[0]) if rows else 0
    }


def import_file_data(db: Session, file_bytes: bytes, filename: str):
    rows = _parse_file_to_rows(file_bytes, filename)

    # Detect if row 0 is a header
    headers_lower = [str(h).strip().lower() for h in rows[0]]
    has_header = any("nombre" in h or "id" == h or "articulo" in h or "artículo" in h for h in headers_lower)

    # Try smart column detection from headers
    col_map = None
    if has_header:
        col_map = _detect_column_mapping(rows[0])

    imported_count = 0
    updated_count = 0
    data_start = 1 if has_header else 0

    for row in rows[data_start:]:
        if not row or len(row) < 2:
            continue
        try:
            if col_map and col_map["name"] is not None:
                # SMART MODE: use detected column positions
                item_id = _safe_int(row[col_map["id"]], default=None) if col_map["id"] is not None and col_map["id"] < len(row) else None
                name = str(row[col_map["name"]]).strip() if col_map["name"] < len(row) else ""
                location = str(row[col_map["location"]]).strip() if col_map["location"] is not None and col_map["location"] < len(row) else "BODEGA"
                stock = _safe_int(row[col_map["stock"]]) if col_map["stock"] is not None and col_map["stock"] < len(row) else 1
                in_use = _safe_int(row[col_map["in_use"]]) if col_map["in_use"] is not None and col_map["in_use"] < len(row) else 0
                damaged = _safe_int(row[col_map["damaged"]]) if col_map["damaged"] is not None and col_map["damaged"] < len(row) else 0
                avail = _safe_int(row[col_map["avail"]]) if col_map["avail"] is not None and col_map["avail"] < len(row) else max(0, stock - in_use - damaged)
                cost_center = str(row[col_map["cost_center"]]).strip() if col_map["cost_center"] is not None and col_map["cost_center"] < len(row) else "Ambas Carreras"
            else:
                # FALLBACK: positional parsing
                val_0 = str(row[0]).strip()
                item_id = _safe_int(val_0, default=None) if val_0.isdigit() else None

                if item_id is not None:
                    name = str(row[1]).strip() if len(row) > 1 else ""
                    location = str(row[2]).strip() if len(row) > 2 else "BODEGA"
                    stock = _safe_int(row[3], 1) if len(row) > 3 else 1
                    in_use = _safe_int(row[4]) if len(row) > 4 else 0
                    damaged = _safe_int(row[5]) if len(row) > 5 else 0
                    avail = _safe_int(row[6], max(0, stock - in_use - damaged)) if len(row) > 6 else max(0, stock - in_use - damaged)
                    cost_center = str(row[7]).strip() if len(row) > 7 else "Ambas Carreras"
                else:
                    name = val_0
                    location = str(row[1]).strip() if len(row) > 1 else "BODEGA"
                    stock = _safe_int(row[2], 1) if len(row) > 2 else 1
                    in_use = _safe_int(row[3]) if len(row) > 3 else 0
                    damaged = _safe_int(row[4]) if len(row) > 4 else 0
                    avail = _safe_int(row[5], max(0, stock - in_use - damaged)) if len(row) > 5 else max(0, stock - in_use - damaged)
                    cost_center = str(row[6]).strip() if len(row) > 6 else "Ambas Carreras"

            if not name:
                continue

            # Auto category detection
            category = "EQUIPOS"
            lower_name = name.lower()
            if any(k in lower_name for k in ["resistencia", "cable", "conector", "sensor", "módulo", "diodo", "transistor", "led", "capacitor"]):
                category = "COMPONENTES"
            elif any(k in lower_name for k in ["multímetro", "osciloscopio", "fuente", "generador", "cautín", "estación"]):
                category = "EQUIPOS"
            elif any(k in lower_name for k in ["alicate", "destornillador", "pinza", "llave", "corta"]):
                category = "HERRAMIENTAS"
            elif any(k in lower_name for k in ["alcohol", "guantes", "mascarilla", "aceite", "limpiador"]):
                category = "INSUMOS"
            elif any(k in lower_name for k in ["frasco", "vaso", "pipeta", "tubo", "matraz", "probeta"]):
                category = "QUÍMICA Y VIDRIERÍA"

            existing = None
            if item_id:
                existing = db.query(models.Item).filter(models.Item.id == item_id).first()
            if not existing:
                existing = db.query(models.Item).filter(models.Item.name == name).first()

            if existing:
                existing.name = name
                existing.location = location
                existing.stock = stock
                existing.in_use = in_use
                existing.damaged = damaged
                existing.avail = avail
                existing.cost_center = cost_center
                existing.category = category
                updated_count += 1
            else:
                new_item = models.Item(
                    id=item_id,
                    name=name,
                    category=category,
                    location=location,
                    stock=stock,
                    in_use=in_use,
                    damaged=damaged,
                    avail=avail,
                    cost_center=cost_center
                )
                db.add(new_item)
                imported_count += 1
        except Exception:
            continue

    db.commit()
    return {"status": "success", "imported": imported_count, "updated": updated_count}

def get_shopping_list(db: Session):
    items = db.query(models.Item).all()
    shopping_items = []
    
    for item in items:
        # Reorder criteria: low stock (avail <= 2) OR damaged items needing replacement
        suggested_qty = 0
        reason = []
        
        if item.avail <= 2:
            suggested_qty += (5 - item.avail)
            reason.append("Stock Crítico / Bajo")
        if item.damaged > 0:
            suggested_qty += item.damaged
            reason.append(f"Reemplazo {item.damaged} dañados")

        if suggested_qty > 0:
            shopping_items.append({
                "id": item.id,
                "name": item.name,
                "location": item.location,
                "stock": item.stock,
                "avail": item.avail,
                "damaged": item.damaged,
                "cost_center": item.cost_center,
                "category": item.category,
                "suggested_qty": suggested_qty,
                "reason": " + ".join(reason)
            })
            
    shopping_items.sort(key=lambda x: (x["avail"], -x["suggested_qty"]))
    return shopping_items
