---
title: "Human Access: AWS IAM & EKS Access Entries"
weight: 3
chapter: false
pre: "<b>4.3.</b> "
---

Một người cần xem trạng thái ứng dụng mà không có quyền quản trị cluster. Bài này tạo IAM role observer và đưa danh tính đó vào EKS qua Access Entry; quyền Kubernetes cụ thể sẽ được cấu hình ở bài RBAC.

## Từ IAM principal đến danh tính Kubernetes

Lab dùng role `eks-did-observer`, access entry map vào group `notes-observers`. Group được bind vào Role chỉ đọc của namespace `notes`. Không associate thêm policy admin cho role này.

## Bước 1: tạo IAM role và Access Entry

1. IAM → Roles → Create role → Custom trust policy. Cho phép **IAM principal quản trị lab của bạn** `sts:AssumeRole`; không dùng wildcard principal hoặc hardcode principal của account ví dụ.

2. Đặt `eks-did-observer`. Identity policy chỉ cần `eks:DescribeCluster` cho ARN cluster `eks-did` để lấy endpoint/config. Kubernetes verbs không nằm trong policy này.

3. EKS → cluster → Access → Create access entry: chọn role ARN, type Standard, Kubernetes group `notes-observers`.

4. Không associate `AmazonEKSClusterAdminPolicy`. Bài tiếp theo tạo RoleBinding.

![Observer Access Entry trên EKS](/images/console-observer-access.png "① Observer role. ② Group notes-observers. ③ Cột access policies.")

Dòng observer sử dụng Kubernetes group và không có EKS access policy admin. Những entries khác trong ảnh thuộc node, add-on hoặc danh tính quản trị của lab.

### Tạo Access Entry qua API (tùy chọn)

Nếu tạo bằng API thay Console, sau khi role tồn tại:

```bash
aws eks create-access-entry --cluster-name eks-did \
  --principal-arn "$OBSERVER_ARN" --type STANDARD --kubernetes-groups notes-observers
```

Không tạo trùng entry đã có. Terraform chứa `aws_iam_role.observer`, `aws_eks_access_entry.observer` tại [data-services.tf](/source/terraform/data-services.tf).

## Kiểm tra Access Entry và các nguồn cấp quyền

### Đối chiếu Access Entry và access policies

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OBSERVER_ARN="arn:aws:iam::$ACCOUNT_ID:role/eks-did-observer"
aws eks list-access-entries --cluster-name eks-did
aws eks describe-access-entry --cluster-name eks-did --principal-arn "$OBSERVER_ARN"
aws eks list-associated-access-policies --cluster-name eks-did --principal-arn "$OBSERVER_ARN"
```


### Kiểm tra các nguồn cấp quyền

EKS access policies và RBAC có thể cùng cấp quyền. RoleBinding read-only không thu hồi quyền admin từ một access policy khác. Kiểm tra cả hai trước khi kết luận observer bị hạn chế. Không xóa bootstrap/admin hiện tại trước khi identity thay thế đã đăng nhập và thực hiện đủ quyền quản trị cần thiết.

Access Entry phải chứa đúng observer role và group `notes-observers`. Danh sách associated access policies của observer phải rỗng trong thiết kế lab. Bài 4.4 tiếp tục tạo RoleBinding và dùng chính role này để kiểm tra quyền đọc và quyền bị từ chối.
