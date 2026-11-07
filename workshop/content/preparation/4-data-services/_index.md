---
title: "Tạo RDS PostgreSQL, SQS và ECR"
weight: 4
chapter: false
pre: "<b>0.4.</b> "
---

## Mục tiêu chuẩn bị

API lưu ghi chú trên RDS. Worker dùng cùng database với SQL user riêng và nhận công việc qua SQS. ECR chứa image do bạn build cho API, worker và Job khởi tạo database.

## Tạo database Security Group và subnet group

1. EKS → cluster → **Configuration → Networking**, copy **Cluster security group ID**. Managed nodes của lab sử dụng group này vì launch template không ghi đè Security Groups.
2. VPC → **Security groups → Create**, tên `eks-did-database`, VPC `eks-did`. Thêm inbound PostgreSQL TCP `5432`, source là **cluster Security Group ID** vừa lấy. Giữ outbound mặc định của lab.
3. RDS → **Subnet groups → Create DB subnet group**, tên `eks-did-database`, VPC `eks-did`. Chọn hai AZ và **hai database subnets** `10.20.64.0/24`, `10.20.65.0/24`.

Security Group này giới hạn nguồn ở mức node. NetworkPolicy sẽ bổ sung giới hạn theo pod trong chương 3.

## Tạo RDS PostgreSQL

1. RDS → **Databases → Create database → Standard create**, engine **PostgreSQL 17**, chọn phiên bản khả dụng trong nhánh 17. Lượt lab dùng `17.11`.
2. DB instance identifier `eks-did`, master username `labadmin`, chọn **Manage master credentials in AWS Secrets Manager**.
3. Chọn instance `db.t3.micro`, Single-AZ, storage **20 GiB gp3**, bật storage encryption. Single-AZ là lựa chọn giảm chi phí của môi trường thực hành.
4. Connectivity: VPC `eks-did`, DB subnet group vừa tạo, **Public access: No**, chỉ gắn Security Group `eks-did-database`. Không tạo thêm kết nối EC2 tự động.
5. Database authentication: **Password and IAM database authentication**. Additional configuration → Initial database name: **`notes`**.
6. Backup retention 1 ngày cho lab; kiểm tra lại các lựa chọn có tính phí trước khi tạo. Đợi database **Available**.

Xác nhận các thông số bằng CLI:

```bash
aws rds describe-db-instances --db-instance-identifier eks-did \
  --query 'DBInstances[0].{Status:DBInstanceStatus,Database:DBName,Public:PubliclyAccessible,IAM:IAMDatabaseAuthenticationEnabled,Encrypted:StorageEncrypted,ResourceID:DbiResourceId,SecretARN:MasterUserSecret.SecretArn}'
```

Kết quả cần có `Status=available`, `Database=notes`, `Public=false`, `IAM=true`, `Encrypted=true`, có ResourceID và SecretARN. Lưu ý **DB resource ID** có dạng `db-…`, dùng cho IAM policy; nó khác identifier `eks-did`.

## Tạo SQS queue

1. SQS → **Queues → Create queue**, type **Standard**, tên `eks-did-reports`.
2. Visibility timeout **60 giây**, message retention **1 ngày**, giữ các cấu hình khác ở giá trị phù hợp cho lab.
3. Encryption: bật server-side encryption, chọn **Amazon SQS key (SSE-SQS)**. Access policy không cấp quyền public; role API/worker sẽ có identity policies riêng.
4. Tạo queue, ghi lại **Queue URL** và **Queue ARN**. URL dùng khi gọi API SQS; ARN dùng trong IAM policy.

![Queue và cơ chế mã hóa](/images/console-sqs-encryption.png "① Cột Encryption. ② Queue sử dụng SSE-SQS.")

## Tạo ECR repository

1. ECR → **Private repositories → Create repository**, tên `eks-did/notes`.
2. Image tag mutability **Immutable**, encryption **AES-256**. Bật basic scan on push ở cấu hình registry nếu được phép; enhanced scanning được thực hành ở chương 5.
3. Tạo repository và ghi Repository URI. Repository chưa có image ở thời điểm này.

## Kiểm tra tài nguyên sẵn sàng

```bash
aws sqs get-queue-url --queue-name eks-did-reports
aws ecr describe-repositories --repository-names eks-did/notes \
  --query 'repositories[0].{URI:repositoryUri,Mutability:imageTagMutability,Encryption:encryptionConfiguration.encryptionType}'
```

SQS trả QueueUrl; ECR trả URI của đúng account, mutability `IMMUTABLE`, encryption `AES256`. RDS phải Available trước khi triển khai Job khởi tạo ở bước 7.

Tiếp tục [chuẩn bị certificate và WAF](/preparation/5-https-waf/).
