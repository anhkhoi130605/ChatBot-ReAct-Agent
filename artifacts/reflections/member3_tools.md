# Tự reflection — TV3 Tool Interface Engineer

### Họ tên: [Điền họ và tên] — MSSV: [Điền MSSV]

## 1. Vai trò và phạm vi

Tôi đảm nhận vai trò **Tool Interface Engineer (Kỹ sư Giao diện Công cụ)** cho bài Lab IT Helpdesk Agent. 
- **Phạm vi file phụ trách:** `starter_v0/artifacts/tools.yaml` (ở vòng cải tiến `v2`) và file reflection này.
- **Mục tiêu cốt lõi:** Chuẩn hóa khai báo 9 tool (6 core tools và 3 advanced tools), phân định rạch ròi ranh giới năng lực (capability boundaries), tối ưu hóa JSON schema, kiểu dữ liệu, các giá trị `enum` và mô tả tham số nhằm giảm thiểu tối đa các lỗi chọn sai công cụ (`wrong_tool`), sai tham số (`wrong_arg_value`) và vi phạm ranh giới an toàn (`wrong_boundary`).

---

## 2. Phân tích ranh giới công cụ và thay đổi trong `tools.yaml`

Một trong những bài học lớn nhất của bài lab là: **Tên tool, description và JSON schema đều là một phần quan trọng của prompt**. Nếu description không rõ ranh giới, model sẽ phân vân hoặc đoán mò tham số. Tôi đã tập trung tinh chỉnh các ranh giới then chốt:

1. **`clarify` vs `create_ticket` (Ranh giới xác nhận an toàn):**
   - *Vấn đề quan sát ở v0/v1:* Ở case `H12_confirm_before_ticket`, model gọi thẳng `create_ticket(confirmed=false)` thay vì gọi `clarify` để hỏi người dùng. Mặc dù implementation của tool có guardrail trả về `needs_confirmation` để chặn ghi file, nhưng evaluator vẫn chấm FAIL vì sai routing.
   - *Điều chỉnh:* Bổ sung cảnh báo nghiêm ngặt trong description của `create_ticket`: *"CHỈ gọi tool này khi người dùng ĐÃ xác nhận đồng ý rõ ràng trong hội thoại (confirmed=true). Nếu chưa có xác nhận tường minh, TUYỆT ĐỐI KHÔNG gọi tool này với confirmed=false, mà phải gọi `clarify` với `response_type='yes_no'` để xin xác nhận."*

2. **`check_service_status` vs `inspect_device` (Dịch vụ dùng chung vs Thiết bị đơn lẻ):**
   - Phân biệt rõ dịch vụ hạ tầng dùng chung (`vpn`, `email`, `sso`, `wifi`, `printing`) trên môi trường `production`/`staging` với trạng thái nội bộ của một máy tính cụ thể (`LT-xxx`, `DT-xxx`). 
   - Khóa chặt `environment` với enum `[production, staging]`, mặc định là `production`.

3. **`inspect_device` vs `lookup_user` (Ranh giới định danh Identifier):**
   - *Vấn đề quan sát:* Ở case `H04_user_routing`, model bị nhầm lẫn và gọi thêm `inspect_device` với mã phòng ban/nhân viên.
   - *Điều chỉnh:* Trong `inspect_device.parameters.asset_id`, ghi rõ convention: *"Chỉ chấp nhận mã tài sản nội bộ có định dạng như LT-xxx, DT-xxx, PR-xxx; tuyệt đối không truyền employee_id (như EMP-xxxx) hoặc tên phòng ban"*. Tương tự, `lookup_user.parameters.employee_id` được ghi chú chỉ nhận mã nhân viên định danh.
   - Định nghĩa chặt chẽ enum cho `check` trong `inspect_device`: `[all, network, vpn, security, hardware, software]`, hướng dẫn model chọn đúng phạm vi chẩn đoán cụ thể (giải quyết lỗi `H05` và `H17` khi model chọn thừa `all` thay vì `vpn`).

4. **`search_kb` vs `policy` (Tài liệu kỹ thuật vận hành vs Chính sách nội bộ):**
   - *Vấn đề quan sát ở Extension suite:* Các case `E01_access_policy`, `E02_privacy_policy`, `E03_incident_priority_policy` đều bị FAIL `wrong_tool` vì model gọi nhầm sang `search_kb`.
   - *Điều chỉnh:* Tách bạch rõ ràng mục đích sử dụng:
     - `search_kb`: Dùng để tra cứu hướng dẫn kỹ thuật thực hành (how-to, troubleshooting Wi-Fi, cài đặt máy in, khắc phục lỗi mạng). Hạn định enum `category: [all, vpn, email, wifi, printing, account, security, hardware, software, meeting_room]`.
     - `policy`: Dùng để tra cứu quy tắc tuân thủ, quyền hạn, SLA, quy định bảo mật, phân loại sự cố và ranh giới chia sẻ dữ liệu. Hạn định enum `policy_area: [all, access_control, data_privacy, external_tools, incident_response, service_operations, ticketing]`.

5. **`search_device_info` (Ranh giới bảo mật thông tin ra ngoài Web Search):**
   - Khai báo bắt buộc 3 tham số: `manufacturer`, `model`, `query_type` (`specs`, `drivers`, `support`, `compatibility`).
   - Bổ sung rào chắn bảo vệ dữ liệu PII: Cấm truyền bất kỳ thông tin nội bộ nào như `asset_id`, `serial`, `hostname`, `location`, `employee_id` hay `diagnostics` ra query tìm kiếm bên ngoài.

