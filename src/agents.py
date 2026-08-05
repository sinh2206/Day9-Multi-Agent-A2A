"""One free OpenRouter 9B call per case; deterministic agents preserve the quota."""
import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MODEL = "nvidia/nemotron-nano-9b-v2:free"  # 9B, within the course 10B limit.
URL = "https://openrouter.ai/api/v1/chat/completions"


def load_dotenv():
    path = Path(__file__).resolve().parents[1] / ".env"
    if not path.exists(): return
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()


def handoff(agent: str, facts: dict) -> dict:
    """Call the remote PolicyAgent; Python policy remains the source of truth."""
    key = os.getenv("OPENROUTER_API_KEY")
    if not key: raise RuntimeError("Missing OPENROUTER_API_KEY. Create .env from .env.example.")
    prompt = (f"You are {agent}. Audit only supplied e-commerce facts. Do not invent IDs, dates or money. "
              "Reply as compact JSON with verdict and audit_vi.\n" + json.dumps(facts, ensure_ascii=False, default=str))
    request = Request(URL, json.dumps({"model": MODEL, "temperature": 0, "max_tokens": 120,
        "messages": [{"role": "user", "content": prompt}]}).encode(),
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=90) as response: result = json.load(response)
            message = result["choices"][0].get("message") or {}
            text = message.get("content") or message.get("reasoning") or message.get("reasoning_content") or ""
            if isinstance(text, list): text = " ".join(x.get("text", "") if isinstance(x, dict) else str(x) for x in text)
            if not text: audit = {"verdict": "empty_content", "audit_vi": "API không trả content; policy deterministic được giữ nguyên."}
            else:
                try: audit = json.loads(text)
                except (json.JSONDecodeError, TypeError): audit = {"verdict": "unparsed", "audit_vi": str(text)}
            time.sleep(float(os.getenv("OPENROUTER_REQUEST_DELAY", "1")))
            return {"agent": agent, "mode": "remote_llm", "model": MODEL, "facts": facts, "audit": audit}
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503} or attempt == 2:
                raise RuntimeError(f"OpenRouter HTTP {error.code}: {error.read().decode(errors='replace')}") from error
        except URLError as error:
            if attempt == 2: raise RuntimeError(f"OpenRouter unavailable: {error.reason}") from error
        time.sleep(2 ** attempt)
