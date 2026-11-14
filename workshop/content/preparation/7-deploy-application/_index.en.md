---
title: "Build and deploy the application"
weight: 70
chapter: false
pre: "<b>0.7.</b> "
---

## Preparation goal

Turn source into Kubernetes workloads. API, worker, and db-init share an image but execute different functions; frontend uses Nginx. Database and queue already exist outside the cluster.

## Discover account configuration

From the source root, activate the virtual environment and set your actual zone:

```bash
source .venv/bin/activate
export AWS_PROFILE=guru AWS_REGION=us-east-1
export DNS_ZONE_NAME='example.com.'
# Replace example.com. with the public zone used to validate your certificate.
source scripts/env.sh
python3 scripts/capture-config.py
```

Expected output:

```text
Saved .local/lab.json and .local/lab.env; no secret values are fetched.
```

Discovery reads EKS, RDS, subnets, queue, ECR, certificate, WAF, KMS, and hosted zone metadata. Missing WAF permission/ACL stops it before saving: a working website alone does not prove WAF association. The demonstration KMS key is not a Notes dependency; Console users may create it in 5.4, so missing key metadata is DEFERRED. Discovery requires no Terraform state and retrieves no master password. `DNS_ZONE_NAME` disambiguates multiple zones.

If account restrictions deliberately exclude WAF/KMS, pass `--without-waf`/`--without-kms` and record that exercise as **unverified**. Do not use skip flags to conceal discovery failure in a full workshop run.

Load the saved environment:

```bash
source scripts/env.sh
printf 'App: %s\nVPC: %s\nECR: %s\n' "$APP_HOST" "$VPC_ID" "$ECR_REPO"
```

`APP_HOST` is now loaded from `.local/lab.env`. Require your lab hostname, VPC ID, and ECR URI. This infrastructure metadata stays in `.local/`.

## Build and push to ECR

```bash
bash scripts/build-push.sh
```

The script obtains ECR login, builds `app/Dockerfile` for `linux/amd64`, pushes a new tag, and saves a digest URI in `.local/image.txt`.

The last line has this shape:

```text
Pinned image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/eks-did/notes@sha256:…
```

Compare the pushed image in **ECR → eks-did/notes → Images**. A tag identifies the build; digest identifies its content.

![Pushed ECR image](/images/console-ecr-images.png "① Image digest. ② Tags. Initially only your build exists; signature and test artifacts appear in chapter 5.")

## Install controller and deploy manifests

First verify metadata belongs to the current account:

```bash
python3 scripts/preflight.py --stage deploy
```

Account/Region match, EKS cluster, and pinned-image checks must PASS. After changing accounts, rediscover and rebuild; do not reuse the old account's metadata, kubeconfig, or Terraform state.

```bash
bash scripts/deploy.sh
```

Compare script operations with output:

| Operation | Result |
|---|---|
| Update kubeconfig | Cluster `eks-did`, file `.local/kubeconfig` |
| Helm install/upgrade controller | Chart `3.6.2`, `kube-system`, ServiceAccount already associated with Pod Identity |
| Run `render.py` | Generate application/policy manifests using real metadata |
| Apply `application.yaml` | Namespace, ConfigMaps, ServiceAccounts, RBAC, Job, Deployments, Services, Ingress |
| Wait for `db-init` | RDS schema, `notes_api`/`notes_worker`, SQL grants |
| Wait for rollout | Frontend 2, API 2, worker 1 ready replicas |

Require Job completion and successful rollouts. The application baseline includes non-root/Restricted settings, but **does not apply `network-policies.yaml`**. Chapter 3 explains hardening fields and compares pre/post-isolation behavior.

Inspect components individually:

```bash
kubectl -n kube-system rollout status deployment/aws-load-balancer-controller
kubectl get job db-init -n notes
kubectl get deployments,pods,services,ingress -n notes
```

On rerun, a Complete `db-init` Job has its log saved to `.local/db-init-previous.log`, then is recreated to avoid immutable-template errors. Bootstrap SQL can run again. The script stops for inspection if the Job is still running or failed. With chapter 5 admission enabled, assess a new digest using `python3 scripts/scan-gate.py --candidate`; only on ALLOW sign with `bash scripts/supply-chain.sh --candidate` before redeploying. Use the already trusted key. After rollout, run `deployed-image.py` and default scan gate to record running-image evidence.

Expect Job `1/1`, Deployments `2/2`, `2/2`, `1/1`, and an ALB DNS name in Ingress ADDRESS. For incomplete initialization, read `kubectl logs job/db-init -n notes`. For missing ALB, read controller logs/Ingress events before proceeding to DNS.

## Publish application DNS and inspect ALB

```bash
python3 scripts/publish-dns.py
```

This UPSERTs the application's CNAME pointing to the Ingress-created ALB. The `notes` record differs from ACM's validation record.

1. **Route 53 → zone → notes**: target is your ALB.
2. **EC2 → Load Balancers → eks-did-notes**: Active, HTTP:80 redirects to HTTPS:443, HTTPS forwards to frontend target group.
3. **Target group → Targets**: IP type, HTTP:8080, frontend targets Healthy.

![Controller-created ALB](/images/console-alb.png "Active, Application, internet-facing load balancer.")

![Frontend IP targets](/images/console-targets.png "① IP type. ② HTTP:8080. ③ Healthy targets. ④ Pod IPs/ports. Rollout may include old Draining targets.")

**Expected state:** ready controller, completed initializer, all three Deployments ready, Active ALB, healthy targets, and correct DNS record. Continue to [baseline verification](/preparation/8-baseline/).
