#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

kubectl delete ingress web -n payments --ignore-not-found
kubectl delete deployment web -n payments --ignore-not-found
kubectl delete service web -n payments --ignore-not-found
kubectl delete networkpolicy default-deny allow-dns-egress allow-pod-identity-agent allow-frontend-to-web allow-alb-subnets-to-web -n payments --ignore-not-found
kubectl delete serviceaccount web-reader -n payments --ignore-not-found
kubectl delete rolebinding payments-deployers payments-observers -n payments --ignore-not-found
kubectl delete role payments-deployer payments-observer -n payments --ignore-not-found
kubectl delete deployment connectivity-check -n frontend --ignore-not-found
kubectl delete deployment blocked-client -n default --ignore-not-found

if [[ -n "${CLUSTER_NAME:-}" && -n "${AWS_REGION:-}" ]]; then
  ASSOCIATION_ID="$(aws eks list-pod-identity-associations --cluster-name "$CLUSTER_NAME" --namespace payments --region "$AWS_REGION" --query "associations[?serviceAccount=='web-reader'].associationId | [0]" --output text)"
  if [[ -n "$ASSOCIATION_ID" && "$ASSOCIATION_ID" != "None" ]]; then
    aws eks delete-pod-identity-association --cluster-name "$CLUSTER_NAME" --association-id "$ASSOCIATION_ID" --region "$AWS_REGION"
  fi
fi

printf '\nRemoved the sample workloads, policies, Ingress, and Pod Identity association.\n'
printf 'The payments and frontend namespaces are left in place to protect any unrelated resources.\n'
printf 'Review the ECR repository and IAM role separately before deleting them.\n'
