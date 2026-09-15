<<<<<<< HEAD
# Self-Reflection — Thành Viên 4 (Evaluation Specialist)

### Họ tên: [Điền họ và tên] — MSSV: [Điền MSSV]
- **Vai trò/phần việc được nhận:** Evaluation Specialist — Thiết kế 10 test case trong `starter_v0/data/eval_group.json`, kiểm thử suite group.
- **Những gì tôi đã thay đổi trong repo chung:**
- **File hoặc artifact liên quan:** `starter_v0/data/eval_group.json`
- **Commit hash hoặc pull request:**
- **Một quyết định kỹ thuật tôi đã đưa ra và lý do:**
- **Khó khăn tôi gặp và cách tôi xử lý:**
- **Điều tôi học được từ phần việc này:**
- **Nếu làm lại, tôi sẽ cải thiện điều gì:**
=======
# Member 4 Reflection — Tác giả Đánh giá & Kiểm thử

## 1. Tóm tắt đóng góp

Tôi được phân công vai trò **Evaluation & Test Author** trong nhóm. Trách nhiệm của tôi là thiết kế và xác thực bộ dữ liệu đánh giá nhóm cho IT Helpdesk Agent.

Trong phần đóng góp này, tôi đã tạo bộ kiểm thử nhóm gốc tại `starter_v0/data/eval_group.json` với đúng 10 test case:

- 5 test case single-turn
- 5 test case multi-turn

Các test case được thiết kế để đánh giá khả năng của mô hình trong việc:

- định tuyến đến đúng công cụ
- truyền đúng tham số
- duy trì ngữ cảnh qua nhiều lượt hội thoại
- cập nhật thông tin trước đó khi người dùng sửa lại
- yêu cầu làm rõ khi cần thiết
- từ chối các yêu cầu không liên quan đến IT
- tránh sử dụng công cụ không cần thiết
- duy trì đúng ranh giới xác nhận trước khi thực hiện các hành động ghi hoặc thay đổi dữ liệu

## 2. Mục tiêu thiết kế kiểm thử

Bộ đánh giá nhóm được thiết kế để bao phủ các dạng lỗi phổ biến nhất trong bài lab này, thay vì chỉ lặp lại các test case cố định trong bộ base.

Các chủ đề chính bao gồm:

- định tuyến dịch vụ và xử lý môi trường
- kiểm tra thiết bị với giá trị `check` chính xác
- định tuyến tới knowledge base
- yêu cầu làm rõ khi thiếu employee ID hoặc thiếu ngữ cảnh
- xử lý các yêu cầu ngoài phạm vi
- xử lý việc người dùng sửa thông tin qua nhiều lượt hội thoại
- hủy hành động sau khi trước đó đã yêu cầu thực hiện
- sử dụng nhiều công cụ song song cho các yêu cầu hỗn hợp
- xử lý yêu cầu chỉ định dạng nội dung mà không gọi lại dữ liệu một cách không cần thiết

## 3. Các file liên quan

- `starter_v0/data/eval_group.json`
- `starter_v0/artifacts/reflections/member4_eval.md`

## 4. Xác thực và bằng chứng

Tôi đã xác thực cấu trúc JSON và kiểm tra số lượng test case theo từng loại:

- tổng số test case: 10
- single-turn: 5
- multi-turn: 5

Lệnh xác thực được sử dụng:

```powershell
cd "C:\Users\Chi Cong\K4A-Day04-GooseGooseDuck\starter_v0"

python -c "import json; d=json.load(open(r'data\eval_group.json', encoding='utf-8')); print('total=', len(d['cases'])); print('single=', sum('query' in c for c in d['cases'])); print('multi=', sum('turns' in c for c in d['cases']))"
```

Kết quả quan sát được:

```text
total= 10
single= 5
multi= 5
```

Điều này xác nhận rằng bộ dữ liệu đáp ứng đúng định dạng và số lượng yêu cầu của group suite.

## 5. Bài học rút ra

Vai trò này rất quan trọng vì một bộ đánh giá tốt không chỉ kiểm tra xem mô hình có trả lời được câu hỏi hay không. Nó còn xác minh xem agent có hành xử đúng trong các tình huống helpdesk thực tế hay không, chẳng hạn như:

- thay đổi asset ID giữa cuộc hội thoại
- thay đổi service nhưng vẫn giữ đúng ngữ cảnh environment
- hủy một hành động trước đó khi người dùng rút lại yêu cầu
- lựa chọn nhiều hơn một công cụ khi yêu cầu cần nhiều nguồn bằng chứng
- ưu tiên chỉ dẫn mới nhất của người dùng so với các thông tin ở những lượt trước

Đây chính là những trường hợp biên giúp phát hiện liệu agent có thực sự hiểu cách định tuyến công cụ và duy trì ngữ cảnh hội thoại hay không.

## 6. Ghi chú cuối cùng

Với vai trò **Evaluation & Test Author**, tôi đã đóng góp bộ kiểm thử nhóm gốc, giúp nhóm đánh giá xem helpdesk agent có đang được cải thiện theo cách có thể đo lường và tái lập hay không. Bộ dữ liệu này hữu ích trong việc xác thực độ chính xác của định tuyến công cụ, tính đúng đắn của tham số, khả năng xử lý hội thoại nhiều lượt và việc tuân thủ các ranh giới hành động trước khi dự án được hoàn thiện.
>>>>>>> 2ed42848b5b06b70ef673edbfb7eb04ff6e2f33d
