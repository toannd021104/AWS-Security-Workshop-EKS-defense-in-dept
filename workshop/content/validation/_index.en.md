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

The [initial bilingual review on 2026-11-14](/evidence/learner-review-2026-11-14.md) and [local/browser checks](/evidence/bilingual-validation-2026-11-14.json) ran after the earlier reference environment stopped, without a cloud replay.

A [later live AWS replay on the same date](/evidence/live-learner-replay-2026-11-14.json) started from a fresh public GitHub clone and fresh Terraform state. It found an unavailable default EBS key and a frontend rollout returning 502. The source now explicitly selects the EBS key and adds ALB readiness gates and a shutdown delay. After corrections, the final suite passed 25/25, network proofs passed 4/4 before and 5/5 after isolation, and 28/28 HTTP samples during one rollout returned 200. The [59 executed command blocks](/evidence/executed-command-blocks-2026-11-14.json) retain initial failures and successful retests.

The tested scope is the Terraform path and operational exercises, with an explicit node-group recovery; Console provisioning was not executed end to end. Cleanup destroyed 65 Terraform resources and passed 18/18 checks, retaining the existing hosted zone; the demo KMS key is scheduled for deletion after seven days. The initial RDS timeout and recovery are recorded separately. These results do not mean the original instructions passed on the first attempt. The [2026-11-13 report](/evidence/archive/2026-11-13/verification.json) is archived separately; results below carry the new run timestamp.

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
