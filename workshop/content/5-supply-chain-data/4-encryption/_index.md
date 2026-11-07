---
title: "Data Encryption với AWS KMS"
weight: 4
chapter: false
pre: "<b>5.4.</b> "
---

## Vấn đề

Dữ liệu của ứng dụng tồn tại trên nhiều dịch vụ, mỗi dịch vụ có cấu hình mã hóa riêng. Bài này xác định từng ranh giới mã hóa và thực hành KMS để kiểm tra quan hệ giữa ciphertext, quyền sử dụng key và encryption context.

## Kiến thức cần dùng

![Các ranh giới mã hóa](/images/encryption.svg)

| Đoạn / nơi lưu | Cơ chế trong lab |
|---|---|
| Client → ALB | TLS certificate ACM |
| ALB → Nginx → API | HTTP private; chưa mã hóa end-to-end |
| API/worker → RDS | TLS `verify-full` với RDS CA bundle |
| RDS storage | Encryption dùng key mặc định của RDS trong account |
| EBS node disks | Encrypted EBS |
| SQS | SSE-SQS; không phải demo CMK bên dưới |
| ECR | AES-256 repository encryption |
| KMS lab key | CMK riêng cho bài Encrypt/Decrypt, không tự bảo vệ toàn bộ tài nguyên |

## Thực hiện

### Tạo KMS key và đối chiếu cấu hình dịch vụ

KMS → Customer managed keys → Create symmetric Encrypt/Decrypt key → alias `eks-did`. Giới hạn key administrators/users vào identity lab cần thiết, bật rotation. Terraform tạo `aws_kms_key.lab` và alias, tùy chọn tắt nếu SCP không cho.

RDS → Configuration kiểm tra storage encrypted và KMS key ID. ECR và SQS có cấu hình riêng; đối chiếu key và cơ chế mã hóa của từng dịch vụ.

![Encryption và IAM authentication của RDS](/images/console-rds-encryption.png "① Storage encryption. ② AWS KMS key. ③ IAM DB authentication.")

Key `aws/rds` bảo vệ storage của RDS. IAM database authentication là cơ chế xác thực kết nối; không thay thế storage encryption hoặc quyền SQL.

![Cơ chế mã hóa của queue SQS](/images/console-sqs-encryption.png "① Encryption. ② Amazon SQS key (SSE-SQS).")

Queue dùng SSE-SQS, độc lập với customer managed KMS key sẽ thực hành bên dưới.

### Mã hóa và giải mã dữ liệu thử nghiệm

```bash
mkdir -p .local
printf 'eks-defense-in-depth-demo' > .local/plaintext.txt
aws kms encrypt --key-id alias/eks-did \
  --plaintext fileb://.local/plaintext.txt \
  --encryption-context Workshop=eks-did \
  --query CiphertextBlob --output text | base64 --decode > .local/ciphertext.bin
aws kms decrypt --ciphertext-blob fileb://.local/ciphertext.bin \
  --encryption-context Workshop=eks-did \
  --query Plaintext --output text | base64 --decode > .local/decrypted.txt
cmp .local/plaintext.txt .local/decrypted.txt
```

`cmp` trả exit code 0 khi dữ liệu giải mã trùng plaintext. Encryption context là additional authenticated data (AAD), được ràng buộc với ciphertext nhưng không phải dữ liệu bí mật. Phần kiểm chứng tiếp theo thay context để quan sát kết quả từ chối.

## Kiểm chứng kết quả

### Kiểm tra encryption context và vòng đời key

At-rest encryption không chặn principal được cấp quyền hợp lệ đọc plaintext qua API. KMS policy, IAM và resource permissions vẫn quan trọng. Khi teardown, CMK được schedule deletion sau 7 ngày, không biến mất ngay; xem trạng thái PendingDeletion. Không xóa key bảo vệ dữ liệu còn cần khôi phục.

Thử giải mã lại ciphertext với context khác:

```bash
aws kms decrypt --ciphertext-blob fileb://.local/ciphertext.bin \
  --encryption-context Workshop=other \
  --query Plaintext --output text
```

Lệnh phải thất bại với `InvalidCiphertextException`. Lần giải mã đúng context cho file trùng plaintext (`cmp` exit 0); lần sai context bị từ chối chứng minh ciphertext được ràng buộc với encryption context.
