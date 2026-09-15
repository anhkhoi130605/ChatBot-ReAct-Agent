# Tool Folder Contract

Mỗi tool nằm trong thư mục riêng:

```text
tools/<tool_name>/
  TOOL.md
  tool.py
```

`tools/__init__.py` là registry dùng chung cho eval, CLI chat và UI.

Frontmatter tối thiểu của `TOOL.md`:

```yaml
---
name: tool_name
track: core | bonus
kind: live_api | local_knowledge | local_status | local_inventory | local_formatter | action | control
provider: optional_provider_name
requires_env: []
inputs: [arg_name]
outputs: [field_name]
side_effect: false | true | local_file_write
requires_confirmation: true
---
```

Chỉ action tool mới dùng `requires_confirmation`. Nếu nhóm chọn làm bonus tool,
tool đó phải dùng dữ liệu giả lập, output JSON ổn định, có lỗi rõ ràng cho input
không tồn tại và có smoke test. Không thêm dữ liệu thật, credential hoặc thông
tin cá nhân.
