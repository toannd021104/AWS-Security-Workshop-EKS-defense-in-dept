---
title: "Human Access: AWS IAM & EKS Access Entries"
weight: 3
chapter: false
pre: "<b>4.3.</b> "
---

## Từ IAM role đến Kubernetes group

Lab dùng role `eks-did-observer`, access entry map vào group `notes-observers`. Group được bind vào Role chỉ đọc của namespace `notes`. Không associate thêm policy admin cho role này.

### Console: tạo đúng đường cấp quyền

1. IAM → Roles → Create role → Custom trust policy. Cho phép **IAM principal quản trị lab của bạn** `sts:AssumeRole`; không dùng wildcard principal hoặc hardcode principal của account ví dụ.
2. Đặt `eks-did-observer`. Identity policy chỉ cần `eks:DescribeCluster` cho ARN cluster `eks-did` để lấy endpoint/config. Kubernetes verbs không nằm trong policy này.
3. EKS → cluster → Access → Create access entry: chọn role ARN, type Standard, Kubernetes group `notes-observers`.
4. Không associate `AmazonEKSClusterAdminPolicy`. Bài tiếp theo tạo RoleBinding.



![Ảnh AWS Console thực tế](/images/console-access.png "Observer map vào group notes-observers và không có access policy admin; bootstrap identity được quản lý riêng.")

### CLI/API tương đương

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OBSERVER_ARN="arn:aws:iam::$ACCOUNT_ID:role/eks-did-observer"
aws eks list-access-entries --cluster-name eks-did
aws eks describe-access-entry --cluster-name eks-did --principal-arn "$OBSERVER_ARN"
aws eks list-associated-access-policies --cluster-name eks-did --principal-arn "$OBSERVER_ARN"
```

Nếu tạo bằng API thay Console, sau khi role tồn tại:

```bash
aws eks create-access-entry --cluster-name eks-did \
  --principal-arn "$OBSERVER_ARN" --type STANDARD --kubernetes-groups notes-observers
```

Không tạo trùng entry đã có. Terraform chứa `aws_iam_role.observer`, `aws_eks_access_entry.observer` tại [data-services.tf](/source/terraform/data-services.tf).

### Gotcha: permissions có thể cộng thêm

EKS access policies và RBAC có thể cùng cấp quyền. RoleBinding read-only không thu hồi quyền admin từ một access policy khác. Kiểm tra cả hai trước khi kết luận observer bị hạn chế. Không xóa bootstrap/admin hiện tại trước khi identity thay thế đã đăng nhập và thực hiện đủ quyền quản trị cần thiết.
