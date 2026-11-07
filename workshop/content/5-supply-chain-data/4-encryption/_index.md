---
title: "Data Encryption với AWS KMS"
weight: 4
chapter: false
pre: "<b>5.4.</b> "
---

## Mã hóa ở đâu, bằng key nào?

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

### Console: tạo và kiểm tra key

KMS → Customer managed keys → Create symmetric Encrypt/Decrypt key → alias `eks-did`. Giới hạn key administrators/users vào identity lab cần thiết, bật rotation. Terraform tạo `aws_kms_key.lab` và alias, tùy chọn tắt nếu SCP không cho.

RDS → Configuration kiểm tra storage encrypted và KMS key ID. ECR/SQS có cấu hình riêng; đừng nhìn thấy một CMK rồi kết luận mọi dịch vụ đang sử dụng nó.

### CLI/API: round-trip có thể tái lập

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

Mong đợi `cmp` exit 0. Negative test: decrypt cùng ciphertext nhưng context `Workshop=other` phải trả `InvalidCiphertextException`. Encryption context là AAD, không phải secret; không đặt dữ liệu nhạy cảm trong đó.

### Giới hạn và cleanup

At-rest encryption không chặn principal được cấp quyền hợp lệ đọc plaintext qua API. KMS policy, IAM và resource permissions vẫn quan trọng. Khi teardown, CMK được schedule deletion sau 7 ngày, không biến mất ngay; xem trạng thái PendingDeletion. Không xóa key bảo vệ dữ liệu còn cần khôi phục.
