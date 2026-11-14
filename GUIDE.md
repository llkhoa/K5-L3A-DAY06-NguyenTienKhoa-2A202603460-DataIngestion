# Hướng dẫn thực hành

## 1. Chọn dữ liệu (0:00–0:25)

Chọn một chủ đề hẹp: handbook sinh viên, hướng dẫn sản phẩm, tài liệu kỹ thuật, chính sách công khai, hoặc báo cáo thường niên. Gợi ý nguồn công khai: [OpenStax](https://openstax.org/subjects), [Project Gutenberg](https://www.gutenberg.org/), [World Bank Open Knowledge Repository](https://openknowledge.worldbank.org/). Kiểm tra giấy phép và quyền tái phân phối của **từng tài liệu**; không đưa thông tin cá nhân, mật hay tài liệu không được phép vào repo hoặc API.

Đơn vị tối thiểu: **30 trang nội dung hữu ích**. Với PDF, đếm trang thực có nội dung liên quan; loại trang bìa, mục lục, trang trống và trang chỉ có tài liệu tham khảo. Có thể kết hợp nhiều file. Ghi rõ số trang vật lý, các trang được tính và cách tính trong manifest. Với HTML/Markdown/text không có phân trang, dùng 30 đơn vị nguồn độc lập có ý nghĩa hoặc chia theo thứ tự thành các đơn vị có ít nhất **1.500 ký tự nội dung đã chuẩn hóa**; lưu ID, ranh giới và số ký tự mỗi đơn vị. Không nhân bản để đạt số lượng. Chọn corpus có cấu trúc và metadata để thử ít nhất hai cách chunk và một filter hữu ích. Nếu có scan, xử lý OCR hoặc thay bằng đủ trang trích xuất được; ghi lại phần lỗi/không đọc được.

Manifest tối thiểu: `source_id`, `title`, `source_path_or_url`, `license_or_permission`, `accessed_at`, danh sách page ID/số trang, số ký tự. Ghi snapshot/version nếu có. Không tự đoán ngày hiệu lực.

## 2. Chốt benchmark (0:25–1:00)

Viết ít nhất **20 câu hỏi trước khi chạy thử**, theo hướng dẫn trong [BENCHMARK.md](BENCHMARK.md); tối thiểu 15 dev / 5 test. Nên có câu trực tiếp, diễn đạt lại và câu có điều kiện/ngoại lệ; có ít nhất 3 câu kiểm tra metadata filter, trong đó ít nhất 1 câu thuộc test. Chia theo tài liệu/chủ đề khi khả thi và ghi nguy cơ rò rỉ. Mỗi câu cần đáp án, nguồn/trang và evidence được kiểm chứng; filter do câu hỏi hoặc ngữ cảnh cung cấp trước khi truy xuất. Không dùng câu không có đáp án trong nguồn cho chỉ số bắt buộc.

Kiểm chứng từng đoạn evidence thực sự nằm ở trang nguồn sau chuẩn hóa. Giữ tập và nhãn giống nhau giữa mọi chiến lược. Chuẩn bị thêm các câu hỏi nếu test khó đại diện; không thay đổi bộ test sau khi xem kết quả. Với nhiều nguồn bằng chứng hợp lệ, ghi tất cả và chấp nhận bất kỳ nguồn hợp lệ nào; không coi một câu trả lời đúng là sai chỉ vì trích nguồn hợp lệ khác.

## 3. Pipeline và thí nghiệm (1:00–2:40, gồm 10 phút nghỉ)

Dùng **Python**, đọc và chuẩn hóa Unicode, giữ liên kết về nguồn/trang và ghi lỗi. Tự chọn thư viện đọc tài liệu; nếu dùng OCR, ghi công cụ và kiểm chứng mẫu.

Chọn **một embedding model thật**: API qua OpenRouter, OpenAI, Gemini hoặc model chạy local (ví dụ Sentence Transformers với model đa ngữ). Local có thể không cần API key nhưng có thể cần tải model và tài nguyên máy. Ghi rõ provider, tên/phiên bản model, số chiều, cách xử lý query/document; giữ nguyên các yếu tố đó giữa ba cấu hình. Không dùng vector mock/ngẫu nhiên; TF-IDF chỉ là thí nghiệm thêm, không thay semantic embedding bắt buộc.

Chọn **một vector store** hỗ trợ lưu bền vững, tìm kiếm vector và filter metadata: PostgreSQL + pgvector, Qdrant, Chroma hoặc một store tương đương. Ghi phiên bản, cách khởi tạo, đường dẫn lưu/collection và lệnh chạy. Dùng cùng store và metric cosine cho ba cấu hình; ghi rõ exact hay approximate search nếu biết. Không thay vector store bằng phép tính thuần Python hoặc file SQLite tự quản.

Metadata tối thiểu cho mỗi chunk: `document_id`, `source` và `page` hoặc vị trí truy vết tương đương. Bổ sung **ít nhất một trường** thực sự có ích cho filter, tùy corpus: `section`, `year`, `version`, `category`, `audience`, `language`, `effective_date` hoặc `document_type`. Có thể thêm nhiều trường; ghi kiểu dữ liệu, nguồn giá trị và lý do chọn. Không tự đoán giá trị không có trong nguồn.

Ví dụ 3 cấu hình:

| Cấu hình | Chunk | Metadata / truy xuất |
|---|---|---|
| A | Kích thước cố định, ví dụ 500 ký tự, overlap 50 | Gắn nguồn và trang; không lọc |
| B | Theo heading/đoạn, giới hạn kích thước | Cùng metadata, không lọc |
| C | Giống B | Thêm lọc theo metadata có giá trị đáng tin, chỉ áp dụng khi câu hỏi có filter |

B–C chỉ thay lọc: phù hợp phân tích riêng ảnh hưởng metadata. A–B thay chunking. Corpus phải có ít nhất một trường lọc hữu ích với các giá trị phân biệt được; thiết kế câu hỏi kiểm tra metadata theo [BENCHMARK.md](BENCHMARK.md). Không đưa gold source/đáp án vào query hay filter. Nếu metadata phụ thuộc ngữ cảnh người dùng, ghi rõ filter là **input giả định được cung cấp trước**. Các giá trị lọc phải tồn tại và được kiểm chứng từ nguồn.

Đo số chunk, phân bố độ dài, tổng ký tự/token, thời gian ingest và chi phí (0 nếu không dùng dịch vụ trả phí). Nạp lại cùng phiên bản và kiểm tra không nhân đôi; mô tả cách xử lý tài liệu đổi. Luôn báo lỗi nếu backend không hoạt động, không âm thầm fallback sang mock.

## 4. Chạy và đánh giá (2:40–3:30)

Với mỗi chiến lược, chạy top-3 cho mọi câu hỏi, lưu câu hỏi, ID và text của các chunk, score, metadata, evidence/nhãn. Báo riêng dev và test. Đọc ít nhất 5 câu test cho từng cấu hình; dùng cùng câu hỏi, cùng tiêu chí và ghi nhãn từng trường hợp. Đánh giá năm khía cạnh:

1. **Retrieval accuracy — Hit@1 và Evidence Hit@3:** một hit khi chunk thuộc nguồn/trang gold và chứa **đủ** evidence đã ghi, hoặc bằng chứng tương đương được người chấm xác nhận. Hit@1 = số câu top-1 hit / số câu; Hit@3 = số câu có ít nhất một hit trong top-3 / số câu. Báo số tử/mẫu, không chỉ %. Nếu evidence bị tách qua nhiều chunk, ghi lỗi; có thể bổ sung đánh giá hợp bằng chứng đa chunk nhưng không thay định nghĩa chính.
2. **Chunk coherence:** chọn cùng 10 vị trí nội dung/đoạn nguồn cho mỗi chiến lược (có thể có nhiều chunk bao phủ cùng một vị trí); chấm thủ công chunk chứa vị trí đó: 0 = bị cắt giữa ý/thiếu chủ thể làm không hiểu; 1 = hiểu một phần, thiếu ngữ cảnh; 2 = tự hiểu được và giữ trọn ý. Công bố mẫu, nhãn, lý do và điểm trung bình /2. Xác định vị trí trước khi xem điểm, ví dụ theo 10 page ID đầu đã sắp xếp.
3. **Metadata usefulness:** trên 5 câu test × top-3, kiểm tra thủ công `source`, `page` và trường cần thiết khác so với nguồn. Báo số bản ghi có metadata **đủ và đúng** / tổng bản ghi đã kiểm tra; ghi từng lỗi. Với câu cần filter, báo số câu mà top-3 tuân thủ filter / số câu có filter; nếu tập đang đo không có câu filter thì N/A, không mặc định 100%. Đủ trường không chứng minh hữu ích: giải thích ít nhất một trường giúp truy vết hoặc lọc, và một hạn chế.
4. **Grounding quality:** chỉ đánh giá evidence retrieval, **không tự gọi đây là độ chính xác câu trả lời LLM**. Trên 5 câu test, chấm top-3: 0 = không có bằng chứng; 1 = có nhưng thiếu điều kiện/ngữ cảnh cần thiết; 2 = đủ để trả lời và truy nguồn. Báo số lượng từng mức và trung bình /2 kèm lý do. Có thể báo Evidence Hit@3 tự động như proxy, nhưng không thay nhãn thủ công.
5. **Data strategy impact:** so sánh kết quả, coherence, metadata và tài nguyên giữa A–B, B–C. Nêu đánh đổi, sai số do mẫu nhỏ, trường hợp thất bại và lý do chọn chiến lược; không suy rộng ngoài corpus. Nếu nhiều mục tiêu xung đột, định nghĩa tiêu chí chọn trước khi đọc test (ví dụ ưu tiên Hit@3, sau đó grounding, rồi tài nguyên).

Thực hiện chấm thủ công độc lập với điểm số nếu có thể; ghi rõ người chấm là tác giả và nguy cơ thiên lệch. Không dùng LLM judge mà không ghi phương pháp hoặc xem xét nhãn.

## 5. Demo và nộp bài (3:30–4:00)

Nộp `README` lệnh setup/run, mã nguồn, manifest/corpus hoặc hướng dẫn truy cập, benchmark và gold, cấu hình ba chiến lược, log lỗi, trace đầy đủ, bảng đo dev/test, bảng nhãn thủ công, báo cáo theo mẫu. Có seed khi cần; ghi phiên bản thư viện, model, chi phí và thời điểm chạy. Tập test nhỏ chỉ là minh họa: không tuyên bố chiến lược tốt nhất tổng quát. Nếu dữ liệu/model quá lớn, nộp manifest và cách lấy cùng output nhỏ để kiểm chứng.

## Mở rộng tùy chọn: hybrid retrieval

Nếu còn thời gian, giữ nguyên chunk và metadata filter, kết hợp dense similarity với một phương pháp từ khóa như BM25. Chọn tham số trên dev, so sánh với baseline trên câu hỏi chưa dùng để chỉnh và ghi cả trường hợp hybrid làm xấu kết quả. Không bắt buộc dùng hybrid để đạt điểm tối đa.
