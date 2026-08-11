# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: Baseline (CP0) = 30/100 (41 records, 40 missing required fields, 40 missing enrichment, 0 unique correlation ID, 0 PII leak detected) → CP1 = 100/100 (20 records, 0 missing required fields, 0 missing enrichment, 10 unique correlation ID, 0 PII leak detected)
- Tổng số traces:
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/cp1_correlation_pii.json` — cặp log `request_received`/`response_sent` cùng `correlation_id: "req-0049b068"`
- Evidence PII redaction: cùng file trên, `message_preview` chứa `[REDACTED_EMAIL]` thay vì email thật
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

### Câu hỏi phản biện CP1

**Khác biệt lớn nhất giữa log baseline (CP0) và log sau CP1**: Ở baseline, mọi request đều có `correlation_id = "MISSING"` — không thể trace một request cụ thể xuyên suốt các log event (`request_received` → `response_sent`/`request_failed`). Sau CP1, mỗi request có một `correlation_id` duy nhất (`req-<8-hex>`) được bind vào toàn bộ log của request đó qua `structlog` contextvars, nên có thể lọc/join tất cả log liên quan đến một request chỉ bằng ID này — điều kiện tiên quyết để debug production khi có hàng nghìn request đồng thời. Ngoài ra baseline thiếu hẳn các trường enrichment (`user_id_hash`, `session_id`, `feature`, `model`, `env`) và PII (email, phone) còn xuất hiện nguyên văn; CP1 khắc phục cả hai.

**Vì sao `clear_contextvars()` ở đầu middleware là bắt buộc**: `structlog` contextvars dựa trên `ContextVar`, được gắn với context của task/thread xử lý request hiện tại. Vì server xử lý nhiều request đồng thời (đặc biệt khi có concurrency, như `ThreadPoolExecutor` trong `load_test.py --concurrency`), nếu không clear ở đầu mỗi request thì `correlation_id` và các field enrichment của request trước có thể còn sót lại và bị gán nhầm vào log của request sau — dẫn đến sai lệch khi debug (log lẫn giữa hai request khác nhau) hoặc rò rỉ thông tin của user này sang log của user khác.

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| | | | |
