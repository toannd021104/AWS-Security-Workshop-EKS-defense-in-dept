---
title: "Edge Security: AWS WAF, ALB, and HTTPS"
weight: 3
chapter: false
pre: "<b>2.3.</b> "
---

The public entry point must protect browser traffic and block requests matching a defined rule. Configure domain/certificate/HTTPS, associate WAF, and test both permitted and denied requests.

## What does each component protect?

ALB routes HTTP, ACM supplies the TLS certificate, and WAF inspects HTTP requests. WAF is associated with ALB; it is not a separate proxy machine in front of it.

These resources exist from [preparation](/preparation/5-https-waf/). Inspect them; create only missing resources.

## Step 1: certificate and WAF rule

1. In **Route 53**, use a public zone you control and hostname `notes.<zone>`. Creating a zone without domain delegation is insufficient.
2. In **ACM, us-east-1**, request a public certificate for the hostname using DNS validation. Choose **Create records in Route 53** and wait for **Issued**. Certificate and ALB must be in the same Region.

![Application certificate](/images/console-acm-certificate.png "① Certificate Issued. ② Application domain. ③ Successful DNS validation.")

Configure the HTTPS listener only after Issued. DNS validation proves domain control; your domain differs from the reference screenshot.

3. **WAF → Web ACLs → Create**: Regional scope, name `eks-did`, default action Allow.
4. Add custom rule `workshop-header-test`: **single header** `x-workshop-test`, exactly matches `block-me`, transformation None, action Block. Enable sampled requests/metrics.
5. The Ingress in 2.5 uses the certificate ARN and Web ACL ARN. Once ALB exists, check its WAF association.

![WAF verification rule](/images/console-waf-rule.png "① workshop-header-test rule. ② Block action.")

This fixed-header rule verifies WAF participation. Production managed rules and rate limits require separate selection, testing, and false-positive tuning.

### Optional certificate API

To request through CLI rather than Console:

```bash
aws acm request-certificate --domain-name "$APP_HOST" --validation-method DNS
```

Then read `describe-certificate`, create the validation record, and wait for `ISSUED`. Do not request another certificate if Terraform already created one. See [WAF/ACM Terraform](/source/terraform/data-services.tf).

## Compare allowed and WAF-blocked requests

### Test HTTP, HTTPS, and WAF

```bash
aws acm list-certificates --certificate-statuses ISSUED
curl -sS -o /dev/null -w '%{http_code}\n' "http://$APP_HOST/"
curl -sS -o /dev/null -w '%{http_code}\n' "https://$APP_HOST/"
curl -sS -o /dev/null -w '%{http_code}\n' -H 'x-workshop-test: block-me' "https://$APP_HOST/"
```

Expect HTTP redirect, ordinary HTTPS 200, and the test-header request 403. Do not use `curl -k`: verify the certificate and hostname.

### Where does TLS end?

Client-to-ALB uses HTTPS with ACM. TLS terminates at ALB. ALB-to-frontend port `8080` and frontend-to-API use HTTP. API/worker-to-RDS uses TLS with CA and hostname verification.

![ALB backend protocol](/images/console-target-protocol.png "The backend protocol/port is HTTP:8080.")

The target group protocol describes ALB-to-frontend traffic, separately from the client's HTTPS listener. Inspect both to establish TLS coverage.

> **Protection scope:** Internal IPs, Security Groups, and NetworkPolicy constrain access; they do not encrypt HTTP. This lab uses private HTTP internally to focus on EKS network/workload controls.

This design **does not encrypt the entire request path**. If policy or compliance requires internal encryption, configure ALB-to-frontend HTTPS and frontend-to-API TLS. ALB does not validate an HTTPS target's certificate; workload identity verification needs a separate design.

The redirect establishes HTTP-to-HTTPS behavior; normal HTTPS 200 proves certificate/hostname and application access; the test 403 shows WAF is processing requests.
