# Quy tắc làm bài

## AI, nguồn và tính trung thực

- Được dùng AI để giải thích, viết code và hỗ trợ phân tích; học viên phải hiểu và giải thích được bài làm. Ghi công cụ và cách kiểm tra trong báo cáo.
- Không tự tạo số liệu, nhãn, nguồn, log hoặc kết quả chưa chạy. Điểm thấp vẫn có giá trị nếu được phân tích trung thực.
- Không sao chép bài làm của người khác. Ghi nguồn, giấy phép và thay đổi khi dùng dữ liệu, mã hoặc tài liệu bên ngoài.
- Chỉ dùng tài liệu có quyền xử lý; không đưa dữ liệu mật hoặc cá nhân vào repo hay API. Việc tài liệu được xem công khai không đồng nghĩa được phép tái phân phối hoặc dùng cho mọi mục đích.

## Benchmark và API

- Tự xác minh evidence, tách dev/test và ghi tiêu chí chọn cấu hình trước khi xem test. Nếu xem test để sửa bài, ghi rõ và không coi kết quả đó là kiểm tra độc lập; tạo tập mới nếu cần.
- Giữ nguyên corpus, bộ câu hỏi, model và định nghĩa metric giữa các chiến lược. Ghi thay đổi có chủ đích; không đưa gold answer/source vào query hay filter.
- Không commit `.env`, API key, token, dữ liệu riêng tư, môi trường ảo hay log có secret. Không âm thầm thay model thật bằng vector ngẫu nhiên khi API lỗi.
- Khi gặp lỗi provider, quota hoặc xử lý tài liệu, ghi lại lỗi và phần chưa chạy; nêu đúng phương án dự phòng đã dùng.

Thời hạn và cách nộp cụ thể do giảng viên/coach công bố; không tự suy diễn từ mốc checkpoint.
