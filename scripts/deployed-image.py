#!/usr/bin/env python3
"""Print the pinned digest only when API/worker specs and running pods agree."""
import json
import os
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
kubeconfig = str(root / '.local/kubeconfig')
expected = (root / '.local/image.txt').read_text().strip()
if '@sha256:' not in expected:
    raise SystemExit('Expected an immutable image digest in .local/image.txt.')

def kubernetes(*args):
    return json.loads(subprocess.check_output(['kubectl', '--kubeconfig', kubeconfig, *args, '-o', 'json']))

for name in ['api', 'worker']:
    deployment = kubernetes('get', 'deployment', name, '-n', 'notes')
    images = [c['image'] for c in deployment['spec']['template']['spec']['containers'] if c['name'] == name]
    if images != [expected]:
        raise SystemExit(f'{name} image differs from .local/image.txt. Do not scan or sign it as the deployed digest. Review the build and deployment first.')
    pods = kubernetes('get', 'pods', '-n', 'notes', '-l', f'app={name},workshop-serving=true')['items']
    ready = [p for p in pods if not p['metadata'].get('deletionTimestamp') and any(c['type'] == 'Ready' and c['status'] == 'True' for c in p.get('status', {}).get('conditions', []))]
    if len(ready) < deployment['spec']['replicas']:
        raise SystemExit(f'{name} rollout is incomplete. Wait for ready replicas before recording scan/signature evidence.')
    for pod in ready:
        status = next((c for c in pod['status'].get('containerStatuses', []) if c['name'] == name), {})
        if not status.get('imageID', '').endswith(expected.split('@', 1)[1]):
            raise SystemExit(f'{name} running digest differs from the expected image. Wait for rollout and inspect container imageID.')
print(expected)
