---
title: "Create EKS, CNI role, and managed workers"
weight: 30
chapter: false
pre: "<b>0.3.</b> "
---

## Preparation goal

Create a managed EKS control plane and two EC2 workers in private application subnets. Give VPC CNI its own role so networking initializes with node IMDSv2 required and hop limit 1.

## Create cluster and node IAM roles

**IAM → Roles → Create role**:

| Role | Trusted entity | Permissions |
|---|---|---|
| `eks-did-cluster-role` | AWS service → EKS → EKS Cluster | `AmazonEKSClusterPolicy` |
| `eks-did-node-role` | AWS service → EC2 | `AmazonEKSWorkerNodePolicy`, `AmazonEC2ContainerRegistryPullOnly` |

The control plane uses the cluster role; workers use the node role. Application SQS/database access belongs to separate workload roles later.

## Create the cluster

1. **EKS → Clusters → Add cluster → Create**: `eks-did`, Kubernetes **1.35**, the cluster role above.
2. Choose custom configuration with **managed node groups**; disable **EKS Auto Mode** for this architecture.
3. Select VPC `eks-did` and both **private application subnets**. Retain the EKS-managed cluster SG.
4. Endpoint **Public and private**. Obtain your workstation public IP:

```bash
curl -fsS https://checkip.amazonaws.com
```

Enter the actual IP with `/32`. `203.0.113.10/32` is only an example.

5. Choose authentication mode **EKS API**, retaining bootstrap administrator access for the creating principal.
6. Keep compatible managed CoreDNS, kube-proxy, and VPC CNI add-ons. Create/wait for **Active**; do not create nodes yet.

If terminal and Console use different principals, configure CLI administration first: **EKS → Access → Create access entry**, CLI IAM principal, Standard, associate **AmazonEKSClusterAdminPolicy**, scope **Cluster** for the lab administrator. With SSO/assumed roles, use the IAM role ARN from IAM Console, not an STS session ARN. This bootstraps lab administration; chapter 4 separately restricts observer.

![Created EKS cluster](/images/console-eks.png "Active cluster and reference Kubernetes version.")

New EKS interfaces place networking under **Configuration → Networking**. Compare endpoint and allowlist:

![EKS endpoint configuration](/images/console-eks-endpoint.png "① Public and private endpoint. ② Workstation-specific public CIDR.")

## Create OIDC provider and CNI IRSA role

1. Copy the cluster **OpenID Connect provider URL** from EKS.
2. **IAM → Identity providers → Add provider → OpenID Connect**: issuer URL, audience `sts.amazonaws.com`.
3. **IAM → Roles → Create → Web identity**: that provider/audience, `AmazonEKS_CNI_Policy`, name `eks-did-vpc-cni-role`.
4. **Trust relationships → Edit**: restrict to the CNI ServiceAccount. Replace `ACCOUNT_ID` and `OIDC_HOSTPATH`; the latter is the issuer **without `https://`**:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/OIDC_HOSTPATH"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {"StringEquals": {
      "OIDC_HOSTPATH:aud": "sts.amazonaws.com",
      "OIDC_HOSTPATH:sub": "system:serviceaccount:kube-system:aws-node"
    }}
  }]
}
```

Read values for comparison:

```bash
aws sts get-caller-identity --query Account --output text
aws eks describe-cluster --name eks-did --query 'cluster.identity.oidc.issuer' --output text
```

5. **EKS → Add-ons → Amazon VPC CNI → Edit**: select the CNI role under IAM role for service account (IRSA). Add optional configuration:

```json
{"enableNetworkPolicy":"true"}
```

Preserve other custom settings. Save and verify role/configuration. Check pod/add-on status after compute exists; CoreDNS can be Pending before nodes. Do not apply application NetworkPolicy yet.

6. **Get more add-ons → Amazon EKS Pod Identity Agent**: install a compatible managed version. It starts once nodes exist.

![Lab add-ons](/images/console-eks-addons.png "① Pod Identity Agent. ② VPC CNI. ③ CNI IRSA role.")

## Create launch template and managed node group

1. **EC2 → Launch templates → Create** `eks-did-nodes`. Leave AMI, instance type, subnet, instance profile, and SGs unspecified for EKS/node-group configuration. Do not select a key pair.
2. Root `/dev/xvda`: **20 GiB gp3**, encrypted, Delete on termination Enabled.
3. **Advanced details → Metadata options**: endpoint Enabled, **IMDSv2 required**, hop limit **1**. Save the template version.
4. **EKS → cluster → Compute → Add node group**: `private-workers`, role `eks-did-node-role`, use that launch template/version.
5. Choose compatible AL2023 x86_64, `t3.medium`, On-Demand, desired/min/max **2**. If AMI/type fields are locked, check for template overrides.
6. Select both private application subnets, disable remote SSH, and wait for **Active**.

## Connect kubectl and verify

```bash
source scripts/env.sh
aws eks update-kubeconfig --name eks-did --alias eks-did --kubeconfig "$KUBECONFIG"
kubectl get nodes -o wide
kubectl get pods -n kube-system
```

Illustrative output; node names/IPs differ:

```text
NAME                         STATUS   ROLES    AGE   VERSION
ip-10-20-35-10.ec2.internal   Ready    <none>   5m    v1.35.x
ip-10-20-51-20.ec2.internal   Ready    <none>   5m    v1.35.x
```

Require two Ready nodes with no external public IPs and running aws-node/CoreDNS/kube-proxy/Pod Identity Agent. If nodes do not join, inspect NAT routes, CNI IRSA, and node IAM. For kubectl connection issues, check your current public IP against the allowlist.

Continue to [RDS, SQS, and ECR](/preparation/4-data-services/).
