import json
import matplotlib.pyplot as plt
from datetime import datetime, timezone, timedelta
import matplotlib.dates as mdates

times = []
latencies = []
colors = []

# Múi giờ Việt Nam (GMT+7)
vn_tz = timezone(timedelta(hours=7))

# Đọc dữ liệu từ file logs.jsonl
with open('data/logs.jsonl', 'r') as f:
    for line in f:
        try:
            data = json.loads(line)
            # Lọc lấy các log phản hồi có chứa latency
            if data.get('event') == 'response_sent' and 'latency_ms' in data:
                # Đọc giờ UTC từ log
                ts_utc = datetime.fromisoformat(data['ts'].replace('Z', '+00:00'))
                # Chuyển đổi sang giờ Việt Nam (GMT+7)
                ts_local = ts_utc.astimezone(vn_tz)
                
                latency = data['latency_ms']
                
                times.append(ts_local)
                latencies.append(latency)
                
                # Phân loại màu: Dưới 2000ms là xanh (Bình thường), trên là đỏ (Sự cố)
                if latency > 2000:
                    colors.append('#ff4d4d') # Màu đỏ
                else:
                    colors.append('#2ca02c') # Màu xanh lá
        except:
            pass

# Cấu hình kích thước biểu đồ
plt.figure(figsize=(12, 6))

# Vẽ biểu đồ dạng cột (nhìn rõ từng request)
bars = plt.bar(times, latencies, color=colors, width=0.00005, alpha=0.7)
# Vẽ đường nối các điểm
plt.plot(times, latencies, color='gray', linestyle='-', linewidth=1.5, alpha=0.5, marker='o', markersize=4)

# Vẽ đường SLO (Threshold) màu cam
plt.axhline(y=2000, color='orange', linestyle='--', linewidth=2, label='SLO Threshold (2000ms)')

# Thêm chú thích văn bản trực tiếp vào điểm cao nhất
max_latency = max(latencies)
max_time = times[latencies.index(max_latency)]
plt.annotate(f'Sự cố rag_slow\n{max_latency} ms', 
             xy=(max_time, max_latency), 
             xytext=(0, 10), textcoords='offset points', 
             ha='center', color='red', fontweight='bold')

# Định dạng trục
plt.title('Panel: API Response Latency (P95/Max) - Incident Investigation', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('Thời gian nhận phản hồi (GMT+7)', fontsize=12)
plt.ylabel('Độ trễ - Latency (ms)', fontsize=12)

# Định dạng lại giờ ở trục X (hiển thị Giờ:Phút:Giây) theo đúng chuẩn chiều/tối
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
plt.gcf().autofmt_xdate()

# Hiển thị chú thích (Legend) và lưới
plt.legend(loc='upper left', fontsize=11)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()

# Hiện biểu đồ
plt.show()