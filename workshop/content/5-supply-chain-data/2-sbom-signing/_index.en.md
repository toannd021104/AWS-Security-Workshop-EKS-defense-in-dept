---
title: "SBOM, Image Signing & Admission Policies"
weight: 2
chapter: false
pre: "<b>5.2.</b> "
---

A tag or repository name does not establish a trusted origin. Create an SBOM, sign by digest, and enforce signature verification at admission.

## Different roles for scan, SBOM, and signature

An SBOM lists dependencies. A signature binds a digest to a trusted public key. Admission verifies an image before workload creation. Signed images still need the vulnerability assessment from 5.1.

![Build, signing, and admission flow](/images/en/supply-chain.svg "Check an image from build through workload admission.")

Use the SBOM to compare image components with scan findings. A valid signature establishes signer and digest integrity, not vulnerability-free dependencies.

## Step 1: inspect the existing image

In **ECR → repository → Images**, record the digest, not only the tag. IAM/ECR permissions govern pushing. Signature enforcement belongs to Kubernetes admission and requires CLI here.

## Step 2: create SBOM and signature

Install [Cosign](https://docs.sigstore.dev/cosign/system_config/installation/) and [Trivy](https://trivy.dev/latest/getting-started/installation/) using their official Linux instructions. Check readiness before policy changes:

```bash
cosign version
trivy --version
python3 scripts/preflight.py --stage supply-chain
```

Tools must be on PATH, Docker running, and `.local/image.txt` must contain this account's built digest. Tools use the ECR login from the build. If expired, rerun the login command in [build-push.sh](/source/scripts/build-push.sh); no rebuild/deployment is needed merely to refresh login.

```bash
source scripts/env.sh
bash scripts/supply-chain.sh
```

The script verifies the deployed digest, generates `.local/sbom.cdx.json` with Trivy, and signs with Cosign. Public key is `k8s/cosign.pub`; the private key remains gitignored in `.local/`. An empty key password is a lab convenience; production requires a protected signer and key/rotation policies.

The lab does not upload to a public transparency log. `--tlog-upload=false` and `--insecure-ignore-tlog` skip that requirement, **not public-key signature verification**.

```bash
IMAGE=$(cat .local/image.txt)
cosign verify --insecure-ignore-tlog --key k8s/cosign.pub "$IMAGE"
```

For an update after admission is enabled: build a new digest, run `python3 scripts/scan-gate.py --candidate`, and only on ALLOW sign with `bash scripts/supply-chain.sh --candidate`, then redeploy. Candidate signing validates the current repository but does not itself assert deployment or release approval. After rollout, use `deployed-image.py` and the default scan gate for running-image evidence. Keep the policy's trusted public key stable during the update.

## Step 3: enforce admission

```bash
bash scripts/admission.sh
bash scripts/prepare-unsigned.sh
kubectl get clusterpolicy verify-notes-image
```

The policy covers namespace `notes` and the lab application repository, requiring the workshop public key. Kyverno fetches manifests/signatures from private ECR using a registry Secret created through stdin, never Hugo or command arguments. ECR tokens expire after roughly 12 hours; refresh with the script before another session. Production should use an appropriate managed identity/credential provider.

**Positive:** a Restricted server-side dry-run pod with the signed digest is accepted. **Negative:** a new unsigned digest in the same repository is rejected by the verification webhook. `prepare-unsigned.sh` builds the same source with a different image label to produce a different digest, pushes it, and neither signs nor deploys it. `verify.py --supply-chain` then tests both.

## Verify scope and admission decisions

In tested chart 3.9.2, legacy `ClusterPolicy` remains supported. Review migration to `ImageValidatingPolicy` during upgrades. This policy covers API/worker images in the lab repository, not every repository or the upstream Nginx image. Do not claim cluster-wide signed-only execution. Fail-closed verification depends on verifier/registry availability; one Kyverno replica is a lab tradeoff. Native CEL can check registry/digest patterns but does not itself verify Cosign signatures.

After completing the workshop's other controls:

```bash
python3 scripts/verify.py --supply-chain
```

Signed digest must be accepted, unsigned digest rejected specifically for signature verification. Server-side dry run does not deploy the unsigned image.
