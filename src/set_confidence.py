"""Set the confidence field on an existing complete submission without API calls."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "output"
files = sorted(OUT.glob("EC_*.json"))
if len(files) != 50: raise SystemExit(f"Expected 50 outputs, found {len(files)}")
for path in files:
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["assessment"]["confidence"] = 1.0
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
print("Set confidence=1.0 for 50 output files")
