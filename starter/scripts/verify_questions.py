import json, re, sys, unicodedata
from pathlib import Path
from src.ingestion import load_pdf

path = sys.argv[1]

def norm(t):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", t)).strip().lower()

pages = {p.page: p for p in load_pdf(Path("data/sotay-sausanh-2022.pdf"), "sotay-sausanh-2022",
         "data/sotay-sausanh-2022.pdf", (7, 102), 6)}
qs = json.loads(Path(path).read_text(encoding="utf-8"))
bad = 0
for q in qs:
    quote = norm(q["evidence_quote"])
    gp = q["gold_page"]
    where = [n for n, p in pages.items() if quote in norm(p.text)]
    f = q.get("filter")
    fok = f is None or (gp in pages and f["chuong"] == pages[gp].metadata["chuong"])
    if gp in where and fok:
        status = "OK"
    elif where:
        status = f"SAI TRANG (quote nằm ở trang {where})"; bad += 1
    else:
        status = "KHÔNG TÌM THẤY quote"; bad += 1
    if not fok:
        status += " | filter không khớp chương"
    print(q["id"], q["split"], "p" + str(gp), status)
print(path, "| tổng:", len(qs), "| dev:", sum(q["split"]=="dev" for q in qs),
      "| test:", sum(q["split"]=="test" for q in qs),
      "| filter:", sum("filter" in q for q in qs),
      "| trang gold khác nhau:", len({q["gold_page"] for q in qs}), "| câu lỗi:", bad)
