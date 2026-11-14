---
title: "Assign workload IAM roles and Pod Identity"
weight: 60
chapter: false
pre: "<b>0.6.</b> "
---

## Preparation goal

Before startup, API needs SQS send access, worker needs receive access, db-init must read the RDS master secret, and controller must create ALB. Create operational permissions now; chapter 4 explains and verifies each boundary.

## Collect ARN inputs

Read metadata without retrieving the master password:

```bash
aws sts get-caller-identity --query Account --output text
aws rds describe-db-instances --db-instance-identifier eks-did \
  --query 'DBInstances[0].{DBResourceID:DbiResourceId,MasterSecretARN:MasterUserSecret.SecretArn}'
QUEUE_URL=$(aws sqs get-queue-url --queue-name eks-did-reports --query QueueUrl --output text)
aws sqs get-queue-attributes --queue-url "$QUEUE_URL" \
  --attribute-names QueueArn --query Attributes.QueueArn --output text
```

Use your actual account, DB resource ID, secret ARN, and queue ARN in the following placeholders.

## Create four roles

**IAM → Roles → Create role → Custom trust policy**:

| Role | Namespace | ServiceAccount |
|---|---|---|
| `eks-did-api` | `notes` | `api` |
| `eks-did-worker` | `notes` | `worker` |
| `eks-did-db-init` | `notes` | `db-init` |
| `eks-did-controller` | `kube-system` | `aws-load-balancer-controller` |

For each role, replace `NAMESPACE` and `SERVICE_ACCOUNT` according to its row:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "pods.eks.amazonaws.com"},
    "Action": ["sts:AssumeRole", "sts:TagSession"],
    "Condition": {"StringEquals": {
      "aws:RequestTag/kubernetes-namespace": "NAMESPACE",
      "aws:RequestTag/kubernetes-service-account": "SERVICE_ACCOUNT"
    }}
  }]
}
```

![API role trust](/images/console-api-trust.png "① Pod Identity service principal. ② AssumeRole. ③ TagSession. Conditions restrict namespace and ServiceAccount.")

## Attach permissions

Each role → **Permissions → Add permissions → Create inline policy → JSON**. Replace every placeholder with collected values.

**API**, policy `scoped-application`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect":"Allow","Action":"sqs:SendMessage","Resource":"QUEUE_ARN"},
    {"Effect":"Allow","Action":"rds-db:connect","Resource":"arn:aws:rds-db:us-east-1:ACCOUNT_ID:dbuser:DB_RESOURCE_ID/notes_api"}
  ]
}
```

**Worker**, policy `scoped-application`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect":"Allow","Action":["sqs:ReceiveMessage","sqs:DeleteMessage","sqs:GetQueueAttributes"],"Resource":"QUEUE_ARN"},
    {"Effect":"Allow","Action":"rds-db:connect","Resource":"arn:aws:rds-db:us-east-1:ACCOUNT_ID:dbuser:DB_RESOURCE_ID/notes_worker"}
  ]
}
```

**db-init**, policy `read-one-bootstrap-secret`:

```json
{
  "Version": "2012-10-17",
  "Statement": [{"Effect":"Allow","Action":"secretsmanager:GetSecretValue","Resource":"MASTER_SECRET_ARN"}]
}
```

**Controller**, policy `load-balancer-controller`: copy the entire pinned [controller-policy.json](/source/terraform/controller-policy.json) into the editor. This policy belongs only to controller, not node/application roles.

Frontend only serves/proxies HTTP and needs no application IAM role. Db-init uses master credentials to bootstrap schema/grants. API/worker use IAM DB authentication as separate users.

## Create Pod Identity associations

1. **EKS → eks-did → Access → Pod Identity associations → Create**.
2. Select each role/namespace/ServiceAccount above. Keep session tags enabled because trust conditions use them.
3. Create all four associations. Namespace/ServiceAccount names can be entered before deployment creates those objects.
4. Confirm Pod Identity Agent is Active on nodes under **Add-ons**.

![Role-to-ServiceAccount mapping](/images/console-pod-identity.png "① notes namespace. ② api ServiceAccount. ③ worker ServiceAccount. Compare IAM role on the same row.")

## Verify before deployment

```bash
aws eks list-pod-identity-associations --cluster-name eks-did \
  --query 'associations[].{Namespace:namespace,ServiceAccount:serviceAccount}' --output table
kubectl get daemonset eks-pod-identity-agent -n kube-system
```

Require four correct associations; agent DaemonSet desired/current/ready must cover both nodes. Inspect each association's role ARN in Console.

Continue to [build and deployment](/preparation/7-deploy-application/).
