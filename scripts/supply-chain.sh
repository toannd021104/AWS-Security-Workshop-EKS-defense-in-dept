#!/usr/bin/env bash
set -Eeuo pipefail
LAB_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source "$LAB_ROOT/scripts/env.sh"
IMAGE=$(cat "$LAB_ROOT/.local/image.txt")
export COSIGN_PASSWORD=${COSIGN_PASSWORD:-}
if [[ ! -f "$LAB_ROOT/.local/cosign.key" ]]; then
  cosign generate-key-pair --output-key-prefix "$LAB_ROOT/.local/cosign"
fi
cp "$LAB_ROOT/.local/cosign.pub" "$LAB_ROOT/k8s/cosign.pub"
cosign sign --yes --tlog-upload=false --key "$LAB_ROOT/.local/cosign.key" "$IMAGE"
cosign verify --insecure-ignore-tlog --key "$LAB_ROOT/k8s/cosign.pub" "$IMAGE" > "$LAB_ROOT/.local/signature-verification.json"
trivy image --format cyclonedx --output "$LAB_ROOT/.local/sbom.cdx.json" "$IMAGE"
# Public key signature demo: empty private key password is lab-only. Production uses a protected signer.
