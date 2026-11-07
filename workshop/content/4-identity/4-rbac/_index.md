---
title: "Kubernetes RBAC: Role, ClusterRole và Bindings"
weight: 4
chapter: false
pre: "<b>4.4.</b> "
---

## Vấn đề

Role observer đã được EKS nhận diện, nhưng vẫn cần quy định những tài nguyên và thao tác được phép. Bài này cấp quyền đọc workload trong namespace notes và kiểm tra bằng credentials thật của observer.

## Kiến thức cần dùng

Role có phạm vi namespace. ClusterRole có thể dùng cho cluster-scoped resources hoặc tái sử dụng qua RoleBinding. RoleBinding cấp quyền trong namespace; ClusterRoleBinding có phạm vi toàn cluster. Các quyền được cộng dồn, không có deny Role để hủy allow khác.

## Thực hiện

### Tạo Role và RoleBinding

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

Lưu Role trên vào `.local/observer-rbac.yaml` và bổ sung RoleBinding:

```yaml
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: observer
  namespace: notes
subjects:
  - kind: Group
    name: notes-observers
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: observer
  apiGroup: rbac.authorization.k8s.io
```

Áp dụng bằng danh tính admin của lab:

```bash
kubectl apply -f .local/observer-rbac.yaml
```

Các tài nguyên này cũng có trong [manifest do render.py tạo](/source/scripts/render.py). Không gắn thêm ClusterRoleBinding cho observer.

## Kiểm chứng kết quả

### Đăng nhập bằng observer và thử quyền

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

### Các quyền có khả năng mở rộng phạm vi truy cập

`pods/exec`, đọc Secret, tạo pod với ServiceAccount khác, sửa Ingress hoặc RoleBinding có thể mang lại quyền gián tiếp đáng kể. Lab observer không có các quyền đó. Không cấp wildcard verbs/resources vì tiện demo.
