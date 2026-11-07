---
title: "Tổng quan kiến trúc và các Security Layers"
weight: 4
chapter: false
pre: "<b>1.4.</b> "
---

## Đọc hệ thống qua ba luồng

![AWS architecture với VPC, subnet, EKS, RDS và SQS](/images/aws-architecture.svg "Khung nét đứt biểu diễn ranh giới mạng/logical. Association chứng chỉ/WAF không phải network hop.")

**Luồng ứng dụng:** client phân giải DNS rồi kết nối ALB bằng HTTPS. ALB mở kết nối đến frontend pod trên 8080. Nginx proxy `/api/` qua Service API. API dùng TLS đến RDS, ký token IAM DB auth cho user `notes_api`.

**Luồng nền:** API gửi SQS message. Worker chủ động long-poll SQS, đếm ghi chú và ghi report bằng SQL role `notes_worker`. SQS không đẩy inbound connection vào worker.

**Luồng quản trị:** `kubectl` đến EKS API endpoint qua đường riêng; IAM xác thực, EKS authorizer/RBAC phân quyền. Request này không qua ALB ứng dụng.

### Workload identity là luồng cấp credentials

Pod Identity association liên kết namespace/ServiceAccount với IAM role. SDK lấy credentials tạm thời qua agent; API/worker sau đó dùng credentials để gọi SQS hoặc ký token RDS. Đây không phải đường mà HTTP request từ người dùng phải lần lượt đi qua.

### Những lựa chọn cố định trong lab

| Lựa chọn | Lý do | Đánh đổi |
|---|---|---|
| ALB `ip` | VPC CNI cung cấp pod IP định tuyến được | Phải hiểu pod readiness và target registration |
| Private nodes, RDS isolated | Giảm điểm vào public | Cần outbound cho image/API và đường quản trị phù hợp |
| NetworkPolicy + node SG | Ít thành phần, dễ quan sát | SG không phân biệt từng pod; pod isolation do policy engine |
| Pod Identity | Temporary credentials, role theo ServiceAccount | Cần agent/EKS Auth và SDK tương thích |
| Một NAT, RDS Single-AZ | Giảm chi phí sandbox | Không đạt HA đa AZ cho toàn hệ thống |

**Console:** xem VPC Resource map và EKS Resources. **CLI:** `kubectl get pods,svc,ingress -n notes -o wide`. Đối chiếu pod IP với target group ở 2.6.

Tải [AWS draw.io](/images/aws-architecture.drawio) hoặc [high-level draw.io](/images/high-level.drawio) để chỉnh sửa. Các hình dùng icon từ bộ AWS/Kubernetes đã thống nhất.
