---
title: "Summary"
weight: 70
chapter: false
pre: ""
---

Notes began with working HTTPS access. The exercises checked that path at multiple boundaries: ALB/VPC, pod connectivity, execution privileges, human/workload identity, and application data.

## Compare your evidence

| Question | Exercise | Evidence |
|---|---|---|
| Does the request reach the right frontend? | 2.1, 2.6 | ALB target IP matches pod IP; HTTPS 200 |
| Does WAF participate? | 2.3 | Normal 200; test-header 403 |
| Can an unrelated pod reach API? | 3.2 | Denied after policy; frontend still connects |
| Can containers run arbitrary privileges? | 3.4–3.5 | Noncompliant pod rejected; app runs non-root |
| Can an ordinary pod obtain node credentials? | 3.6 | IMDSv2 required/hop limit 1; tested IMDS path blocked in lab configuration |
| Can observer change workloads? | 4.4 | Reads permitted namespace resources; changes/out-of-scope access denied |
| Do API/worker use their own roles? | 4.5–4.6 | Correct roles; legitimate SQS operations succeed, excess actions fail |
| Is the image eligible for release? | 5.1 | Findings for exact digest and separate gate decision |
| Does admission reject unsigned images? | 5.2 | Signed accepted, unsigned test denied within policy scope |
| Are secrets/KMS controlled? | 5.3–5.4 | Unneeded master-secret access denied; mismatched context cannot decrypt |

These are acceptance criteria, not automatic successes. Compare your output with the [reference report](/validation/results/) and [NetworkPolicy evidence](/evidence/network-proof-after.json), which record actual tests and dates.

## The application must keep working

Repeat the [baseline](/preparation/8-baseline/) note and report transactions after limiting network/permissions. A timeout or AccessDenied alone is insufficient; allowed actions must succeed too.

The [verification page](/validation/) describes the combined checker. Use `--supply-chain` only after signing/admission setup.

## Carry the limitations forward

TLS ends at ALB; frontend/API use internal HTTP. SGs and NetworkPolicy restrict access and do not replace internal TLS where encryption is required.

One NAT, Single-AZ RDS, and one controller/admission replica reduce lab cost. Reassess availability for real systems. Signing policy covers the specified application repository, not every image.

The [reference scan](/evidence/image-scan.json) on **2026-11-13 UTC** recorded 0 CRITICAL, 4 HIGH, 10 MEDIUM, 3 LOW, 0 UNTRIAGED; gate **BLOCK**. Compare timestamp/digest/coverage; do not infer another build's results. Passing functional and authorization tests does not approve that image for release.

## Finish the lab

Save needed evidence and follow [Cleanup](/cleanup/). Never include credentials, Terraform state, kubeconfig, or private signing keys in a report/repository.
