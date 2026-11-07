---
title: "Cleanup: gỡ lab đúng thứ tự"
weight: 90
chapter: false
pre: ""
---

## Đóng website không dừng tính phí

Chạy cleanup trong đúng account/profile. Lab dùng prefix `eks-did` và kubeconfig riêng; không xóa VPC/default resources hoặc dịch vụ của người khác.

### Console: những tài nguyên cần gỡ

1. EKS/Kubernetes: xóa Ingress trước, đợi controller xóa ALB, target groups và SG do nó quản lý. Sau đó gỡ namespace app, Kyverno và controller.
2. Route 53: xóa **record ứng dụng `notes`**, không xóa public hosted zone sandbox.
3. Gỡ node group/add-ons/cluster; RDS, queue, ECR lab; NAT trước khi release EIP; subnet/route/IGW/VPC sau khi ENI không còn.
4. Xóa ACM certificate và record validation thuộc cert lab. Schedule deletion CMK; xóa alias lab.
5. Inspector là account-level setting: chỉ disable nếu chính lab đã bật và không có consumer khác. Không tắt scanning toàn account dùng chung mà không review.

### CLI: gỡ tài nguyên do controller quản lý

```bash
source scripts/env.sh
python3 scripts/cleanup.py
```

Script xác nhận cluster tên `eks-did`, xóa signature policy trước, gỡ Ingress và đợi ALB biến mất, rồi xóa namespace và Helm releases. Nó không destroy VPC/RDS.

### Terraform: chỉ cho tài nguyên được quản lý bằng state này

```bash
terraform -chdir=infrastructure/terraform plan -destroy -out=destroy.tfplan
# Kiểm tra plan chỉ chứa tài nguyên lab của state này.
terraform -chdir=infrastructure/terraform apply destroy.tfplan
```

Lab cấu hình RDS `skip_final_snapshot=true` và ECR `force_delete=true` để teardown disposable data. Không dùng lựa chọn đó cho dữ liệu cần giữ. Nếu tạo bằng Console, xóa bằng Console/API hoặc import state có review, không chạy destroy trong state rỗng rồi cho rằng đã dọn xong.

### Xác minh sau cleanup

```bash
aws eks list-clusters
aws rds describe-db-instances --query 'DBInstances[].DBInstanceIdentifier'
aws elbv2 describe-load-balancers --query 'LoadBalancers[].LoadBalancerName'
aws ec2 describe-nat-gateways --filter Name=state,Values=available,pending \
  --query 'NatGateways[].{id:NatGatewayId,vpc:VpcId}'
```

Kiểm tra EIP, CloudWatch log groups và KMS PendingDeletion. Giữ lại source, public key và báo cáo đã loại credentials; không upload state, registry auth secret hoặc private signing key.
