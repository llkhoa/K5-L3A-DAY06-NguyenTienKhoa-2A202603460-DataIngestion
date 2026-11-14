# Báo cáo cá nhân — Day 6

## Dữ liệu và pipeline

### 1. Chủ đề, nguồn/quyền, số trang và quy tắc tính trang
- **Chủ đề:** Nền tảng Khoa học Dữ liệu (Data Science Fundamentals).
- **Corpus & Nguồn:** Giáo trình đại học mở *"Principles of Data Science"* phát hành bởi OpenStax (Rice University).
  - URL nguồn: https://openstax.org/details/books/principles-data-science
  - Giấy phép: **Creative Commons Attribution 4.0 International (CC BY 4.0)** — cho phép tự do sử dụng, trích xuất và phân phối phục vụ giáo dục & nghiên cứu khi ghi nhận tác giả.
  - File nội bộ: `starter/data/Principles-of-Data-Science-WEB.pdf`.
- **Số trang và quy tắc tính trang:**
  - Tổng số trang vật lý của toàn bộ PDF: 653 trang.
  - Phạm vi nạp vào pipeline: **Chapter 1: What Are Data and Data Science?** từ **trang 19 đến trang 65 vật lý**.
  - Tổng số trang nội dung hợp lệ: **47 trang** .
  - Quy tắc tính trang: Chỉ tính các trang thuộc phần thân bài học (Unit 1, Chapter 1) có trích xuất văn bản thực tế đạt `char_count > 100`. Toàn bộ trang bìa, lời tựa, mục lục (trang 1–18) và các trang chuyển mục/trống đều bị loại bỏ khỏi thống kê corpus.

### 2. Chuẩn hóa, lỗi và giới hạn
- **Phương pháp chuẩn hóa:**
  - Module `starter/src/ingestion.py` đọc PDF bằng `pypdf`, tích hợp cơ chế dự phòng `pymupdf` (fitz) nếu trang không đọc được text.
  - Chuẩn hóa Unicode sang dạng tổ hợp chuẩn **NFC** (`unicodedata.normalize('NFC', text)`).
  - Loại bỏ ký tự điều khiển, byte order mark rác (`\ufeff`, `\u200b`), đồng bộ dấu ngắt dòng `\r\n` và `\r` về `\n`.
  - Chuẩn hóa khoảng trắng ngang (khoảng trắng thừa giữa các từ) nhưng bảo toàn cấu trúc phân đoạn đoạn văn bản (`\n\n`).
- **Lỗi và giới hạn:**
  - Header/footer của PDF ("Access for free at openstax.org", số trang) đôi khi dính vào cuối đoạn văn. Tuy nhiên bộ chia đoạn nhận diện tốt nhờ ranh giới dòng trống.
  - Các hình vẽ minh họa và bảng biểu phức tạp trong PDF được trích xuất dưới dạng văn bản thô (chú thích hình), một phần nội dung trực quan bị tiêu hao thông tin nếu không dùng multimodal/OCR chuyên sâu.

### 3. Embedding model, Vector Store, Metric, Lệnh chạy và Chi phí
- **Embedding Model:** `intfloat/multilingual-e5-large` qua OpenRouter API.
  - Số chiều: **1024 dimensions**.
  - Xử lý tiền tố chuẩn E5: tự động bổ sung `passage: ` cho tài liệu chunk và `query: ` cho câu hỏi tìm kiếm để kích hoạt biểu diễn bất đối xứng (asymmetric retrieval) tối ưu.
  - Chuẩn hoá vector: Chuẩn hoá L2 norm trước khi lưu và tìm kiếm.
- **Vector Store:** **PostgreSQL 16** tích hợp extension **pgvector** chạy trên Docker container local (`day6_student_starter`).
  - Indexing: B-Tree index trên trường `strategy`, GIN index trên trường `metadata` (JSONB) phục vụ truy vấn metadata filtering siêu tốc.
  - Metric tìm kiếm: **Cosine Distance** (`<=>`), tương ứng với Cosine Similarity sau khi đã chuẩn hóa L2 vector.
- **Lệnh chạy:**
  ```bash
  cd starter
  docker compose -p day6_student_starter up -d --wait
  python -m src.run
  ```
