---
title: "Tổng quan kiến trúc và các Security Layers"
weight: 4
chapter: false
pre: "<b>1.4.</b> "
---

Ứng dụng của workshop là một website ghi chú chạy trên Amazon EKS. Kiến trúc được chia thành ba workload: Nginx frontend, Python API và Python worker. RDS PostgreSQL lưu dữ liệu; SQS tách việc tạo báo cáo khỏi request trực tiếp của người dùng.

![Kiến trúc AWS của workshop](/images/aws-architecture.svg "ALB nằm trong public subnets; worker nodes nằm trong private application subnets; RDS sử dụng database subnets riêng. Khung nét đứt biểu diễn các ranh giới mạng và logical.")

### Luồng truy cập ứng dụng

Trình duyệt phân giải domain và kết nối ALB bằng HTTPS. ALB kết thúc TLS rồi chuyển request bằng HTTP đến frontend pod port 8080. Nginx phục vụ giao diện và chuyển các request `/api/` đến Kubernetes Service của API. API kết nối RDS bằng TLS và sử dụng IAM database authentication với user `notes_api`.

> **Phạm vi mã hóa và bảo vệ kết nối:** Lab sử dụng HTTPS để mã hóa lưu lượng từ Internet đến ALB. Từ ALB đến frontend pod và từ frontend đến API, ứng dụng sử dụng HTTP qua địa chỉ IP nội bộ trong VPC. Security Groups giới hạn kết nối ở lớp hạ tầng; Kubernetes NetworkPolicy được bổ sung trong chương 3 để giới hạn kết nối theo workload. Đây là lựa chọn của lab để tập trung thực hành bảo mật mạng và workload trên EKS.

### Luồng xử lý báo cáo

API gửi message vào SQS khi nhận yêu cầu tạo báo cáo. Worker chủ động đọc queue, lấy dữ liệu cần thiết và ghi báo cáo vào RDS bằng user `notes_worker`. SQS không mở kết nối inbound vào worker; worker không cần public endpoint hoặc Kubernetes Service riêng.

### Luồng quản trị và cấp quyền

Người vận hành dùng `kubectl` kết nối đến EKS API endpoint. Đường quản trị này đi riêng với ALB phục vụ website. IAM xác thực danh tính; EKS Access Entries và Kubernetes RBAC cấp quyền thao tác tài nguyên.

API và worker sử dụng EKS Pod Identity để nhận temporary AWS credentials theo ServiceAccount. Sau đó ứng dụng dùng credentials này để gọi SQS hoặc ký token kết nối RDS. Frontend không cần IAM role ứng dụng.

### Các lựa chọn trong lab

ALB sử dụng IP targets để chuyển request đến pod IP do VPC CNI cấp. NetworkPolicy kiểm soát kết nối theo workload; node Security Groups tiếp tục bảo vệ ở lớp tài nguyên AWS. Các lựa chọn và trường hợp thay thế được giải thích trong chương tương ứng.

Lab sử dụng một NAT Gateway và RDS Single-AZ để giảm chi phí. Đây là các đánh đổi của môi trường thực hành; kiến trúc production cần đánh giá thêm yêu cầu availability và đường kết nối private.

Có thể tải [sơ đồ AWS dạng draw.io](/images/aws-architecture.drawio) và [sơ đồ high-level dạng draw.io](/images/high-level.drawio) để xem hoặc chỉnh sửa. Chương 2 bắt đầu bằng việc theo dõi một request qua kiến trúc này.
