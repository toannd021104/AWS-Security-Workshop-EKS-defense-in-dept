#!/usr/bin/env bash
set -Eeuo pipefail
LAB_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export AWS_PROFILE=${AWS_PROFILE:-guru} AWS_REGION=${AWS_REGION:-us-east-1}
export KUBECONFIG="$LAB_ROOT/.local/kubeconfig"
mkdir -p "$LAB_ROOT/.local"
aws eks update-kubeconfig --name eks-did --region "$AWS_REGION" --kubeconfig "$KUBECONFIG" --alias eks-did
vpc=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["vpc_id"])' "$LAB_ROOT/.local/lab.json")
helm repo add eks https://aws.github.io/eks-charts --force-update
helm repo update eks
helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller --version 3.6.2 \
  --namespace kube-system --set clusterName=eks-did --set region="$AWS_REGION" --set vpcId="$vpc" \
  --set serviceAccount.create=true --set serviceAccount.name=aws-load-balancer-controller \
  --set replicaCount=1 --wait --timeout 5m
python3 "$LAB_ROOT/scripts/render.py"
kubectl apply -f "$LAB_ROOT/k8s/application.yaml"
kubectl wait --for=condition=complete job/db-init -n notes --timeout=300s
for app in frontend api worker; do kubectl rollout status "deployment/$app" -n notes --timeout=180s; done
# First inspect the working baseline; enforce isolation after validating the engine.
kubectl get nodes -o wide
kubectl get pods,services,ingress -n notes -o wide
