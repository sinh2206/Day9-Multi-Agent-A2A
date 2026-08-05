import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
INPUT = ROOT / "input"

def rows(name, key):
    result = {}
    with (DATA / name).open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            result.setdefault(row[key], []).append(row)
    return result

orders_map = {x["order_id"]: x for grp in rows("olist_orders_dataset.csv", "order_id").values() for x in grp}
items_map = rows("olist_order_items_dataset.csv", "order_id")
payments_map = rows("olist_order_payments_dataset.csv", "order_id")

from policy import decide

stats = {}
for path in sorted(INPUT.glob("EC_*.json")):
    case = json.loads(path.read_text(encoding="utf-8"))
    oid = case["customer_request"]["claimed_order_id"]
    order = orders_map[oid]
    its = items_map.get(oid, [])
    pays = payments_map.get(oid, [])
    rule = decide(order, its, pays)
    issue = rule["issue"]
    stats.setdefault(issue, {"count": 0, "has_items": 0})
    stats[issue]["count"] += 1
    if its:
        stats[issue]["has_items"] += 1

for issue, s in sorted(stats.items()):
    print(f"{issue}: {s['count']} cases, {s['has_items']} with items in CSV")
