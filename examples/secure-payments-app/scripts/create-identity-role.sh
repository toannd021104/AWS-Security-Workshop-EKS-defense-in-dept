#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

: "${AWS_REGION:?Set AWS_REGION, for example us-east-1}"
: "${CLUSTER_NAME:?Set CLUSTER_NAME to the existing EKS cluster}"
ROLE_NAME="${ROLE_NAME:-EKSDepthSampleWebIdentity}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
CLUSTER_ARN="$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" --query 'cluster.arn' --output text)"
TRUST_POLICY="$(mktemp)"
trap 'rm -f "$TRUST_POLICY"' EXIT

sed -e "s|__ACCOUNT_ID__|${ACCOUNT_ID}|g" -e "s|__CLUSTER_ARN__|${CLUSTER_ARN}|g" \
  "$PROJECT_DIR/iam/pod-identity-trust-policy.example.json" > "$TRUST_POLICY"

if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  aws iam update-assume-role-policy --role-name "$ROLE_NAME" --policy-document "file://${TRUST_POLICY}"
else
  aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document "file://${TRUST_POLICY}" --description "Permissionless role for the EKS Pod Identity workshop sample"
fi

ROLE_ARN="$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)"
printf '\nRole created or updated: %s\n' "$ROLE_ARN"
printf 'No permissions policies were attached.\n'
printf 'Export it before association:\nexport ROLE_ARN=%q\n' "$ROLE_ARN"
