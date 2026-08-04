import os
import csv
import io
from typing import List, Optional
from fastapi import FastAPI, Depends, Request, HTTPException, Response, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
import schemas
import crud
from database import engine, get_db, Base
from seed import seed_database

# Create SQLite tables
Base.metadata.create_all(bind=engine)

# Seed database with initial 197 items
db_session = next(get_db())
try:
    seed_database(db_session)
finally:
    db_session.close()

app = FastAPI(
    title="Gestión de Laboratorio",
    description="Sistema de gestión de inventario y Ficha Digital de Solicitud para Laboratorio en FastAPI + SQLite.",
    version="2.0.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ==========================================
# UI HTML ENDPOINT
# ==========================================
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# ==========================================
# REST API ENDPOINTS
# ==========================================
@app.get("/api/inventory", response_model=List[schemas.ItemResponse])
def read_inventory(
    search: str = "",
    category: str = "TODAS",
    location: str = "TODAS",
    cost_center: str = "TODOS",
    db: Session = Depends(get_db)
):
    items = crud.get_items(db, search=search, category=category, location=location, cost_center=cost_center)
    return [i.to_dict() for i in items]

@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    return crud.get_dashboard_metrics(db)

@app.post("/api/requisitions", response_model=schemas.RequisitionResponse, status_code=201)
def create_requisition(req: schemas.RequisitionCreate, db: Session = Depends(get_db)):
    db_req = crud.create_requisition(db, req)
    return db_req.to_dict()

@app.get("/api/requisitions", response_model=List[schemas.RequisitionResponse])
def get_requisitions(db: Session = Depends(get_db)):
    reqs = db.query(models.Requisition).order_by(models.Requisition.id.desc()).all()
    return [r.to_dict() for r in reqs]

@app.post("/api/requisitions/{requisition_id}/return", response_model=schemas.RequisitionResponse)
def return_requisition_items(requisition_id: int, db: Session = Depends(get_db)):
    returned_req = crud.return_requisition(db, requisition_id)
    return returned_req.to_dict()

@app.get("/api/stats/semester")
def get_stats(db: Session = Depends(get_db)):
    return crud.get_semester_stats(db)

@app.post("/api/inventory/upload-csv")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls', '.txt')):
        raise HTTPException(status_code=400, detail="Por favor suba un archivo válido de Excel (.xlsx, .xls) o CSV (.csv)")
    contents = await file.read()
    return crud.import_file_data(db, contents, file.filename)

@app.post("/api/inventory/preview-upload")
async def preview_upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls', '.txt')):
        raise HTTPException(status_code=400, detail="Formato no soportado")
    contents = await file.read()
    return crud.preview_file_data(contents, file.filename)

@app.get("/api/export/csv")
def export_csv(db: Session = Depends(get_db)):
    items = crud.get_items(db)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    writer.writerow(["ID", "Nombre del Artículo", "Ubicación Bodega", "Stock Total", "En Uso / Prestado", "En Mal Estado", "Stock Disponible", "Centro de Costo", "Categoría"])
    for i in items:
        writer.writerow([i.id, i.name, i.location, i.stock, i.in_use, i.damaged, i.avail, i.cost_center, i.category])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=inventario_laboratorio_actualizado.csv"}
    )

@app.get("/api/shopping-list")
def get_shopping_list(db: Session = Depends(get_db)):
    return crud.get_shopping_list(db)

@app.get("/api/export/shopping-list-csv")
def export_shopping_list_csv(db: Session = Depends(get_db)):
    shopping_items = crud.get_shopping_list(db)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    writer.writerow(["ID", "Nombre Artículo", "Ubicación", "Stock Disp.", "Dañados", "Cantidad Sugerida a Comprar", "Motivo Reposición", "Centro de Costo"])
    for s in shopping_items:
        writer.writerow([s["id"], s["name"], s["location"], s["avail"], s["damaged"], s["suggested_qty"], s["reason"], s["cost_center"]])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=listado_de_compras_laboratorio.csv"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
