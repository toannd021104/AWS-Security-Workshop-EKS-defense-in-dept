---
title: "Data Encryption with AWS KMS"
weight: 4
chapter: false
pre: "<b>5.4.</b> "
---

Application data spans services with independent encryption settings. Identify each boundary, then use KMS to test ciphertext, key permissions, and encryption context.

## Encryption and key access

![Independent encryption boundaries](/images/en/encryption.svg "Separate data-protection scopes in the workshop.")

| Path / storage | Lab mechanism |
|---|---|
| Client → ALB | ACM TLS certificate |
| ALB → Nginx → API | Private HTTP; not end-to-end encrypted |
| API/worker → RDS | TLS `verify-full` with RDS CA bundle |
| RDS storage | Encryption with the account's default RDS key |
| Node EBS disks | Encrypted EBS |
| SQS | SSE-SQS, separate from the CMK exercise |
| ECR | AES-256 repository encryption |
| Lab KMS key | Separate CMK for Encrypt/Decrypt; does not automatically protect all resources |

## Step 1: inspect/create the key and service settings

With Terraform `enable_kms=true`, key/alias `eks-did` already exist; inspect rather than duplicate them. Console users without the key: **KMS → Customer managed keys → Create**, symmetric Encrypt/Decrypt, alias `eks-did`. Limit administrators/users to needed lab identities and enable rotation. Terraform creates `aws_kms_key.lab` and alias; the optional key may be disabled when SCPs prohibit it.

In RDS Configuration, inspect storage encryption and KMS key ID. ECR/SQS use separate mechanisms; compare each service's actual key/settings.

![RDS encryption and IAM authentication](/images/console-rds-encryption.png "① Storage encryption. ② AWS KMS key. ③ IAM DB authentication.")

`aws/rds` protects storage. IAM DB authentication authenticates connections; it replaces neither storage encryption nor SQL privileges.

![SQS encryption](/images/console-sqs-encryption.png "① Encryption. ② Amazon SQS key (SSE-SQS).")

SSE-SQS is independent of the customer-managed key below.

## Step 2: encrypt/decrypt test data

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

`cmp` exits 0 when recovered bytes match plaintext. Encryption context is additional authenticated data (AAD), bound to ciphertext but not secret.

## Compare matching and mismatched context

At-rest encryption does not prevent authorized principals retrieving plaintext through APIs. KMS policy, IAM, and resource permissions still matter. Cleanup schedules CMK deletion after seven days; it remains PendingDeletion meanwhile. Do not delete a key protecting data you still need.

Decrypt the same ciphertext with different context:

```bash
aws kms decrypt --ciphertext-blob fileb://.local/ciphertext.bin \
  --encryption-context Workshop=other \
  --query Plaintext --output text
```

Expect `InvalidCiphertextException`. Matching context produces identical plaintext (`cmp` exit 0); mismatched context fails, demonstrating the binding.
