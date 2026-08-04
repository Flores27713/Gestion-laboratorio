import urllib.request
import json

BASE = "https://gestion-laboratorio-98ze.onrender.com"

def get(path):
    req = urllib.request.Request(f"{BASE}{path}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("=== TEST 1: Dashboard ===")
try:
    data = get("/api/dashboard")
    print(f"  Total Items: {data['total_items']}")
    print(f"  Total Units: {data['total_units']}")
    print(f"  Available: {data['total_avail']}")
    print(f"  In Use: {data['total_in_use']}")
    print(f"  Damaged: {data['total_damaged']}")
    print(f"  Low Stock Items: {len(data.get('low_stock', []))}")
    print("  [OK] Dashboard funciona")
except Exception as e:
    print(f"  [FAIL] {e}")

print("\n=== TEST 2: Inventory ===")
try:
    items = get("/api/inventory")
    print(f"  Total articles: {len(items)}")
    if len(items) > 0:
        print(f"  First item: ID={items[0]['id']} Name={items[0]['name']} Stock={items[0]['stock']} Avail={items[0]['avail']}")
    print("  [OK] Inventory funciona")
except Exception as e:
    print(f"  [FAIL] {e}")

print("\n=== TEST 3: Search ===")
try:
    items = get("/api/inventory?search=arduino")
    print(f"  Arduino results: {len(items)}")
    print("  [OK] Search funciona")
except Exception as e:
    print(f"  [FAIL] {e}")

print("\n=== TEST 4: Shopping List ===")
try:
    items = get("/api/shopping-list")
    print(f"  Items needing reorder: {len(items)}")
    if len(items) > 0:
        print(f"  Top item: {items[0]['name']} - need +{items[0]['suggested_qty']} ({items[0]['reason']})")
    print("  [OK] Shopping list funciona")
except Exception as e:
    print(f"  [FAIL] {e}")

print("\n=== TEST 5: Stats ===")
try:
    data = get("/api/stats/semester")
    print(f"  Top items tracked: {len(data.get('top_items', []))}")
    print(f"  Cost centers: {list(data.get('cost_breakdown', {}).keys())}")
    print("  [OK] Stats funciona")
except Exception as e:
    print(f"  [FAIL] {e}")

print("\n=== TEST 6: CSV Export ===")
try:
    req = urllib.request.Request(f"{BASE}/api/export/csv")
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode("utf-8-sig")
        lines = content.strip().split("\n")
        print(f"  CSV lines (including header): {len(lines)}")
        print(f"  Header: {lines[0][:80]}...")
        print("  [OK] CSV Export funciona")
except Exception as e:
    print(f"  [FAIL] {e}")

print("\n=== TEST 7: Shopping List CSV Export ===")
try:
    req = urllib.request.Request(f"{BASE}/api/export/shopping-list-csv")
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode("utf-8-sig")
        lines = content.strip().split("\n")
        print(f"  Shopping CSV lines: {len(lines)}")
        print("  [OK] Shopping CSV Export funciona")
except Exception as e:
    print(f"  [FAIL] {e}")

print("\n=== TODAS LAS PRUEBAS COMPLETADAS ===")
