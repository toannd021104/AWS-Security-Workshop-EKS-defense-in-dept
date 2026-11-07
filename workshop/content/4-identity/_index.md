---
title: "Identity & Access Management – Securing Permissions"
weight: 5
chapter: false
pre: "<b>4.</b> "
---

Một pod kết nối được đến AWS endpoint chưa có nghĩa nó được phép thực hiện mọi API. Tương tự, người dùng có thể xác thực với AWS nhưng chưa có quyền sửa tài nguyên Kubernetes.

Phần này theo hai đường truy cập: người quản trị đến EKS API và workload đến dịch vụ AWS. Giới hạn endpoint, gắn danh tính qua Access Entries, cấp quyền đọc bằng RBAC, rồi đối chiếu Pod Identity và IAM policies của API/worker.

Các role cần để Notes hoạt động đã có từ phần chuẩn bị. Dùng danh tính observer để thử quyền thực tế và so sánh thao tác SQS hợp lệ với thao tác vượt quyền. Cuối phần, cần chỉ ra được principal nào bị từ chối và lớp nào đưa ra quyết định.

## Các bài trong phần này

4.1. [Authentication vs Authorization](/4-identity/1-authentication-authorization/)

4.2. [EKS API Endpoint Security](/4-identity/2-endpoint/)

4.3. [Human Access: AWS IAM & EKS Access Entries](/4-identity/3-human-access/)

4.4. [Kubernetes RBAC: Role, ClusterRole và Bindings](/4-identity/4-rbac/)

4.5. [Workload Identity: IRSA vs EKS Pod Identity](/4-identity/5-workload-identity/)

4.6. [Least Privilege và IAM Policies](/4-identity/6-least-privilege/)
