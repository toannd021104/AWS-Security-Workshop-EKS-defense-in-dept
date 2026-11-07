---
title: "Authentication vs Authorization"
weight: 1
chapter: false
pre: "<b>4.1.</b> "
---

Người vận hành dùng kubectl, trong khi API và worker gọi AWS services. Các hoạt động này đi qua những hệ thống xác thực và phân quyền khác nhau. Bài này phân biệt các bước đó để xác định đúng lớp kiểm soát khi một request được cho phép hoặc bị từ chối.

## Hai quyết định trong một lần truy cập

Authentication xác định chủ thể; authorization quyết định chủ thể được phép làm hành động nào với resource nào. Hai câu hỏi xuất hiện ở cả Kubernetes, AWS API và database, nhưng do các hệ thống khác nhau trả lời.

| Hành động | Xác thực | Phân quyền |
|---|---|---|
| Người vận hành chạy `kubectl get pods` | EKS IAM authentication | EKS access policy / Kubernetes RBAC |
| API gửi SQS message | AWS temporary credentials | IAM và queue resource policy |
| API ghi vào RDS | IAM DB token | `rds-db:connect` và PostgreSQL grants |
| Người dùng đọc ghi chú | Chưa có trong app demo | Chưa có; không dùng app cho dữ liệu nhạy cảm |

## Bước 1: đối chiếu các danh tính

Mở IAM role của API trong IAM Console và Access Entry của observer trong EKS Console. Sau đó thực hiện các lệnh ở phần kiểm chứng để phân biệt danh tính terminal với quyền Kubernetes.

## Kiểm tra danh tính và quyền tương ứng

### Quan sát danh tính và quyền truy cập

Trong terminal của người quản trị, chạy:

```bash
aws sts get-caller-identity
kubectl auth can-i list pods -n notes
kubectl auth can-i get secrets -n notes
```

Với admin hiện tại, câu trả lời có thể đều `yes`; điều đó không chứng minh observer được hạn chế. Bài 4.4 sẽ dùng credentials của observer thật để thử lại.

### Khi nào bị từ chối ở đâu?

Network timeout không phải `AccessDenied`. Kubernetes trả `Forbidden` khi đã nhận request nhưng principal không có permission cần thiết. AWS trả authorization error khi request được xử lý nhưng thiếu quyền hoặc có explicit deny. PostgreSQL có thể chấp nhận kết nối nhưng từ chối một câu SQL.

Terraform tạo role và access entry; YAML Role/RoleBinding quy định Kubernetes verbs. Không dùng NetworkPolicy để giải quyết lỗi `sqs:SendMessage AccessDenied`, cũng không thêm IAM policy để chữa một connection timeout. Phân biệt các kết quả này giúp xác định lớp kiểm soát cần kiểm tra.

Lệnh `get-caller-identity` xác định AWS principal của terminal. `kubectl auth can-i` trả lời quyền Kubernetes của danh tính đang dùng. Giữ kết quả của admin để đối chiếu với role observer ở bài 4.4; không dùng quyền admin làm bằng chứng cho quyền của observer.
