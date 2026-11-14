---
title: "Terraform: create all lab infrastructure"
weight: 15
chapter: false
pre: ""
sequenceSkip: true
previousLesson: "/preparation/1-workstation/"
nextLesson: "/preparation/7-deploy-application/"
---

## Choose this provisioning path

Terraform **replaces all Console infrastructure steps 0.2–0.6**. Start here directly after tools/account step 0.1; do not create the VPC, EKS, or services manually first.

| Replaced Console steps | Terraform creates |
|---|---|
| 0.2 — VPC | VPC, public/application/database subnets, routes, IGW, NAT |
| 0.3 — EKS | Cluster, roles, managed nodes, launch template, OIDC, add-ons |
| 0.4 — Data | RDS, database SG, SQS, ECR |
| 0.5 — HTTPS/WAF | ACM certificate, validation, optional WAF ACL |
| 0.6 — Workload access | IAM roles/policies and Pod Identity associations |

Terraform uses the domain/public zone prepared in 0.1. **Image build, controller installation, app/Ingress deployment, application DNS, and baseline remain steps 0.7–0.8.** The controller creates ALB from Ingress during deployment.

Choose one provisioning path per environment. Terraform is not an additional step after Console. If you already created resources manually, inspect Terraform as a reference; applying empty state tries to recreate same-name resources.

## Configure inputs

Complete [0.1](/preparation/1-workstation/), install [Terraform CLI](https://developer.hashicorp.com/terraform/install), then from the source root:

```bash
source .venv/bin/activate
export AWS_PROFILE=guru AWS_REGION=us-east-1
aws sts get-caller-identity
curl -fsS https://checkip.amazonaws.com
cp infrastructure/terraform/terraform.tfvars.example infrastructure/terraform/terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
admin_cidr = "YOUR_WORKSTATION_IP/32"
dns_zone_name = "YOUR_PUBLIC_ZONE."
enable_waf = true
enable_kms = true
enable_inspector = true
```

Substitute real IP/zone. If STS reports an assumed-role/SSO session, set `observer_trusted_principal_arn = "YOUR_ADMIN_IAM_ROLE_ARN"` using the IAM role ARN from Console, not the STS session ARN. Terraform checks this before creating observer. Disable optional service flags only when recording their exercises as unverified due to account restrictions. WAF supports the edge test; KMS/Inspector support chapter 5.

## Create infrastructure

```bash
terraform -chdir=infrastructure/terraform init
terraform -chdir=infrastructure/terraform fmt
terraform -chdir=infrastructure/terraform fmt -check
terraform -chdir=infrastructure/terraform validate
terraform -chdir=infrastructure/terraform plan -out=lab.tfplan
```

`fmt` normalizes your edited tfvars; `fmt -check` then verifies formatting. Require successful validation. Read the plan: correct account/Region, lab resources only, no unrelated changes. Then:

```bash
terraform -chdir=infrastructure/terraform apply lab.tfplan
```

Wait for completion. Terraform creates VPC, EKS/nodes/add-ons, RDS/SQS/ECR, ACM/WAF, workload roles/associations, and enabled optional resources. It does not build images or deploy frontend/API/worker.

State/plan contain sensitive infrastructure information; keep them outside Git/website. Teams need an appropriate remote backend and locking before sharing state operations.

## Deploy and verify

After `Apply complete`, continue directly to [0.7 deployment](/preparation/7-deploy-application/) then [0.8 baseline](/preparation/8-baseline/). Discovery reads actual AWS resources for either provisioning path.

Cleanup removes controller-created resources first, then destroys using the same state. Follow [Cleanup](/cleanup/).
