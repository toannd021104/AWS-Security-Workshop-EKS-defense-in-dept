---
title: "VPC Architecture: Public & Private Subnets, Routing, NAT Gateway"
weight: 2
chapter: false
pre: "<b>2.2.</b> "
---

## Vấn đề

ALB cần tiếp nhận request từ Internet; worker nodes cần truy cập các dịch vụ AWS mà không có public IP; database chỉ cần phục vụ kết nối nội bộ. Bài này bố trí ba nhóm subnet và cấu hình route table phù hợp với từng nhu cầu.

## Kiến thức cần dùng

Route table được liên kết với subnet để xác định đường đi theo địa chỉ đích. Route `local` phục vụ kết nối trong VPC. Public subnet có route đến Internet Gateway; application subnet dùng NAT Gateway cho kết nối outbound. NAT Gateway không cung cấp đường cho Internet chủ động kết nối vào private workload.

Một subnet có route đến Internet Gateway không làm mọi EC2 trong đó tự public: tài nguyên vẫn cần địa chỉ public phù hợp và rule cho phép. Ngược lại, private subnet không tự ngăn kết nối nội bộ VPC.

| Nhóm | AZ A | AZ B | Default route |
|---|---|---|---|
| Public | 10.20.0.0/20 | 10.20.16.0/20 | Internet Gateway |
| Application | 10.20.32.0/20 | 10.20.48.0/20 | Một NAT Gateway ở AZ A |
| Database | 10.20.64.0/24 | 10.20.65.0/24 | Không có; chỉ local VPC |

## Thực hiện

Các tài nguyên này đã được dựng trong [phần chuẩn bị lab](/preparation/2-vpc/). Đối chiếu cấu hình hiện có theo các bước dưới đây; chỉ tạo mới nếu tài nguyên tương ứng chưa tồn tại.

### Tạo VPC, subnets và route tables

1. VPC → Your VPCs → Create VPC → **VPC only**, Name `eks-did`, IPv4 `10.20.0.0/16`. Bật DNS resolution và DNS hostnames trong VPC settings.

2. Subnets → Create subnet: tạo sáu subnet theo bảng, dùng hai AZ khả dụng. Đặt tên `eks-did-public-a/b`, `eks-did-private-a/b`, `eks-did-database-a/b`. Private/database không auto-assign public IP.

![Ba nhóm subnet của VPC lab](/images/console-subnets.png "① Public subnet. ② Private application subnet. ③ Database subnet.")

Các dòng khoanh đỏ thuộc VPC `eks-did`, có CIDR bắt đầu bằng `10.20`. Những dòng `172.31` còn lại thuộc default VPC của tài khoản AWS.

3. Internet Gateways → tạo `eks-did-igw`, attach vào VPC.

4. Route tables → tạo `eks-did-public`, thêm `0.0.0.0/0 → IGW`, associate đúng hai public subnets. Route local đã có sẵn.

5. NAT Gateways → tạo **public NAT**, public subnet AZ A, allocate Elastic IP. Đợi `Available`.

6. Tạo route table `eks-did-private`, thêm `0.0.0.0/0 → NAT`, associate hai application subnets.

7. Tạo route table `eks-did-database-isolated`, chỉ giữ route local, associate hai DB subnets.

8. Tag public subnets `kubernetes.io/role/elb=1`, application subnets `kubernetes.io/role/internal-elb=1`.

![Vị trí subnet và NAT trong AWS architecture](/images/aws-architecture.svg)

### Cấu hình tương đương qua API

Khi tạo thủ công, AWS API tương ứng là `CreateVpc`, `CreateSubnet`, `CreateRouteTable`, `CreateRoute` và `AssociateRouteTable`. Ví dụ tạo public route sau khi export hai ID thực:

```bash
aws ec2 create-route --route-table-id "$PUBLIC_ROUTE_TABLE_ID" \
  --destination-cidr-block 0.0.0.0/0 --gateway-id "$INTERNET_GATEWAY_ID"
```

Chỉ chạy khi route chưa tồn tại. Terraform tương ứng nằm trong [main.tf](/source/terraform/main.tf) và [data-services.tf](/source/terraform/data-services.tf).

## Kiểm chứng kết quả

### Kiểm tra routes và subnet associations

```bash
VPC_ID=$(aws ec2 describe-vpcs --filters Name=tag:Name,Values=eks-did --query 'Vpcs[0].VpcId' --output text)
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[].{id:SubnetId,cidr:CidrBlock,az:AvailabilityZone,publicIP:MapPublicIpOnLaunch}'
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'RouteTables[].{id:RouteTableId,subnets:Associations[].SubnetId,routes:Routes}'
```


### Lựa chọn một NAT Gateway cho lab

Một NAT tiết kiệm chi phí nhưng tạo phụ thuộc AZ và có thể phát sinh cross-AZ traffic. Production cần đánh giá NAT theo AZ hoặc VPC Endpoints. Endpoint cho ECR API/DKR vẫn còn dependency S3, EKS Auth, DNS và dịch vụ app; thêm một endpoint không chứng minh có thể bỏ NAT.

Kết quả đúng có ba loại route: public có `0.0.0.0/0` đến `igw-…`; application có default route đến `nat-…`; database chỉ có route local. Kiểm tra `Associations[].SubnetId` để xác nhận từng route table gắn đúng nhóm subnet. Tên subnet hoặc tên route table chưa đủ làm bằng chứng.
