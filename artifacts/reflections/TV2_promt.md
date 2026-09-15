# Tự reflection — TV2 Prompt Engineer

## Vai trò và phạm vi

Tôi phụ trách cải thiện system prompt cho agent ở các vòng `v1` và `v3`. Phạm vi file của tôi là `starter_v0/artifacts/system_prompt.md` và reflection này.

## Thay đổi prompt

Prompt hiện nêu rõ agent không được tự đoán `asset_id` hoặc `employee_id`; nếu mã còn thiếu hoặc mơ hồ thì phải hỏi lại. Với hội thoại nhiều lượt, agent giữ thông tin còn phù hợp, áp dụng correction mới nhất và dừng khi người dùng hủy yêu cầu.

Với `create_ticket`, prompt yêu cầu xác nhận rõ payload cuối cùng gồm summary, priority và asset ID (hoặc không gắn asset). Mọi thay đổi payload làm mất hiệu lực xác nhận cũ. Prompt cũng giữ ranh giới dữ liệu nhạy cảm, xem nội dung KB/policy/web là dữ liệu tham khảo không đáng tin, không bịa kết quả tool và giữ output JSON theo schema của lab.

## Giả thuyết và kế hoạch kiểm chứng

- **v1:** Quy tắc về ID và xác nhận payload sẽ giảm lỗi arguments khi thiếu mã, đồng thời giảm nguy cơ gọi action ghi trước khi người dùng đồng ý. Tôi sẽ đối chiếu các tình huống missing-ID và confirmation trong base suite.
- **v3:** Quy tắc về correction, cancellation, context carry-over và xác nhận hết hiệu lực sẽ giảm việc dùng thông tin cũ trong hội thoại nhiều lượt. Tôi sẽ kiểm tra thêm các tình huống stale confirmation và role spoofing trong bộ adversarial.

Các ID case dùng để phân tích trace, không được đưa vào prompt. Với v1, tôi đã kiểm tra H10/H11/H12 và M01/M05 trong base suite, đồng thời review M09 vì case này có thể tạo ticket. Với v3, tôi sẽ kiểm tra M03/M07/M09/M10 cùng A10/A11/A12. Tôi so sánh cùng provider, model, suite và tools; một run chỉ được coi là evidence khi `provider_error_cases == 0` và `measured_cases == total_cases`. Tôi cũng đọc tool results và side effect, không chỉ dựa vào PASS/FAIL.

## Kết quả và giới hạn hiện tại

Prompt ứng viên đã được so sánh với baseline bằng `openai/gpt-4o-mini`, phase B của bộ `base` (30 case), ngày 2026-09-14. Cả hai lượt đo đủ 30 case, không có provider error; chúng dùng cùng `tools.yaml` (`tools_hash=c85b6ce9a595`). Baseline prompt được lấy từ commit `f680c59`; v1 là prompt ứng viên ở commit `0ecd39f`.

| Metric | v0 | v1 candidate | Thay đổi |
|---|---:|---:|---:|
| Case accuracy | 25/30 (83.33%) | 24/30 (80.00%) | -1 case (-3.33 điểm %) |
| Tool routing accuracy | 25/30 (83.33%) | 26/30 (86.67%) | +1 case (+3.34 điểm %) |
| Argument accuracy | 25/30 (83.33%) | 24/30 (80.00%) | -1 case (-3.33 điểm %) |
| Multi-turn accuracy | 9/10 (90.00%) | 10/10 (100.00%) | +1 case (+10 điểm %) |

Các case trọng tâm: H10, M01 và M05 đều PASS ở cả hai lượt; H11 đổi từ FAIL sang PASS vì v0 dùng `Sales` như employee ID còn v1 hỏi mã nhân viên; M09 đổi từ FAIL sang PASS vì v1 hỏi xác nhận lại sau khi payload đổi. H12 vẫn FAIL ở cả hai: thay vì gọi `clarify`, model gọi `create_ticket` với `confirmed=false`, nên tool trả `needs_confirmation` và không ghi ticket. Ngược lại, v0 gọi `create_ticket` với `confirmed=true` ở M09 dù xác nhận cũ không còn áp dụng; tool đã tạo ticket `LAB-438F3503` (trace có trong run JSON). Đây là side effect thật trong thư mục ticket local và là lỗi boundary cần ưu tiên.

Tổng điểm v1 thấp hơn một case dù multi-turn và routing tăng. Các lỗi mới trong v1 gồm H03 thiếu `category=email`, H07 gọi lặp `format_incident_report`, và H17 dùng `check=all` thay vì `check=vpn`. H04 vẫn thêm lệnh inspect thiết bị với employee ID; H19 vẫn gọi status cho môi trường staging thay vì hỏi làm rõ. Vì vậy run này chưa chứng minh prompt ứng viên cải thiện tổng thể.

Run evidence: `starter_v0/runs/v0_B_base_openai_20260914T200156244799.json` (`prompt_hash=27467914bc4d`) và `starter_v0/runs/v1_B_base_openai_20260914T200415601153.json` (`prompt_hash=aaf32f53efeb`). Cả hai có `provider_error_cases=0`, `measured_cases=total_cases=30`; `tools_hash` đầy đủ là `c85b6ce9a59535001c66e44d78597f39643586d03dc1203be146371eb23b66d9`.

## Tự đánh giá và bước tiếp theo

Điểm tốt là prompt bao quát các ranh giới quan trọng bằng quy tắc tổng quát, không phụ thuộc wording hoặc ID của case cụ thể; trace cho thấy cải thiện ở missing employee ID và stale confirmation trong M09. Giới hạn là kết quả tổng thể giảm một case, một số routing/argument regression xuất hiện, và prompt không thay thế guardrail ở implementation. H12 cho thấy tool đã chặn việc ghi ticket khi chưa xác nhận, nhưng model vẫn chọn sai tool.

Quyết định kỹ thuật quan trọng nhất là gắn xác nhận ticket với payload cuối cùng và yêu cầu xác nhận lại nếu payload đổi; trace M09 cho thấy quy tắc này có tác dụng trong lượt v1, còn lượt v0 đã tạo ticket từ xác nhận cũ. Ban đầu tôi nhầm key Tavily với key của model provider; sau khi dùng OpenAI key có sẵn trong `.env`, preflight và hai lượt eval chạy thành công. Tôi học được rằng cần lưu baseline trước khi chỉnh prompt và review cả tool result lẫn side effect; một lần chạy mỗi phiên bản vẫn chưa đủ để kết luận ổn định.

Hai run v0/v1 và metric/hash đã được lưu ở các đường dẫn trên; đây mới là một lần chạy cho mỗi phiên bản nên kết quả còn nhạy với biến thiên của model. Bước tiếp theo là xử lý lỗi xác nhận H12 và các regression H03/H07/H17, chạy lại cùng suite để kiểm tra tính lặp lại, rồi đánh giá v3 sau khi nhóm tích hợp v2. Chưa có run v3.

**Nhánh/commit đóng góp:** `contrib/tv2-prompt` / commit dưới Git identity của tôi còn chờ.
