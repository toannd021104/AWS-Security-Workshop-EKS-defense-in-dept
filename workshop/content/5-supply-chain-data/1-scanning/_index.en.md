---
title: "Container Image Scanning with ECR & Inspector"
weight: 1
chapter: false
pre: "<b>5.1.</b> "
---

A working image may still contain vulnerable dependencies. Enable scanning, inspect the correct digest, and evaluate the release gate before accepting an image.

## Scan the running image

Scanning identifies known package/dependency vulnerabilities. Assess severity, exploitability, available fixes, and any time-limited exception. A scan alone does not stop Kubernetes running an image.

## Step 1: configure ECR scanning

1. **ECR → Private registry → Features & Settings → Scanning**: inspect the mode. Basic scanning focuses on OS packages; Inspector enhanced scanning can also cover supported language packages.
2. **Inspector → Activate → ECR scanning** requires account-level permissions. Review account/Region scope before changing shared settings.
3. In repository `eks-did/notes`, inspect the pushed digest and wait for scan completion. No findings while pending does not mean a clean image.

![ECR image digest and tags](/images/console-ecr-images.png "① Image digest. ② Image tags.")

Select the deployed digest before opening findings. Signature artifacts and the unsigned admission-test image are not scan evidence for the running application.

4. Open a finding and inspect affected package, installed/fixed versions, and severity. A vulnerability finding is not evidence that exploitation occurred.

## Read findings and the gate decision

### Select the exact digest

```bash
source scripts/env.sh
IMAGE=$(python3 scripts/deployed-image.py)
printf '%s\n' "$IMAGE"
aws ecr describe-images --repository-name eks-did/notes \
  --query 'imageDetails[].{digest:imageDigest,tags:imageTags,scan:imageScanStatus.status}'
```

Do not rebuild during this observation. The helper compares `.local/image.txt` with API/worker Deployment images and Ready pods' `imageID`; mismatch stops the check rather than attributing a candidate scan to deployment. For new builds, use the separate candidate gate below before release, then verify deployed evidence after rollout.

Enhanced scanning uses Inspector APIs, filtered by exact hash rather than repository-wide findings:

```bash
SCAN_FILTER=$(jq -cn --arg digest "${IMAGE##*@}" \
  '{ecrImageHash:[{comparison:"EQUALS",value:$digest}],findingStatus:[{comparison:"EQUALS",value:"ACTIVE"}]}')
aws inspector2 batch-get-account-status \
  --account-ids "$(aws sts get-caller-identity --query Account --output text)"
aws inspector2 list-findings --filter-criteria "$SCAN_FILTER" \
  --query 'findings[].{severity:severity,title:title}'
```

Basic scan and Inspector APIs have different lifecycles/statuses. `start-image-scan` does not control enhanced scanning.

### Evaluate release eligibility

```bash
python3 scripts/scan-gate.py
```

The script requires completed scan coverage for the **deployed digest**. It exits 1 for HIGH/CRITICAL findings or incomplete coverage. The [scan report](/evidence/image-scan.json) records timestamp/digest. The reference scan on **2026-11-14 UTC** found 0 CRITICAL, 4 HIGH, 10 MEDIUM, 3 LOW, 1 UNTRIAGED; gate **BLOCK**. Do not apply these results to another image or scan. Missing fixes do not silently waive HIGH/CRITICAL findings. Continued use for network/identity exercises is not production release approval.

When patches are available, update base/dependencies and build a new digest. Before signing/deploying, run `python3 scripts/scan-gate.py --candidate`. It validates repository/account and assesses `.local/image.txt` without claiming the image is running. Wait for Inspector coverage and rerun if incomplete. Continue release only on ALLOW; candidate evidence is saved separately in `evidence/candidate-image-scan.json`. Fix remaining HIGH/CRITICAL findings rather than bypassing the gate. After rollout, run the default gate against the running image.

### Repository and coverage settings

`aws_ecr_repository.app` enables immutable tags/basic scan; optional `aws_inspector2_enabler.ecr` activates Inspector ECR scanning. Review registry filters to ensure the repository is covered. Build with a new tag instead of overwriting an immutable one.

The workshop records real results rather than promising zero CVEs. Gate exit codes can support release workflows; scanning alone does not block a Kubernetes deployment.

Success in this lesson means identifying the correct digest, waiting for coverage, and interpreting the decision. BLOCK for remaining HIGH/CRITICAL findings demonstrates the gate works, not that the image is approved.
