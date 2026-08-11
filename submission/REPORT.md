# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: Nhóm Day 13 - K4
- Repository URL: https://github.com/Tiendat051205/Day13-K4-Observability
- Commit SHA cuối:26c9fc04f298f2a351c2d89dd238da56422cbb74
- Thành viên và vai trò:
  1. Đoàn Ngọc Linh (2A202601762) - Tech Lead/Backend Engineer (Phụ trách CP1: Logging & PII)
  2. Nguyễn Tiến Đạt (2A202601850) - SRE & Alerts Engineer (Phụ trách CP2: Tracing, SLO & Alert)
  3. Nguyễn Công Đạt (2A202601526) - QA & Chief Investigator (Phụ trách CP3: Dashboard, Incident Response & Report)

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: Baseline (CP0) = 30/100 (41 records, 40 missing required fields, 40 missing enrichment, 0 unique correlation ID, 0 PII leak detected) → CP1 = 100/100 (20 records, 0 missing required fields, 0 missing enrichment, 10 unique correlation ID, 0 PII leak detected)
- Tổng số traces: ~50 traces (Đã bao gồm các Trace từ lệnh load test CP0, CP1 và 5 request từ CP3 Challenge).
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: Vẽ local qua script `view_dashboard.py` (đọc trực tiếp từ file `data/logs.jsonl`).

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/cp1_correlation_pii.json` — cặp log `request_received`/`response_sent` cùng `correlation_id: "req-0049b068"`
- Evidence PII redaction: cùng file trên, `message_preview` chứa `[REDACTED_EMAIL]` thay vì email thật
- Evidence trace waterfall: `submission/evidence/trace_incident.png`
- Giải thích một span đáng chú ý: Trong file `trace_incident.png`, span `run` của khâu RAG mất tới **3.56s** (bình thường < 1s). Đây là điểm thắt cổ chai (bottleneck) trực tiếp gây ra độ trễ cao của toàn hệ thống khi bị tiêm lỗi `rag_slow`.

### Câu hỏi phản biện CP1

**Khác biệt lớn nhất giữa log baseline (CP0) và log sau CP1**: Ở baseline, mọi request đều có `correlation_id = "MISSING"` — không thể trace một request cụ thể xuyên suốt các log event (`request_received` → `response_sent`/`request_failed`). Sau CP1, mỗi request có một `correlation_id` duy nhất (`req-<8-hex>`) được bind vào toàn bộ log của request đó qua `structlog` contextvars, nên có thể lọc/join tất cả log liên quan đến một request chỉ bằng ID này — điều kiện tiên quyết để debug production khi có hàng nghìn request đồng thời. Ngoài ra baseline thiếu hẳn các trường enrichment (`user_id_hash`, `session_id`, `feature`, `model`, `env`) và PII (email, phone) còn xuất hiện nguyên văn; CP1 khắc phục cả hai.

**Vì sao `clear_contextvars()` ở đầu middleware là bắt buộc**: `structlog` contextvars dựa trên `ContextVar`, được gắn với context của task/thread xử lý request hiện tại. Vì server xử lý nhiều request đồng thời (đặc biệt khi có concurrency, như `ThreadPoolExecutor` trong `load_test.py --concurrency`), nếu không clear ở đầu mỗi request thì `correlation_id` và các field enrichment của request trước có thể còn sót lại và bị gán nhầm vào log của request sau — dẫn đến sai lệch khi debug (log lẫn giữa hai request khác nhau) hoặc rò rỉ thông tin của user này sang log của user khác.

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: `production`
- Version/label candidate: `staging`
- Trace ID của mỗi version: v1 (production): `11f808a2cf2b9cdcba8d1b4497f35d03` | v2 (staging): `b40183db0ff9e9178c283ebe2695060e`
- Bằng chứng đổi label hoặc rollback: `submission/evidence/prompt_rollback.png`

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: Đạt tiêu chuẩn hợp lệ (`HỢP LỆ: 6/6 panel có trong dashboard contract.`)
- Evidence dashboard: `submission/evidence/dashboard_incident.png`
- SLO đã chọn và lý do: **P95 Latency < 2000ms**. Lý do: Dựa trên log baseline CP0, thời gian phản hồi trung bình của API nằm trong khoảng 1000ms - 1100ms. Ngưỡng 2000ms (gấp đôi) là mức an toàn để đảm bảo trải nghiệm người dùng không bị gián đoạn, đồng thời đủ nhạy để phát hiện sự cố.
- Alert rules và runbook: Đã được định nghĩa trong `config/alert_rules.yaml` và lưu hồ sơ xử lý tại `docs/alerts.md`.

## 6. Điều tra challenge

- Challenge ID: `day13-k4-observability-v1` (Thuộc Cohort: K4)
- Triệu chứng từ metrics: Độ trễ (Client-side Latency) tăng vọt lên **18,296.3ms** (hơn 18 giây) dưới tải `concurrency = 5`, vi phạm nghiêm trọng SLO 2000ms.
- Trace ID liên quan: `af385074519a776297051bae0038ccae` (Thuộc Session: `k4-challenge-s01`)
- Log line/correlation ID liên quan: `req-0eda538e`
- Root cause: Bằng chứng từ log cho thấy hệ thống kích hoạt incident `rag_slow` lúc 08:48:07Z. Sự cố này làm module truy xuất dữ liệu (RAG) bị nghẽn, thời gian xử lý nội server của mỗi request đội lên > 3.5s. Do API server xử lý đồng bộ (synchronous), 5 request gửi tới cùng lúc tạo thành hàng đợi, gây ra hiệu ứng Domino (request sau phải đợi request trước). Request cuối cùng phải chờ gần 18 giây mới được xử lý xong.
- Fix action: Gọi API ngắt cờ sự cố (`python scripts/inject_incident.py --scenario rag_slow --disable`) để khôi phục hiệu năng ngay lập tức.
- Preventive measure:
  1. Cấu hình Timeout cứng (VD: 1.5s) cho truy vấn Vector DB/Retrieval, nếu vượt quá sẽ fallback về câu trả lời mặc định.
  2. Tối ưu kiến trúc bằng cách áp dụng xử lý bất đồng bộ (`async`/`await`) tại API để không block server khi phải I/O chờ dữ liệu, hoặc gắn Circuit Breaker để ngắt tải khi DB có dấu hiệu suy giảm hiệu năng.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên      | Phần việc                                                                                                                                                  | Commit/PR         | Điều đã học                                                                                                                                    |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Đoàn Ngọc Linh  | **CP1:** Xây dựng Middleware sinh UUID, thiết lập contextvars cho enrichment logs, viết hàm Regex che PII. Đạt 100/100 Validator.                          | Tham chiếu `main` | Hiểu cơ chế phân lập log trong môi trường đa luồng qua ContextVar; Tầm quan trọng của dữ liệu sạch (PII) trước khi đẩy lên cloud.              |
| Nguyễn Tiến Đạt | **CP2:** Setup Langfuse Cloud, gắn decorator vào code AI, thiết lập SLO trong file yaml và xây dựng Alert Runbook.                                         | Tham chiếu `main` | Cách cắm trace vào luồng thực thi phức tạp; Tư duy vận hành SRE khi thiết lập ngưỡng cảnh báo (SLO/Alert) có cơ sở từ thực tế.                 |
| Nguyễn Công Đạt | **CP3:** Chạy Load Test tạo Challenge, trực quan hóa Dashboard từ `logs.jsonl`, truy vết từ Metrics -> Traces -> Logs để tìm Root Cause; Tổng hợp báo cáo. | Tham chiếu `main` | Nắm được toàn bộ quy trình Post-mortem thực tế: Từ lúc nhận tín hiệu nhiễu (Metrics) -> Khoanh vùng vùng lỗi (Traces) -> Chốt thủ phạm (Logs). |