6. **`format_incident_report`:**
   - Định nghĩa schema chi tiết cho mảng `findings` (gồm `label`, `detail`, `source`, `status`) và enum `template: [brief, technical, handoff]`. Nêu rõ tool này chỉ format các dữ liệu đã thu thập, không tự ý query lại dữ liệu.

---

## 3. Giả thuyết và kế hoạch kiểm chứng

- **Giả thuyết cho vòng v2 (Chỉ cải tiến `tools.yaml`):**
  > *"Nếu tinh chỉnh mô tả ranh giới giữa `search_kb` và `policy`, bổ sung chỉ dẫn cấm gọi `create_ticket` khi chưa xác nhận, và chuẩn hóa các enum cho `check`, `category`, `policy_area`, thì tỷ lệ `tool_routing_accuracy` trên bộ extension và `argument_accuracy` trên bộ base sẽ tăng đáng kể mà không cần thay đổi code Python bên dưới."*

- **Kế hoạch kiểm chứng:**
  - Giữ nguyên baseline prompt (hoặc kết hợp prompt v1) và chạy đánh giá trên cùng model `openai/gpt-4o-mini`.
  - Bộ kiểm thử trọng tâm:
    - Suite `base` (30 case): Đo lường sự cải thiện ở các case `H03` (kb category), `H04` (user routing), `H05` (device check arg), `H12` (confirm before ticket), `H17` (three sources triage).
    - Suite `extension` (10 case): Đo lường việc giải quyết 3 case policy routing `E01`, `E02`, `E03` và case `E08` (confirmation revision).
  - Tiêu chuẩn hợp lệ: `provider_error_cases == 0`, `measured_cases == total_cases`. Kiểm tra thủ công payload trong run JSON để chắc chắn không có rò rỉ dữ liệu nhạy cảm ra ngoài web.

---

## 4. Phân tích kết quả và đối chiếu kỹ thuật

Dựa trên các run thực tế của nhóm:
- **Tại Baseline v0 (`tools_hash=eb3e2243f237`):**
  - Suite `base`: Đạt 21/30 (70.0%), `tool_routing_accuracy: 76.67%`, `argument_accuracy: 70.0%`. Các ca lỗi gồm `H04` (wrong_tool), `H10`, `H11`, `H19` (missing_info), `H12`, `M05`, `M09` (wrong_boundary), `H13`, `H17` (wrong_tool).
  - Suite `extension`: Đạt 6/10 (60.0%), trong đó `E01`, `E02`, `E03` đều FAIL vì chọn sai tool sang `search_kb`.
- **Hiệu quả khi tối ưu hóa schema (`tools_hash=c85b6ce9a595`):**
  - Ranh giới giữa `search_kb` và `policy` được phân lập rõ rệt nhờ mô tả chi tiết và bộ enum `policy_area`.
  - Hạn chế được việc model truyền giá trị tùy tiện nhờ việc bắt buộc các trường `required` và định danh enum rõ ràng.
  - Tuy nhiên, một số ca biên (như `H12` khi model vẫn cố chấp gọi action tool với `confirmed=false`) cho thấy chỉ sửa `tools.yaml` là chưa đủ mà bắt buộc phải kết hợp quy tắc răn đe toàn cục từ `system_prompt.md` của TV2.

---

## 5. Tự đánh giá và bài học kinh nghiệm

- **Một quyết định kỹ thuật tôi đã đưa ra và lý do:**
  - *Quyết định:* Đưa các giá trị hợp lệ vào trực tiếp thuộc tính `enum` trong JSON schema thay vì chỉ viết thành câu văn tự do trong `description`.
  - *Lý do:* Các API Function/Tool Calling hiện đại (như OpenAI structured outputs) sử dụng JSON schema để ép kiểu chặt chẽ (constrained sampling). Việc định nghĩa enum ở cấp độ schema ngăn chặn triệt để tình trạng model sinh ra các đối số lạ (như `check: "hardware_and_vpn"` thay vì `check: "hardware"`).

- **Khó khăn gặp phải và cách xử lý:**
  - *Khó khăn:* Mô tả tool quá dài có thể khiến model bị loãng ngữ cảnh hoặc chú ý không đồng đều giữa các tools, trong khi mô tả quá ngắn lại dẫn đến việc chọn sai ranh giới.
  - *Cách xử lý:* Tôi áp dụng công thức viết description 3 phần súc tích: (1) Mục đích cốt lõi; (2) Ranh giới KHÔNG được dùng (anti-use-cases); (3) Định dạng dữ liệu đầu ra và lưu ý an toàn.

- **Điều tôi học được từ phần việc này:**
  - Prompt Engineering không chỉ là viết các đoạn văn bản hướng dẫn (system prompt), mà cấu trúc giao diện Tool (Function calling schema) chính là lớp phòng thủ kỹ thuật quan trọng hàng đầu giúp AI tương tác an toàn và chính xác với thế giới bên ngoài.
  - Hiểu sâu về cách tách biệt dữ liệu: Dữ liệu nhạy cảm nội bộ không bao giờ được xuất hiện trong tham số của các công cụ external search.

- **Nếu làm lại, tôi sẽ cải thiện điều gì:**
  - Tôi sẽ xây dựng thêm các schema validation test tự động bằng Python (sử dụng thư viện `jsonschema` hoặc `pydantic`) để kiểm tra tính nhất quán giữa các hàm thực thi trong thư mục `starter_v0/tools/` với khai báo trong `tools.yaml` trước khi chạy eval, tránh lệch tên tham số.

---

**Nhánh/commit đóng góp:** `contrib/tv3-tools` / commit dưới Git identity của Thành viên 3.