- **Thời gian và chi phí:**
  - Thời gian trích xuất & chunking: ~2.5 giây.
  - Thời gian tạo embedding: ~35 giây cho 343 chunks.
  - Chi phí API OpenRouter: ~$0.001 USD cho ~45,000 tokens văn bản.

### 4. Metadata bắt buộc, trường lọc bổ sung và lý do chọn
- **Metadata bắt buộc:** `document_id` (`openstax_data_science`), `source` (`openstax`), `page` (trang vật lý trong PDF để truy vết nguồn chính xác), `char_start`, `char_end`.
- **Trường lọc bổ sung:**
  - `chapter`: Gán nhãn `"Chapter 1"` cho toàn bộ văn bản khảo sát.
  - `section`: Phân cấp chi tiết từ mục con của sách giáo khoa:
    - `"1.1"` (What Is Data Science? - Trang 19–21)
    - `"1.2"` (Applications of Data Science - Trang 22–25)
    - `"1.3"` (Data and Datasets - Trang 26–37)
    - `"1.4"` (Tools for Data Science - Trang 38–39)
    - `"1.5"` (Hands-on Data Science with Python - Trang 40–65)
- **Lý do chọn `section`:** Đây là cấu trúc phân cấp tự nhiên của tài liệu kỹ thuật/giáo trình. Khi người dùng hoặc hệ thống RAG biết trước phạm vi kiến thức cần tra cứu (ví dụ tra cứu về các kiểu dữ liệu ở mục 1.3), metadata filter cho phép thu hẹp không gian tìm kiếm, loại trừ hoàn toàn các đoạn văn nhiễu ở các mục khác.

---

## Cấu hình và benchmark

### 1. Cấu hình A / B / C
- **Chiến lược A (Fixed-size):** Phân mảnh kích thước cố định `size = 500` ký tự, độ gối đầu `overlap = 50` ký tự. Sinh ra tổng cộng **229 chunks**. Không áp dụng lọc metadata.
- **Chiến lược B (By-paragraph):** Phân mảnh dựa theo ranh giới đoạn văn bản (`\n\s*\n`), giới hạn `max_size = 1000` ký tự (chỉ cắt nhỏ nếu một đoạn đơn lẻ vượt quá 1000 ký tự). Sinh ra tổng cộng **114 chunks**. Không áp dụng lọc metadata.
- **Chiến lược C (By-paragraph + Metadata Filter):** Sử dụng **cùng tập 114 chunks** với Chiến lược B (đảm bảo so sánh kiểm soát chặt chẽ chỉ khác biệt duy nhất ở bước lọc). Khi truy vấn, nếu câu hỏi có metadata filter (`filter: {"section": "..."}`), hệ thống thực hiện lọc trong SQL bằng toán tử JSONB `@>`.

### 2. Bộ câu hỏi Benchmark (≥20 câu)
Bộ câu hỏi gồm **20 câu hỏi** được xây dựng và kiểm chứng độc lập trước khi chạy thử nghiệm pipeline, lưu tại `starter/data/benchmark.json` và `benchmark/benchmark.json`:
- **Phân chia:** **15 câu Dev** (`dev_01` đến `dev_15`) và **5 câu Test** (`test_01` đến `test_05`).
- **Câu kiểm tra Metadata Filter:** Có **4 câu** có nhãn filter:
  - `dev_03` (`filter: {"section": "1.1"}`)
  - `dev_06` (`filter: {"section": "1.2"}`)
  - `dev_09` (`filter: {"section": "1.3"}`)
  - `test_03` (`filter: {"section": "1.3"}`)
- **Kiểm chứng Evidence:** Từng đoạn `evidence_quote` trong benchmark được trích dẫn trực tiếp từ văn bản sách đã chuẩn hóa và xác nhận số trang vật lý chính xác (`gold_page`).

### 3. Tiêu chí chọn chiến lược chốt trước khi xem kết quả Test
1. Ưu tiên cao nhất: **Evidence Hit@3** (đảm bảo context đưa vào LLM không bị bỏ sót bằng chứng).
2. Ưu tiên thứ hai: **Hit@1** (độ chính xác định vị hàng đầu).
3. Ưu tiên thứ ba: **Chunk Coherence** (đoạn trích dẫn không bị cụt ý hay mất chủ ngữ).
4. Ưu tiên thứ tư: **Chi phí tài nguyên** (số lượng chunk và dung lượng lưu trữ vector).

