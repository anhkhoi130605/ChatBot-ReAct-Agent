---
article_id: KB-VPN-006
title: Gia hạn certificate VPN trên macOS
category: vpn
updated_at: 2026-09-01
tags: [vpn, macos, certificate, expiry]
---

## Scope

Dùng khi VPN client trên macOS cảnh báo certificate sắp hết hạn.

## Steps

1. Kiểm tra ngày giờ hệ thống và trạng thái VPN production.
2. Không xóa certificate hiện tại trước khi certificate mới được cấp thành công.
3. Khởi động approved VPN client và chọn quy trình renew certificate.
4. Không yêu cầu người dùng gửi private key, password hoặc MFA code.
5. Nếu renew thất bại, tạo ticket sau khi người dùng xác nhận.
