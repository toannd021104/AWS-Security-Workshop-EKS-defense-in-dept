---
title: "AWS account, tools, and source"
weight: 10
chapter: false
pre: "<b>0.1.</b> "
---

## Preparation goal

Use an Internet-connected Ubuntu Linux x86_64 workstation and an AWS account. AWS steps prioritize Console; terminal commands build containers, manage Kubernetes, and collect precise evidence.

Create resources in **US East (N. Virginia), us-east-1**, prefix `eks-did`. Use the same account/Region in Console and terminal. If a same-name lab exists, inspect it before creating another.

## Sign in and verify the account

1. Sign in to your AWS Console, check the account ID, and select **us-east-1**.
2. Prepare a public domain or correctly delegated public Route 53 zone. Use `notes.<domain>` and a public ACM certificate. A zone without delegation does not make the domain Internet-resolvable.
3. Check the provided local profile:

```bash
export AWS_PROFILE=guru
export AWS_REGION=us-east-1
aws sts get-caller-identity
```

Example output; account/ARN differ in your environment:

```json
{
  "UserId": "EXAMPLE",
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:user/lab-user"
}
```

`guru` is a local profile name, not an AWS account name. Configure yours with `aws configure --profile guru` if needed. Temporary credentials require a valid session token; SSO uses `aws configure sso`. SSO/temporary sessions do not require creating long-lived access keys.

The STS account must match Console. Continue only after STS succeeds.

## Prepare tools

Check what is installed:

```bash
aws --version
kubectl version --client
helm version --short
docker version
python3 --version
git --version
```

| Tool | Use |
|---|---|
| AWS CLI v2 | Read AWS configuration and obtain kubeconfig |
| kubectl compatible with EKS 1.35 | Deploy and inspect Kubernetes resources |
| Helm 3 | Install AWS Load Balancer Controller and later Kyverno |
| Docker | Build/push API/worker image to ECR |
| Python 3, boto3, PyYAML | Discover configuration, render manifests, verify behavior |
| Git, curl, unzip, jq | Get source and inspect results |

For a fresh Ubuntu workstation:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl unzip jq git python3-venv docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

Start a new terminal login for Docker group membership. `docker version` must show both **Client** and **Server**. Install [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html), [kubectl](https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html), and [Helm 3](https://helm.sh/docs/intro/install/) using official Linux instructions. Match kubectl's minor version to cluster 1.35 or stay within supported version skew.

Terraform is needed only for its alternative path. Hugo Extended is needed only to edit/build this workshop website locally.

## Get source and set up the workspace

```bash
git clone https://github.com/toannd021104/AWS-Security-Workshop-EKS-defense-in-dept.git
cd AWS-Security-Workshop-EKS-defense-in-dept
mkdir -p .local
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-lab.txt
export AWS_PROFILE=guru AWS_REGION=us-east-1
source scripts/env.sh
```

Alternatively, extract the [lab ZIP](/downloads/eks-defense-in-depth-lab.zip) and work in the directory containing `app/`, `scripts/`, `k8s/`, and `infrastructure/`.

| Path | Contents |
|---|---|
| `app/` | API/worker source, Dockerfile, frontend interface |
| `scripts/` | Discovery, build/deploy, verification |
| `k8s/` | Manifests rendered for your account |
| `infrastructure/terraform/` | Equivalent Terraform infrastructure |
| `.local/` | Local kubeconfig, lab metadata, temporary files |
| `requirements-lab.txt` | Pinned script dependencies |

`source scripts/env.sh` sets `KUBECONFIG` to `.local/kubeconfig`. Before discovery, `.local/lab.env` does not exist and `APP_HOST` is not loaded automatically. Set your domain for certificate creation:

```bash
export DNS_ZONE_NAME='example.com.'
# Replace example.com. with your actual hosted zone; keep the trailing dot.
export APP_HOST="notes.${DNS_ZONE_NAME%.}"
printf 'Region: %s\nApp hostname: %s\n' "$AWS_REGION" "$APP_HOST"
```

Illustrative output:

```text
Region: us-east-1
App hostname: notes.example.com
```

In each new terminal, reactivate `.venv`, set profile/Region, and source `scripts/env.sh`. Until discovery is complete, also restore your chosen `DNS_ZONE_NAME`.

## Check prerequisites before creating resources

```bash
python3 scripts/preflight.py --stage setup
```

This read-only script checks tools, Docker daemon, Python dependencies, and AWS STS. Example final lines:

```text
PASS | Docker daemon | linux/x86_64
PASS | AWS identity | Account 123456789012; Region us-east-1
Readiness: PASSED (setup)
```

Account/CPU architecture depend on your environment. A `FAIL` stops preparation: fix that input and rerun. `PASSED` does not guarantee creation permissions or quotas. Terraform users also check `terraform version`; Console users do not need it.

Chapter 5 needs **Cosign** and **Trivy**. They are not required for baseline; installation/readiness instructions appear in that chapter.

## Permissions and costs

You need permission to create/manage VPC, EC2, EKS, IAM roles/PassRole, ELB, RDS, SQS, ECR, ACM, and Route 53, plus WAF, Inspector, and KMS for their exercises. Investigate IAM/organization restrictions if an operation is denied.

EKS, EC2, ALB, NAT/public IPv4, RDS, and security services can incur charges while the lab exists. See [Cleanup](/cleanup/) for dependency order.

| Resource | Expected quantity | Continuing charges |
|---|---|---|
| EKS control plane | 1 standard-support cluster | Exists even without pods |
| EC2 managed workers | 2 × t3.medium + EBS | Running nodes and storage |
| NAT Gateway | 1 + public IPv4 | Time, processed data, possible cross-AZ traffic |
| ALB | 1 + public IPv4 | Time and capacity/LCU |
| PostgreSQL RDS | 1 db.t3.micro, Single-AZ | Instance, storage, additional backups |
| WAF, KMS, Inspector, ECR, Route 53 | According to enabled exercises | ACL/rules/requests, key, scans, image storage, DNS |

Estimate for your Region/duration with [AWS Pricing Calculator](https://calculator.aws/). This is a pricing-input list, not a fixed quote. Two nodes across AZs do not make a single NAT or Single-AZ RDS highly available. Between sessions, retain source/evidence and clean up/rebuild if appropriate. Stopping pods or closing Console does not stop infrastructure charges.

**Expected state:** correct STS account, tools installed, Docker daemon available, and source in your workspace.

## Choose infrastructure provisioning

- **[Terraform: create all lab infrastructure](/preparation/9-terraform/)** replaces Console 0.2–0.6. After `Apply complete`, continue directly to [0.7 deployment](/preparation/7-deploy-application/) and [0.8 baseline](/preparation/8-baseline/).
- **[Console: start with VPC](/preparation/2-vpc/)** follows 0.2–0.6, then 0.7–0.8.

Use one path per environment; do not run both against the same resources.
