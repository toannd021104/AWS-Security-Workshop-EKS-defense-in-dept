---
title: "Chuẩn bị lab"
weight: 2
chapter: false
pre: ""
---

Phần này dựng ứng dụng nền từ một tài khoản AWS trước khi thực hành các lớp bảo vệ. Hoàn thành công cụ và tài khoản, sau đó chọn một trong hai cách tạo hạ tầng bên dưới.

Ứng dụng gồm frontend, API và worker trên EKS; database dùng RDS và hàng đợi dùng SQS. Có thể xem [kiến trúc tổng quan](/1-introduction/4-architecture/) trước khi bắt đầu.

## Chọn cách tạo hạ tầng trước khi bắt đầu

1. Hoàn thành [0.1: tài khoản, công cụ và mã nguồn](/preparation/1-workstation/).
2. Chọn **[Terraform: tạo toàn bộ hạ tầng lab](/preparation/9-terraform/)** để thay thế các bước Console 0.2–0.6, hoặc chọn **[Console: tạo từng thành phần](/preparation/2-vpc/)**.
3. Cả hai nhánh đều tiếp tục ở [0.7: triển khai ứng dụng](/preparation/7-deploy-application/) và [0.8: baseline](/preparation/8-baseline/).

**Không tạo hạ tầng bằng Console rồi chạy thêm Terraform với state rỗng.** Hai nhánh là hai lựa chọn thay thế nhau.

## Tài liệu cho từng bước

0.1. [Tài khoản AWS, công cụ và mã nguồn](/preparation/1-workstation/)

[Terraform: tạo toàn bộ hạ tầng lab](/preparation/9-terraform/)

0.2. [Tạo VPC, subnets và đường định tuyến](/preparation/2-vpc/)

0.3. [Tạo EKS, CNI role và managed worker nodes](/preparation/3-eks/)

0.4. [Tạo RDS PostgreSQL, SQS và ECR](/preparation/4-data-services/)

0.5. [Chuẩn bị domain, ACM certificate và WAF](/preparation/5-https-waf/)

0.6. [Cấp IAM roles và Pod Identity cho workload](/preparation/6-workload-permissions/)

0.7. [Build image và triển khai ứng dụng lên EKS](/preparation/7-deploy-application/)

0.8. [Kiểm tra lab hoạt động trước khi học các lớp bảo vệ](/preparation/8-baseline/)

## Trình tự thực hiện

**Nhánh Console:** 0.1 → 0.2 → 0.3 → 0.4 → 0.5 → 0.6 → 0.7 → 0.8.

**Nhánh Terraform:** 0.1 → Terraform (thay thế 0.2–0.6) → 0.7 → 0.8.

Sau bước 0.8, lab có domain HTTPS, ba workload chạy được, đọc/ghi RDS và xử lý SQS. NetworkPolicy chưa được áp dụng để còn quan sát trạng thái trước/sau trong chương 3. Cấu hình non-root và quyền workload cần để chạy ứng dụng đã nằm trong baseline; các chương sau giải thích và kiểm chứng chi tiết.

Ảnh được chụp từ lab tham chiếu; các output mẫu có chú thích và giá trị minh họa. Thay account ID, domain, resource IDs và IP bằng giá trị của môi trường đang sử dụng. [Cleanup](/cleanup/) hướng dẫn dừng tài nguyên có tính phí khi kết thúc.
