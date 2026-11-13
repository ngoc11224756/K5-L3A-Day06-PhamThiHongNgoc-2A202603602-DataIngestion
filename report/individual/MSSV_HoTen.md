# Báo cáo cá nhân — Day 6

## Dữ liệu và pipeline
- Chủ đề, nguồn/quyền, số trang và quy tắc tính trang:  Tài liệu `sotay-sausanh-2022.pdf` [điền: tiêu đề, tổ chức phát hành], nguồn [điền: URL/đường dẫn], quyền sử dụng [điền: giấy phép/cho phép],
  truy cập ngày [điền]. Dùng 96 trang nội dung (trang in 1–96 = chỉ số trang PDF
  0-based 7–102); loại các trang trước đó (bìa, mục lục). Số trang in = chỉ số PDF − 6;
  `gold_page` trong benchmark dùng số trang in. Không có trang rỗng sau trích xuất.
- Chuẩn hóa, lỗi và giới hạn: Chuẩn hóa Unicode NFC, gộp khoảng trắng, giữ ngắt dòng/đoạn, bỏ dòng số trang in ở đầu trang. Ban đầu dùng pypdf nhưng làm vỡ dấu tiếng Việt (vd. "co h ồi",
  "ti ết sữa"); chuyển sang PyMuPDF [điền: phiên bản] cho kết quả sạch (cùng một
  bộ text cho cả A, B, C). Hạn chế: chunk theo từng trang nên câu vắt qua ranh giới
  trang bị cắt; mảnh dưới 60 ký tự được gộp vào mảnh kề (nên B có chunk tối đa 859 ký tự).
- Embedding model/provider/version/số chiều, vector store/version, metric, lệnh chạy và chi phí:
 Model local `intfloat/multilingual-e5-small` qua sentence-transformers [điền: phiên bản],
  384 chiều, vector chuẩn hóa; tiền tố `passage: ` cho văn bản và `query: ` cho câu hỏi.
  PostgreSQL 16 + pgvector [điền: phiên bản], metric cosine, [điền: exact (không dùng index
  xấp xỉ) nếu đã bỏ HNSW]. Chạy: `docker compose -p day6_student_starter up -d --wait`,
  `python -m src.run`. Chi phí 0 (model local).
  Nạp lại cùng phiên bản không nhân đôi: khóa chính `(config, chunk_id)`, `chunk_id` ổn
  định, `upsert` ghi đè rồi xóa chunk cũ không còn xuất hiện (xử lý tài liệu đổi).
  Nạp 2 lần đều cho A = 178, B = 119, không có cặp trùng (log: `results/idempotency_check.txt`)
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

| Strategy | Coherence trung bình /2 (n) | Metadata đủ và đúng (n/N) | Filter tuân thủ (n/N hoặc N/A) | Grounding 0/1/2 (số câu) và trung bình /2 |
|---|---|---|---|---|

Đường dẫn trace, nhãn thủ công và cách chọn mẫu:

## Phân tích và kết luận
- So sánh A–B và B–C; 2 ví dụ sai có ID câu và nguồn:
- Chiến lược chọn, đánh đổi, điều kiện áp dụng:
- Hạn chế của dữ liệu, nhãn, test nhỏ, đo thời gian/chi phí:
- Nếu làm lại hoặc mở rộng, cải tiến gì?
