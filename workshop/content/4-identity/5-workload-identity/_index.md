---
title: "Workload Identity: IRSA vs EKS Pod Identity"
weight: 5
chapter: false
pre: "<b>4.5.</b> "
---

## Mỗi chức năng một role, không nhúng access key

![Cấp temporary credentials theo workload](/images/workload-identity.svg)

| | IRSA | EKS Pod Identity — app của lab |
|---|---|---|
| Liên kết | OIDC trust + ServiceAccount annotation | EKS association namespace/ServiceAccount/role |
| Cấp credentials | STS AssumeRoleWithWebIdentity | Agent + EKS Auth + SDK credential provider |
| Khi chọn | Cấu hình hiện có, môi trường/compute cần IRSA | EKS compute được hỗ trợ, muốn quản lý association qua EKS |
| Dependency | OIDC provider, STS, SDK | Agent, EKS Auth, SDK tương thích |

Lab dùng Pod Identity cho API, worker, db-init và controller. VPC CNI dùng IRSA riêng để bootstrap mạng không phụ thuộc node IMDS. Không gán đồng thời hai cơ chế cho cùng một workload rồi đoán SDK dùng cái nào.

### Console: tạo trust và association

1. EKS → Add-ons: Pod Identity Agent `ACTIVE` trên managed nodes.
2. IAM → tạo các role `eks-did-api`, `eks-did-worker`, `eks-did-db-init`, `eks-did-controller`.
3. Trust service principal `pods.eks.amazonaws.com`, actions `sts:AssumeRole`, `sts:TagSession`. Dùng điều kiện session tags giới hạn namespace/ServiceAccount như [data-services.tf](/source/terraform/data-services.tf).
4. EKS → Access → Pod Identity associations: namespace `notes`, ServiceAccount tương ứng `api`, `worker`, `db-init`; controller là `kube-system/aws-load-balancer-controller`.
5. Gắn identity policies theo 4.6. Association có thể tạo trước ServiceAccount nhưng workload chỉ chạy đúng khi cả hai có mặt.

### CLI/API: tạo và đọc association

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

### Kiểm chứng identity trong pod

```bash
kubectl exec -n notes deployment/api -- python -c \
  'import boto3; print(boto3.client("sts").get_caller_identity()["Arn"])'
```

ARN phải là assumed role `eks-did-api`, không phải node role. Egress phải cho agent `169.254.170.23:80` và AWS APIs cần thiết. `automountServiceAccountToken: false` tắt token Kubernetes API mặc định; Pod Identity vẫn có projected token riêng do EKS cấp, không mâu thuẫn với cấu hình đó.
