#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd -- "$PROJECT_DIR/../.." && pwd)"

: "${AWS_REGION:?Set AWS_REGION, for example us-east-1}"
ECR_REPOSITORY="${ECR_REPOSITORY:-secure-payments-workshop}"
IMAGE_TAG="${IMAGE_TAG:-$(git -C "$REPO_ROOT" rev-parse --short=12 HEAD)}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
REGISTRY="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE_URI="${REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"

if ! aws ecr describe-repositories --region "$AWS_REGION" --repository-names "$ECR_REPOSITORY" >/dev/null 2>&1; then
  aws ecr create-repository --region "$AWS_REGION" --repository-name "$ECR_REPOSITORY" --image-tag-mutability IMMUTABLE --image-scanning-configuration scanOnPush=true >/dev/null
fi

aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$REGISTRY"
docker build --platform linux/amd64 --tag "$IMAGE_URI" "$PROJECT_DIR/app"
docker push "$IMAGE_URI"

printf '\nImage pushed: %s\n' "$IMAGE_URI"
printf 'Export it before deployment:\nexport IMAGE_URI=%q\n' "$IMAGE_URI"
