"""Rebuild 50 deterministic outputs after a policy/evidence change; no API calls."""
import json

from main import INPUT, OUTPUT, build, rows
from policy import decide
from validator import valid

orders = {x["order_id"]: x for group in rows("olist_orders_dataset.csv", "order_id").values() for x in group}
items, payments = rows("olist_order_items_dataset.csv", "order_id"), rows("olist_order_payments_dataset.csv", "order_id")
files = sorted(INPUT.glob("EC_*.json"))
if len(files) != 50: raise SystemExit(f"Expected 50 inputs, found {len(files)}")
OUTPUT.mkdir(exist_ok=True)
for path in files:
    case = json.loads(path.read_text(encoding="utf-8")); oid = case["customer_request"]["claimed_order_id"]
    doc = build(case, orders[oid], items.get(oid, []), payments.get(oid, []), decide(orders[oid], items.get(oid, []), payments.get(oid, [])))
    doc["assessment"]["confidence"] = 1.0
    valid(doc, path.name, orders, items, payments)
    (OUTPUT / path.name).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
print("Rebuilt 50 outputs with rule-specific evidence; no API calls")
