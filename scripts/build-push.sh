#!/usr/bin/env bash
set -Eeuo pipefail
LAB_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export AWS_PROFILE=${AWS_PROFILE:-guru} AWS_REGION=${AWS_REGION:-us-east-1}
repo=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["image_repository"])' "$LAB_ROOT/.local/lab.json")
tag=${1:-"lab-$(date -u +%Y%m%d%H%M%S)"}
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${repo%%/*}"
docker build --platform linux/amd64 -t "$repo:$tag" "$LAB_ROOT/app"
docker push "$repo:$tag"
digest=$(aws ecr describe-images --repository-name eks-did/notes --image-ids imageTag="$tag" --query 'imageDetails[0].imageDigest' --output text)
mkdir -p "$LAB_ROOT/.local"
printf '%s@%s\n' "$repo" "$digest" > "$LAB_ROOT/.local/image.txt"
printf 'Pinned image: %s@%s\n' "$repo" "$digest"
