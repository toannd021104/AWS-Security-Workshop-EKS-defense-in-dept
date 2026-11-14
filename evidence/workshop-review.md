# Workshop review — 2026-11-13

> Historical review: resource-state statements below describe the November 13 run. See [the November 14 live learner replay](live-learner-replay-2026-11-14.json) for current execution, corrections, and cleanup.

An independent agent reviewed all 46 learner pages, source generators, application manifests, Terraform, deployment, discovery, verification and signing scripts. The review was static; the primary agent ran the AWS checks separately.

Nine initial findings and follow-up regressions were corrected: controller-owned network probes; probes excluded from Service backends; timeout distinguished from connection refusal; deployed digest checked before scanning/signing; explicit candidate scan/sign path; Terraform resource reuse; complete observer IAM inputs/policies; completed initializer Job lifecycle; dependency-ordered cleanup; required WAF discovery and deferred demonstration KMS key.

Fresh reference infrastructure was provisioned using Terraform/CLI with profile guru in us-east-1. This does not establish that the Console provisioning path was executed end to end. Network proofs passed 4/4 before isolation and 5/5 afterward. After signed redeployment, all 25 functional/security/admission checks passed. The full report and image scan carry their own timestamps and outcomes. The image scan gate remains BLOCK for four active HIGH findings; passing functional tests is not release approval.

Browser checks covered all 46 pages at 1500px and 390px, navigation, Vietnamese search, clipboard behavior, image zoom, natural-size scrolling, keyboard access, Escape and focus restoration. A repeat deployment recreated the completed db-init Job without an immutable-template error; its signed replacement completed under the admission policy. Terraform validate passed and its isolated-state refresh plan reported no changes. Python and shell syntax, Hugo generation and local references were checked. Full teardown has not been executed; cloud resources remain running for review.

Review closure means no unresolved source blocker remained among the findings reviewed. It is not a production readiness or exhaustive security certification.
