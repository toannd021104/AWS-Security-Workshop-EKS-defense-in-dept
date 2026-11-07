---
title: "Authentication vs Authorization"
weight: 1
chapter: false
pre: "<b>4.1.</b> "
---

## Đăng nhập thành công chưa có nghĩa được làm mọi việc

Authentication xác định chủ thể; authorization quyết định chủ thể được phép làm hành động nào với resource nào. Hai câu hỏi xuất hiện ở cả Kubernetes, AWS API và database, nhưng do các hệ thống khác nhau trả lời.

| Hành động | Xác thực | Phân quyền |
|---|---|---|
| Người vận hành chạy `kubectl get pods` | EKS IAM authentication | EKS access policy / Kubernetes RBAC |
| API gửi SQS message | AWS temporary credentials | IAM và queue resource policy |
| API ghi vào RDS | IAM DB token | `rds-db:connect` và PostgreSQL grants |
| Người dùng đọc ghi chú | Chưa có trong app demo | Chưa có; không dùng app cho dữ liệu nhạy cảm |

### Console và CLI: quan sát hai identity

Console → IAM → role API; EKS → Access → observer access entry. Đây là hai quyền riêng.

```bash
aws sts get-caller-identity
kubectl auth can-i list pods -n notes
kubectl auth can-i get secrets -n notes
```

Với admin hiện tại, câu trả lời có thể đều `yes`; điều đó không chứng minh observer được hạn chế. Bài 4.4 sẽ dùng credentials của observer thật để thử lại.

### Khi nào bị từ chối ở đâu?

Network timeout không phải `AccessDenied`. Kubernetes trả `Forbidden` khi đã nhận request nhưng principal không có permission cần thiết. AWS trả authorization error khi request được xử lý nhưng thiếu quyền hoặc có explicit deny. PostgreSQL có thể chấp nhận kết nối nhưng từ chối một câu SQL.

Terraform tạo role và access entry; YAML Role/RoleBinding quy định Kubernetes verbs. Không dùng NetworkPolicy để giải quyết lỗi `sqs:SendMessage AccessDenied`, cũng không thêm IAM policy để chữa một connection timeout. Việc phân biệt này giúp người đọc biết bước tiếp theo phải kiểm tra lớp nào.
