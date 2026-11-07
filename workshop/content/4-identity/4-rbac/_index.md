---
title: "Kubernetes RBAC: Role, ClusterRole và Bindings"
weight: 4
chapter: false
pre: "<b>4.4.</b> "
---

## Role định nghĩa quyền; Binding gắn quyền với chủ thể

Role có phạm vi namespace. ClusterRole có thể dùng cho cluster-scoped resources hoặc tái sử dụng qua RoleBinding. RoleBinding cấp quyền trong namespace; ClusterRoleBinding có phạm vi toàn cluster. Các quyền được cộng dồn, không có deny Role để hủy allow khác.

### Console trước

EKS → Access xác nhận observer group và không có admin policy. Kubernetes Resources có thể hiển thị roles/bindings tùy quyền của người xem. Tạo Role bằng manifest:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: observer
  namespace: notes
rules:
  - apiGroups: [""]
    resources: ["pods", "services"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch"]
```

RoleBinding của lab gắn Role này với group `notes-observers`, xem manifest tạo bởi [render.py](/source/scripts/render.py).

### CLI: thử bằng credentials thật

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws eks update-kubeconfig --name eks-did \
  --role-arn "arn:aws:iam::$ACCOUNT_ID:role/eks-did-observer" \
  --kubeconfig .local/observer-kubeconfig --alias observer
kubectl --kubeconfig .local/observer-kubeconfig get pods -n notes
kubectl --kubeconfig .local/observer-kubeconfig auth can-i patch deployments -n notes
kubectl --kubeconfig .local/observer-kubeconfig get secrets -n notes
```

Mong đợi: list pods thành công, patch `no`, đọc Secret `Forbidden`. Dùng server-side dry run để thử sửa Deployment mà không thay đổi workload thật:

```bash
kubectl --kubeconfig .local/observer-kubeconfig patch deployment api -n notes \
  --type merge -p '{"spec":{"replicas":1}}' --dry-run=server
```

Phải bị từ chối. `--as` là impersonation test, không thay thế việc chứng minh IAM role đăng nhập được; bộ kiểm tra dùng observer credentials thật.

### Quyền “chỉ deploy app” vẫn cần review

`pods/exec`, đọc Secret, tạo pod với ServiceAccount khác, sửa Ingress hoặc RoleBinding có thể mang lại quyền gián tiếp đáng kể. Lab observer không có các quyền đó. Không cấp wildcard verbs/resources vì tiện demo.
