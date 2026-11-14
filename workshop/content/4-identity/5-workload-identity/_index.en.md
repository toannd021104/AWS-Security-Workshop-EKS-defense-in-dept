---
title: "Workload Identity: IRSA vs EKS Pod Identity"
weight: 5
chapter: false
pre: "<b>4.5.</b> "
---

API sends SQS messages; worker receives and deletes them. Give each a separate AWS identity without storing access keys in containers.

## How does a pod receive credentials?

AWS SDKs consume temporary credentials from workload identity. A Pod Identity association maps cluster, namespace, and ServiceAccount to an IAM role; its policies define allowed AWS operations. IRSA instead uses OIDC trust and a ServiceAccount annotation.

![Temporary workload credentials](/images/en/workload-identity.svg "Pod Identity Agent supplies temporary credentials for calls such as SQS.")

| | IRSA | EKS Pod Identity — lab application |
|---|---|---|
| Mapping | OIDC trust + ServiceAccount annotation | EKS namespace/ServiceAccount/role association |
| Credential path | STS AssumeRoleWithWebIdentity | Agent + EKS Auth + SDK credential provider |
| Choose when | Existing setup or compute/environment requires IRSA | Supported EKS compute and EKS-managed associations are suitable |
| Dependencies | OIDC provider, STS, SDK | Agent, EKS Auth, compatible SDK |

API, worker, db-init, and controller use Pod Identity. VPC CNI uses separate IRSA so network bootstrap does not depend on node IMDS. Do not assign both mechanisms to one workload and guess which the SDK uses.

These resources exist from [preparation](/preparation/6-workload-permissions/); create only missing resources.

## Step 1: trust and associations

1. Confirm Pod Identity Agent `ACTIVE` on managed nodes in **EKS → Add-ons**.
2. Inspect/create roles `eks-did-api`, `eks-did-worker`, `eks-did-db-init`, and `eks-did-controller`.
3. Trust `pods.eks.amazonaws.com` for `sts:AssumeRole` and `sts:TagSession`. Restrict namespace/ServiceAccount using session-tag conditions as in [data-services.tf](/source/terraform/data-services.tf).

![API role trust policy](/images/console-api-trust.png "① pods.eks.amazonaws.com. ② sts:AssumeRole. ③ sts:TagSession.")

The Condition scopes trust to namespace `notes` and ServiceAccount `api`. Trust decides who can assume the role; permissions decide which AWS APIs the role can call.

4. **EKS → Access → Pod Identity associations**: associate `notes/api`, `notes/worker`, and `notes/db-init`; associate the controller as `kube-system/aws-load-balancer-controller`.

![Application associations](/images/console-pod-identity.png "① notes namespace. ② api ServiceAccount. ③ worker ServiceAccount.")

Read IAM role, namespace, and ServiceAccount on the same row. API/worker have distinct roles despite sharing a namespace.

5. Attach the policies from 4.6. Associations may precede ServiceAccounts, but both must exist for workloads to work.

### Optional association API

```bash
aws eks list-pod-identity-associations --cluster-name eks-did
kubectl get daemonset eks-pod-identity-agent -n kube-system
```

Create an association only if missing:

```bash
export API_ROLE_ARN=$(aws iam get-role --role-name eks-did-api --query 'Role.Arn' --output text)
aws eks create-pod-identity-association --cluster-name eks-did \
  --namespace notes --service-account api --role-arn "$API_ROLE_ARN"
```

Terraform manages `aws_eks_pod_identity_association.workload`. After changing an association, roll out pods so credential injection/caches reflect it.

## Verify the role inside a pod

```bash
kubectl exec -n notes deployment/api -- python -c \
  'import boto3; print(boto3.client("sts").get_caller_identity()["Arn"])'
```

Expect `assumed-role/eks-did-api/`, not a node role. Egress must allow agent `169.254.170.23:80` and needed AWS APIs. `automountServiceAccountToken: false` disables the default Kubernetes API token; Pod Identity has its own EKS-projected token, so those settings are compatible.

The Console association proves configuration; the observed ARN inside the pod proves which identity the application actually receives.
