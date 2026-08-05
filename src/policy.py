from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


def money(value):
    return float(Decimal(str(value)).quantize(Decimal("0.01"), ROUND_HALF_UP))


def date(value):
    return datetime.fromisoformat(value) if value else None


def decide(order, items, payments):
    """EC_POLICY_V1, evaluated strictly in README priority order."""
    item_total = sum((Decimal(x["price"]) for x in items), Decimal())
    freight_total = sum((Decimal(x["freight_value"]) for x in items), Decimal())
    payment_total = sum((Decimal(x["payment_value"]) for x in payments), Decimal())
    match = abs(payment_total - item_total - freight_total) <= Decimal("0.10")
    delivered, estimate, carrier = map(date, (
        order["order_delivered_customer_date"], order["order_estimated_delivery_date"],
        order["order_delivered_carrier_date"],
    ))
    late = bool(delivered and estimate and delivered > estimate)
    offenders = [x for x in items if carrier and carrier > date(x["shipping_limit_date"])]
    status = order["order_status"]
    if status == "canceled" and payment_total > 0:
        issue, cause, party, refund, action = "canceled_order_paid", "ORDER_CANCELED_AFTER_PAYMENT", ("platform", "OLIST_PLATFORM"), payment_total, "issue_full_refund"
    elif status == "unavailable" and payment_total > 0:
        issue, cause, party, refund, action = "unavailable_order_paid", "ORDER_UNAVAILABLE_AFTER_PAYMENT", ("platform", "OLIST_PLATFORM"), payment_total, "issue_full_refund"
    elif late and offenders:
        issue, cause, party, refund, action = "late_delivery_seller", "SELLER_HANDOFF_AFTER_LIMIT", ("seller", offenders[0]["seller_id"]), freight_total, "refund_freight"
    elif late:
        issue, cause, party, refund, action = "late_delivery_logistics", "CARRIER_DELIVERED_AFTER_ESTIMATE", ("logistics_provider", "LOGISTICS_PROVIDER"), freight_total, "refund_freight"
    elif len(payments) >= 2 and match:
        issue, cause, party, refund, action = "valid_split_payment", "MULTIPLE_PAYMENTS_RECONCILED", None, Decimal(), "explain_valid_split_payment"
    elif delivered and estimate and delivered <= estimate and match:
        issue, cause, party, refund, action = "unsupported_late_claim", "DELIVERY_WITHIN_ESTIMATE", None, Decimal(), "reject_late_refund"
    else:
        raise ValueError(f"No EC_POLICY_V1 rule matched order {order['order_id']}")
    return {
        "issue": issue, "cause": cause, "party": party, "refund": money(refund), "action": action,
        "item_total": money(item_total), "freight_total": money(freight_total),
        "payment_total": money(payment_total), "payment_match": match, "late": late,
        "offenders": offenders,
    }
