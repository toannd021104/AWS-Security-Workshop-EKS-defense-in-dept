#!/usr/bin/env bash
set -euo pipefail

ALLOWED_CLIENT="$(kubectl get pod -n frontend -l app.kubernetes.io/name=connectivity-check -o jsonpath='{.items[0].metadata.name}')"
BLOCKED_CLIENT="$(kubectl get pod -n default -l app.kubernetes.io/name=blocked-client -o jsonpath='{.items[0].metadata.name}')"
SERVICE_URL="http://web.payments.svc.cluster.local"

printf '%s\n' 'Allowed frontend → payments request (expect HTTP 200):'
kubectl exec -n frontend "$ALLOWED_CLIENT" -- wget -T 5 -qO- "$SERVICE_URL/"

printf '\n%s\n' 'Pod Identity credential-provider check (expect container-role):'
kubectl exec -n frontend "$ALLOWED_CLIENT" -- wget -T 5 -qO- "$SERVICE_URL/api/identity"

printf '\n%s\n' 'Blocked default namespace → payments request (must fail):'
if kubectl exec -n default "$BLOCKED_CLIENT" -- wget -T 3 -qO- "$SERVICE_URL/"; then
  printf '%s\n' 'ERROR: traffic crossed the namespace boundary.' >&2
  exit 1
else
  printf '%s\n' 'PASS: the unrelated namespace cannot reach the payments pods.'
fi

printf '\n%s\n' 'Current policy and pod state:'
kubectl get networkpolicy,pods,service -n payments
