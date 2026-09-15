# Self-Reflection — Thành Viên 1 (Nhóm Trưởng)

### Họ tên: Nguyễn Trung Kiên — MSSV: [Điền MSSV]
- **Vai trò/phần việc được nhận:** 
  - Nhóm trưởng (Team Lead / DevOps / Baseline).
  - Khởi tạo và thiết lập repository fork chung của nhóm, phân quyền cộng tác cho các thành viên.
  - Xây dựng ma trận công việc và quy trình Git chống conflict tuyệt đối (`WORK-MATRIX.md`).
  - Khởi tạo danh sách thành viên `TEAMMATES.md` ở thư mục gốc.
  - Chạy và ghi nhận số liệu phiên bản mốc ban đầu (Baseline `v0`) trên suite `base` vào `version_log.csv`.
  - Quản lý, điều phối việc review, merge các Pull Request từ thành viên và tổng hợp báo cáo chung.

- **Những gì tôi đã thay đổi trong repo chung:**
  - Tạo mới file `TEAMMATES.md` chứa thông tin các thành viên và vai trò phân công.
  - Cập nhật dòng `v0` vào `starter_v0/artifacts/version_log.csv` từ kết quả chạy thực tế với OpenAI (`case_accuracy: 0.70`).
  - Thiết lập quy trình phân vùng tệp tin độc lập `WORK-MATRIX.md` và cấu trúc thư mục `artifacts/reflections/` để cả 5 thành viên tự commit reflection mà không bị merge conflict.
  - Chạy bộ kiểm thử baseline `v0_B_base_openai_20260914T184037608852.json`.

- **File hoặc artifact liên quan:**
  - `TEAMMATES.md`
  - `WORK-MATRIX.md`
  - `starter_v0/artifacts/version_log.csv`
  - `starter_v0/runs/v0_B_base_openai_20260914T184037608852.json`
  - `starter_v0/artifacts/reflections/member1_lead.md`

- **Commit hash hoặc pull request:**
  - Commit ban đầu trên nhánh `main`: `feat(setup): add TEAMMATES.md, record v0 baseline and member1 reflection`

- **Một quyết định kỹ thuật tôi đã đưa ra và lý do:**
  - *Quyết định:* Tách mục `C2. Self-reflection` ra thành 5 tệp tin độc lập trong `starter_v0/artifacts/reflections/` thay vì để cả 5 thành viên cùng chỉnh sửa trực tiếp vào file `REPORT.md`.
  - *Lý do:* Theo dõi và xử lý merge conflict trong Git thường xảy ra khi nhiều người cùng chỉnh sửa một file markdown dài. Việc phân lập file giúp 5 thành viên có thể commit độc lập 100%, Git merge tự động không bao giờ xung đột, đồng thời vẫn giữ được commit history minh bạch cho từng cá nhân theo yêu cầu chấm điểm của lab.

- **Khó khăn tôi gặp và cách tôi xử lý:**
  - *Khó khăn:* Khi chạy kiểm thử ban đầu với các provider khác nhau (OpenRouter / OpenAI), có một số lỗi liên quan đến key và environment loader hoặc bộ test `eval_group.json` trống.
  - *Cách xử lý:* Sử dụng trực tiếp provider `openai` ổn định với model `gpt-4o-mini`, đảm bảo `provider_error_cases == 0` và `measured_cases == 30/30` đúng tiêu chuẩn evidence của bài lab; đồng thời làm rõ thứ tự thực hiện giữa các thành viên.

- **Điều tôi học được từ phần việc này:**
  - Hiểu sâu sắc về quy trình đo lường định lượng trong Prompt Engineering: baseline là mốc chuẩn để đánh giá, không phải phiên bản cần điểm cao ngay.
  - Nâng cao kỹ năng quản lý repository cộng tác nhóm lớn trong Git, kỹ thuật phân rã tác vụ (Task Decomposition) và thiết kế luồng CI/CD / PR mượt mà.

- **Nếu làm lại, tôi sẽ cải thiện điều gì:**
  - Tôi sẽ tự động hóa script tiền kiểm tra (pre-commit check) bằng PowerShell/Bash để cảnh báo nếu thành viên vô tình chỉnh sửa file ngoài phạm vi phân công trước khi push lên remote.
