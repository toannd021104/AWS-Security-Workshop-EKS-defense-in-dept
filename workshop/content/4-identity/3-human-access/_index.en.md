---
title: "Human Access: AWS IAM & EKS Access Entries"
weight: 3
chapter: false
pre: "<b>4.3.</b> "
---

A user needs application status without cluster administration. Create an observer role, map it into EKS, and configure its Kubernetes permissions in the next lesson.

**Terraform path:** observer role and Access Entry already exist. Inspect rather than recreate them. **Console path:** create missing resources here. Both continue with the same observer test in 4.4.

## From IAM principal to Kubernetes identity

Role `eks-did-observer` maps to group `notes-observers`, bound to a read-only Role in namespace `notes`. Do not associate an additional administrator access policy.

## Step 1: IAM role and Access Entry

Terraform users compare existing trust/permissions with the following. Console users create the role/entry if absent.

First identify the lab account:

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OBSERVER_ARN="arn:aws:iam::$ACCOUNT_ID:role/eks-did-observer"
aws sts get-caller-identity --query Arn --output text
```

Choose the IAM principal allowed to assume observer. Use an IAM user ARN directly. If the output is `arn:aws:sts::…:assumed-role/…`, open **IAM → Roles → current administrator role → Summary** and obtain the **IAM role ARN**, including any path. Do not paste an STS session ARN.

Replace `YOUR_ADMIN_IAM_PRINCIPAL_ARN` in the custom trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": "YOUR_ADMIN_IAM_PRINCIPAL_ARN"},
    "Action": "sts:AssumeRole"
  }]
}
```

The **observer role** identity policy only describes the lab cluster. Replace `YOUR_ACCOUNT_ID` with the actual `$ACCOUNT_ID`:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "eks:DescribeCluster",
    "Resource": "arn:aws:eks:us-east-1:YOUR_ACCOUNT_ID:cluster/eks-did"
  }]
}
```

The calling administrator also needs `sts:AssumeRole` on `$OBSERVER_ARN`, subject to permissions boundaries/SCPs. If missing, add this statement to an appropriate policy on the **administrator principal**, not the observer:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "sts:AssumeRole",
    "Resource": "arn:aws:iam::YOUR_ACCOUNT_ID:role/eks-did-observer"
  }]
}
```

Replace all placeholders before using these JSON documents. These IAM permissions do not grant Kubernetes verbs.

1. **IAM → Roles → Create role → Custom trust policy**: trust your administrator IAM principal for `sts:AssumeRole`. Avoid wildcard principals and example-account identities.
2. Name it `eks-did-observer`; grant only `eks:DescribeCluster` for cluster `eks-did` to obtain endpoint configuration.
3. **EKS → cluster → Access → Create access entry**: role ARN, Standard type, Kubernetes group `notes-observers`.
4. Do not associate `AmazonEKSClusterAdminPolicy`. The next lesson creates the RoleBinding.

![Observer Access Entry](/images/console-observer-access.png "① Observer role. ② notes-observers group. ③ Access policies column.")

Observer uses the Kubernetes group without an EKS administrator policy. Other screenshot entries belong to nodes, add-ons, or lab administrators.

### Optional Access Entry API

After the role exists:

```bash
aws eks create-access-entry --cluster-name eks-did \
  --principal-arn "$OBSERVER_ARN" --type STANDARD --kubernetes-groups notes-observers
```

Do not duplicate an existing entry. Terraform uses `aws_iam_role.observer` and `aws_eks_access_entry.observer` in [data-services.tf](/source/terraform/data-services.tf).

## Verify the entry and all permission sources

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OBSERVER_ARN="arn:aws:iam::$ACCOUNT_ID:role/eks-did-observer"
aws eks list-access-entries --cluster-name eks-did
aws eks describe-access-entry --cluster-name eks-did --principal-arn "$OBSERVER_ARN"
aws eks list-associated-access-policies --cluster-name eks-did --principal-arn "$OBSERVER_ARN"
```

EKS access policies and RBAC can both grant permissions. A read-only RoleBinding does not revoke administrator access granted elsewhere. Inspect both before claiming restriction. Keep bootstrap/admin access until a replacement identity has successfully performed the required administration.

The entry must map the correct role to `notes-observers`, and associated access policies must be empty for this lab. Next, bind RBAC and test this actual role's allowed and denied operations.