---

## Kết quả thực nghiệm

### 1. Bảng đo lường Retrieval Accuracy (Hit@1 và Evidence Hit@3)

| Strategy | Split | Hit@1 (n/N) | Hit@1 (%) | Evidence Hit@3 (n/N) | Evidence Hit@3 (%) | Chunk count | Thời gian | Chi phí |
|---|---|---|---|---|---|---|---|---|
| **A (Fixed-size)** | Dev | 6/15 | 40.0% | 10/15 | 66.67% | 229 | ~1.5s | ~$0.0006 |
| **A (Fixed-size)** | Test | 3/5 | 60.0% | 4/5 | 80.0% | 229 | ~0.5s | ~$0.0002 |
| **B (Paragraph)** | Dev | 7/15 | 46.67% | 11/15 | 73.33% | 114 | ~1.2s | ~$0.0003 |
| **B (Paragraph)** | Test | 3/5 | 60.0% | 5/5 | 100.0% | 114 | ~0.4s | ~$0.0001 |
| **C (Paragraph + Filter)** | Dev | **8/15** | **53.33%** | 11/15 | 73.33% | 114 | ~1.2s | $0 (tái sử dụng B) |
| **C (Paragraph + Filter)** | Test | 3/5 | 60.0% | **5/5** | **100.0%** | 114 | ~0.4s | $0 (tái sử dụng B) |

---

### 2. Bảng đánh giá thủ công 5 khía cạnh chất lượng

| Strategy | Coherence trung bình /2 (n=10) | Metadata đủ và đúng (n/15) | Filter tuân thủ (n/N) | Grounding 0/1/2 (số câu) | Grounding TB /2 (n=5) |
|---|---|---|---|---|---|
| **A (Fixed-size)** | 1.1 / 2 | 15/15 (100%) | N/A | [0: 1 câu, 1: 0 câu, 2: 4 câu] | 1.6 / 2 |
| **B (Paragraph)** | **1.9 / 2** | 15/15 (100%) | N/A | [0: 0 câu, 1: 0 câu, 2: 5 câu] | **2.0 / 2** |
| **C (Paragraph + Filter)** | **1.9 / 2** | 15/15 (100%) | **1/1 (100%)** | [0: 0 câu, 1: 0 câu, 2: 5 câu] | **2.0 / 2** |

#### Ghi chú chi tiết về mẫu đánh giá thủ công:
* **Mẫu Coherence (10 vị trí nguồn từ trang 19 đến 28):**
  - Chiến lược A (cắt cứng 500 ký tự): 8/10 vị trí bị cắt đứt giữa câu hoặc mất phần mở đầu/chủ ngữ của mệnh đề, gây khó hiểu độc lập (đạt trung bình 1.1/2).
  - Chiến lược B & C: Giữ nguyên vẹn toàn bộ đoạn văn bản, câu mở đầu và câu kết luận trọn vẹn (đạt 1.9/2).
* **Mẫu Metadata Accuracy:** Kiểm tra 5 câu test $\times$ Top-3 = 15 chunks retrieved. Tất cả 15/15 chunks đều ghi nhận chính xác `document_id`, `page` vật lý trùng khớp 100% với file PDF gốc.
* **Mẫu Filter Compliance:** Câu test có filter là `test_03` (`filter: {"section": "1.3"}`). Cả 3/3 chunks trả về trong top-3 của Chiến lược C đều mang chính xác `section = "1.3"`, đạt tỷ lệ tuân thủ 100%.
* **Mẫu Grounding Quality (5 câu test):**
  - `test_01` (Data visualization): B và C trích xuất đầy đủ định nghĩa (Score 2/2).
  - `test_02` (Oakland Athletics / Sabermetrics): Cả 3 cấu hình đều lấy đúng đoạn trích dẫn (Score 2/2).
  - `test_03` (Nominal & Ordinal data): Đủ ngữ cảnh phân loại dữ liệu định tính (Score 2/2).
  - `test_04` (Thư viện Pandas): Trích xuất chính xác vai trò thao tác dữ liệu (Score 2/2).
  - `test_05` (Thư viện Matplotlib): Ở cấu hình A, chunk bị cắt xén khiến từ khóa Matplotlib nằm ở chunk tiếp theo không lọt vào top-3 (Score 0/2). Ở cấu hình B và C, đoạn văn trọn vẹn đưa bằng chứng vào top-3 (Score 2/2).

