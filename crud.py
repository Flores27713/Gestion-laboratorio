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
