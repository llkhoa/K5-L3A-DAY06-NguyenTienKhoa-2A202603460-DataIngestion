# Gợi ý công nghệ và thiết lập

Chọn **một** phương án embedding model thật và **một** vector store; không cần cài tất cả. Ghi phiên bản, tên model, số chiều, cách chạy và chi phí trong báo cáo. Giữ cùng model, store và metric giữa ba cấu hình.

## Embedding model

- **API:** chọn OpenRouter, OpenAI hoặc Gemini và cấu hình key ở máy local. Kiểm tra chi phí và quyền gửi tài liệu tới provider.
- **Local:** ví dụ [Sentence Transformers](https://sbert.net/docs/sentence_transformer/pretrained_models.html) với model đa ngữ phù hợp tiếng Việt, như `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Chuẩn bị model và dependencies trước buổi học; lần tải đầu có thể cần mạng và dung lượng. Model chạy local không bắt buộc key.

Ghi model/version và cách xử lý query, document theo tài liệu model; không âm thầm fallback sang mock khi lỗi. TF-IDF có thể dùng để tham khảo thêm, không thay embedding bắt buộc.

## Vector store

| Lựa chọn | Đặc điểm cho lab | Tài liệu |
|---|---|---|
| PostgreSQL + pgvector | Phù hợp khi muốn dùng SQL và chạy PostgreSQL riêng | [pgvector](https://github.com/pgvector/pgvector) |
| Qdrant | Hỗ trợ vector search và lọc theo payload; có thể chạy local | [Qdrant quickstart](https://qdrant.tech/documentation/quickstart/) |
| Chroma | Có client local lưu trên đĩa; hỗ trợ metadata filter | [Chroma docs](https://docs.trychroma.com/) |

Có thể chọn vector store khác nếu hỗ trợ **lưu bền vững, vector similarity search và metadata filtering**; ghi rõ cách xác minh và chạy lại. Dùng cùng một store cho ba cấu hình. Mode chỉ lưu trong RAM không đủ yêu cầu lưu bền vững.

Nếu dùng PDF, chuẩn bị công cụ trích text; trang scan cần OCR hoặc được ghi lỗi và thay bằng đủ trang trích xuất được. Khi chọn approximate search, nêu cấu hình và lưu ý filter có thể ảnh hưởng số kết quả; không giả định mọi backend có cùng hành vi. Lưu cách khởi động, collection/index, model và dependency để người chấm tái lập.