* **Đường dẫn lưu vết (Traces):**
  - [starter/results/trace_A_fixed.json](file:///f:/Vin%20AI/Lab%206/K5-L3A-DAY06-ChuVanHiep-2A202603382-DataIngestion/starter/results/trace_A_fixed.json)
  - [starter/results/trace_B_paragraph.json](file:///f:/Vin%20AI/Lab%206/K5-L3A-DAY06-ChuVanHiep-2A202603382-DataIngestion/starter/results/trace_B_paragraph.json)
  - [starter/results/trace_C_paragraph_filtered.json](file:///f:/Vin%20AI/Lab%206/K5-L3A-DAY06-ChuVanHiep-2A202603382-DataIngestion/starter/results/trace_C_paragraph_filtered.json)

---

## Phân tích và kết luận

### 1. So sánh có kiểm soát: A–B và B–C

#### So sánh A vs B (Tác động của kỹ thuật phân mảnh Chunking):
* **Số lượng chunk:** Chiến lược A tạo ra 229 chunks (do kích thước nhỏ 500 ký tự), trong khi B chỉ tạo 114 chunks (giảm 50% số lượng vector cần lưu trữ và tính toán).
* **Hiệu năng retrieval:**
  - Trên tập Dev, B tăng Hit@1 từ 40.0% lên 46.67% và Hit@3 từ 66.67% lên 73.33%.
  - Trên tập Test, B đạt **Evidence Hit@3 tuyệt đối 100% (5/5)** so với 80.0% (4/5) của A.
  - Trường hợp điển hình `dev_05` ("What does the Internet of Things describe?") và `dev_10` ("How is a dataset defined in the text?"): Ở cấu hình A, định nghĩa bị cắt đôi giữa hai chunk khiến embedding vector bị loãng ngữ nghĩa, cả hai đều trượt top-3 (`hit_3 = False`). Ở cấu hình B, toàn bộ câu định nghĩa nằm trọn trong một đoạn văn, giúp câu hỏi khớp chính xác vào Top-1 (`hit_1 = True`).

#### So sánh B vs C (Tác động của Metadata Filtering):
* B và C dùng chung 100% dữ liệu chunk, chỉ khác duy nhất ở bước truy vấn có áp dụng lọc SQL JSONB.
* Trên tập Dev, Chiến lược C đã **tăng Hit@1 từ 46.67% lên 53.33%** (tăng thêm 1 câu trả lời trúng ngay Top-1).
* **Minh chứng thực nghiệm tại câu `dev_09`:**
  - *Câu hỏi:* "What type of methods is usually used to analyze quantitative data?" (Yêu cầu thông tin tại mục 1.3, trang 28).
  - *Tại cấu hình B (không filter):* Do từ khóa "methods" và "analyze" xuất hiện dày đặc trong cả cuốn sách, một chunk ở Section 1.1 (trang 19) bị nhầm là phù hợp nhất và chiếm vị trí Top-1, đẩy đoạn chứa gold evidence xuống vị trí Top-2 $\rightarrow$ `hit_1 = False, hit_3 = True`.
  - *Tại cấu hình C (có filter `{"section": "1.3"}`):* Nhờ bộ lọc loại bỏ toàn bộ các đoạn ngoài mục 1.3, đoạn chứa gold evidence được đưa thẳng lên vị trí **Top-1** $\rightarrow$ `hit_1 = True`.

---

### 2. Phân tích 2 trường hợp truy xuất thất bại (Error Analysis)

* **Trường hợp 1: Câu `dev_08` (Thất bại ở cả A, B và C)**
  - *Câu hỏi:* "What did Ancient Egyptians invent to journal their data?"
  - *Gold Source:* `openstax_data_science`, trang 27.
  - *Evidence:* "invented a first form of paper-papyrus-in order to journal their data".
  - *Nguyên nhân thất bại:* Câu hỏi mang tính chất lịch sử cổ đại ("Ancient Egyptians", "papyrus"), trong khi model `multilingual-e5-large` khi nhúng văn bản giáo trình Khoa học Dữ liệu có xu hướng gán trọng số ngữ nghĩa cao hơn cho các đoạn bàn về cơ sở dữ liệu hiện đại, công cụ bảng tính hoặc máy tính. Các đoạn ở trang 38–41 nói về công cụ lưu trữ dữ liệu chiếm trọn Top-3, đẩy đoạn lịch sử Ai Cập cổ đại ra ngoài Top-3.

* **Trường hợp 2: Câu `dev_11` (Thất bại ở cả A, B và C)**
  - *Câu hỏi:* "Which programming language's syntax does JSON use?"
  - *Gold Source:* `openstax_data_science`, trang 31.
  - *Evidence:* "uses the syntax of a programming language named JavaScript".
  - *Nguyên nhân thất bại:* Câu hỏi rất ngắn gọn và tập trung vào cú pháp JSON. Các chunk mô tả chi tiết cấu trúc file JSON và ví dụ code JSON (cũng ở trang 31 và 32) có độ tương đồng cosine rất cao với từ khóa "JSON syntax", do đó chúng chiếm trọn 3 vị trí đầu tiên. Câu nói mang tính dẫn nhập *"uses the syntax of a programming language named JavaScript"* nằm ở một đoạn văn ngắn liền kề bị xếp ở vị trí thứ 4.

---

### 3. Chiến lược lựa chọn, Đánh đổi (Trade-offs) và Điều kiện áp dụng
* **Chiến lược được chọn:** **Chiến lược C (Paragraph-aware Chunking + Metadata Filtering)** là chiến lược tối ưu nhất:
  - Đạt Hit@3 cao nhất trên cả Dev (73.33%) và Test (100.0%).
  - Đạt Hit@1 cao nhất trên Dev (53.33%) nhờ loại bỏ nhiễu liên-mục.
  - Tiết kiệm 50% số lượng chunk lưu trữ so với Fixed-size (114 vs 229 chunks).
  - Độ mạch lạc ngữ nghĩa (Chunk Coherence) đạt 1.9/2, bảo đảm LLM đọc hiểu trọn vẹn ngữ cảnh khi trả lời.
* **Đánh đổi (Trade-offs):**
  - *Phân đoạn theo paragraph:* Nếu tài liệu có những đoạn văn quá dài (ví dụ >2000 ký tự), bắt buộc phải có thuật toán phụ để cắt nhỏ, làm tăng độ phức tạp của code tiền xử lý.
  - *Metadata Filtering:* Đòi hỏi tài liệu phải có cấu trúc rõ ràng hoặc cần một bước trích xuất metadata (LLM extractor / rule-based). Nếu metadata bị gán sai (false negative), câu truy vấn sẽ bỏ lọt hoàn toàn chunk chứa câu trả lời đúng.

---

### 4. Hạn chế và Hướng cải tiến

* **Hạn chế:**
  - Tập test nhỏ (5 câu) chỉ mang tính chất minh họa kiểm chứng giả thuyết, chưa đủ lớn để khái quát hóa thống kê cho toàn bộ các tình huống thực tế.
  - Metadata `section` hiện tại được gán dựa trên khoảng trang PDF vật lý thay vì nhận diện tiêu đề Heading tự động bằng OCR/Layout Parser.
* **Hướng cải tiến nếu làm tiếp:**
  1. **Hybrid Retrieval (Dense + Sparse):** Kết hợp vector search của `multilingual-e5-large` với BM25/Full-text search của PostgreSQL để khắc phục các trường hợp tìm kiếm từ khóa thực thể hiếm (như câu "Ancient Egyptians" hay "JavaScript").
  2. **Hierarchical / Parent Document Retriever:** Lưu các chunk con nhỏ (sentence-level) để embedding chính xác, nhưng khi retrieve sẽ trả về toàn bộ đoạn văn (parent chunk) chứa nó để tối ưu ngữ cảnh cho LLM sinh câu trả lời.
