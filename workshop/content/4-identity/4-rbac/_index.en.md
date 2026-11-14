---
title: "Kubernetes RBAC: Role, ClusterRole, and Bindings"
weight: 4
chapter: false
pre: "<b>4.4.</b> "
---

EKS recognizes observer, but it still needs explicit resource/verb permissions. Grant workload read access in namespace `notes` and test real observer credentials.

## Read access within a namespace

A Role is namespace-scoped. A ClusterRole can describe cluster-scoped access or be reused through a RoleBinding. RoleBinding grants within its namespace; ClusterRoleBinding applies cluster-wide. Grants are additive; there is no deny Role overriding another allow.

## Step 1: Role and RoleBinding

Confirm observer's EKS group and absence of administrator policies. The resource browser can display roles/bindings according to viewer permissions. Define the Role:

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

Save it to `.local/observer-rbac.yaml`, then append this RoleBinding:

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

Apply using the lab administrator identity:

```bash
kubectl apply -f .local/observer-rbac.yaml
```

[render.py](/source/scripts/render.py) also includes these resources. Do not add a ClusterRoleBinding for observer.

## Test allowed and denied access as observer

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws eks update-kubeconfig --name eks-did \
  --role-arn "arn:aws:iam::$ACCOUNT_ID:role/eks-did-observer" \
  --kubeconfig .local/observer-kubeconfig --alias observer
kubectl --kubeconfig .local/observer-kubeconfig get pods -n notes
kubectl --kubeconfig .local/observer-kubeconfig auth can-i patch deployments -n notes
kubectl --kubeconfig .local/observer-kubeconfig get secrets -n notes
```

Expect pod listing to succeed, patch permission `no`, and Secret read `Forbidden`. Use server-side dry run to test a Deployment change without changing it:

```bash
kubectl --kubeconfig .local/observer-kubeconfig patch deployment api -n notes \
  --type merge -p '{"spec":{"replicas":1}}' --dry-run=server
```

It must be denied. `--as` impersonation is not a substitute for proving the IAM role can authenticate; these tests use real observer credentials.

### Permissions with indirect consequences

`pods/exec`, Secret reads, pod creation with another ServiceAccount, and edits to Ingress/RoleBinding can expand access considerably. Observer has none of them. Avoid wildcard verbs/resources for convenience.
