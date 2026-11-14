# Báo cáo cá nhân — Day 6

## Dữ liệu và pipeline
- Chủ đề, nguồn/quyền, số trang và quy tắc tính trang:  
Tài liệu "Sổ tay chăm sóc bà mẹ sau đẻ và trẻ sơ sinh" (Bộ Y tế, Trường ĐH Điều dưỡng
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
- Chuẩn hóa, lỗi và giới hạn: 
Chuẩn hóa Unicode NFC, gộp khoảng trắng, giữ ngắt dòng/đoạn, bỏ dòng số trang in ở đầu trang. Ban đầu dùng pypdf nhưng làm vỡ dấu tiếng Việt (vd. "co h ồi",
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
- Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do chọn: 
Bắt buộc: `document_id`, `source`, `page`. Trường lọc: `chuong` (INTEGER 1–7), lấy từ heading "CHƯƠNG n" bằng regex ở đầu dòng, các trang sau kế thừa chương hiện hành.
  Phạm vi: Ch.1 tr.1–9, Ch.2 tr.10–27, Ch.3 tr.28–33, Ch.4 tr.34–52, Ch.5 tr.53–56,
  Ch.6 tr.57–67, Ch.7 tr.68–96. Lý do: phân biệt được 7 phạm vi, có trong nguồn,
  không tự đoán giá trị. Hạn chế: chỉ lọc theo chương, không lọc được theo chủ đề nhỏ.


## Cấu hình và benchmark
- A: `fixed_size(size=500, overlap=50)`, không filter, 178 chunk.
  B: `by_paragraph(max_size=1000)`, không filter, 119 chunk.
  C: giống B (dùng chung 119 chunk với B), khác biệt duy nhất: áp metadata filter `chuong`
  trong bước `search()` khi câu hỏi có cung cấp `filter`.

- 20 câu (`data/benchmark.json`): 15 dev (q01–q15) / 5 test (q16–q20), tách trước khi chạy thử,
  không chỉnh sau khi xem kết quả. 4 câu có filter theo `chuong` (q05, q10, q14 ở dev; q19 ở test)
  → đủ ≥3 câu filter, ≥1 câu thuộc test. Mỗi câu có `gold_source_id`, `gold_page`, `evidence_quote`
  đã đối chiếu thủ công với PDF trước khi chạy (đúng trang, đúng nội dung).
  
- Tiêu chí chọn chiến lược đã chốt trước khi xem test: Không có — tiêu chí lựa chọn chiến lược cuối
  cùng (ưu tiên coherence và filter compliance, chấp nhận đánh đổi Hit@1 test thấp hơn) được xác
  định sau khi đã xem toàn bộ kết quả dev/test. 

## Kết quả
| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian | Chi phí |
|---|---|---|---|---|---|---|
| A | dev  | 13/15 (0.87) | 14/15 (0.93) | 178 | 0.8s (ingest+embed) | 0 |
| A | test | 5/5 (1.00)   | 5/5 (1.00)   | 178 | 0.8s (ingest+embed) | 0 |
| B | dev  | 14/15 (0.93) | 14/15 (0.93) | 119 | 0.6s (ingest+embed) | 0 |
| B | test | 4/5 (0.80)   | 5/5 (1.00)   | 119 | 0.6s (ingest+embed) | 0 |
| C | dev  | 14/15 (0.93) | 14/15 (0.93) | 119 | dùng chung chunk với B, không ingest riêng | 0 |
| C | test | 4/5 (0.80)   | 5/5 (1.00)   | 119 | dùng chung chunk với B, không ingest riêng | 0 |

Tổng thời gian chạy toàn bộ pipeline (3 cấu hình, gồm load model + ingest + search + eval): 9.94s (`time python -m src.run`, macOS, CPU, không dùng GPU).

| Strategy | Coherence trung bình /2 (n) | Metadata đủ và đúng (n/N) | Filter tuân thủ (n/N hoặc N/A) | Grounding 0/1/2 (số câu) và trung bình /2 |
|---|---|---|---|---|
| A | 1.10/2 (n=10) | 15/15 | N/A (0 câu filter) | 0/0/5, TB 2.00/2 |
| B | 1.30/2 (n=10) | 15/15 | N/A (0 câu filter) | 0/0/5, TB 2.00/2 |
| C | 1.30/2 (n=10) — chung nhãn với B (chung chunk) | 15/15 | dev 3/3, test 1/1 | 0/0/5, TB 2.00/2 |

Đường dẫn trace, nhãn thủ công và cách chọn mẫu:
- Trace retrieval: `results/summary.json` (Hit@1/Hit@3 theo strategy × split, filter compliance).
- Nhãn thủ công: `results/coherence_labels.csv` (20 dòng, 10 vị trí × A và B/C),
  `results/grounding_labels.csv` (15 dòng, 5 câu test × A/B/C),
  `results/metadata_labels.csv` (45 dòng, 5 câu test × top-3 × 3 cấu hình).
- Chọn mẫu coherence: 10 vị trí đầu tiên theo trang in tăng dần (trang 1–10), chốt trước khi xem
  nội dung chunk, dùng chung cho cả A và B/C.
- Chọn mẫu grounding/metadata: toàn bộ 5 câu test (q16–q20), không lấy mẫu con.
- Người chấm: Phạm Thị Hồng Ngọc (tác giả bài làm). Đã xem kết quả Hit@1/Hit@3 tự động
  (`results/summary.json`) trước khi chấm nhãn thủ công → có nguy cơ thiên lệch xác nhận
  (confirmation bias); giảm thiểu bằng cách dùng `scripts/label.py`, công cụ cố ý ẩn cột
  `is_match`/điểm cosine/gold_page khi hiển thị để chấm.

## Phân tích và kết luận
- **So sánh A–B (thay đổi chunking):** B có ít chunk hơn (119 so với 178, giảm ~33%) và dài hơn
  (TB 554.7 ký tự so với 393.7). B đạt coherence cao hơn rõ rệt (TB 1.30/2 so với 1.10/2) vì chia
  theo đoạn/heading giữ trọn ý tốt hơn cắt cố định 500 ký tự. Nhưng B lại thấp hơn A ở Hit@1 test
  (4/5 so với 5/5) — ví dụ cụ thể: câu **q17** ("cuống rốn rụng khi nào") ở B/C, top-1 là chunk
  trang 87 (nói về viêm rốn nói chung) không chứa đáp án, trong khi đáp án đúng (trang 71) chỉ
  xếp hạng 3; ở A, top-1 ngay trang 71 chứa đáp án trực tiếp. Ngược lại A thấp hơn B ở Hit@1 dev
  (13/15 so với 14/15). → không có cấu hình nào thắng tuyệt đối trên cả hai split.
  - **So sánh B–C (thay đổi filter):** metadata và coherence giống hệt nhau (dùng chung chunk).
  C đạt tuân thủ filter tuyệt đối (dev 3/3, test 1/1) trong khi B không áp filter nên 100% top-3
  của B có thể lẫn chunk khác chương (ví dụ câu q19 ở B có 2/3 top-3 thuộc chương 2 và 5, không
  phải chương 7 được hỏi). Hit@1/Hit@3 của B và C bằng nhau tuyệt đối ở mọi split — cho thấy
  áp filter theo `chuong` không làm giảm chất lượng truy xuất trong benchmark này, vì các câu có
  filter đều có gold đúng nằm sẵn trong đúng chương được lọc.
  **2 ví dụ sai cụ thể:**
  1. Câu **q17** (test), chiến lược B/C: top-1 = `sotay-sausanh-2022_p87_b0` (chương 7, nói về
     viêm rốn) — không chứa evidence; đáp án đúng (trang 71, "Cuống rốn thường rụng từ 10-14
     ngày") chỉ đạt rank 3. Nguồn: `results/metadata_labels.csv`, dòng B/q17/rank1 và rank3.
  2. Câu **q12** (dev) — "Nứt núm vú có thể do nguyên nhân nào liên quan đến trẻ?" — **miss hoàn
     toàn trong top-3 ở cả A và B** (gold: trang 43, evidence "vi khuẩn từ miệng trẻ truyền sang
     đầu vú của mẹ"). Đây là lỗi chung cho cả 2 chiến lược chunking khác nhau, gợi ý nguyên nhân
     nằm ở bước embedding/truy vấn chứ không phải cách chia chunk: có thể do câu hỏi dùng từ
     "nứt núm vú" trong khi văn bản gốc nói "nứt núm vú" ở một đoạn khác (chủ đề tưa miệng/nấm
     men) tách biệt với đoạn chứa evidence chính xác, khiến vector câu hỏi gần với đoạn sai hơn.
     Nguồn: `results/traces.json`, strategy A và B, id q12, `hit_rank: null`.
- Chiến lược chọn, đánh đổi, điều kiện áp dụng: 
  Chọn **C** làm khuyến nghị chính — giữ coherence
  cao của B (1.30/2) và Hit@3 ổn định (1.00 ở test), đồng thời đạt tuân thủ filter tuyệt đối khi câu
  hỏi cần thu hẹp phạm vi theo chương. Đánh đổi: C/B có Hit@1 test thấp hơn A (0.80 so với 1.00) —
  phù hợp khi ứng dụng chấp nhận đọc cả top-3 thay vì chỉ tin kết quả đầu tiên, hoặc khi cần lọc
  theo chương là yêu cầu bắt buộc (vd tra cứu theo đúng giai đoạn chăm sóc). Nếu ứng dụng chỉ hiển
  thị 1 kết quả duy nhất (không có top-3), A phù hợp hơn do Hit@1 test tuyệt đối.
- Hạn chế của dữ liệu, nhãn, test nhỏ, đo thời gian/chi phí: 
  - Test set chỉ 5 câu — quá nhỏ để kết luận chắc chắn về khác biệt Hit@1 (chênh lệch 1 câu/5
    đã đổi tỷ lệ 20%); grounding TB 2.00/2 tuyệt đối ở cả 3 cấu hình có thể chỉ phản ánh benchmark
    chưa đủ khó để phân biệt, không phải bằng chứng cả 3 cấu hình grounding ngang nhau trong thực tế.
  - Coherence chỉ chấm 10 vị trí (trang 1–10, đầu tài liệu) — chưa chắc đại diện cho toàn bộ 96
    trang, đặc biệt các chương có cấu trúc liệt kê dày đặc hơn (vd chương 4, 7) có thể bị cắt khác.
  - Người chấm là tác giả, đã biết kết quả tự động trước khi chấm thủ công → nguy cơ thiên lệch
    xác nhận dù đã dùng công cụ ẩn điểm khi hiển thị.
  - Đo thời gian chỉ 1 lần chạy trên máy cá nhân (không lặp lại nhiều lần lấy trung bình), có thể
    dao động do tải CPU nền.
  - Trường filter `chuong` khá thô — chỉ phân biệt 7 phạm vi lớn, không lọc được theo chủ đề nhỏ
    trong cùng chương (ví dụ không tách được "chăm sóc rốn" và "chăm sóc da" dù cùng chương 7).
- Nếu làm lại hoặc mở rộng, cải tiến gì?
  - Tăng benchmark test lên ≥15–20 câu để Hit@1/Hit@3 ổn định hơn, giảm nhiễu do mẫu nhỏ.
  - Thêm trường filter thứ hai mịn hơn (vd `section` theo đề mục con) để kiểm tra metadata hữu ích
    hơn khi corpus có nhiều chủ đề nhỏ trong cùng chương.
  - Thử overlap lớn hơn ở A (vd 100 thay vì 50) để giảm tình trạng cắt mất ý ở ranh giới chunk.
  - Chấm coherence trên nhiều hơn 10 vị trí, trải đều qua các chương thay vì chỉ 10 trang đầu.
  - Với các câu bị miss cả top-3 ở mọi chiến lược (như q12), nên kiểm tra lại cách diễn đạt câu
    hỏi so với văn bản gốc — có thể cần viết lại câu hỏi gần với từ vựng nguồn hơn, hoặc đây là
    dấu hiệu embedding model chưa đủ mạnh cho loại câu hỏi nguyên nhân/quan hệ gián tiếp.
