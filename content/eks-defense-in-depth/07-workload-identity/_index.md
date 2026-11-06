---
title: "7. Workload identity and secrets"
weight: 7
chapter: false
---

## Goal

Give an application a short-lived AWS identity without storing access keys in its image, environment, or Kubernetes Secret. EKS Pod Identity is the path used here; IRSA is a valid alternative when its OIDC trust model better fits your organization.

**Runnable example:** in the [Secure Payments project](https://github.com/toannd021104/AWS-Security-Workshop-EKS-defense-in-dept/tree/main/examples/secure-payments-app), the app checks that the SDK received credentials from the Pod Identity provider and returns only the provider name and expiry. The example IAM role intentionally has no AWS permissions.

## Move VPC CNI permissions off the node role

The VPC CNI needs EC2 permissions to allocate pod IP addresses. AWS recommends a separate IAM role for its `kube-system/aws-node` service account. This is a cluster add-on identity, distinct from both the node role and application roles. The procedure below uses IRSA; the same CNI add-on also supports EKS Pod Identity.

The VPC CNI managed add-on supports an IAM role directly. In **IAM → Roles → Create role → Web identity**, select this cluster's OIDC provider, set audience `sts.amazonaws.com`, and set the subject to `system:serviceaccount:kube-system:aws-node`. Attach `AmazonEKS_CNI_Policy`. This avoids putting pod-IP management permissions on every node.

The equivalent AWS API sequence first reads the OIDC issuer, then creates a trust policy restricted to the `aws-node` service account:

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OIDC_ISSUER=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" \
  --query 'cluster.identity.oidc.issuer' --output text)
OIDC_HOSTPATH="${OIDC_ISSUER#https://}"
OIDC_PROVIDER_ARN="arn:aws:iam::${ACCOUNT_ID}:oidc-provider/${OIDC_HOSTPATH}"

cat > /tmp/vpc-cni-trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "${OIDC_PROVIDER_ARN}"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {"StringEquals": {
      "${OIDC_HOSTPATH}:aud": "sts.amazonaws.com",
      "${OIDC_HOSTPATH}:sub": "system:serviceaccount:kube-system:aws-node"
    }}
  }]
}
EOF

aws iam create-role --role-name AmazonEKSVPCCNIRole \
  --assume-role-policy-document file:///tmp/vpc-cni-trust.json
aws iam attach-role-policy --role-name AmazonEKSVPCCNIRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
ROLE_ARN=$(aws iam get-role --role-name AmazonEKSVPCCNIRole \
  --query 'Role.Arn' --output text)
aws eks update-addon --cluster-name "$CLUSTER_NAME" --addon-name vpc-cni \
  --service-account-role-arn "$ROLE_ARN" --resolve-conflicts PRESERVE \
  --region "$AWS_REGION"
```

If the VPC CNI add-on is not managed yet, use `aws eks create-addon` with the same role ARN instead of `update-addon`. The Terraform fallback in [`infrastructure/terraform`](../../infrastructure/terraform/) creates this role and configures the add-on. Expected result: add-on status returns to `ACTIVE` and its role ARN is the dedicated role. Confirm it:

```bash
aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name vpc-cni \
  --region "$AWS_REGION" --query 'addon.{Status:status,Role:serviceAccountRoleArn}'
```

Existing `aws-node` pods may need to restart to receive the updated identity; watch the DaemonSet recover one node at a time:

```bash
kubectl rollout restart daemonset/aws-node -n kube-system
kubectl rollout status daemonset/aws-node -n kube-system --timeout=10m
kubectl get pods -n kube-system -l k8s-app=aws-node -o wide
```

Expected result: every `aws-node` pod is `2/2 Ready`. If networking degrades, restore the previous node-role permission before continuing.

After confirming the CNI role works, remove `AmazonEKS_CNI_Policy` from the node role in IAM if it was attached during node-role setup. Do not remove the policy before the add-on has assumed its replacement role. This workshop's recommended node role omits it; the check matters if the console created a broader role.

## Why the node role is not the app role

If every pod can use the EC2 node role, one compromised container may inherit permissions intended for the whole node group. Give each workload a separate IAM role and grant only the API actions and resource ARNs it needs. Keep the node role for node operations such as joining the cluster and pulling images.

## Create the application service account

Create a dedicated service account; do not let the workload use the namespace's default identity:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: web-reader
  namespace: payments
automountServiceAccountToken: false
```

