---
title: "Workload Identity: IRSA vs EKS Pod Identity"
weight: 5
chapter: false
pre: "<b>4.5.</b> "
---

API cần gửi message vào SQS, còn worker cần nhận và xóa message. Hai workload cần danh tính AWS riêng mà không lưu access key trong container. Bài này so sánh IRSA với EKS Pod Identity và cấu hình association theo từng ServiceAccount.

## Pod nhận AWS credentials như thế nào?

AWS SDK sử dụng temporary credentials do cơ chế workload identity cấp. Pod Identity association liên kết cluster, namespace và ServiceAccount với một IAM role; IAM policy của role quy định thao tác AWS được phép. IRSA thực hiện liên kết bằng OIDC trust và ServiceAccount annotation.

![Cấp temporary credentials theo workload](/images/workload-identity.svg)

| | IRSA | EKS Pod Identity — app của lab |
|---|---|---|
| Liên kết | OIDC trust + ServiceAccount annotation | EKS association namespace/ServiceAccount/role |
| Cấp credentials | STS AssumeRoleWithWebIdentity | Agent + EKS Auth + SDK credential provider |
| Khi chọn | Cấu hình hiện có, môi trường/compute cần IRSA | EKS compute được hỗ trợ, muốn quản lý association qua EKS |
| Dependency | OIDC provider, STS, SDK | Agent, EKS Auth, SDK tương thích |

Lab dùng Pod Identity cho API, worker, db-init và controller. VPC CNI dùng IRSA riêng để bootstrap mạng không phụ thuộc node IMDS. Không gán đồng thời hai cơ chế cho cùng một workload rồi đoán SDK dùng cái nào.

Các tài nguyên này đã được dựng trong [phần chuẩn bị lab](/preparation/6-workload-permissions/). Đối chiếu cấu hình hiện có theo các bước dưới đây; chỉ tạo mới nếu tài nguyên tương ứng chưa tồn tại.

## Bước 1: tạo trust policy và Pod Identity associations

1. EKS → Add-ons: Pod Identity Agent `ACTIVE` trên managed nodes.

2. IAM → tạo các role `eks-did-api`, `eks-did-worker`, `eks-did-db-init`, `eks-did-controller`.

3. Trust service principal `pods.eks.amazonaws.com`, actions `sts:AssumeRole`, `sts:TagSession`. Dùng điều kiện session tags giới hạn namespace/ServiceAccount như [data-services.tf](/source/terraform/data-services.tf).

![Trust policy của API role](/images/console-api-trust.png "① pods.eks.amazonaws.com. ② sts:AssumeRole. ③ sts:TagSession.")

Phần Condition phía dưới giới hạn namespace `notes` và ServiceAccount `api`. Trust policy xác định bên được assume role; permissions policy xác định role được gọi AWS API nào.

4. EKS → Access → Pod Identity associations: namespace `notes`, ServiceAccount tương ứng `api`, `worker`, `db-init`; controller là `kube-system/aws-load-balancer-controller`.

![Pod Identity associations của ứng dụng](/images/console-pod-identity.png "① Namespace notes. ② ServiceAccount api. ③ ServiceAccount worker.")

Đọc cùng hàng từ IAM role đến namespace và ServiceAccount để kiểm tra association. API và worker sử dụng role khác nhau dù cùng namespace.

5. Gắn identity policies theo 4.6. Association có thể tạo trước ServiceAccount nhưng workload chỉ chạy đúng khi cả hai có mặt.

### Đọc association qua EKS API (tùy chọn)

```bash
aws eks list-pod-identity-associations --cluster-name eks-did
kubectl get daemonset eks-pod-identity-agent -n kube-system
```

Ví dụ API tạo association **nếu chưa tồn tại**:

```bash
aws eks create-pod-identity-association --cluster-name eks-did \
  --namespace notes --service-account api --role-arn "$API_ROLE_ARN"
```

Terraform tự quản lý `aws_eks_pod_identity_association.workload`. Sau khi đổi association, rollout pod để credentials injection/caches phản ánh đúng cấu hình.

## Kiểm tra AWS role thực tế trong pod

### Xác nhận IAM role bên trong pod

```bash
kubectl exec -n notes deployment/api -- python -c \
  'import boto3; print(boto3.client("sts").get_caller_identity()["Arn"])'
```

ARN phải là assumed role `eks-did-api`, không phải node role. Egress phải cho agent `169.254.170.23:80` và AWS APIs cần thiết. `automountServiceAccountToken: false` tắt token Kubernetes API mặc định; Pod Identity vẫn có projected token riêng do EKS cấp, không mâu thuẫn với cấu hình đó.

ARN trả về phải chứa `assumed-role/eks-did-api/`, không phải node role. Association trên Console và ARN quan sát bên trong pod cung cấp hai bằng chứng: cấu hình liên kết đúng và ứng dụng thực sự nhận đúng danh tính.
