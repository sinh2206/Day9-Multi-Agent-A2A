"""Check payment ordering and other potential issues."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
INPUT = ROOT / "input"

def load_csv(name, key):
    result = {}
    with (DATA / name).open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            result.setdefault(row[key], []).append(row)
    return result

pays_map = load_csv("olist_order_payments_dataset.csv", "order_id")
items_map = load_csv("olist_order_items_dataset.csv", "order_id")

# Check payment ordering in valid_split_payment cases
for path in sorted(INPUT.glob("EC_*.json")):
    case = json.loads(path.read_text(encoding="utf-8"))
    oid = case["customer_request"]["claimed_order_id"]
    pays = pays_map.get(oid, [])
    if len(pays) >= 2:
        seqs = [p["payment_sequential"] for p in pays]
        print(f"{path.name}: order_id={oid[:8]}... payment_sequentials={sorted(seqs)}, types={[p['payment_type'] for p in pays]}")

print()
print("=== Item IDs ordering check (multi-item cases) ===")
for path in sorted(INPUT.glob("EC_*.json")):
    case = json.loads(path.read_text(encoding="utf-8"))
    oid = case["customer_request"]["claimed_order_id"]
    its = items_map.get(oid, [])
    if len(its) >= 2:
        ids = [x["order_item_id"] for x in its]
        print(f"{path.name}: {len(its)} items, item_ids={ids}")
