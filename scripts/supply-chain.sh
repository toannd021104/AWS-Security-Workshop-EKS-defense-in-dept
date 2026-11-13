#!/usr/bin/env bash
set -Eeuo pipefail
LAB_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source "$LAB_ROOT/scripts/env.sh"
python3 "$LAB_ROOT/scripts/preflight.py" --stage supply-chain
case "${1:-}" in
  "") IMAGE=$(python3 "$LAB_ROOT/scripts/deployed-image.py") ;;
  --candidate)
    IMAGE=$(cat "$LAB_ROOT/.local/image.txt")
    if [[ "$IMAGE" != "$ECR_REPO"@sha256:* ]] || [[ ! "${IMAGE##*@sha256:}" =~ ^[0-9a-f]{64}$ ]]; then
      echo 'Candidate must be a valid digest in the current lab ECR repository.' >&2
      exit 1
    fi
    echo 'Signing candidate image; this does not claim it is deployed or approved by the scan gate.'
    ;;
  *) echo 'Usage: supply-chain.sh [--candidate]' >&2; exit 2 ;;
esac
export COSIGN_PASSWORD=${COSIGN_PASSWORD:-}
if [[ ! -f "$LAB_ROOT/.local/cosign.key" ]]; then
  cosign generate-key-pair --output-key-prefix "$LAB_ROOT/.local/cosign"
fi
cp "$LAB_ROOT/.local/cosign.pub" "$LAB_ROOT/k8s/cosign.pub"
cosign sign --yes --tlog-upload=false --key "$LAB_ROOT/.local/cosign.key" "$IMAGE"
cosign verify --insecure-ignore-tlog --key "$LAB_ROOT/k8s/cosign.pub" "$IMAGE" > "$LAB_ROOT/.local/signature-verification.json"
trivy image --format cyclonedx --output "$LAB_ROOT/.local/sbom.cdx.json" "$IMAGE"
# Public key signature demo: empty private key password is lab-only. Production uses a protected signer.
