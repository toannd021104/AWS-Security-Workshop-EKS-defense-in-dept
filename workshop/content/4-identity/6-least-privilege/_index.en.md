---
title: "Least Privilege and IAM Policies"
weight: 6
chapter: false
pre: "<b>4.6.</b> "
---

A separate IAM role is not enough: restrict its actions and resources, and combine IAM database authentication with PostgreSQL grants.

## Permissions by responsibility

| Identity | AWS permissions | SQL permissions |
|---|---|---|
| Frontend | No application role | No database user |
| API | `sqs:SendMessage` on lab queue; `rds-db:connect` as `notes_api` | Insert/select notes, select reports |
| Worker | Receive/Delete/GetQueueAttributes on lab queue; connect as `notes_worker` | Select notes, insert/select reports |
| db-init | GetSecretValue on the RDS master secret only | Bootstrap schema/users; Job ends afterward |
| Controller | Pinned ELB controller release policy | None |

## Step 1: narrow IAM actions/resources

**IAM → API role → Add permissions → Inline policy → JSON**. Queue statement:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "sqs:SendMessage",
    "Resource": "arn:aws:sqs:us-east-1:YOUR_ACCOUNT_ID:eks-did-reports"
  }]
}
```

Substitute your account. Add `rds-db:connect` with `arn:aws:rds-db:REGION:ACCOUNT:dbuser:DB_RESOURCE_ID/notes_api`. Use the **DB resource ID**, not its database identifier or ordinary instance ARN. Worker uses its own username. See complete statements in [Terraform](/source/terraform/data-services.tf).

```bash
aws rds describe-db-instances --db-instance-identifier eks-did \
  --query 'DBInstances[0].{resourceID:DbiResourceId,secret:MasterUserSecret.SecretArn}'
```

## Compare business operations and excess privileges

```bash
curl -fsS "https://$APP_HOST/api/reports" -X POST
kubectl logs -n notes deployment/worker --tail=10
curl -fsS "https://$APP_HOST/api/reports"
```

API returns a task ID, worker writes the report, and GET returns the same ID. This crosses SQS, IAM, and the database.

```bash
kubectl exec -n notes deployment/api -- python -c '
import boto3,os
from botocore.exceptions import ClientError
try:
    boto3.client("sqs").receive_message(QueueUrl=os.environ["QUEUE_URL"],WaitTimeSeconds=0)
    raise SystemExit("UNEXPECTED: API can receive messages")
except ClientError as e:
    print(e.response["Error"]["Code"])
    assert "AccessDenied" in e.response["Error"]["Code"]'
```

Expect AccessDenied. Separately test SQL using the application user:

```bash
kubectl exec -n notes deployment/api -- python -c '
import main, psycopg
try:
    with main.connect() as conn:
        conn.execute("INSERT INTO notes.reports(id,note_count) VALUES(gen_random_uuid(),0)")
    raise SystemExit("UNEXPECTED: API can insert reports")
except psycopg.errors.InsufficientPrivilege:
    print("DENIED: notes_api cannot insert reports")'
```

Expect `DENIED`, while POST/GET `/api/notes` still work. Network, TLS, and IAM DB authentication have already succeeded; SQL can still reject a particular operation. `rds-db:connect` grants no automatic `INSERT`, `SELECT`, or database administrator privileges.

The SDK signs IAM DB tokens locally using temporary credentials. There is no `rds:GenerateDBAuthToken` IAM action to grant. Tokens expire for new-connection authentication; they are not master passwords to store in Secrets. Db-init reads the master secret only for bootstrap; its completed pod can be removed. API/worker must not read that secret.
