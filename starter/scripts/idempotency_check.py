"""Đếm chunk theo cấu hình trong DB và ghi nối vào results/idempotency_check.txt."""
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
label = sys.argv[1] if len(sys.argv) > 1 else "kiểm tra"

with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    counts = conn.execute(
        "SELECT config, count(*) FROM chunks GROUP BY config ORDER BY config"
    ).fetchall()
    dups = conn.execute(
        "SELECT count(*) FROM (SELECT config, chunk_id FROM chunks "
        "GROUP BY config, chunk_id HAVING count(*) > 1) t"
    ).fetchone()[0]

line = f"{datetime.now():%Y-%m-%d %H:%M:%S} | {label} | {dict(counts)} | trùng (config, chunk_id): {dups}"
print(line)
out = Path(__file__).resolve().parents[1] / "results"
out.mkdir(exist_ok=True)
with open(out / "idempotency_check.txt", "a", encoding="utf-8") as f:
    f.write(line + "\n")
