---
title: "Kubernetes Secrets & AWS Secrets Manager"
weight: 3
chapter: false
pre: "<b>5.3.</b> "
---

Database initialization needs a privileged account; the running API/worker do not need the master password. Separate bootstrap access and test secret restrictions.

## Which secrets does the application need?

Kubernetes Secret YAML commonly represents values as Base64. Base64 is not encryption. A principal able to read a Secret or exec into a workload containing it may retrieve its contents.

## Step 1: inspect RDS master-secret metadata

**RDS → database → Configuration → Master credentials ARN** opens Secrets Manager. Inspect the encryption key and access policy. Do not reveal the password for a workshop screenshot.

Only `eks-did-db-init` has `GetSecretValue` on that ARN. The Job creates schema and users `notes_api`/`notes_worker`, grants `rds_iam`, and applies minimal SQL permissions. API/worker do not read the master password; their SDKs sign short-lived IAM DB tokens for connections using TLS verify-full.

![RDS IAM authentication and managed credentials](/images/console-rds.png "① Database Available. ② IAM authentication Enabled. Secrets Manager manages the master credentials.")

Inspect state and ARN only; the screenshot contains no database password.

## Verify metadata and secret permissions

### Inspect bootstrap

```bash
aws secretsmanager describe-secret --secret-id "$DB_SECRET_ARN" \
  --query '{arn:ARN,rotation:RotationEnabled,key:KmsKeyId}'
kubectl get job db-init -n notes
kubectl logs job/db-init -n notes
```

Expect a completed initializer with no password in logs. Verify rotation against actual RDS settings; the existence of a Secret alone proves no rotation behavior.

### Test master-secret access

1. Observer Kubernetes Secret reads must return `Forbidden` (4.4).
2. API `GetSecretValue` on the master ARN must return `AccessDenied`.
3. API still reads/writes its permitted tables through IAM DB authentication.

```bash
kubectl exec -n notes deployment/api -- python -c '
import boto3,os
from botocore.exceptions import ClientError
try:
    boto3.client("secretsmanager").get_secret_value(SecretId=os.environ["DB_SECRET_ARN"])
    raise SystemExit("UNEXPECTED: API can read master secret")
except ClientError as e:
    print(e.response["Error"]["Code"])
    assert "AccessDenied" in e.response["Error"]["Code"]'
```

The bootstrap code in [main.py](/source/app/main.py) does not print the secret. Remove the completed Job pod when no longer needed for inspection. Retiring bootstrap association/role after schema initialization is a further hardening step; it is not a normal application identity.
