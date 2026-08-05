import csv
import json
import re
from decimal import Decimal
from pathlib import Path

from policy import decide

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
ID = re.compile(r"^(order:[0-9a-f]+|item:[0-9a-f]+:[0-9]+|payment:[0-9a-f]+:[0-9]+|seller:[0-9a-f]+|policy:[A-Z_]+)$")


def load(name, key):
    found = {}
    with (ROOT / "data" / name).open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f): found.setdefault(row[key], []).append(row)
    return found


def valid(doc, name, orders, item_map, payment_map):
    assert doc["case_id"] == name[:-5]
    assert doc["assessment"]["case_status"] in {"action_required", "no_action"}
    assert 0 <= doc["assessment"]["confidence"] <= 1
    assert len(doc["evidence_ids"]) <= 10 and all(ID.match(x) for x in doc["evidence_ids"])
    assert len(doc["root_cause_analysis"]["ranked_causes"]) <= 3
    assert len(doc["root_cause_analysis"]["responsible_parties"]) <= 3
    assert len(doc["resolution_actions"]) <= 5
    for values in doc["affected_entities"].values(): assert len(values) <= 5
    for key, value in doc["financial_resolution"].items():
        if key != "currency": assert round(value, 2) == value
    refund = doc["financial_resolution"]["recommended_refund_brl"]
    assert (refund > 0) == (doc["assessment"]["case_status"] == "action_required")
    oid = doc["affected_entities"]["order_ids"][0]
    assert oid in orders
    items, payments = item_map.get(oid, []), payment_map.get(oid, [])
    rule = decide(orders[oid], items, payments)
    assert doc["assessment"]["primary_issue"] == rule["issue"]
    assert doc["financial_resolution"] == {"currency": "BRL", "item_total_brl": rule["item_total"], "freight_total_brl": rule["freight_total"], "payment_total_brl": rule["payment_total"], "recommended_refund_brl": rule["refund"]}
    valid_items = {f"{oid}:{x['order_item_id']}" for x in items}
    valid_payments = {f"{oid}:{x['payment_sequential']}" for x in payments}
    valid_sellers = {x["seller_id"] for x in items}
    for value in doc["affected_entities"]["item_ids"]: assert value in valid_items
    for value in doc["affected_entities"]["payment_ids"]: assert value in valid_payments
    for value in doc["affected_entities"]["seller_ids"]: assert value in valid_sellers


def main():
    files = sorted(OUT.glob("EC_*.json")); assert len(files) == 50, f"Expected 50 outputs, got {len(files)}"
    orders = {x["order_id"]: x for group in load("olist_orders_dataset.csv", "order_id").values() for x in group}
    item_map = load("olist_order_items_dataset.csv", "order_id")
    payment_map = load("olist_order_payments_dataset.csv", "order_id")
    for path in files: valid(json.loads(path.read_text(encoding="utf-8")), path.name, orders, item_map, payment_map)
    print("OK: 50 output files passed structural validation")


if __name__ == "__main__": main()
