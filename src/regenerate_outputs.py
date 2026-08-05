"""Regenerate deterministic outputs after a presentation-only policy fix; no API call."""
import json
from pathlib import Path

from main import INPUT, OUTPUT, build, rows
from policy import decide
from validator import valid

orders = {x["order_id"]: x for group in rows("olist_orders_dataset.csv", "order_id").values() for x in group}
items = rows("olist_order_items_dataset.csv", "order_id")
payments = rows("olist_order_payments_dataset.csv", "order_id")
OUTPUT.mkdir(exist_ok=True)
for path in sorted(INPUT.glob("EC_*.json")):
    case = json.loads(path.read_text(encoding="utf-8")); oid = case["customer_request"]["claimed_order_id"]
    doc = build(case, orders[oid], items.get(oid, []), payments.get(oid, []), decide(orders[oid], items.get(oid, []), payments.get(oid, [])))
    valid(doc, path.name, orders, items, payments)
    (OUTPUT / path.name).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
print("Regenerated and validated 50 outputs without an API call.")
