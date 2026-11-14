---
title: "NetworkPolicy Enforcement with Amazon VPC CNI"
weight: 3
chapter: false
pre: "<b>3.3.</b> "
---

Kubernetes can accept a NetworkPolicy even without an enforcement engine. Enable Amazon VPC CNI NetworkPolicy and confirm its node agents before interpreting connectivity tests.

## What enforces the policy?

Kubernetes stores rules through its API. VPC CNI's network policy agent enforces them using eBPF on each Linux worker. This lab uses EC2 managed nodes; verify support before choosing another compute platform.

## Step 1: enable the feature

1. **EKS → cluster → Add-ons → Amazon VPC CNI → Edit**.
2. Choose a version compatible with your EKS version, kernel, and instances using AWS documentation.
3. In optional configuration values, enable `enableNetworkPolicy`:

```json
{"enableNetworkPolicy":"true"}
```

4. Save and wait for `ACTIVE`. If the add-on is self-managed, do not overlay a second managed copy on the existing DaemonSet.

![EKS CNI and identity add-ons](/images/console-eks-addons.png "① Pod Identity Agent. ② Amazon VPC CNI. ③ Dedicated CNI IAM role.")

The screenshot establishes installation and role assignment. Verify the feature configuration and running policy-agent container below.

### Optional EKS API equivalent

If not already enabled:

```bash
aws eks update-addon --cluster-name eks-did --addon-name vpc-cni \
  --configuration-values '{"enableNetworkPolicy":"true"}' --resolve-conflicts PRESERVE
```

Preserve existing custom `configuration-values`: read the configuration before updating. Terraform uses `aws_eks_addon.vpc_cni` in [main.tf](/source/terraform/main.tf).

## Check every worker node

### Confirm configuration and agent containers

```bash
aws eks describe-addon --cluster-name eks-did --addon-name vpc-cni \
  --query 'addon.{version:addonVersion,status:status,configuration:configurationValues}'
kubectl get daemonset aws-node -n kube-system
kubectl get pods -n kube-system -l k8s-app=aws-node \
  -o jsonpath='{range .items[*]}{.metadata.name}{"  "}{.spec.containers[*].name}{"\n"}{end}'
```

Expect `aws-eks-nodeagent` alongside `aws-node`. Names can vary by release; compare images/add-on version. The DaemonSet must cover both nodes.

### Standard and strict mode

The lab starts in standard mode: a new pod may have a window before policy reconciliation completes. Strict mode starts with default deny, requiring explicit DNS, credential, and dependency access. This is NetworkPolicy enforcement mode, distinct from Security Groups for Pods mode.

Do not infer isolation from add-on status alone. Run the same connectivity comparison before/after policy and record the startup window as a limitation; this lab does not claim zero-window isolation.

Consult current [EKS NetworkPolicy documentation](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy.html) before changing compute/CNI.

ACTIVE status plus an agent on each node are prerequisites. Actual evidence comes from frontend-to-API success and unrelated-pod denial in 3.2; a listed policy object alone proves no enforcement.
