---
title: "Supply Chain & Data Security"
weight: 6
chapter: false
pre: "<b>5.</b> "
---

Network and IAM controls narrow access but do not establish whether an image contains vulnerabilities or who can retrieve a secret. This section examines deployment inputs and application data.

Scan the actual running digest, read its release gate, create an SBOM/signature, and test admission with an unsigned image. Then inspect RDS master-secret access, bootstrap permissions, and KMS encryption context.

Evaluate scans separately from functional success. The reference scan on **2026-11-13 UTC** recorded 0 CRITICAL, 4 HIGH, 10 MEDIUM, 3 LOW, and 0 UNTRIAGED findings; release gate **BLOCK**. Check the report's timestamp, digest, and coverage. These results do not apply automatically to another build or scan. Finish with [Summary](/summary/) before cleanup.

## Lessons

5.1. [Container Image Scanning with ECR & Inspector](/5-supply-chain-data/1-scanning/)

5.2. [SBOM, Image Signing & Admission Policies](/5-supply-chain-data/2-sbom-signing/)

5.3. [Kubernetes Secrets & AWS Secrets Manager](/5-supply-chain-data/3-secrets/)

5.4. [Data Encryption with AWS KMS](/5-supply-chain-data/4-encryption/)
