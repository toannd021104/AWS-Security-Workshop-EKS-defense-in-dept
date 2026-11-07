---
title: "Least Privilege và IAM Policies"
weight: 6
chapter: false
pre: "<b>4.6.</b> "
---

Có IAM role riêng chưa bảo đảm workload chỉ thực hiện đúng công việc được giao. Bài này giới hạn action và resource của từng role, kết hợp quyền IAM database authentication với SQL grants trong PostgreSQL.

## Quyền được tách theo nhiệm vụ

| Identity | Quyền AWS | Quyền SQL |
|---|---|---|
| Frontend | Không có role ứng dụng | Không có user DB |
| API | `sqs:SendMessage` trên queue lab; `rds-db:connect` cho `notes_api` | Insert/select notes, select reports |
| Worker | Receive/Delete/GetQueueAttributes trên queue lab; connect `notes_worker` | Select notes, insert/select reports |
| db-init | GetSecretValue đúng RDS master secret | Bootstrap schema/users; job kết thúc sau khởi tạo |
| Controller | Policy ELB controller release đã pin | Không có |

## Bước 1: giới hạn IAM actions và resources

IAM → role API → Add permissions → Inline policy → JSON. Ví dụ queue policy cho role API:

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

Thay account thật; thêm statement `rds-db:connect` với ARN dạng `arn:aws:rds-db:REGION:ACCOUNT:dbuser:DB_RESOURCE_ID/notes_api`. Đây là **DB resource ID**, không phải DB identifier hoặc ARN instance thông thường. Worker dùng username riêng. Toàn bộ statements có trong [Terraform](/source/terraform/data-services.tf).

```bash
aws rds describe-db-instances --db-instance-identifier eks-did \
  --query 'DBInstances[0].{resourceID:DbiResourceId,secret:MasterUserSecret.SecretArn}'
```

## So sánh thao tác nghiệp vụ với thao tác vượt quyền

### Thử luồng nghiệp vụ và thao tác vượt quyền

```bash
curl -fsS "https://$APP_HOST/api/reports" -X POST
kubectl logs -n notes deployment/worker --tail=10
curl -fsS "https://$APP_HOST/api/reports"
```

API trả task ID; worker ghi report; GET trả cùng ID. Đây là bài test xuyên SQS/IAM/DB.

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

Phải bị AccessDenied. Kiểm tra SQL riêng: API không được insert `notes.reports`; IAM connect không tự cấp quyền SQL. Db-init dùng master secret chỉ cho bootstrap; sau khi hoàn tất, pod job có thể xóa, và không cấp quyền đọc secret cho API/worker.
