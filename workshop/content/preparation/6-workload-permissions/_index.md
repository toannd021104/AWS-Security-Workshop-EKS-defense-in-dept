---
title: "Cấp IAM roles và Pod Identity cho workload"
weight: 6
chapter: false
pre: "<b>0.6.</b> "
---

## Mục tiêu chuẩn bị

Ứng dụng cần temporary AWS credentials trước khi chạy: API gửi SQS, worker nhận message, Job db-init đọc master secret để khởi tạo database, controller tạo ALB. Tạo các quyền cần thiết ở đây để baseline hoạt động; chương 4 tiếp tục giải thích và kiểm chứng từng ranh giới quyền.

## Chuẩn bị các giá trị ARN

Đọc các giá trị metadata sau, không lấy nội dung master password:

```bash
aws sts get-caller-identity --query Account --output text
aws rds describe-db-instances --db-instance-identifier eks-did \
  --query 'DBInstances[0].{DBResourceID:DbiResourceId,MasterSecretARN:MasterUserSecret.SecretArn}'
QUEUE_URL=$(aws sqs get-queue-url --queue-name eks-did-reports --query QueueUrl --output text)
aws sqs get-queue-attributes --queue-url "$QUEUE_URL" \
  --attribute-names QueueArn --query Attributes.QueueArn --output text
```

Dùng account ID, DB resource ID, secret ARN và queue ARN thực tế để thay các placeholders trong policies dưới đây.

## Tạo bốn IAM roles

Trong IAM → **Roles → Create role → Custom trust policy**, tạo lần lượt:

| Role name | Namespace | ServiceAccount |
|---|---|---|
| `eks-did-api` | `notes` | `api` |
| `eks-did-worker` | `notes` | `worker` |
| `eks-did-db-init` | `notes` | `db-init` |
| `eks-did-controller` | `kube-system` | `aws-load-balancer-controller` |

Dùng trust policy sau cho từng role, thay `NAMESPACE` và `SERVICE_ACCOUNT` theo đúng hàng trong bảng:

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

![Trust policy của API role](/images/console-api-trust.png "① EKS Pod Identity service principal. ② AssumeRole. ③ TagSession. Condition giới hạn namespace và ServiceAccount.")

## Gắn permissions policy cho từng role

Mở từng role → **Permissions → Add permissions → Create inline policy → JSON**. Các placeholders sau cần được thay bằng giá trị ở bước đầu.

**Role API**, policy name `scoped-application`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect":"Allow","Action":"sqs:SendMessage","Resource":"QUEUE_ARN"},
    {"Effect":"Allow","Action":"rds-db:connect","Resource":"arn:aws:rds-db:us-east-1:ACCOUNT_ID:dbuser:DB_RESOURCE_ID/notes_api"}
  ]
}
```

**Role worker**, policy name `scoped-application`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect":"Allow","Action":["sqs:ReceiveMessage","sqs:DeleteMessage","sqs:GetQueueAttributes"],"Resource":"QUEUE_ARN"},
    {"Effect":"Allow","Action":"rds-db:connect","Resource":"arn:aws:rds-db:us-east-1:ACCOUNT_ID:dbuser:DB_RESOURCE_ID/notes_worker"}
  ]
}
```

**Role db-init**, policy name `read-one-bootstrap-secret`:

```json
{
  "Version": "2012-10-17",
  "Statement": [{"Effect":"Allow","Action":"secretsmanager:GetSecretValue","Resource":"MASTER_SECRET_ARN"}]
}
```

**Role controller**, policy name `load-balancer-controller`: mở [controller-policy.json đã pin theo release](/source/terraform/controller-policy.json), copy toàn bộ JSON vào inline policy editor. Policy dành riêng cho controller; không gắn quyền này lên node role hoặc app roles.

Frontend chỉ phục vụ HTTP/proxy nên không có IAM role ứng dụng. Job db-init dùng master credentials một lần để tạo schema và SQL grants; API/worker sử dụng IAM database authentication với user riêng.

## Tạo EKS Pod Identity associations

1. EKS → cluster `eks-did` → **Access → Pod Identity associations → Create**.
2. Chọn IAM role, namespace và ServiceAccount theo bảng bốn roles ở trên. Giữ session tags hoạt động vì trust policy sử dụng các tags này.
3. Tạo đủ bốn associations. Có thể nhập namespace/ServiceAccount trước khi chúng được manifest tạo ở bước triển khai.
4. Trong **Add-ons**, xác nhận Amazon EKS Pod Identity Agent đang Active trên các nodes.

![Liên kết role với ServiceAccount](/images/console-pod-identity.png "① Namespace notes. ② API ServiceAccount. ③ Worker ServiceAccount. Đọc IAM role ở cùng hàng để đối chiếu.")

## Kiểm tra trước khi deploy

```bash
aws eks list-pod-identity-associations --cluster-name eks-did \
  --query 'associations[].{Namespace:namespace,ServiceAccount:serviceAccount}' --output table
kubectl get daemonset eks-pod-identity-agent -n kube-system
```

Cần có bốn associations đúng namespace/ServiceAccount; DaemonSet agent có desired/current/ready tương ứng hai nodes. Có thể mở từng association trên Console để kiểm tra role ARN.

Tiếp tục [build image và triển khai ứng dụng](/preparation/7-deploy-application/).
