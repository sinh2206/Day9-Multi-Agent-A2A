# Multi-Agent A2A Architecture

## Mục tiêu

Hệ thống xử lý 50 khiếu nại Olist. Coordinator nhận `input/EC_xxx.json`, lookup `claimed_order_id` trong CSV, điều phối agent theo domain, áp `EC_POLICY_V1` và ghi `output/EC_xxx.json` có evidence.

## Luồng A2A và quota API

```text
input + CSV lookup
       |
       +-> OrderSellerAgent (deterministic) --+
       +-> PaymentAgent     (deterministic) --+-> PolicyAgent (OpenRouter 9B)
       +-> DeliveryAgent    (deterministic) --+             |
                                                       VerifierAgent (deterministic)
                                                                  |
                                     output/EC_xxx.json + trace.jsonl + metadata.json
```

OpenRouter free giới hạn 50 request/ngày, nên mỗi case chỉ dùng **một** remote call ở `PolicyAgent`: `nvidia/nemotron-nano-9b-v2:free` (9B, không vượt giới hạn 10B). Ba domain agent có contract riêng, join/kiểm facts trực tiếp từ CSV và handoff facts cho PolicyAgent; VerifierAgent join lại CSV trước khi ghi file. Đây không phải một prompt xử lý toàn bộ dữ liệu: domain analysis, policy calculation, verification và LLM audit được tách thành các bước độc lập. Mỗi case vẫn có năm trace event, tổng 250 handoff.

## Agent, quyền truy cập và contract

| Agent | Mode | Facts được cấp | Handoff |
|---|---|---|---|
| `OrderSellerAgent` | Deterministic | Status, item, seller, shipping limit | Order/item facts đã kiểm CSV |
| `PaymentAgent` | Deterministic | Payment rows, item + freight totals | Payment reconciliation |
| `DeliveryAgent` | Deterministic | Customer/estimate/carrier date | Lateness và seller vi phạm |
| `PolicyAgent` | OpenRouter API, Nemotron 9B | Ba handoff trước và candidate rule | Audit JSON tiếng Việt; không được tạo facts |
| `VerifierAgent` | Deterministic | Draft output và source CSV | Hard-gate evidence, tiền, issue, refund/action |

`src/policy.py` là nguồn quyết định: timestamp, BRL `Decimal`, thứ tự policy và evidence IDs không phụ thuộc LLM. `src/agents.py` chỉ gửi PolicyAgent một request/case, retry ngắn cho lỗi tạm thời và đọc `OPENROUTER_API_KEY` từ `.env`; key không được commit. `src/validator.py` kiểm độc lập 50 file sau khi chạy.

## Artifacts và kiểm chứng

- `output/EC_001.json` … `EC_050.json`: 50 quyết định.
- `logging/trace.jsonl` và `trace.jsonl`: 250 handoff mới nhất.
- `logging/metadata.json` và `metadata.json`: model 9B, OpenRouter API, quota design.
- `python src/validator.py`: hard gate schema, evidence, policy và financial resolution.
