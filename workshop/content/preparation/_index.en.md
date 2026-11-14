---
title: "Lab preparation"
weight: 2
chapter: false
pre: ""
---

Build the application baseline in an AWS account before studying its protection layers. Prepare tools/account, then choose one infrastructure path.

Frontend, API, and worker run on EKS; RDS stores data and SQS queues reports. Review the [architecture](/1-introduction/4-architecture/) first if needed.

## Choose an infrastructure path

1. Complete [0.1: account, tools, and source](/preparation/1-workstation/).
2. Choose **[Terraform: create all lab infrastructure](/preparation/9-terraform/)** instead of Console steps 0.2–0.6, or follow **[Console: build each component](/preparation/2-vpc/)**.
3. Both paths rejoin at [0.7: deploy](/preparation/7-deploy-application/) and [0.8: baseline](/preparation/8-baseline/).

**Do not build in Console and then run Terraform with empty state.** These are alternative paths.

## Preparation steps

0.1. [AWS account, tools, and source](/preparation/1-workstation/)

[Terraform: create all lab infrastructure](/preparation/9-terraform/)

0.2. [Create VPC, subnets, and routing](/preparation/2-vpc/)

0.3. [Create EKS, CNI role, and managed workers](/preparation/3-eks/)

0.4. [Create RDS PostgreSQL, SQS, and ECR](/preparation/4-data-services/)

0.5. [Prepare domain, ACM certificate, and WAF](/preparation/5-https-waf/)

0.6. [Assign workload IAM roles and Pod Identity](/preparation/6-workload-permissions/)

0.7. [Build and deploy the application](/preparation/7-deploy-application/)

0.8. [Verify the application baseline](/preparation/8-baseline/)

## Sequence

**Console:** 0.1 → 0.2 → 0.3 → 0.4 → 0.5 → 0.6 → 0.7 → 0.8.

**Terraform:** 0.1 → Terraform (replaces 0.2–0.6) → 0.7 → 0.8.

After 0.8, HTTPS works, all three workloads run, and RDS/SQS operations succeed. NetworkPolicy is deliberately not applied yet, preserving chapter 3's before/after comparison. Non-root configuration and workload permissions required for operation are already in the baseline; later lessons explain and test them.

Screenshots show the reference lab; sample outputs are illustrative. Substitute your account, domain, resource IDs, and IPs. Follow [Cleanup](/cleanup/) to remove billable resources afterward.
