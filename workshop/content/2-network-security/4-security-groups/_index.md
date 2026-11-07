---
title: "Network Access Control: Security Groups & NACLs"
weight: 4
chapter: false
pre: "<b>2.4.</b> "
---

## Vấn đề

Ứng dụng cần nhận request trên 443 và kết nối database trên 5432, nhưng hai cổng này không có cùng phạm vi truy cập. Bài này cấu hình các rule theo nguồn và đích thực tế, rồi xác định giới hạn của Security Groups khi nhiều pod dùng chung node.

## Kiến thức cần dùng

Security Group gắn với network interface (ENI), tổng hợp các allow rules và theo dõi trạng thái kết nối. NACL gắn subnet, có allow/deny theo thứ tự và phải cho cả chiều trả về. Chúng không thay thế NetworkPolicy chọn pod theo label.

## Thực hiện

### Cấu hình Security Groups và xem NACLs

1. VPC → Security groups → Create `eks-did-database` trong VPC lab. Inbound TCP 5432, **source là cluster/node SG thực tế**, không phải `0.0.0.0/0`. Gắn SG này vào RDS.

2. EKS → Configuration → Networking → Cluster security group (giao diện cũ: Networking). EC2 → node → Network interface kiểm tra SG thực sự gắn vào node/ENI. Lab launch template không đặt SG thay thế, nên managed nodes dùng cluster SG.

3. Sau khi tạo Ingress, xem SG do controller tạo cho ALB và rule cho backend. Listener chỉ mở 80/443; backend cần 8080 từ SG của load-balancing path, không public 8080.

4. VPC → Network ACLs → xem association và rule numbers. Lab giữ default NACL để tập trung SG/NetworkPolicy; không tự siết ephemeral ports khi chưa có traffic matrix.

### Cấu hình Security Group qua API

Nếu tạo database SG bằng API, `AuthorizeSecurityGroupIngress` dùng referenced group:

```bash
aws ec2 authorize-security-group-ingress --group-id "$DB_SG_ID" \
  --ip-permissions "IpProtocol=tcp,FromPort=5432,ToPort=5432,UserIdGroupPairs=[{GroupId=$NODE_SG}]"
```

Không thêm lại rule đã tồn tại. Terraform dùng `aws_vpc_security_group_ingress_rule.database`.

## Kiểm chứng kết quả

### Đọc các rule đang có hiệu lực

```bash
aws ec2 describe-security-group-rules \
  --filters "Name=group-id,Values=$NODE_SG" \
  --query 'SecurityGroupRules[].{egress:IsEgress,port:FromPort,to:ToPort,source:ReferencedGroupInfo.GroupId,cidr:CidrIpv4}'
aws ec2 describe-network-acls --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'NetworkAcls[].{id:NetworkAclId,associations:Associations[].SubnetId,rules:Entries}'
```


### Phạm vi bảo vệ của node Security Group

Tất cả pod dùng node SG có thể đi qua lớp SG đến RDS nếu không có kiểm soát bổ sung. **SG này không chỉ cho phép API/worker.** Module 3 dùng NetworkPolicy chặn frontend → RDS, còn PostgreSQL grants và IAM DB auth giới hạn quyền sử dụng DB. Security Groups for Pods là lựa chọn nâng cao khi cần SG theo workload, không được bật trong lab này.

Đối chiếu inbound của database: TCP 5432 phải tham chiếu Security Group của node, không mở Internet. Luồng ghi chú ở bài 2.1 vẫn phải hoạt động. Ở bài 3.2, thử thêm frontend → RDS để kiểm chứng giới hạn theo pod; Security Group dùng chung của node chưa chứng minh được sự cách ly đó.
