"""In nguyên văn một trang in (dùng khi chấm metadata): python scripts/show_page.py 43"""
import sys
from pathlib import Path
from src.ingestion import load_pdf

n = int(sys.argv[1])
pages = {p.page: p for p in load_pdf(Path("data/sotay-sausanh-2022.pdf"), "sotay-sausanh-2022",
         "data/sotay-sausanh-2022.pdf", (7, 102), 6)}
p = pages[n]
print(f"--- trang in {n} (PDF index {n + 6}, chuong {p.metadata['chuong']}) ---")
print(p.text)
