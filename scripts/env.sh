# Source this file from the project root: source scripts/env.sh
LAB_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export LAB_ROOT AWS_PROFILE=${AWS_PROFILE:-guru} AWS_REGION=${AWS_REGION:-us-east-1}
export KUBECONFIG="$LAB_ROOT/.local/kubeconfig"
export CLUSTER=eks-did NAMESPACE=notes
if [[ -f "$LAB_ROOT/.local/lab.env" ]]; then source "$LAB_ROOT/.local/lab.env"; fi