For EKS Pod Identity, EKS injects a separate projected, short-lived token and credential-provider settings into pods that use an associated service account. The application does not need a Kubernetes API token, so `automountServiceAccountToken: false` can remain. Never bind this service account to a Kubernetes Role merely to obtain AWS credentials.

```bash
kubectl apply -f web-reader-serviceaccount.yaml
aws eks create-addon --cluster-name "$CLUSTER_NAME" \
  --addon-name eks-pod-identity-agent --region "$AWS_REGION"
```

If the add-on already exists, inspect its status instead of creating it again:

```bash
aws eks describe-addon --cluster-name "$CLUSTER_NAME" \
  --addon-name eks-pod-identity-agent --region "$AWS_REGION" \
  --query 'addon.{Status:status,Version:addonVersion}' --output table
```

Expected result: add-on status `ACTIVE`. The cluster needs the Pod Identity Agent on nodes and a compatible AWS SDK in the application.

If private nodes have no NAT route, create the interface endpoint **com.amazonaws.<region>.eks-auth** in the VPC, enable private DNS, and allow TCP 443 from the node security group. This endpoint is required for the agent to call EKS Auth; the pod-to-agent link-local address alone is not enough.

## Create a least-privilege role

This example allows `GetObject` only under one S3 prefix. Create a bucket for the lab and replace the account, region, bucket, and cluster values before using the policy. If the bucket uses a customer-managed KMS key, the role also needs the narrowly scoped KMS decrypt permission and key policy permission.

In **Amazon S3 → Create bucket**, use a globally unique name, keep **Block all public access** enabled, and leave default encryption enabled. Upload a harmless file such as `payments/example.txt` and another file under `unrelated/` for the allow/deny check. Record the bucket name; do not use a production bucket.

Trust policy `pod-identity-trust.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "pods.eks.amazonaws.com"},
    "Action": ["sts:AssumeRole", "sts:TagSession"],
    "Condition": {
      "StringEquals": {
        "aws:RequestTag/eks-cluster-arn": "arn:aws:eks:us-east-1:123456789012:cluster/eks-depth-lab",
        "aws:RequestTag/kubernetes-namespace": "payments",
        "aws:RequestTag/kubernetes-service-account": "web-reader"
      }
    }
  }]
}
```

Create the role and the permissions policy. These IAM changes can also be made in **IAM → Roles**; the CLI is shown so the policy document is reviewable and repeatable. The trust conditions bind the role to this cluster, namespace, and service account. For accounts in AWS Organizations, consider also requiring `aws:SourceOrgId` as an additional confused-deputy guard.

```bash
aws iam create-role --role-name EKSDepthPaymentsWebReader \
  --assume-role-policy-document file://pod-identity-trust.json
```

Save as `payments-s3-read.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::REPLACE_WITH_BUCKET/payments/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::REPLACE_WITH_BUCKET",
      "Condition": {"StringLike": {"s3:prefix": ["payments", "payments/*"]}}
    }
  ]
}
```

```bash
aws iam put-role-policy --role-name EKSDepthPaymentsWebReader \
  --policy-name ReadPaymentsObjects --policy-document file://payments-s3-read.json
```

Check the trust policy is limited to the intended cluster and account. Avoid `s3:*`, `Resource: "*"`, and a trust policy that lets arbitrary clusters assume the role.

## Associate the IAM role with the service account

```bash
export WORKLOAD_ROLE_ARN=arn:aws:iam::123456789012:role/EKSDepthPaymentsWebReader
aws eks create-pod-identity-association --cluster-name "$CLUSTER_NAME" \
  --namespace payments --service-account web-reader \
  --role-arn "$WORKLOAD_ROLE_ARN" --region "$AWS_REGION"
```

