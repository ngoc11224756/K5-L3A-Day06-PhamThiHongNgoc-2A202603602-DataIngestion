"""Xuất bảng chấm thủ công và liệt kê câu sai ở dev."""
import csv
import json
import re
import unicodedata
from pathlib import Path

from src.chunking import by_paragraph, fixed_size
from src.ingestion import load_pdf


def norm(t):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", t)).strip().lower()


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


R = Path("results")
traces = json.loads((R / "traces.json").read_text(encoding="utf-8"))
qs = {q["id"]: q for q in json.loads(Path("data/benchmark.json").read_text(encoding="utf-8"))}

# 1. Câu chưa đạt ở dev (Hit@1 hoặc Hit@3 trượt)
print("=== CÂU SAI Ở DEV ===")
for t in traces:
    if t["split"] == "dev" and not t["hit_at_1"]:
        got = [(h["page"], round(h["score"], 3)) for h in t["hits"]]
        print(f'{t["strategy"]} {t["id"]} gold_p{qs[t["id"]]["gold_page"]} '
              f'hit_rank={t["hit_rank"]} top3(page,score)={got}')

# 2. Coherence: 10 vị trí cố định (dòng giữa của trang in 1-10), xác định trước khi xem điểm
pages = load_pdf(Path("data/sotay-sausanh-2022.pdf"), "sotay-sausanh-2022",
                 "data/sotay-sausanh-2022.pdf", (7, 102), 6)
rows = []
for p in pages[:10]:
    lines = [l for l in p.text.splitlines() if l.strip()]
    if not lines:
        continue
    anchor = norm(lines[len(lines) // 2])[:25]
    for strat, fn in (("A", lambda pg: fixed_size(pg, 500, 50)),
                      ("B/C", lambda pg: by_paragraph(pg, 800))):
        chunk = next((c for c in fn(p) if anchor in norm(c.text)), None)
        rows.append({
            "strategy": strat, "page": p.page, "anchor": anchor,
            "chunk_id": chunk.chunk_id if chunk else "",
            "text": chunk.text if chunk else "(không tìm thấy chunk chứa vị trí)",
            "score_0_2": "", "reason": "",
        })
write_csv(R / "coherence_labels.csv", rows)

# 3. Metadata: 5 câu test x top-3 x 3 cấu hình
meta = []
for t in traces:
    if t["split"] != "test":
        continue
    q = qs[t["id"]]
    for h in t["hits"]:
        meta.append({
            "strategy": t["strategy"], "qid": t["id"], "rank": h["rank"],
            "chunk_id": h["chunk_id"], "source": h["source"], "page": h["page"],
            "chuong": h["chuong"], "gold_page": q["gold_page"],
            "filter": json.dumps(q.get("filter")), "content": h["content"],
            "metadata_dung_du_1_0": "", "ghi_chu_loi": "",
        })
write_csv(R / "metadata_labels.csv", meta)

# 4. Grounding: 5 câu test x 3 cấu hình, chấm top-3 theo thang 0-2
g = []
for t in traces:
    if t["split"] != "test":
        continue
    q = qs[t["id"]]
    g.append({
        "strategy": t["strategy"], "qid": t["id"], "question": q["question"],
        "expected_answer": q["expected_answer"], "evidence_quote": q["evidence_quote"],
        "top3": " || ".join(f'[p{h["page"]}] {h["content"]}' for h in t["hits"]),
        "grounding_0_2": "", "reason": "",
    })
write_csv(R / "grounding_labels.csv", g)

print("Đã ghi coherence_labels.csv, metadata_labels.csv, grounding_labels.csv trong results/")
