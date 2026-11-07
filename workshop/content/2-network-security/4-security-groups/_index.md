---
title: "Network Access Control: Security Groups & NACLs"
weight: 4
chapter: false
pre: "<b>2.4.</b> "
---

## SG stateful, NACL stateless

SG gắn vào ENI, tổng hợp allow rules và theo dõi connection. NACL gắn subnet, có allow/deny theo thứ tự và phải cho cả chiều trả về. Chúng không thay thế NetworkPolicy chọn pod theo label.

### Console: dựng và đọc các rule

1. VPC → Security groups → Create `eks-did-database` trong VPC lab. Inbound TCP 5432, **source là cluster/node SG thực tế**, không phải `0.0.0.0/0`. Gắn SG này vào RDS.
2. EKS → Networking → cluster security group. EC2 → node → Network interface kiểm tra SG thực sự gắn vào node/ENI. Lab launch template không đặt SG thay thế, nên managed nodes dùng cluster SG.
3. Sau khi tạo Ingress, xem SG do controller tạo cho ALB và rule cho backend. Listener chỉ mở 80/443; backend cần 8080 từ SG của load-balancing path, không public 8080.
4. VPC → Network ACLs → xem association và rule numbers. Lab giữ default NACL để tập trung SG/NetworkPolicy; không tự siết ephemeral ports khi chưa có traffic matrix.

### CLI/API: xem bằng chứng

```bash
aws ec2 describe-security-group-rules \
  --filters "Name=group-id,Values=$NODE_SG" \
  --query 'SecurityGroupRules[].{egress:IsEgress,port:FromPort,to:ToPort,source:ReferencedGroupInfo.GroupId,cidr:CidrIpv4}'
aws ec2 describe-network-acls --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'NetworkAcls[].{id:NetworkAclId,associations:Associations[].SubnetId,rules:Entries}'
```

Nếu tạo database SG bằng API, `AuthorizeSecurityGroupIngress` dùng referenced group:

```bash
aws ec2 authorize-security-group-ingress --group-id "$DB_SG_ID" \
  --ip-permissions "IpProtocol=tcp,FromPort=5432,ToPort=5432,UserIdGroupPairs=[{GroupId=$NODE_SG}]"
```

Không thêm lại rule đã tồn tại. Terraform dùng `aws_vpc_security_group_ingress_rule.database`.

### Giới hạn phải hiểu

Tất cả pod dùng node SG có thể đi qua lớp SG đến RDS nếu không có kiểm soát bổ sung. **SG này không chỉ cho phép API/worker.** Module 3 dùng NetworkPolicy chặn frontend → RDS, còn PostgreSQL grants và IAM DB auth giới hạn quyền sử dụng DB. Security Groups for Pods là lựa chọn nâng cao khi cần SG theo workload, không được bật trong lab này.
