---
title: "Tạo VPC, subnets và đường định tuyến"
weight: 2
chapter: false
pre: "<b>0.2.</b> "
---

## Mục tiêu chuẩn bị

ALB cần public subnets để nhận request từ Internet. Worker nodes chạy trong private application subnets; RDS sử dụng database subnets riêng. NAT Gateway cung cấp outbound cho private workers khi tải image và gọi AWS APIs.

![Kiến trúc AWS sẽ triển khai](/images/aws-architecture.svg "Ba nhóm subnet phục vụ điểm vào, workload và database.")

## Tạo VPC và subnets trên Console

1. Mở **VPC → Your VPCs → Create VPC**, chọn **VPC only**. Đặt Name `eks-did`, IPv4 CIDR `10.20.0.0/16`, tenancy Default.
2. Sau khi tạo, chọn VPC → **Actions → Edit VPC settings**, bật **DNS resolution** và **DNS hostnames**.
3. Mở **Subnets → Create subnet**, chọn VPC vừa tạo. Dùng hai AZ có sẵn trong account, ví dụ `us-east-1a` và `us-east-1b`:

| Name | AZ | IPv4 CIDR |
|---|---|---|
| `eks-did-public-a` | AZ A | `10.20.0.0/20` |
| `eks-did-public-b` | AZ B | `10.20.16.0/20` |
| `eks-did-private-a` | AZ A | `10.20.32.0/20` |
| `eks-did-private-b` | AZ B | `10.20.48.0/20` |
| `eks-did-database-a` | AZ A | `10.20.64.0/24` |
| `eks-did-database-b` | AZ B | `10.20.65.0/24` |

Tên cần chứa `-public-`, `-private-` hoặc `-database-` để script nhận diện vai trò subnet. Tên trong ảnh có hậu tố AZ hoặc số khác bảng nhưng giữ cùng quy tắc này.

![Các nhóm subnet trên Console](/images/console-subnets.png "① Public subnet. ② Private application subnet. ③ Database subnet. Các subnet 172.31 thuộc default VPC.")

4. Chọn từng private/database subnet → **Actions → Edit subnet settings**: tắt **Enable auto-assign public IPv4 address**.
5. Trong **Tags**, thêm `kubernetes.io/role/elb = 1` cho hai public subnets, và `kubernetes.io/role/internal-elb = 1` cho hai private application subnets.

## Tạo Internet Gateway, NAT và route tables

1. **Internet gateways → Create internet gateway**, tên `eks-did-igw`. Sau khi tạo, chọn **Actions → Attach to VPC**, chọn `eks-did`.
2. **Route tables → Create route table**, tên `eks-did-public`, VPC `eks-did`. Mở **Routes → Edit routes → Add route**, destination `0.0.0.0/0`, target Internet Gateway vừa attach.
3. Mở **Subnet associations → Edit subnet associations**, chọn **hai public subnets**, lưu lại.
4. **NAT gateways → Create NAT gateway**, tên `eks-did-nat`, chọn public subnet AZ A, connectivity type **Public**, chọn **Allocate Elastic IP**, tạo và chờ **Available**.
5. Tạo route table `eks-did-private`. Thêm `0.0.0.0/0` đến **NAT Gateway** vừa tạo. Trong Subnet associations, chọn hai private application subnets.
6. Tạo route table `eks-did-database-isolated`. Giữ route `10.20.0.0/16 → local` có sẵn, không thêm default route; associate hai database subnets.

| Route table | Subnets được associate | Default route |
|---|---|---|
| `eks-did-public` | Public A, B | `0.0.0.0/0 → igw-…` |
| `eks-did-private` | Application A, B | `0.0.0.0/0 → nat-…` |
| `eks-did-database-isolated` | Database A, B | Không có |

Route table phải được associate đúng subnet mới có tác dụng. Một NAT cho hai AZ là đánh đổi chi phí của lab; thiết kế production cần đánh giá availability và cross-AZ traffic.

## Kiểm tra trước khi tạo EKS

Từ thư mục lab, chạy:

```bash
export VPC_ID=$(aws ec2 describe-vpcs --filters Name=tag:Name,Values=eks-did \
  --query 'Vpcs[0].VpcId' --output text)
printf 'VPC: %s\n' "$VPC_ID"
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[].{Name:Tags[?Key==`Name`]|[0].Value,CIDR:CidrBlock,AZ:AvailabilityZone,PublicIP:MapPublicIpOnLaunch}' --output table
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'RouteTables[].{ID:RouteTableId,Subnets:Associations[].SubnetId,Routes:Routes}'
```

Kết quả cần có: sáu subnet đúng CIDR; private/database không tự cấp public IP; hai public subnets dùng IGW; hai application subnets dùng NAT; hai database subnets chỉ dùng local route. Route table main tự tạo của VPC có thể vẫn tồn tại, nhưng sáu subnet lab phải có các explicit associations nêu trên.

Tiếp tục [tạo EKS và worker nodes](/preparation/3-eks/).
