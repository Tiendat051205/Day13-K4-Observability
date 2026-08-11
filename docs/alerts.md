# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: high_latency_p95
- Severity: warning
- SLI/SLO liên quan: latency_p95_ms (Target: P95 < 3000ms)
- Điều kiện và thời gian duy trì: latency_p95 > 3000ms kéo dài trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng phản hồi ứng dụng chạy rất chậm, thời gian chờ câu trả lời từ AI kéo dài gây trải nghiệm xấu.
- Ba bước kiểm tra đầu tiên:
  1. Mở Dashboard kiểm tra panel Latency xem P95 vọt lên ở bước nào (LLM Generation hay Retrieval/RAG).
  2. Mở Langfuse tìm các Traces có latency cao, kiểm tra span nào chiếm nhiều thời gian nhất.
  3. Đọc log trong `data/logs.jsonl` theo `correlation_id` của trace đó để kiểm tra lỗi timeout hoặc nghẽn mạng/database.
- Mitigation tạm thời: Tạm thời chuyển traffic sang prompt nhẹ hơn hoặc giảm tham số `max_tokens` / tắt tính năng RAG tìm kiếm chuyên sâu.
- Owner: on-call-engineer

## Alert 2

- Tên: elevated_error_rate
- Severity: critical
- SLI/SLO liên quan: error_rate_pct (Target: Error Rate < 2%)
- Điều kiện và thời gian duy trì: error_rate_pct > 5% kéo dài trong 3 phút
- Ảnh hưởng tới người dùng: Nhiều người dùng nhận thông báo lỗi hệ thống (HTTP 500/503), không nhận được phản hồi từ AI.
- Ba bước kiểm tra đầu tiên:
  1. Mở Dashboard xem panel Errors để phân loại nhóm lỗi chính (`error_type` như 500 Internal, 429 Rate Limit, Timeout...).
  2. Mở Langfuse lọc các Trace có trạng thái `ERROR` để xem chi tiết thông báo lỗi từ LLM Provider.
  3. Tra cứu log hệ thống để kiểm tra stack trace và xác định nguyên nhân gốc (ví dụ: hết API quota, sai định dạng prompt, hoặc lỗi server).
- Mitigation tạm thời: Rollback về phiên bản Prompt ổn định gần nhất (`prompt_version` cũ) hoặc kích hoạt Fallback Model dự phòng.
- Owner: on-call-engineer

## Alert 3

- Tên: cost_budget_exceeded
- Severity: warning
- SLI/SLO liên quan: daily_cost_usd (Target: Daily Cost <= $2.5)
- Điều kiện và thời gian duy trì: daily_cost_usd > 2.5
- Ảnh hưởng tới người dùng: Không ảnh hưởng trực tiếp tới trải nghiệm người dùng ngay lập tức, nhưng nguy cơ ứng dụng bị ngừng phục vụ do cạn kiệt ngân sách.
- Ba bước kiểm tra đầu tiên:
  1. Mở Dashboard xem panel Cost và Tokens để xác định sự tăng đột biến đến từ `tokens_in` hay `tokens_out`.
  2. Kiểm tra Langfuse để tìm các Session ID hoặc User ID tiêu tốn lượng token bất thường trong thời gian ngắn.
  3. Lọc log để kiểm tra xem có dấu hiệu bị tấn công spam request (DDoS) hoặc vòng lặp vô tận (infinite loop) ở client không.
- Mitigation tạm thời: Áp dụng Rate Limit theo `user_id_hash` đối với các tài khoản dùng quá lưu lượng, hoặc chuyển tạm thời traffic sang phiên bản model rẻ hơn.
- Owner: team-lead