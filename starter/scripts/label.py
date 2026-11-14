"""Hiển thị từng dòng CSV và nhập nhãn thủ công, lưu sau mỗi dòng. Chạy lại để làm tiếp."""
import csv, sys

path, score_col, show = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
allowed = set(sys.argv[4].split(",")) if len(sys.argv) > 4 else None
with open(path, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
reason_col = "reason" if "reason" in rows[0] else "ghi_chu_loi"

for i, r in enumerate(rows):
    if r[score_col].strip():
        continue
    print("\n" + "=" * 72, f"\nDòng {i + 1}/{len(rows)}")
    for c in show:
        print(f"{c}: {r[c]}")
    while True:
        v = input(f"\n{score_col} {sorted(allowed) if allowed else ''} (s = lưu và thoát): ").strip()
        if v.lower() == "s" or not allowed or v in allowed:
            break
    if v.lower() == "s":
        break
    r[score_col] = v
    r[reason_col] = input("Lý do/ghi chú: ").strip()
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
print("Đã lưu.")
