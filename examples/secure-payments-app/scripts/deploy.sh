#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

: "${IMAGE_URI:?Build and push the image, then export IMAGE_URI}"

kubectl apply -f "$PROJECT_DIR/k8s/00-namespace.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/01-service-account.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/30-network-policy.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/50-connectivity-checks.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/20-service.yaml"
sed "s|REPLACE_WITH_IMAGE_URI|${IMAGE_URI}|g" "$PROJECT_DIR/k8s/10-deployment.yaml" | kubectl apply -f -

if [[ -n "${ACM_CERTIFICATE_ARN:-}" ]]; then
  : "${ALB_ALLOWED_CIDR:?Set ALB_ALLOWED_CIDR to a trusted client CIDR, preferably your current public IP /32}"
  ingress_file="$(mktemp)"
  trap 'rm -f "$ingress_file"' EXIT
  if [[ -n "${WAF_ACL_ARN:-}" ]]; then
    sed \
      -e "s|REPLACE_WITH_ACM_CERTIFICATE_ARN|${ACM_CERTIFICATE_ARN}|g" \
      -e "s|REPLACE_WITH_ALLOWED_CLIENT_CIDR|${ALB_ALLOWED_CIDR}|g" \
      -e "s|# alb.ingress.kubernetes.io/wafv2-acl-arn: REPLACE_WITH_REGIONAL_WEB_ACL_ARN|alb.ingress.kubernetes.io/wafv2-acl-arn: ${WAF_ACL_ARN}|" \
      "$PROJECT_DIR/k8s/40-ingress.example.yaml" > "$ingress_file"
  else
    sed \
      -e "s|REPLACE_WITH_ACM_CERTIFICATE_ARN|${ACM_CERTIFICATE_ARN}|g" \
      -e "s|REPLACE_WITH_ALLOWED_CLIENT_CIDR|${ALB_ALLOWED_CIDR}|g" \
      "$PROJECT_DIR/k8s/40-ingress.example.yaml" > "$ingress_file"
  fi
  kubectl apply -f "$ingress_file"
else
  printf 'ACM_CERTIFICATE_ARN not set; skipping public Ingress.\n'
fi

kubectl rollout status deployment/web -n payments --timeout=5m
kubectl rollout status deployment/connectivity-check -n frontend --timeout=5m
kubectl rollout status deployment/blocked-client -n default --timeout=5m
printf '\nDeployment ready. Run scripts/verify.sh to check the allow and deny paths.\n'
