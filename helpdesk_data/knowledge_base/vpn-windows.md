---
article_id: KB-VPN-001
title: Khắc phục VPN trên Windows 11
category: vpn
updated_at: 2026-08-20
tags: [vpn, windows, authentication, timeout]
---

## Scope

Dùng khi VPN client trên Windows báo lỗi xác thực hoặc timeout.

## Steps

1. Kiểm tra trạng thái dịch vụ VPN production trước khi thay đổi máy người dùng.
2. Xác nhận đồng hồ hệ thống được đồng bộ.
3. Ngắt kết nối, đóng VPN client rồi mở lại.
4. Nếu lỗi `AUTH_TIMEOUT` vẫn còn và status page đang degraded, không reset tài khoản; liên kết incident hiện hành.
5. Nếu status page bình thường, thu thập phiên bản client và tạo ticket sau khi người dùng xác nhận.
