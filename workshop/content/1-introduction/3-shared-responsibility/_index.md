---
title: "AWS Shared Responsibility Model"
weight: 3
chapter: false
pre: "<b>1.3.</b> "
---

## Xác định việc AWS làm và việc bạn phải làm

Lab sử dụng **EKS managed node groups**, không dùng Fargate hoặc Auto Mode. Ranh giới trách nhiệm phụ thuộc lựa chọn compute.

| Thành phần | AWS quản lý | Bạn cấu hình và kiểm chứng |
|---|---|---|
| EKS control plane | Hạ tầng và vận hành control plane | Endpoint exposure, access entries, authorization |
| Managed node group | Cơ chế provisioning/update tích hợp | Chọn phiên bản AMI, rollout cập nhật, IAM, IMDS, workload placement |
| VPC | Hạ tầng mạng AWS | Subnet, route, SG/NACL, outbound |
| Workload | Kubernetes API/compute nền | Image, pod privileges, NetworkPolicy, identity |
| RDS | Hạ tầng dịch vụ DB theo cấu hình | Public access, SG, users/grants, backup, encryption |

### Thực hành đọc ranh giới

**Console:** EKS → Compute → node group, ghi phiên bản AMI release và Kubernetes version. RDS → database → Connectivity & security, xác nhận Publicly accessible = No.

```bash
aws eks describe-nodegroup --cluster-name eks-did --nodegroup-name private-workers \
  --query 'nodegroup.{status:status,version:version,release:releaseVersion}'
aws rds describe-db-instances --db-instance-identifier eks-did \
  --query 'DBInstances[0].{public:PubliclyAccessible,encrypted:StorageEncrypted,multiAZ:MultiAZ}'
```

Mong đợi: node group `ACTIVE`, DB private và encrypted. `MultiAZ=false` là giảm chi phí lab, không phải khuyến nghị HA cho production.

### Bài học

Có encryption không đồng nghĩa mọi người đều bị chặn đọc dữ liệu: IAM/SQL/RBAC vẫn quyết định quyền truy cập. Có managed nodes không đồng nghĩa node image luôn được cập nhật theo yêu cầu của bạn. Trong Terraform, cấu hình ở `aws_eks_node_group.private` và `aws_db_instance.this`; xem [mã hạ tầng](/source/terraform/main.tf).


![Ảnh AWS Console thực tế](/images/console-eks.png "EKS cluster thực tế: trạng thái Active, version 1.35 và managed control plane.")
