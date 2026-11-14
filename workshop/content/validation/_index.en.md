---
title: "Verification and practical results"
weight: 80
chapter: false
pre: ""
---

## Intended behavior and observed behavior are different

Run this after NetworkPolicy, IAM/RBAC, PSA, and KMS exercises. The checker creates/deletes probe pods, writes test notes/reports, and **reapplies the lab NetworkPolicy**. Do not use it for the pre-isolation baseline; use `network-proof.py --stage before` in 3.2 instead.

Lessons describe expected outcomes; the report records observations. `PASS` applies only to the named test and is not a production-readiness certification.

```bash
source scripts/env.sh
python3 scripts/verify.py
# After completing signing/admission and preparing the unsigned image:
python3 scripts/verify.py --supply-chain
```

Tests cover application transactions, WAF, network allow/deny, real observer credentials, IAM denials, SQL grants, PSA, IMDS, and KMS. They do not exploit vulnerabilities or run privileged workloads.

The [image scan/release gate](/evidence/image-scan.json) is separate and can block release despite functional PASS. Download the [CycloneDX SBOM](/evidence/sbom.cdx.json). The [independent review and test scope](/evidence/workshop-review.md) records corrections and limitations.

## Learner walkthrough review

The [bilingual learner review dated 2026-11-14](/evidence/learner-review-2026-11-14.md) checks Console/Terraform order, commands, and the downloadable ZIP. [Local and browser results](/evidence/bilingual-validation-2026-11-14.json) record the checks actually executed. The reference AWS environment has stopped; this review neither reprovisioned it nor reran cloud tests. The AWS report retains its earlier run timestamp.

## Interpret a denied result

| Evidence | Layer tested | Positive control |
|---|---|---|
| Test header returns 403 | WAF associated with ALB | Same URL without header returns 200 |
| Untrusted pod times out to API IP | NetworkPolicy | Frontend probe and API business transactions work |
| Observer Secret read returns `Forbidden` | Kubernetes authorization | Same observer lists pods |
| API ReceiveMessage returns `AccessDenied` | Workload IAM actions/resources | API sends and worker processes reports |
| API report insert gets `InsufficientPrivilege` | PostgreSQL grants | API still creates/reads notes |
| Dry run reports `violates PodSecurity` | PSA | Compliant Restricted manifest accepted |
| Unsigned digest rejected by verifier | Signature admission | Signed digest in same repository accepted |

An error name alone does not prove causation. Check the request, identity, and successful control. Expired credentials or unavailable dependencies do not count as successful negative tests.

See [observed results](/validation/results/) for test scope and limitations. Detailed local logs remain gitignored under `.local/`; public reports are sanitized.
