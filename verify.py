"""
Script de Verificación de Integridad y Lógica de Negocio de LabInventory Pro (FastAPI + SQLite)
"""
from fastapi.testclient import TestClient
from app import app
from database import get_db

client = TestClient(app)

def test_system():
    print("=== INICIANDO VERIFICACION DE LABINVENTORY PRO (PYTHON / FASTAPI) ===")

    # 1. Probar GET /api/dashboard
    response = client.get("/api/dashboard")
    assert response.status_code == 200, f"Error en /api/dashboard: {response.text}"
    dash = response.json()

    print(f"[OK] Total Articulos Precargados: {dash['total_items']}")
    print(f"[OK] Unidades Fisicas Totales: {dash['total_units']}")
    print(f"[OK] Stock Disponible Inicial: {dash['total_avail']}")
    print(f"[OK] En Uso / Prestado Inicial: {dash['total_in_use']}")

    assert dash['total_items'] == 197, f"Esperados 197 articulos, se obtuvieron {dash['total_items']}"

    # 2. Probar GET /api/inventory
    resp_inv = client.get("/api/inventory?search=Arduino")
    assert resp_inv.status_code == 200
    arduinos = resp_inv.json()
    print(f"[OK] Busqueda por 'Arduino': {len(arduinos)} articulos encontrados.")

    # 3. Probar emision de Ficha de Solicitud (Descuento automatico de stock)
    arduino_uno = next(i for i in arduinos if "Arduino Uno" in i["name"])
    initial_avail = arduino_uno["avail"]
    initial_in_use = arduino_uno["in_use"]

    req_payload = {
        "applicant": "Diego Torres",
        "rut": "20.987.654-3",
        "career": "Informatica",
        "course": "Robotica Avanzada",
        "professor": "Ing. Carlos Mendoza",
        "return_date": "2026-08-15",
        "items": [
            {"item_id": arduino_uno["id"], "quantity": 2}
        ]
    }

    resp_req = client.post("/api/requisitions", json=req_payload)
    assert resp_req.status_code == 201, f"Error al emitir ficha: {resp_req.text}"
    req_data = resp_req.json()
    print(f"[OK] Ficha Emitida con Codigo: {req_data['code']} para {req_data['applicant']}")

    # Check updated stock for Arduino Uno
    resp_inv_after = client.get(f"/api/inventory?search=Arduino Uno")
    updated_arduino = resp_inv_after.json()[0]
    print(f"[OK] Stock Disponible de Arduino Uno descontado: de {initial_avail} -> {updated_arduino['avail']} (Solicitados: 2)")
    print(f"[OK] En Uso incrementado: de {initial_in_use} -> {updated_arduino['in_use']}")

    assert updated_arduino["avail"] == initial_avail - 2
    assert updated_arduino["in_use"] == initial_in_use + 2

    # 4. Probar Devolucion de Materiales
    resp_return = client.post(f"/api/requisitions/{req_data['id']}/return")
    assert resp_return.status_code == 200
    returned_data = resp_return.json()
    assert returned_data["status"] == "DEVUELTO"
    print(f"[OK] Solicitud {returned_data['code']} devuelta con exito.")

    # Check restored stock
    resp_inv_restored = client.get(f"/api/inventory?search=Arduino Uno")
    restored_arduino = resp_inv_restored.json()[0]
    assert restored_arduino["avail"] == initial_avail
    print(f"[OK] Stock de Arduino Uno restaurado a {restored_arduino['avail']}.")

    print("=== TODAS LAS PRUEBAS AUTOMATICAS PASARON CON EXITO (100% FUNCIONAL) ===")

if __name__ == "__main__":
    test_system()
