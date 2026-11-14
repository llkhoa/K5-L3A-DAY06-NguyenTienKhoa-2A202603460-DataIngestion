# Checkpoints — Day 06

Bài **cá nhân**, thời lượng dự kiến 240 phút. Các mốc tính từ lúc bắt đầu và là điểm tự kiểm tra tại lớp, không phải hạn nộp bài. Deadline do giảng viên/coach thông báo.

| Mốc | Mục tiêu | Minh chứng / tự kiểm tra |
|---|---|---|
| 0:25 | Chọn dữ liệu và setup | Ghi nguồn/quyền, số trang nội dung và quy tắc tính trang; công cụ đọc hoạt động. Có thể dùng [starter](starter/README.md) để kiểm tra pgvector. |
| 1:00 | Xây benchmark | ≥20 câu có trang và evidence; tách 15 dev / 5 test, xác minh evidence trước khi chạy thử. |
| 1:50 | Đọc, chuẩn hóa và thử chunk | Có log trang lỗi/rỗng, metadata truy nguồn; xuất được hai cấu hình chunk. |
| 2:00 | Nghỉ | |
| 2:40 | Lưu vector và chạy ba chiến lược | Cả ba index có thể truy xuất top-3; ghi model, tham số, thời gian/chi phí và kiểm tra nạp lại. |
| 3:30 | Benchmark và audit | Có trace, Hit@1/Hit@3 dev/test và mẫu chấm coherence, metadata, grounding. |
| 4:00 | Báo cáo và nộp | Có bảng so sánh, ví dụ lỗi, kết luận và các file theo [SUBMISSION.md](SUBMISSION.md). |

Chi tiết và tiêu chí tính xem [GUIDE.md](GUIDE.md). Nếu thiết lập chậm, dùng một embedding model local cùng Chroma hoặc Qdrant local; chuẩn bị model, thư viện và dữ liệu trước buổi học.
