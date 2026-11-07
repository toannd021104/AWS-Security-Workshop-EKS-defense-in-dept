#!/usr/bin/env bash
set -Eeuo pipefail
LAB_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source "$LAB_ROOT/scripts/env.sh"
helm repo add kyverno https://kyverno.github.io/kyverno --force-update
helm upgrade --install kyverno kyverno/kyverno --version 3.9.2 \
  --namespace kyverno --create-namespace \
  --set admissionController.replicas=1 --set backgroundController.enabled=false \
  --set cleanupController.enabled=false --set reportsController.enabled=false \
  --wait --timeout 5m
# Private ECR token is passed via stdin; it is not put in a process argument or static website.
python3 - <<'PY'
import base64,json,os,subprocess
repo=os.environ['ECR_REPO'];reg=repo.split('/')[0]
token=subprocess.check_output(['aws','ecr','get-login-password']).decode().strip()
config={'auths':{reg:{'auth':base64.b64encode(('AWS:'+token).encode()).decode()}}}
secret={'apiVersion':'v1','kind':'Secret','metadata':{'name':'ecr-verify','namespace':'kyverno'},'type':'kubernetes.io/dockerconfigjson','data':{'.dockerconfigjson':base64.b64encode(json.dumps(config).encode()).decode()}}
subprocess.run(['kubectl','apply','-f','-'],input=json.dumps(secret).encode(),check=True)
PY
python3 - <<'PY'
import os,pathlib,yaml
r=pathlib.Path(os.environ['LAB_ROOT']);repo=os.environ['ECR_REPO']
p={'apiVersion':'kyverno.io/v1','kind':'ClusterPolicy','metadata':{'name':'verify-notes-image'},'spec':{'validationFailureAction':'Enforce','background':False,'webhookConfiguration':{'failurePolicy':'Fail'},'rules':[{'name':'require-workshop-signature','match':{'any':[{'resources':{'kinds':['Pod'],'namespaces':['notes']}}]},'verifyImages':[{'imageReferences':[repo+'*'],'imageRegistryCredentials':{'secrets':['ecr-verify']},'mutateDigest':False,'verifyDigest':True,'required':True,'attestors':[{'entries':[{'keys':{'publicKeys':(r/'k8s/cosign.pub').read_text(),'rekor':{'ignoreTlog':True}}}]}]}]}]}}
(r/'k8s/verify-images.yaml').write_text(yaml.safe_dump(p,sort_keys=False))
PY
kubectl apply -f "$LAB_ROOT/k8s/verify-images.yaml"
kubectl get clusterpolicy verify-notes-image
