# Báo cáo cá nhân — Day 6

## Dữ liệu và pipeline
- Chủ đề, nguồn/quyền, số trang và quy tắc tính trang:  T  Tài liệu "Sổ tay chăm sóc bà mẹ sau đẻ và trẻ sơ sinh" (Bộ Y tế, Trường ĐH Điều dưỡng
  Nam Định, 2022; chủ biên Lê Thanh Tùng, Phạm Thị Thanh Hương), file
  `sotay-sausanh-2022.pdf` (105 trang PDF, 1,83 MB). Nguồn:
  https://projects.tuni.fi/app/uploads/2023/09/d3fa1053-wp8-postpartum-care-handbook-viet.pdf
  Quyền sử dụng: tài liệu được công bố công khai trên trang dự án; các trang đầu/cuối
  không nêu giấy phép hay điều khoản tái phân phối, nên chỉ dùng cho mục đích học tập
  và không phân phối lại file PDF (repo lưu manifest và đường dẫn tải).
  Truy cập: 2026-11-13.
  Dùng 96 trang nội dung (trang in 1–96, tương ứng chỉ số PDF 0-based 7–102); loại
  bìa, trang biên soạn, lời nói đầu, mục lục (index 0–6) và tài liệu tham khảo
  (index 103–104). Số trang in = chỉ số PDF − 6; `gold_page` dùng số trang in.
  Không có trang rỗng sau trích xuất.
- Chuẩn hóa, lỗi và giới hạn: Chuẩn hóa Unicode NFC, gộp khoảng trắng, giữ ngắt dòng/đoạn, bỏ dòng số trang in ở đầu trang. Ban đầu dùng pypdf nhưng làm vỡ dấu tiếng Việt (vd. "co h ồi",
  "ti ết sữa"); chuyển sang PyMuPDF 2.1 cho kết quả sạch (cùng một
  bộ text cho cả A, B, C). Hạn chế: chunk theo từng trang nên câu vắt qua ranh giới
  trang bị cắt; mảnh dưới 60 ký tự được gộp vào mảnh kề (nên B có chunk tối đa 859 ký tự).
- Embedding model/provider/version/số chiều, vector store/version, metric, lệnh chạy và chi phí:
 Model local `intfloat/multilingual-e5-small` qua sentence-transformers 6.3.0
  (torch 2.15.0, transformers 5.22.2), 384 chiều, vector chuẩn hóa; tiền tố `passage: `
  cho văn bản và `query: ` cho câu hỏi. Vector store: PostgreSQL 16.16 + pgvector 0.8.7
  (Docker, cổng 127.0.0.1:55433), metric cosine (`<=>`). Tìm kiếm là exact (quét tuần tự):
  ban đầu có tạo index HNSW nhưng đã bỏ, vì HNSW kết hợp filter có thể trả về ít hơn 3 kết
  quả ở cấu hình C và làm sai Hit@3. Corpus chỉ 178 và 119 chunk nên exact vẫn rất nhanh.
  Môi trường: Python 3.14.4, macOS arm64; psycopg 3.3.8, pgvector (Python) 0.5.1,
  numpy 2.5.4, PyMuPDF 2.1. Lệnh chạy: `docker compose -p day6_student_starter up -d --wait`,
  `python -m src.run`. Chi phí: 0 (model local)
  Nạp 2 lần đều cho A = 178, B = 119, không có cặp trùng (log: `starter/results/idempotency_check.txt`).
- Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do chọn: Bắt buộc: `document_id`, `source`, `page`. Trường lọc: `chuong` (INTEGER 1–7), lấy từ heading "CHƯƠNG n" bằng regex ở đầu dòng, các trang sau kế thừa chương hiện hành.
  Phạm vi: Ch.1 tr.1–9, Ch.2 tr.10–27, Ch.3 tr.28–33, Ch.4 tr.34–52, Ch.5 tr.53–56,
  Ch.6 tr.57–67, Ch.7 tr.68–96. Lý do: phân biệt được 7 phạm vi, có trong nguồn,
  không tự đoán giá trị. Hạn chế: chỉ lọc theo chương, không lọc được theo chủ đề nhỏ.


## Cấu hình và benchmark
- A / B / C (tham số cụ thể, khác biệt duy nhất B–C):
- ≥20 câu: phân chia ≥15 dev / ≥5 test, câu metadata filter và cách kiểm chứng evidence:
- Tiêu chí chọn chiến lược đã chốt trước khi xem test:

## Kết quả
| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian | Chi phí |
|---|---|---|---|---|---|---|
| A | dev  | 13/15 (0.87) | 14/15 (0.93) | 178 | [cần số liệu] | 0 |
| A | test | 5/5 (1.00)   | 5/5 (1.00)   | 178 | [cần số liệu] | 0 |
| B | dev  | 14/15 (0.93) | 14/15 (0.93) | 119 | [cần số liệu] | 0 |
| B | test | 4/5 (0.80)   | 5/5 (1.00)   | 119 | [cần số liệu] | 0 |
| C | dev  | 14/15 (0.93) | 14/15 (0.93) | 119 | [cần số liệu] | 0 |
| C | test | 4/5 (0.80)   | 5/5 (1.00)   | 119 | [cần số liệu] | 0 |

| Strategy | Coherence trung bình /2 (n) | Metadata đủ và đúng (n/N) | Filter tuân thủ (n/N hoặc N/A) | Grounding 0/1/2 (số câu) và trung bình /2 |
|---|---|---|---|---|
| A | 1.10/2 (n=10) | 15/15 | N/A (0 câu filter) | 0/0/5, TB 2.00/2 |
| B | 1.30/2 (n=10) | 15/15 | N/A (0 câu filter) | 0/0/5, TB 2.00/2 |
| C | 1.30/2 (n=10) — chung nhãn với B (chung chunk) | 15/15 | dev 3/3, test 1/1 | 0/0/5, TB 2.00/2 |
Đường dẫn trace, nhãn thủ công và cách chọn mẫu:

## Phân tích và kết luận
- So sánh A–B và B–C; 2 ví dụ sai có ID câu và nguồn:
- Chiến lược chọn, đánh đổi, điều kiện áp dụng:
- Hạn chế của dữ liệu, nhãn, test nhỏ, đo thời gian/chi phí:
- Nếu làm lại hoặc mở rộng, cải tiến gì?
