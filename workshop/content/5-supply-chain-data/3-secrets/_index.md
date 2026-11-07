---
title: "Kubernetes Secrets & AWS Secrets Manager"
weight: 3
chapter: false
pre: "<b>5.3.</b> "
---

## Credentials phải được bảo vệ cả lúc lưu và lúc sử dụng

Kubernetes Secret thường biểu diễn dữ liệu bằng Base64 khi xuất YAML. Base64 không phải encryption. Ai có quyền đọc Secret hoặc exec vào workload có secret có thể tiếp cận dữ liệu đó.

### Console: quan sát secret do RDS quản lý

RDS → database → Configuration → Master credentials ARN → mở Secrets Manager. Kiểm tra encryption key và access policy. Không bấm hiển thị password để chụp ảnh đưa lên workshop.

Lab chỉ cấp `GetSecretValue` trên ARN này cho role `eks-did-db-init`. Job khởi tạo schema và hai user `notes_api`, `notes_worker`, cấp `rds_iam` và SQL grants tối thiểu. API/worker không đọc master password; SDK ký IAM DB auth token ngắn hạn khi mở connection, kết hợp TLS verify-full.



![Ảnh AWS Console thực tế](/images/console-rds.png "① RDS Available. ② IAM authentication Enabled; master credentials do Secrets Manager quản lý.")

### CLI/API: xem metadata, không in secret

```bash
aws secretsmanager describe-secret --secret-id "$DB_SECRET_ARN" \
  --query '{arn:ARN,rotation:RotationEnabled,key:KmsKeyId}'
kubectl get job db-init -n notes
kubectl logs job/db-init -n notes
```

Mong đợi init job hoàn tất và log không chứa password. RDS master credential rotation do dịch vụ quản lý cần được kiểm tra theo cấu hình; không suy ra chỉ từ việc secret tồn tại.

### Negative tests

1. Observer đọc Kubernetes Secrets phải `Forbidden` (bài 4.4).
2. API gọi `GetSecretValue` trên master ARN phải `AccessDenied`.
3. API vẫn đọc/ghi đúng bảng bằng IAM DB auth. Điều đó chứng minh việc bỏ master secret không làm app mất quyền nghiệp vụ cần thiết.

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

Job không print secret; mã bootstrap nằm trong [main.py](/source/app/main.py). Sau khi hoàn tất, xóa pod job nếu không cần giữ để quan sát. Thu hồi association/bootstrap role khi đã chốt schema là bước hardening tiếp theo; role này không dành cho app chạy thường xuyên.
