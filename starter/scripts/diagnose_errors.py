import json, os, re, unicodedata
from pathlib import Path
from dotenv import load_dotenv
from src.embeddings import MyEmbedder
from src.store import PgVectorStore

load_dotenv()

def norm(t):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", t)).strip().lower()

qs = {q["id"]: q for q in json.loads(Path("data/benchmark.json").read_text(encoding="utf-8"))}
emb = MyEmbedder()
store = PgVectorStore(os.environ["DATABASE_URL"], emb.dimensions)

for qid in ("q06", "q12", "q13"):
    q = qs[qid]
    quote = norm(q["evidence_quote"])
    qv = emb.embed_query(q["question"])
    print("=" * 70)
    print(qid, "| gold trang", q["gold_page"], "|", q["question"])
    for tag in ("A", "B"):
        hits = store.search(tag, qv, top_k=300)
        has_quote = [(i, h["page"], round(1 - h["distance"], 3))
                     for i, h in enumerate(hits, 1) if quote in norm(h["content"])]
        gold_page = [(i, round(1 - h["distance"], 3))
                     for i, h in enumerate(hits, 1) if h["page"] == q["gold_page"]]
        print(f"--- Cấu hình {tag}: chunk chứa trọn quote (hạng, trang, score): {has_quote or 'KHÔNG CÓ chunk nào (quote bị cắt)'}")
        print(f"    mọi chunk của trang gold (hạng, score): {gold_page}")
        for i, h in enumerate(hits[:3], 1):
            print(f"    top{i} [p{h['page']}, {1 - h['distance']:.3f}] {h['content'][:160]!r}")
