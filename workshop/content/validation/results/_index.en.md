---
title: "Observed verification results"
weight: 1
---

Recorded at (UTC): 2026-11-14T05:33:49.154729+00:00

> This reference run required corrections and node-group recovery. These 25 checks do not rerun provisioning or the Console path. See the [live learner replay and its limitations](/evidence/live-learner-replay-2026-11-14.json).

| Test | Result | Detail |
|---|---|---|
| HTTPS frontend | PASS | 200 |
| API health | PASS | {'status': 'ok', 'workload': 'api'} |
| WAF negative header | PASS | 403 |
| Database note flow | PASS | HTTPS → frontend → API → RDS insert/read succeeds |
| Queue and worker report flow | PASS | API SendMessage → worker Receive/Delete → RDS report persisted |
| Node private placement and IMDS options | PASS | Two private workers; IMDSv2 required; hop limit 1 |
| IMDS token blocked from ordinary pod | PASS | IMDS token unreachable from ordinary pod  |
| VPC CNI policy agent | PASS | Expected behavior observed |
| NetworkPolicy frontend to API allowed | PASS | TCP allowed  |
| NetworkPolicy untrusted to API denied | PASS | TCP timeout; compare against the positive application checks  |
| NetworkPolicy frontend to RDS denied | PASS | TCP timeout; compare against the positive application checks  |
| After isolation: API DB still works | PASS | [{'id': 5, 'body': 'validation-0f2e6afe'}, {'id': 4, 'body': 'validation-401babfc'}, {'id': 3, 'body': 'validation-3d17336e'}, {'id': 2, 'body': 'Hello from the request path'}, {'id': 1, 'body': 'baseline-note'}] |
| After isolation: SQS and worker still work | PASS | API SendMessage → worker Receive/Delete → RDS report persisted |
| Frontend has no injected AWS application credentials | PASS | No application or fallback node credentials  |
| API Pod Identity role | PASS | API uses its dedicated role  |
| API cannot receive SQS | PASS | AccessDenied  |
| Worker cannot send SQS | PASS | AccessDenied  |
| API cannot read master secret | PASS | AccessDeniedException  |
| API SQL cannot write reports | PASS | SQL privilege denied as expected  |
| Real observer authorization | PASS | Real assumed IAM role: list pods allowed; secrets/patch/exec denied |
| Restricted Pod Security Admission | PASS | Restricted rejects noncompliant pod before creation |
| Container nonroot and read-only filesystem | PASS | UID 10001; root filesystem write rejected  |
| KMS encryption and context binding | PASS | Roundtrip succeeds; mismatched encryption context rejected |
| Admission signed image allowed | PASS | Signed digest accepted |
| Admission unsigned image denied | PASS | Unsigned digest rejected by verifier admission |

### Limitations

- Single NAT, Single-AZ RDS and single admission/controller replicas are lab cost tradeoffs.
- ALB→frontend→API uses private HTTP, not end-to-end TLS.
- NetworkPolicy standard startup mode; HTTPS egress is not restricted by hostname.
- Signing policy covers app repository, not all images; registry verification token expires.
- Console instructions are documented; actual provisioning was performed with Terraform/CLI.