Expected result: the response includes an association ID. Associations are scoped to a cluster, namespace, and service account. Confirm it:

```bash
aws eks list-pod-identity-associations --cluster-name "$CLUSTER_NAME" \
  --namespace payments --region "$AWS_REGION" --output table
```

The same association can be created in **EKS → Cluster → Access → Pod Identity → Create** by selecting the IAM role, namespace `payments`, and service account `web-reader`. The identity creating the association needs `iam:PassRole` for this workload role and permission to create EKS Pod Identity associations.

Use `serviceAccountName: web-reader` in the application pod template. Roll out the workload after the association exists so the Pod Identity Agent can provide credentials.

## Verify from inside a test workload

Use a temporary AWS CLI Job with `serviceAccountName: web-reader`; do not print credentials. Save this as `identity-check.yaml`:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: identity-check
  namespace: payments
spec:
  template:
    spec:
      restartPolicy: Never
      serviceAccountName: web-reader
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: awscli
          image: public.ecr.aws/aws-cli/aws-cli:2
          command: ["sh", "-c", "sleep 3600"]
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          env:
            - name: HOME
              value: /tmp
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir: {}
```

Apply it, then run:

```bash
kubectl apply -f identity-check.yaml
kubectl wait -n payments --for=condition=Ready pod \
  -l job-name=identity-check --timeout=120s
export IDENTITY_POD=$(kubectl get pods -n payments -l job-name=identity-check \
  -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n payments "$IDENTITY_POD" -- aws sts get-caller-identity
kubectl exec -n payments "$IDENTITY_POD" -- \
  aws s3api list-objects-v2 --bucket REPLACE_WITH_BUCKET --prefix payments/
kubectl exec -n payments "$IDENTITY_POD" -- \
  aws s3api list-objects-v2 --bucket REPLACE_WITH_BUCKET --prefix unrelated/
```

Expected: the first command returns the workload role ARN; the permitted prefix works; the unrelated prefix is denied. A failed STS request often means the Pod Identity Agent, trust conditions, service-account association, or node egress is wrong. Do not fix it by attaching the policy to the node role.

## Store application secrets separately

Use AWS Secrets Manager or Systems Manager Parameter Store for application secrets. Retrieve them through the workload role or a supported Secrets Store CSI/External Secrets integration, scoped to specific secret ARNs. Enable customer-managed KMS keys only when key ownership or separation requirements justify the added key-policy operations. Never put credentials in a ConfigMap, image layer, Git repository, or screenshot.

EKS Kubernetes Secret data is base64-encoded, not encrypted by base64. Review EKS envelope encryption for Kubernetes API secrets, restrict `get/list/watch` on `secrets`, and avoid exposing secret values through logs or environment dumps. Secret rotation is not complete until the workload reloads the new value and old credentials are revoked.

### Screenshots to capture

Save these as `07-01-pod-identity-association.png` and `07-02-workload-aws-permissions.png`.

- **07-01 Pod Identity association:** Place after creating the association. AWS Console → **EKS → Clusters → select the lab cluster → Access → Pod Identity associations**. Show the `payments` namespace, `web-reader` service account, and associated IAM role. Blur account ID and role ARN.
- **07-02 Workload permission test:** Place after running the allow/deny S3 checks. Show terminal output from inside the test workload where `sts get-caller-identity` succeeds, the allowed `payments/` S3 object can be read, and the unrelated prefix is denied. Do not show access keys, tokens, object contents, or full bucket names if private.

### Further reading

- [EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)
- [Configure the Pod Identity Agent](https://docs.aws.amazon.com/eks/latest/userguide/pod-id-agent-setup.html)
- [Assign an IAM role to a Kubernetes service account](https://docs.aws.amazon.com/eks/latest/userguide/pod-id-association.html)
- [Configure the VPC CNI to use IRSA](https://docs.aws.amazon.com/eks/latest/userguide/cni-iam-role.html)
