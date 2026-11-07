#!/usr/bin/env bash
set -Eeuo pipefail
LAB_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source "$LAB_ROOT/scripts/env.sh"
tag="unsigned-$(date -u +%Y%m%d%H%M%S)"
docker build --platform linux/amd64 --label workshop-signature=unsigned -t "$ECR_REPO:$tag" "$LAB_ROOT/app"
docker push "$ECR_REPO:$tag"
digest=$(aws ecr describe-images --repository-name eks-did/notes --image-ids imageTag="$tag" --query 'imageDetails[0].imageDigest' --output text)
printf '%s@%s\n' "$ECR_REPO" "$digest" > "$LAB_ROOT/.local/unsigned-image.txt"
