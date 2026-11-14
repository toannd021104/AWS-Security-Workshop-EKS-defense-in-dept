---
title: "Create RDS PostgreSQL, SQS, and ECR"
weight: 40
chapter: false
pre: "<b>0.4.</b> "
---

## Preparation goal

API stores notes in RDS. Worker shares the database through a separate SQL user and receives jobs from SQS. ECR stores the image used by API, worker, and database initialization.

## Database Security Group and subnet group

1. **EKS → cluster → Configuration → Networking**: copy **Cluster security group ID**. Lab nodes use it because their launch template does not override SGs.
2. **VPC → Security groups → Create** `eks-did-database` in VPC `eks-did`. Allow inbound PostgreSQL TCP `5432` from that **cluster SG ID**. Keep the lab's default outbound rule.
3. **RDS → Subnet groups → Create DB subnet group**: `eks-did-database`, VPC `eks-did`, both AZs and database subnets `10.20.64.0/24`/`10.20.65.0/24`.

This SG restricts nodes, not individual workloads. Chapter 3 adds pod-level policy.

## Create PostgreSQL RDS

1. **RDS → Databases → Create → Standard create**: PostgreSQL **17**, an available 17.x release. The reference run used `17.11`.
2. Identifier `eks-did`, master username `labadmin`, **Manage master credentials in AWS Secrets Manager**.
3. `db.t3.micro`, Single-AZ, **20 GiB gp3**, storage encryption enabled. Single-AZ reduces lab costs.
4. Connectivity: VPC `eks-did`, the database subnet group above, **Public access: No**, only SG `eks-did-database`. Do not add automatic EC2 connectivity.
5. Authentication: **Password and IAM database authentication**. Additional configuration → initial database **`notes`**.
6. Backup retention one day for the lab; review billable options before creation. Wait for **Available**.

Verify configuration:

```bash
aws rds describe-db-instances --db-instance-identifier eks-did \
  --query 'DBInstances[0].{Status:DBInstanceStatus,Database:DBName,Public:PubliclyAccessible,IAM:IAMDatabaseAuthenticationEnabled,Encrypted:StorageEncrypted,ResourceID:DbiResourceId,SecretARN:MasterUserSecret.SecretArn}'
```

Expect `Status=available`, `Database=notes`, `Public=false`, `IAM=true`, `Encrypted=true`, plus ResourceID and SecretARN. The **DB resource ID** starts `db-…` and is used in IAM; it differs from identifier `eks-did`.

## Create SQS queue

1. **SQS → Queues → Create**: Standard, name `eks-did-reports`.
2. Visibility timeout **60 seconds**, retention **one day**; retain suitable lab defaults elsewhere.
3. Enable server-side encryption using **Amazon SQS key (SSE-SQS)**. Do not grant public access; API/worker receive separate identity policies.
4. Record **Queue URL** for SQS requests and **Queue ARN** for IAM policies.

![Queue encryption](/images/console-sqs-encryption.png "① Encryption column. ② SSE-SQS.")

## Create ECR repository

1. **ECR → Private repositories → Create** `eks-did/notes`.
2. Tag mutability **Immutable**, encryption **AES-256**. Enable basic scan on push in registry settings if permitted; enhanced scanning is covered in chapter 5.
3. Record the Repository URI. It is empty until the build step.

## Verify readiness

```bash
aws sqs get-queue-url --queue-name eks-did-reports
aws ecr describe-repositories --repository-names eks-did/notes \
  --query 'repositories[0].{URI:repositoryUri,Mutability:imageTagMutability,Encryption:encryptionConfiguration.encryptionType}'
```

SQS returns QueueUrl. ECR returns your account's URI, `IMMUTABLE`, and `AES256`. RDS must be Available before step 7's initializer.

Continue to [certificate and WAF](/preparation/5-https-waf/).
