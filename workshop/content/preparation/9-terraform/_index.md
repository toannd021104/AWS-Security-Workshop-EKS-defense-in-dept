---
title: "Terraform: tạo toàn bộ hạ tầng lab"
weight: 15
chapter: false
pre: ""
sequenceSkip: true
previousLesson: "/preparation/1-workstation/"
nextLesson: "/preparation/7-deploy-application/"
---

## Chọn nhánh triển khai

Nhánh Terraform **thay thế toàn bộ các bước tạo hạ tầng trên Console 0.2–0.6**. Sau khi hoàn thành công cụ và tài khoản ở bước 0.1, có thể thực hiện ngay trang này, không cần tạo VPC, EKS hoặc các dịch vụ bằng tay trước.

| Các bước Console được thay thế | Terraform tạo tương ứng |
|---|---|
| 0.2 — VPC | VPC, public/private/database subnets, routing, Internet Gateway, NAT Gateway |
| 0.3 — EKS | Cluster, IAM roles, managed nodes, launch template, OIDC provider và add-ons |
| 0.4 — Dịch vụ dữ liệu | RDS, database Security Group, SQS và ECR |
| 0.5 — HTTPS/WAF | ACM certificate, DNS validation và WAF Web ACL khi bật `enable_waf` |
| 0.6 — Quyền workload | IAM roles/policies và Pod Identity associations |

Domain và public hosted zone được chuẩn bị ở 0.1; Terraform sử dụng hosted zone đó. **Build image, cài controller, triển khai ứng dụng/Ingress, tạo record ứng dụng và kiểm tra baseline vẫn thực hiện ở 0.7–0.8.** ALB được controller tạo từ Ingress ở bước triển khai.

Chọn một nhánh tạo tài nguyên cho mỗi môi trường; Terraform không phải bước bổ sung sau khi đã tạo xong bằng Console.

Nếu đã tạo bằng Console, có thể đọc mã Terraform để đối chiếu cấu hình. `terraform apply` với state rỗng sẽ cố tạo lại các tài nguyên cùng tên, nên không dùng nó như bước tiếp theo của nhánh Console.

## Cấu hình đầu vào

Hoàn thành công cụ, profile AWS và domain ở [bước 0.1](/preparation/1-workstation/), cài [Terraform CLI](https://developer.hashicorp.com/terraform/install), rồi chạy từ thư mục source:

```bash
source .venv/bin/activate
export AWS_PROFILE=guru AWS_REGION=us-east-1
aws sts get-caller-identity
curl -fsS https://checkip.amazonaws.com
cp infrastructure/terraform/terraform.tfvars.example infrastructure/terraform/terraform.tfvars
```

Sửa `terraform.tfvars`:

```hcl
admin_cidr = "YOUR_WORKSTATION_IP/32"
dns_zone_name = "YOUR_PUBLIC_ZONE."
enable_waf = true
enable_kms = true
enable_inspector = true
```

Thay IP và zone bằng giá trị thật. Các flags liên quan dịch vụ bị giới hạn bởi quyền truy cập hoặc chính sách tài khoản chỉ được tắt khi đã ghi nhận phần bài tương ứng chưa được kiểm chứng. WAF cần cho phép thử edge; KMS và Inspector được dùng ở chương 5.

## Tạo hạ tầng

```bash
terraform -chdir=infrastructure/terraform init
terraform -chdir=infrastructure/terraform fmt -check
terraform -chdir=infrastructure/terraform validate
terraform -chdir=infrastructure/terraform plan -out=lab.tfplan
```

`validate` cần báo cấu hình hợp lệ. Đọc plan: account/Region đúng, chỉ tạo tài nguyên lab và không có thay đổi tài nguyên khác. Sau đó:

```bash
terraform -chdir=infrastructure/terraform apply lab.tfplan
```

Chờ apply hoàn tất. Terraform tạo VPC, EKS/nodes/add-ons, RDS/SQS/ECR, ACM/WAF, workload roles/associations và các tài nguyên được bật trong cấu hình. Nó chưa build image và chưa triển khai frontend/API/worker.

State và plan lưu thông tin hạ tầng nhạy cảm; giữ ngoài Git và website. Nhóm nhiều người cần remote backend và locking phù hợp trước khi cùng thao tác state.

## Triển khai và kiểm tra

Sau `Apply complete`, tiếp tục [bước 0.7: Build image và triển khai ứng dụng](/preparation/7-deploy-application/), rồi [bước 0.8: Baseline](/preparation/8-baseline/). `capture-config.py` đọc tài nguyên AWS thực tế nên dùng chung cho cả Console và Terraform.

Cleanup của nhánh này gỡ tài nguyên do Kubernetes controller tạo trước, sau đó dùng đúng state để destroy. Xem [hướng dẫn cleanup](/cleanup/).
