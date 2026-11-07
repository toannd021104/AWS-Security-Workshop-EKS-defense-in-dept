---
title: "Defense in Depth là gì?"
weight: 1
chapter: false
pre: "<b>1.1.</b> "
---

## Một request hợp lệ không chứng minh toàn hệ thống an toàn

Giả sử website chỉ mở HTTPS, worker nodes không có public IP. Người dùng vẫn có thể khai thác lỗi trong API. Nếu API kết nối được mọi pod và mang quyền AWS rộng, tác động vượt xa một endpoint bị lỗi.

Defense in Depth là phối hợp nhiều lớp kiểm soát để giảm khả năng xâm nhập và giới hạn phạm vi ảnh hưởng khi một lớp không đủ. Trong workshop này, chúng ta tập trung vào **phòng ngừa và giới hạn quyền**, không dựng hệ thống detection/response.

| Câu hỏi | Lớp kiểm soát |
|---|---|
| Ai đến được điểm vào? | ALB listener, HTTPS, WAF, Security Group |
| Pod nào gọi được API? | NetworkPolicy |
| Container được chạy với đặc quyền gì? | Pod Security Admission, securityContext |
| Ai sửa được workload? | EKS Access Entry, Kubernetes RBAC |
| Pod được gọi AWS API nào? | Pod Identity và IAM policy |
| Artifact và dữ liệu được bảo vệ thế nào? | Scanning, signature gate, TLS, encryption, secret access |

### Quan sát ngay trong lab

**Console:** VPC → Subnets kiểm tra workers ở private subnet; EKS → Resources xem frontend, API, worker. Đây mới là quan sát cấu hình.

**CLI/API:** kiểm tra những controls hiện có:

```bash
kubectl get pods -n notes -o wide
kubectl get networkpolicy -n notes
kubectl get serviceaccounts -n notes
```

Nếu chưa có NetworkPolicy, namespace vẫn không tự cô lập traffic. Nếu đã có policy, vẫn cần phép thử để biết engine có thực thi.

### Quyết định của lab

Mỗi lớp có một phép thử dương và âm. Sau khi mở frontend → API, chúng ta còn thử pod không liên quan → API. Sau khi cấp API quyền gửi SQS, thử nhận message bằng cùng role phải bị từ chối.

Terraform/YAML là bản mô tả ý định; kết quả kết nối và kết quả authorization mới chứng minh hành vi. Bài kế tiếp xác định những khoảng trống cụ thể trên EKS.
