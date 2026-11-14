# Benchmark — năm tiêu chí đánh giá

Mục tiêu là so sánh **ít nhất ba chiến lược dữ liệu** trên cùng corpus, model và bộ câu hỏi để chọn chiến lược phù hợp, kèm bằng chứng và lý do. Benchmark gồm bộ câu hỏi có gold, kết quả truy xuất, mẫu chấm thủ công và phân tích theo **năm tiêu chí** dưới đây.

| Tiêu chí | Cần đo hoặc kiểm tra | Minh chứng |
|---|---|---|
| **1. Độ chính xác truy xuất** | Hit@1 và Evidence Hit@3 trên cùng bộ câu hỏi | Số câu đúng/tổng câu, top-3 và gold theo từng chiến lược |
| **2. Tính mạch lạc của chunk** | Chunk có giữ trọn ý và đủ ngữ cảnh để hiểu không? | Chấm thủ công cùng 10 vị trí nguồn cho mỗi chiến lược, thang 0–2, kèm lý do |
| **3. Tính hữu dụng của metadata** | Metadata có đúng, đủ để truy vết và giúp lọc phạm vi không? | Kiểm tra `source`, `page` và trường lọc trong top-3; tỷ lệ tuân thủ filter khi có yêu cầu |
| **4. Chất lượng thông tin nền (Grounding Quality)** | Top-3 có đủ bằng chứng và điều kiện để trả lời, có truy được nguồn không? | Chấm thủ công 5 câu test mỗi chiến lược, thang 0–2, kèm lý do |
| **5. Tác động của chiến lược dữ liệu** | Các thay đổi về chunking/metadata ảnh hưởng kết quả, chất lượng và tài nguyên ra sao? | So sánh A–B và B–C, số chunk, thời gian, chi phí, ví dụ lỗi và đánh đổi |

Định nghĩa chi tiết thang điểm, mẫu và công thức xem [GUIDE.md](GUIDE.md). **Grounding ở đây đánh giá độ đủ của bằng chứng truy xuất**, không phải độ chính xác của câu trả lời LLM. Hit@3 không thay cho chấm thủ công coherence hoặc grounding. Điểm bài làm theo [RUBRIC.md](RUBRIC.md); năm tiêu chí trên là các khía cạnh cần báo cáo, không phải năm loại câu hỏi.

## Bộ câu hỏi và gold

Tự xây **ít nhất 20 câu** từ corpus, chia trước tối thiểu **15 dev / 5 test**. Nên có câu hỏi trực tiếp, diễn đạt lại, điều kiện/ngoại lệ và câu cần phân biệt bằng metadata, tùy dữ liệu. Đây là **gợi ý để phủ các lỗi**, không bắt buộc một tỷ lệ số câu cố định. Chọn và ghi cách phân chia trước khi thử nghiệm; có ít nhất **3 câu có filter**, trong đó ít nhất **1 câu test**, để kiểm tra metadata filter. Không điều chỉnh chiến lược dựa vào test; nếu đã xem test để sửa bài, ghi rõ và tạo tập test mới nếu có thể.

Mỗi câu ghi: `id`, `split`, `question`, `expected_answer`, `gold_source_id`, `gold_page`, `evidence_quote` và `filter` nếu dùng. Có thể thêm nhãn loại câu để phân tích lỗi. `gold_page` là số trang PDF hoặc ID đơn vị truy vết tương đương.

Trước khi chạy, kiểm chứng evidence tồn tại ở nguồn và đủ hỗ trợ đáp án, kể cả điều kiện/ngoại lệ. Nếu nhiều nguồn hoặc trang hợp lệ, ghi tất cả và chấp nhận một trong số đó. Không đưa đáp án hoặc gold source vào query/filter; giá trị filter phải được người dùng hoặc ngữ cảnh cung cấp **trước khi truy xuất**. Với câu không có filter, cấu hình C chạy không filter cho câu đó và ghi rõ. Không dùng câu không có đáp án trong nguồn cho chỉ số bắt buộc.

Filter cần dựa vào metadata đáng tin, ví dụ `year`, `section`, `category`, `audience`, `language` hoặc `version`. Chọn corpus có ít nhất hai phạm vi phân biệt được; không tạo giá trị giả để filter đạt điểm. Xem [data/format-example.json](data/format-example.json) để tham khảo cấu trúc, không phải benchmark hoàn chỉnh.
