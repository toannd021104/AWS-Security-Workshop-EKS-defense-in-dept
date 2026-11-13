---
title: "Cleanup: gỡ lab đúng thứ tự"
weight: 90
chapter: false
pre: ""
---

## Đóng website không dừng tính phí

Chạy cleanup trong đúng account/profile. Lab dùng prefix `eks-did` và kubeconfig riêng; không xóa VPC/default resources hoặc dịch vụ của người khác.

### Console: gỡ theo quan hệ phụ thuộc

Nhánh Console cần gỡ cả những tài nguyên tiền đề đã tạo thủ công. Nhánh Terraform dùng cùng thứ tự gỡ phần Kubernetes, sau đó destroy bằng đúng state; không xóa tay tài nguyên Terraform rồi bỏ qua việc đối chiếu state.

1. **Kubernetes/ALB:** xóa policy ký image trước; xóa Ingress `notes`, giữ controller chạy đến khi ALB `eks-did-notes`, target groups và SG do controller tạo đã biến mất. Gỡ Deployment probe nếu còn, namespace `notes`, Kyverno và AWS Load Balancer Controller. `cleanup.py` thực hiện phần này và dừng nếu ALB chưa được gỡ.
2. **DNS:** Route 53 → zone đang sử dụng → xóa record ứng dụng `notes`. Giữ public hosted zone, delegation và records của ứng dụng khác.
3. **EKS:** xóa managed node group `private-workers`, chờ EC2 instances kết thúc; xóa add-ons và cluster `eks-did`. Không xóa IAM roles/OIDC provider khi node/add-on còn sử dụng chúng.
4. **RDS/SQS/ECR:** xóa RDS `eks-did` theo lựa chọn snapshot cho dữ liệu cần giữ; lab disposable không giữ final snapshot. Chờ DB xóa xong rồi gỡ DB subnet group đã ghi ở RDS Connectivity (`eks-did-database` khi tạo theo Console, `eks-did` khi dùng Terraform) và SG `eks-did-database`. Xóa queue `eks-did-reports`; xóa images/signatures/test digest trước khi xóa ECR repo `eks-did/notes`. Master secret do RDS quản lý được gỡ theo lifecycle của DB; kiểm tra metadata, không chụp hoặc xuất secret value.
5. **WAF/ACM:** WAF → Web ACL `eks-did` → Associated AWS resources phải rỗng sau khi ALB bị xóa, rồi xóa Web ACL để dừng phí ACL/rules. Xóa ACM certificate của hostname lab khi không còn in use; chỉ xóa DNS validation record tương ứng, không xóa record dùng chung với certificate khác.
6. **Mạng:** xóa NAT Gateway, chờ Deleted rồi release EIP của lab. Sau khi EC2/RDS/ALB ENIs đã biến mất, xóa các SG riêng còn lại, route associations/tables và sáu subnets lab. Detach/delete IGW rồi xóa VPC `eks-did`. Không xóa default VPC hay SG của tài nguyên khác.
7. **IAM/OIDC:** detach managed policies, xóa inline policies rồi xóa các role `eks-did-cluster-role`, `eks-did-node-role`, `eks-did-vpc-cni-role`, `eks-did-api`, `eks-did-worker`, `eks-did-db-init`, `eks-did-controller`, `eks-did-observer`. Xóa OIDC provider khớp issuer của cluster vừa gỡ; không xóa provider dùng bởi cluster khác. Access Entries/Pod Identity associations thuộc cluster đã xóa không cần giữ lại.
8. **KMS/logs/Inspector:** xóa alias `alias/eks-did`, schedule deletion key lab với waiting period 7 ngày. Xem CloudWatch Logs và xóa log groups riêng của lab nếu không cần giữ. Inspector là cấu hình account/Region: chỉ disable nếu lab đã bật và không có consumer khác; không tắt scanning của account dùng chung để dọn một repository.

Ghi lại tên/ID trước khi xóa để đối chiếu. Một role còn tồn tại thường không tính phí, nhưng Web ACL, EIP, storage hoặc tài nguyên đang chạy có thể vẫn phát sinh phí sau khi đóng trang web.

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

Kiểm tra thêm WAF, EIP và các tài nguyên phụ trợ:

```bash
aws wafv2 list-web-acls --scope REGIONAL \
  --query 'WebACLs[?Name==`eks-did`].Name'
aws ec2 describe-addresses --filters Name=tag:Name,Values=eks-did-nat \
  --query 'Addresses[].AllocationId'
aws iam list-roles --query 'Roles[?starts_with(RoleName, `eks-did-`)].RoleName'
aws kms list-aliases --query 'Aliases[?AliasName==`alias/eks-did`].AliasName'
```

WAF, EIP, IAM roles và alias lab cần không còn trong kết quả. Key đã schedule deletion có thể còn trạng thái PendingDeletion đến hết waiting period; giữ Key ID trong ghi chép nếu cần đối chiếu. Kiểm tra CloudWatch log groups theo tên cluster. Giữ lại source, public key và báo cáo đã loại credentials; không upload state, registry auth secret hoặc private signing key.
