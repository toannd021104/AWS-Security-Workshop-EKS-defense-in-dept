#!/usr/bin/env bash
set -euo pipefail

: "${AWS_REGION:?Set AWS_REGION, for example us-east-1}"
: "${CLUSTER_NAME:?Set CLUSTER_NAME to the existing EKS cluster}"
: "${ROLE_ARN:?Set ROLE_ARN to the role created for this sample}"

if ! aws eks describe-addon --cluster-name "$CLUSTER_NAME" --addon-name eks-pod-identity-agent --region "$AWS_REGION" >/dev/null 2>&1; then
  aws eks create-addon --cluster-name "$CLUSTER_NAME" --addon-name eks-pod-identity-agent --region "$AWS_REGION"
fi

ASSOCIATION_ID="$(aws eks list-pod-identity-associations --cluster-name "$CLUSTER_NAME" --namespace payments --region "$AWS_REGION" --query "associations[?serviceAccount=='web-reader'].associationId | [0]" --output text)"

if [[ -n "$ASSOCIATION_ID" && "$ASSOCIATION_ID" != "None" ]]; then
  aws eks update-pod-identity-association --cluster-name "$CLUSTER_NAME" --association-id "$ASSOCIATION_ID" --role-arn "$ROLE_ARN" --region "$AWS_REGION"
else
  aws eks create-pod-identity-association --cluster-name "$CLUSTER_NAME" --namespace payments --service-account web-reader --role-arn "$ROLE_ARN" --region "$AWS_REGION"
fi

printf '\nWait for the Pod Identity Agent add-on to become ACTIVE, then restart the Deployment:\n'
printf 'kubectl rollout restart deployment/web -n payments\n'
printf 'kubectl rollout status deployment/web -n payments\n'
