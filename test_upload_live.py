"""
Test de upload contra el servidor LIVE en Render.
1. Lee el estado actual del item ID=1 (DISPLAY)
2. Sube un CSV que cambia su stock
3. Verifica si realmente cambio
4. Restaura el valor original
"""
import urllib.request
import json
import io

BASE = "https://gestion-laboratorio-98ze.onrender.com"

def api_get(path):
    req = urllib.request.Request(f"{BASE}{path}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def api_upload(filename, file_bytes, content_type):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    
    req = urllib.request.Request(
        f"{BASE}/api/inventory/upload-csv",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

# STEP 1: Read current state of item ID=1
print("=== PASO 1: Estado actual del item ID=1 ===")
items = api_get("/api/inventory?search=DISPLAY")
item1 = [i for i in items if i["id"] == 1][0]
original_stock = item1["stock"]
original_avail = item1["avail"]
original_in_use = item1["in_use"]
print(f"  DISPLAY: stock={original_stock}, avail={original_avail}, in_use={original_in_use}")

# STEP 2: Upload CSV that changes stock to 999
print("\n=== PASO 2: Subiendo CSV con stock=999 para DISPLAY ===")
test_csv = "ID;Nombre del Artículo;Ubicación Bodega;Stock Total;En Uso / Prestado;En Mal Estado;Stock Disponible;Centro de Costo\n"
test_csv += "1;DISPLAY;BO-EST-01;999;0;0;999;Informática\n"
csv_bytes = test_csv.encode("utf-8-sig")

result = api_upload("test_upload.csv", csv_bytes, "text/csv")
print(f"  Response: {result}")

# STEP 3: Verify if it actually changed
print("\n=== PASO 3: Verificando si cambio ===")
items = api_get("/api/inventory?search=DISPLAY")
item1_after = [i for i in items if i["id"] == 1][0]
print(f"  DISPLAY ahora: stock={item1_after['stock']}, avail={item1_after['avail']}, in_use={item1_after['in_use']}")

if item1_after["stock"] == 999:
    print("  [OK] EL UPLOAD FUNCIONA CORRECTAMENTE - el stock cambio a 999")
else:
    print(f"  [FAIL] El stock NO cambio. Sigue en {item1_after['stock']}")

# STEP 4: Restore original values
print("\n=== PASO 4: Restaurando valores originales ===")
restore_csv = "ID;Nombre del Artículo;Ubicación Bodega;Stock Total;En Uso / Prestado;En Mal Estado;Stock Disponible;Centro de Costo\n"
restore_csv += f"1;DISPLAY;BO-EST-01;{original_stock};{original_in_use};0;{original_avail};Informática\n"
restore_bytes = restore_csv.encode("utf-8-sig")

result2 = api_upload("restore.csv", restore_bytes, "text/csv")
print(f"  Restore response: {result2}")

items = api_get("/api/inventory?search=DISPLAY")
item1_restored = [i for i in items if i["id"] == 1][0]
print(f"  DISPLAY restaurado: stock={item1_restored['stock']}, avail={item1_restored['avail']}")

print("\n=== TEST COMPLETADO ===")
