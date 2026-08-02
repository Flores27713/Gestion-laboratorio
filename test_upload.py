"""Diagnóstico: prueba de carga de archivo Excel/CSV al endpoint upload-csv"""
import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from app import app
from database import get_db, engine, Base
import json

client = TestClient(app)

# 1. Get current state
print("=== ESTADO ACTUAL DE LA BD ===")
res = client.get("/api/inventory?limit=5")
items = res.json()
print(f"Total items returned (first 5): {len(items)}")
for i in items[:5]:
    print(f"  ID={i['id']} | {i['name']} | stock={i['stock']} avail={i['avail']} in_use={i['in_use']} damaged={i['damaged']}")

# 2. Create a test CSV with modified values
print("\n=== CREANDO CSV DE PRUEBA ===")
test_csv = """ID;Nombre del Artículo;Ubicación Bodega;Stock Total;En Uso / Prestado;En Mal Estado;Stock Disponible;Centro de Costo
1;DISPLAY;BO-EST-01;20;3;0;17;Informática
2;LCD 16X2;BO-DE-B;25;5;2;18;Informática
"""
print(test_csv)

# 3. Upload
print("=== SUBIENDO CSV DE PRUEBA ===")
import io
files = {"file": ("test_inventario.csv", io.BytesIO(test_csv.encode("utf-8-sig")), "text/csv")}
res = client.post("/api/inventory/upload-csv", files=files)
print(f"Status: {res.status_code}")
print(f"Response: {res.json()}")

# 4. Check if data actually changed
print("\n=== VERIFICANDO CAMBIOS EN BD ===")
res = client.get("/api/inventory?limit=5")
items = res.json()
for i in items[:5]:
    if i['id'] in [1, 2]:
        print(f"  ID={i['id']} | {i['name']} | stock={i['stock']} avail={i['avail']} in_use={i['in_use']} damaged={i['damaged']}")
        if i['id'] == 1:
            if i['stock'] == 20 and i['avail'] == 17 and i['in_use'] == 3:
                print("    ✅ ID=1 ACTUALIZADO CORRECTAMENTE")
            else:
                print(f"    ❌ ID=1 NO SE ACTUALIZÓ - esperaba stock=20, avail=17, in_use=3")
        if i['id'] == 2:
            if i['stock'] == 25 and i['avail'] == 18 and i['in_use'] == 5 and i['damaged'] == 2:
                print("    ✅ ID=2 ACTUALIZADO CORRECTAMENTE")
            else:
                print(f"    ❌ ID=2 NO SE ACTUALIZÓ - esperaba stock=25, avail=18, in_use=5, damaged=2")

# 5. Now test with Excel (.xlsx)
print("\n=== PROBANDO CON ARCHIVO EXCEL (.xlsx) ===")
try:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["ID", "Nombre del Artículo", "Ubicación Bodega", "Stock Total", "En Uso / Prestado", "En Mal Estado", "Stock Disponible", "Centro de Costo"])
    ws.append([1, "DISPLAY", "BO-EST-01", 23, 0, 0, 23, "Informática"])  # restore original
    ws.append([2, "LCD 16X2", "BO-DE-B", 29, 1, 0, 28, "Informática"])   # restore original
    
    xlsx_buffer = io.BytesIO()
    wb.save(xlsx_buffer)
    xlsx_buffer.seek(0)
    
    files = {"file": ("test_inventario.xlsx", xlsx_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    res = client.post("/api/inventory/upload-csv", files=files)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.json()}")
    
    res = client.get("/api/inventory?limit=5")
    items = res.json()
    for i in items[:5]:
        if i['id'] in [1, 2]:
            print(f"  ID={i['id']} | {i['name']} | stock={i['stock']} avail={i['avail']} in_use={i['in_use']} damaged={i['damaged']}")
            if i['id'] == 1 and i['stock'] == 23 and i['avail'] == 23:
                print("    ✅ ID=1 RESTAURADO CORRECTAMENTE VÍA EXCEL")
            elif i['id'] == 1:
                print(f"    ❌ ID=1 NO SE RESTAURÓ VÍA EXCEL")
except Exception as e:
    print(f"❌ Error con Excel: {e}")

print("\n=== DIAGNÓSTICO COMPLETADO ===")
