# Member Role Report — Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Đinh Văn Sinh |
| MSSV | 2A202601613 |
| Khóa/Lớp | K3 |
| Vai trò chính | Coordinator, Policy và Validation Engineer |
| Ngày hoàn thành | 2026-08-05 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Điều phối A2A và API | `src/main.py`, `src/agents.py` | Case JSON, CSV và handoff trước | 5 trace event/case; 1 API call/case | Hoàn thành mã nguồn; chờ chạy runtime |
| Policy và validation | `src/policy.py`, `src/validator.py` | Order, item, payment rows; output JSON | Quyết định EC_POLICY_V1 và hard gate | Hoàn thành mã nguồn; chờ chạy runtime |
| Kiến trúc và metadata | `architecture.md`, `logging/metadata.json` | Thiết kế và model config | Tài liệu nộp bài | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Phân tích dữ liệu đề bài | Pipeline chung | Xác định 3 CSV lõi và quy tắc evidence ID |
| Thiết kế trong quota free API | Runtime OpenRouter | Giảm từ 250 xuống 50 request bằng một LLM call/case |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Tách năm agent có handoff tuần tự | `src/main.py`, `src/agents.py` | Domain handoff, policy audit, verifier event | `logging/trace.jsonl` có 250 dòng sau run |
| Áp policy bằng code xác định | `src/policy.py` | Sáu primary issue đúng EC_POLICY_V1 | Dry-run 50 input: 8/8/8/8/9/9 theo sáu nhóm |
| Chặn output không khớp CSV | `src/validator.py` | Kiểm ID, tiền, issue, refund và schema | `python src/validator.py` |

Artifact cụ thể là policy dry-run: `late_delivery_seller` 8, `late_delivery_logistics` 8, `canceled_order_paid` 8, `unavailable_order_paid` 8, `valid_split_payment` 9 và `unsupported_late_claim` 9. Đây là kiểm tra logic, không phải khẳng định runtime API đã hoàn tất.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Một phản ánh không đủ để quy trách nhiệm. Pipeline phải join order-item-payment, so sánh mốc giao, đối soát BRL và chỉ đưa evidence có thể dựng lại từ CSV. Đồng thời OpenRouter free có 50 request/ngày, trong khi 50 case × 5 LLM agent sẽ vượt quota.

### Cách triển khai

`main.py` tải CSV một lần, sau đó OrderSellerAgent, PaymentAgent và DeliveryAgent tạo facts theo domain bằng code. Chỉ PolicyAgent gọi `nvidia/nemotron-nano-9b-v2:free` qua OpenRouter để audit handoff; đây là model 9B, đúng giới hạn đề bài. `policy.py` dùng `Decimal`, timestamp và EC_POLICY_V1 làm nguồn quyết định; LLM không có quyền sửa số tiền, ID hoặc rule. VerifierAgent dùng `validator.valid()` để join lại CSV trước khi output được ghi.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | `input/EC_xxx.json`; CSV orders, order_items, order_payments |
| Output | `output/EC_xxx.json`; trace JSONL và metadata |
| Module phụ thuộc | OpenRouter API, `OPENROUTER_API_KEY` trong `.env`, Nemotron Nano 9B V2 free |
| Module sử dụng output | Validator, leaderboard và ZIP nộp bài |
| Điều kiện lỗi cần xử lý | Thiếu API key, HTTP 429, order ID thiếu, policy không match, evidence sai, output không đủ 50 file |

### Cách xác minh

```powershell
Copy-Item .env.example .env
# Điền OPENROUTER_API_KEY vào .env
python -m py_compile src/agents.py src/policy.py src/main.py src/validator.py
python src/main.py
python src/validator.py
```

- **Kết quả mong đợi:** 50 JSON, 250 handoff, 50 remote calls và validator in `OK: 50 output files passed structural validation`.
- **Kết quả thực tế:** Đã kiểm tra cú pháp và dry-run policy; cần ghi kết quả runtime API sau khi chạy.
- **Artifact/log:** `output/`, `logging/trace.jsonl`, `logging/metadata.json`; không chứa secret.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Chạy 5 API agent × 50 case cần 250 request nhưng OpenRouter free chỉ cho 50 request/ngày.
- **Các phương án đã cân nhắc:** (1) Gọi 5 LLM agent/case; (2) dùng deterministic domain agents và chỉ gọi LLM PolicyAgent một lần/case.
- **Phương án đã chọn:** Phương án 2 với `nvidia/nemotron-nano-9b-v2:free`.
- **Lý do:** Giữ handoff, phân quyền domain và validator độc lập, nhưng nằm trong quota free và không để model bịa dữ liệu.
- **Bằng chứng:** Dry-run phân loại toàn bộ 50 input vào sáu nhóm hợp lệ, không có case không match policy.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi:** Thiết kế ban đầu cần 250 request, vượt 50 request/ngày của OpenRouter free.
- **Lệnh hoặc bước tái hiện:** Chạy 50 case với 5 remote agent/case.
- **Nguyên nhân gốc:** Quota free tính theo tổng request, không theo số case.
- **Cách xử lý:** Chuyển 3 domain agent và VerifierAgent sang deterministic; chỉ PolicyAgent gọi Nemotron 9B, có retry cho lỗi tạm thời.
- **Cách xác minh sau khi sửa:** Kiểm `remote_calls_per_case: 1` trong metadata và 250 trace event gồm 50 event `remote_llm`.
- **Điều học được:** Thiết kế multi-agent cần tối ưu theo quota mà vẫn giữ contract/handoff có thể audit.

## 7. Hiểu biết về luồng end-to-end

1. Input cung cấp `claimed_order_id`; Coordinator join orders, items và payments để tạo facts.
2. Ba domain agent độc lập kiểm status/item-seller, thanh toán và delivery rồi handoff facts.
3. PolicyAgent 9B nhận các handoff để audit candidate policy; code áp thứ tự EC_POLICY_V1 để giữ quyết định tái lập được.
4. VerifierAgent và validator join lại CSV, chặn evidence hoặc financial resolution sai trước khi ghi output.
5. Run thành công có 50 JSON, 250 trace event, 50 remote call và metadata ghi model 9B; chỉ `output/` được zip để nộp.

## 8. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng runtime.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đinh Văn Sinh
**Ngày xác nhận:** 2026-08-05
