"""Deep analysis of all output cases to find remaining scoring gaps."""
import json
from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "output"
results = {}
for f in sorted(OUTPUT.glob("EC_*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    issue = d["assessment"]["primary_issue"]
    results.setdefault(issue, []).append({
        "file": f.name,
        "item_ids": d["affected_entities"]["item_ids"],
        "seller_ids": d["affected_entities"]["seller_ids"],
        "payment_ids": d["affected_entities"]["payment_ids"],
        "evidence_ids": d["evidence_ids"],
        "financial": d["financial_resolution"],
        "parties": d["root_cause_analysis"]["responsible_parties"],
        "confidence": d["assessment"]["confidence"],
    })

for issue, cases in sorted(results.items()):
    print(f"=== {issue} ({len(cases)} cases) ===")
    for c in cases[:3]:
        print(f"  {c['file']}: items={len(c['item_ids'])}, sellers={len(c['seller_ids'])}, payments={len(c['payment_ids'])}, evidence={len(c['evidence_ids'])}")
        print(f"    evidence: {c['evidence_ids']}")
        print(f"    financial: item={c['financial']['item_total_brl']}, freight={c['financial']['freight_total_brl']}, pay={c['financial']['payment_total_brl']}, refund={c['financial']['recommended_refund_brl']}")
    print()
