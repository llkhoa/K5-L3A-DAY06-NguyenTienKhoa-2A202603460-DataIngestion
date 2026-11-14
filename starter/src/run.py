"""Pipeline entry point for Day 06 Lab - Data Ingestion."""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

from src.ingestion import load_pdf
from src.chunking import fixed_size, by_paragraph
from src.embeddings import MyEmbedder
from src.store import PgVectorStore
from src.evaluation import evaluate_query, summarize

def main() -> None:
    load_dotenv()

    # 1. Setup Data & Infrastructure
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/vectordb")

    print("Initializing Embedder and Vector Store...")
    embedder = MyEmbedder()
    store = PgVectorStore(database_url=db_url, dimensions=embedder.dimensions)
    store.create_schema()

    # 2. Load Corpus
    data_dir = Path("data")
    pdf_path = data_dir / "Principles-of-Data-Science-WEB.pdf"

    # Load toàn bộ trang từ PDF
    print(f"\nLoading {pdf_path}...")
    pages = load_pdf(pdf_path, document_id="openstax_data_science", source="openstax")

    # 1. Lấy CHÍNH XÁC từ trang 19 đến 65 (PDF vật lý) - Nội dung Part 1, Unit 1
    content_pages = [p for p in pages if 19 <= p.page <= 65]

    # 2. Lọc bỏ các trang trống/rác (nếu có) bên trong khoảng này
    valid_pages = [p for p in content_pages if p.metadata.get("char_count", 0) > 100]

    print(f"Extracted {len(valid_pages)} valid content pages for ingestion.")

    # 3. Gán metadata "section" chính xác dựa trên Page Offset (PDF Page = Book Page + 10)
    for p in valid_pages:
        p.metadata["chapter"] = "Chapter 1" # Tất cả đều thuộc Chapter 1

        # Gán section dựa theo trang PDF vật lý
        if 19 <= p.page <= 21:
            p.metadata["section"] = "1.1"
        elif 22 <= p.page <= 25:
            p.metadata["section"] = "1.2"
        elif 26 <= p.page <= 37:
            p.metadata["section"] = "1.3"
        elif 38 <= p.page <= 39:
            p.metadata["section"] = "1.4"
        elif 40 <= p.page <= 65:
            p.metadata["section"] = "1.5"
        else:
            p.metadata["section"] = "unknown"

    # 3. Build Strategies (A: Fixed size, B: Paragraph)
    # Lưu ý: Cấu hình C sử dụng chung kho chunk với B, chỉ khác ở bước Search có metadata filter.
    strategies = {
        "A_fixed": [],
        "B_paragraph": []
    }

    print("\nChunking documents...")
    for page in valid_pages:
        # Chiến lược A: Fixed size
        strategies["A_fixed"].extend(fixed_size(page, size=500, overlap=50))

        # Chiến lược B: Paragraph
        strategies["B_paragraph"].extend(by_paragraph(page, max_size=1000))

    # 4. Embed and Store
    print("\nEmbedding and Storing vectors...")
    force_reindex = os.getenv("FORCE_REINDEX", "false").lower() == "true"
    for strategy_name, chunks in strategies.items():
        if not chunks:
            continue

        existing_count = store.count(strategy_name)
        if existing_count == len(chunks) and not force_reindex:
            print(f"--> Strategy '{strategy_name}' already indexed ({existing_count} chunks). Skipping re-embedding.")
            continue

        print(f"--> Processing {len(chunks)} chunks for strategy: {strategy_name}")
        texts = [chunk.text for chunk in chunks]

        # Embed
        vectors = embedder.embed_documents(texts)

        # Lưu vào PostgreSQL
        store.upsert(strategy=strategy_name, chunks=chunks, vectors=vectors)

    # 5. Run Benchmark
    benchmark_path = data_dir / "benchmark.json"
    if not benchmark_path.exists():
        print(f"\nNo {benchmark_path} found. Skipping evaluation.")
        print("Please create benchmark.json with at least 20 questions to complete the Lab.")
        return

    with open(benchmark_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    all_traces = { "A_fixed": [], "B_paragraph": [], "C_paragraph_filtered": [] }

    print(f"\nRunning evaluation on {len(questions)} questions...")
    for q in questions:
        query_vector = embedder.embed_query(q["question"])

        # Strategy A (Fixed, no filter)
        hits_A = store.search("A_fixed", query_vector, top_k=3)
        all_traces["A_fixed"].append(evaluate_query(q, hits_A))

        # Strategy B (Paragraph, no filter)
        hits_B = store.search("B_paragraph", query_vector, top_k=3)
        all_traces["B_paragraph"].append(evaluate_query(q, hits_B))

        # Strategy C (Paragraph, with metadata filter)
        # Sử dụng kho chunk của B_paragraph, áp dụng filter metadata nếu câu hỏi có yêu cầu
        filters = q.get("filter", None)
        hits_C = store.search("B_paragraph", query_vector, top_k=3, filters=filters)
        all_traces["C_paragraph_filtered"].append(evaluate_query(q, hits_C))

    # 6. Summarize Metrics
    for strat, traces in all_traces.items():
        print(f"\n=== Results for {strat} ===")
        stats = summarize(traces)
        print(json.dumps(stats, indent=2))

        # Lưu file trace để phân tích lỗi
        trace_file = Path(f"results/trace_{strat}.json")
        trace_file.parent.mkdir(parents=True, exist_ok=True)
        with open(trace_file, "w", encoding="utf-8") as f:
            json.dump(traces, f, indent=2, ensure_ascii=False)
        print(f"Traces saved to {trace_file}")

if __name__ == "__main__":
    main()