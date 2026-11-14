"""Suggested pipeline entry point; TODO: implement the orchestration."""


"""Pipeline: ingest -> chunk -> embed -> store -> benchmark."""
import json
import os
import statistics
import time
from pathlib import Path

from dotenv import load_dotenv

from .chunking import by_paragraph, fixed_size
from .embeddings import MyEmbedder
from .evaluation import evaluate_query, summarize
from .ingestion import load_pdf
from .store import PgVectorStore

RESULTS = Path("results")
QUESTIONS = Path("data/benchmark.json")

# C dùng lại chunk của B; chỉ khác ở bước search có filter
CONFIGS = {
    "A": {"chunk_tag": "A", "use_filter": False},
    "B": {"chunk_tag": "B", "use_filter": False},
    "C": {"chunk_tag": "B", "use_filter": True},
}


def build_chunks(pages, tag):
    chunks = []
    for page in pages:
        if tag == "A":
            chunks += fixed_size(page, size=500, overlap=50)
        else:
            chunks += by_paragraph(page, max_size=800)
    return chunks


def main() -> None:
    load_dotenv()
    RESULTS.mkdir(exist_ok=True)

    # 1. Đọc tài liệu (đúng số trong manifest.json)
    pages = load_pdf(
        path=Path("data/sotay-sausanh-2022.pdf"),
        document_id="sotay-sausanh-2022",
        source="data/sotay-sausanh-2022.pdf",
        page_range=(7, 102),
        page_offset=6,
    )
    print(f"Đọc {len(pages)} trang, {sum(len(p.text) for p in pages)} ký tự")

    # 2. Embedding + store
    embedder = MyEmbedder()
    print(f"Model {embedder.model_name}, {embedder.dimensions} chiều")
    store = PgVectorStore(os.environ["DATABASE_URL"], embedder.dimensions)
    store.create_schema()

    # 3. Ingest A và B (C dùng lại B)
    stats = {}
    for tag in ("A", "B"):
        t0 = time.time()
        chunks = build_chunks(pages, tag)
        vectors = embedder.embed_documents([c.text for c in chunks])
        store.upsert(tag, chunks, vectors)
        lens = [len(c.text) for c in chunks]
        stats[tag] = {
            "n_chunks": len(chunks),
            "total_chars": sum(lens),
            "mean_len": round(statistics.mean(lens), 1),
            "median_len": statistics.median(lens),
            "min_len": min(lens),
            "max_len": max(lens),
            "ingest_seconds": round(time.time() - t0, 1),
            "cost_usd": 0,
        }
        print(tag, stats[tag])
    (RESULTS / "ingest_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 4. Benchmark top-3
    if not QUESTIONS.exists():
        print(f"Chưa có {QUESTIONS}, dừng sau bước ingest.")
        return
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))

    all_traces = []
    for name, cfg in CONFIGS.items():
        for q in questions:
            qvec = embedder.embed_query(q["question"])
            flt = q.get("filter") if cfg["use_filter"] else None
            hits = store.search(cfg["chunk_tag"], qvec, top_k=3, filters=flt)
            trace = evaluate_query(q, hits, filter_used=flt is not None)
            trace["strategy"] = name
            all_traces.append(trace)

    (RESULTS / "traces.json").write_text(
        json.dumps(all_traces, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    # 5. Chỉ số tự động, báo riêng dev/test
    summary = summarize(all_traces)
    (RESULTS / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for strat, splits in summary.items():
        for split, s in splits.items():
            flt = f"{s['filter_ok']}/{s['filter_n']}" if s["filter_n"] else "N/A"
            print(f"{strat} {split}: Hit@1 {s['hit_at_1']}/{s['n']}, "
                  f"Hit@3 {s['hit_at_3']}/{s['n']}, filter {flt}")


if __name__ == "__main__":
    main()