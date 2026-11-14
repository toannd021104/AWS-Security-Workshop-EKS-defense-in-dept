---
title: "AWS Load Balancer Controller and Kubernetes Ingress"
weight: 5
chapter: false
pre: "<b>2.5.</b> "
---

An Ingress definition alone does not create an AWS ALB. The controller and its permissions translate Kubernetes intent into load-balancer resources.

## Who creates the ALB?

Ingress defines hosts, paths, and backends. AWS Load Balancer Controller watches Ingress, Service, and EndpointSlice objects, then calls ELB/EC2 APIs to create ALB, listeners, target groups, and SG rules. It does not proxy each application request.

These resources already exist from [deployment](/preparation/7-deploy-application/). Inspect existing resources and create only missing ones.

## Step 1: controller permissions

In **IAM → Roles → eks-did-controller**, trust `pods.eks.amazonaws.com` for `sts:AssumeRole` and `sts:TagSession`. In **EKS → Access → Pod Identity associations**, associate namespace `kube-system`, ServiceAccount `aws-load-balancer-controller`, and that role. Use the controller release policy, not `AdministratorAccess`.

AWS Console is not a complete Kubernetes resource editor. Helm installation and Ingress creation therefore use CLI.

## Step 2: controller and Ingress

[deploy.sh](/source/scripts/deploy.sh) pins chart `3.6.2` and passes Region/VPC ID explicitly, avoiding discovery through IMDS:

```bash
source scripts/env.sh
bash scripts/deploy.sh
kubectl -n kube-system rollout status deployment/aws-load-balancer-controller
kubectl -n notes get ingress notes -o yaml
```

Key annotations in [render.py](/source/scripts/render.py):

```yaml
alb.ingress.kubernetes.io/scheme: internet-facing
alb.ingress.kubernetes.io/target-type: ip
alb.ingress.kubernetes.io/healthcheck-path: /healthz
alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80},{"HTTPS":443}]'
alb.ingress.kubernetes.io/ssl-redirect: '443'
```

Certificate ARN, public subnet IDs, and WAF ARN are rendered from your account configuration rather than another account's examples.

![Controller-created ALB](/images/console-alb.png "ALB eks-did-notes is Active, type Application, and internet-facing.")

```bash
kubectl get ingress -n notes --watch
# When ADDRESS contains the ALB hostname, stop watching with Ctrl-C.
python3 scripts/publish-dns.py
```

## Verify controller-created resources

### Compare Ingress and AWS

EC2 Console should show the managed ALB/target group. `curl https://$APP_HOST/` must succeed after DNS updates. If ALB is missing, inspect controller logs/events before testing the app. Avoid manual ALB edits that conflict with reconciliation.

Permission to edit Ingress can change AWS infrastructure. The lab does not use a shared IngressGroup; only the lab administrator edits Ingress. The versioned policy is [controller-policy.json](/source/terraform/controller-policy.json).

Compare `kubectl get ingress -n notes` with ALB's DNS name. Require Active ALB, healthy targets, and application HTTP 200: resource creation and functional backends are separate evidence.
