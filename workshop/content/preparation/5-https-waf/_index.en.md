---
title: "Prepare domain, ACM certificate, and WAF"
weight: 50
chapter: false
pre: "<b>0.5.</b> "
---

## Preparation goal

Use hostname `notes.<domain>`. The certificate must exist before HTTPS Ingress; create the application ALB record after the load balancer exists.

## Confirm the public hosted zone

1. **Route 53 → Hosted zones**: select your public domain zone and record its name, for example `example.com.`.
2. Compare NS records with delegation at the parent domain/registrar. Preserve correct existing delegation.
3. In the terminal, set the actual zone:

```bash
export DNS_ZONE_NAME='example.com.'
export APP_HOST="notes.${DNS_ZONE_NAME%.}"
printf '%s\n' "$APP_HOST"
```

Replace `example.com.` before running. The application record is not needed yet; ACM uses a separate validation record.

## Request the ACM certificate

1. **ACM in us-east-1 → Request certificate → Request a public certificate**.
2. Enter your application hostname, for example `notes.example.com`; choose **DNS validation**.
3. Open the request → **Create records in Route 53**, select the domain, and create the validation record.
4. Wait for **Issued** and validation **Success**. Record the ARN. Certificate and ALB must share a Region.

![Application certificate](/images/console-acm-certificate.png "① Issued. ② Domain. ③ Successful DNS validation.")

## Create the lab WAF Web ACL

1. **WAF & Shield → Web ACLs → Create**: `eks-did`, **Regional**, `us-east-1`.
2. Default action **Allow**. ALB does not exist yet, so defer resource association.
3. Add regular custom rule `workshop-header-test`, match **single header** `x-workshop-test`.
4. **Exactly matches string** `block-me`, transformation **None**, action **Block**. Enable sampled requests/metrics and save rule/ACL.
5. Record the ARN. Discovery locates the ACL by name; the controller associates it through Ingress.

![WAF verification rule](/images/console-waf-rule.png "① workshop-header-test. ② Block action.")

The fixed header creates a clear test result. Selecting production managed rules is outside the baseline. For denied WAF creation, investigate IAM/organization policies. Claim this exercise only after the ACL exists and is associated with ALB.

## Verify before deployment

```bash
aws acm list-certificates --certificate-statuses ISSUED \
  --query 'CertificateSummaryList[].{Domain:DomainName,ARN:CertificateArn}'
aws wafv2 list-web-acls --scope REGIONAL \
  --query 'WebACLs[?Name==`eks-did`].{Name:Name,ARN:ARN}'
```

Require a certificate for your hostname and Web ACL `eks-did`. Do not curl the domain yet: neither ALB nor application DNS record exists. Continue to [workload permissions](/preparation/6-workload-permissions/).
