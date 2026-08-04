"""Test the parser with the user's REAL Excel file."""
import sys
sys.path.insert(0, '.')

from crud import _parse_file_to_rows, _detect_column_mapping

# Read the real file
with open(r'C:\Users\omarf\Downloads\Prueba_1.xlsx', 'rb') as f:
    file_bytes = f.read()

print("=== PARSING REAL EXCEL ===")
rows = _parse_file_to_rows(file_bytes, "Prueba_1.xlsx")

print(f"Total rows after cleanup: {len(rows)}")
print(f"Columns per row: {len(rows[0])}")

print(f"\nRow 0 (headers): {rows[0]}")
print(f"Row 1 (first data): {rows[1]}")
print(f"Row 2 (second data): {rows[2]}")

print("\n=== COLUMN DETECTION ===")
col_map = _detect_column_mapping(rows[0])
for k, v in col_map.items():
    header_name = rows[0][v] if v is not None and v < len(rows[0]) else "N/A"
    print(f"  {k:12s} -> col {v} = '{header_name}'")

print("\n=== FIRST 5 DATA ROWS (parsed values) ===")
from crud import _safe_int
for i, row in enumerate(rows[1:6]):
    item_id = _safe_int(row[col_map["id"]], default=None) if col_map["id"] is not None else None
    name = str(row[col_map["name"]]).strip() if col_map["name"] is not None else ""
    stock = _safe_int(row[col_map["stock"]]) if col_map["stock"] is not None else 0
    in_use = _safe_int(row[col_map["in_use"]]) if col_map["in_use"] is not None else 0
    damaged = _safe_int(row[col_map["damaged"]]) if col_map["damaged"] is not None else 0
    avail = _safe_int(row[col_map["avail"]]) if col_map["avail"] is not None else 0
    cost = str(row[col_map["cost_center"]]).strip() if col_map["cost_center"] is not None else ""
    print(f"  ID={item_id} | {name:30s} | stock={stock} in_use={in_use} damaged={damaged} avail={avail} | {cost}")

print("\n=== TEST COMPLETADO ===")
