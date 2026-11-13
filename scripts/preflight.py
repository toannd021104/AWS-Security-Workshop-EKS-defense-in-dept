#!/usr/bin/env python3
"""Read-only readiness checks for the selected workshop stage."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['setup', 'deploy', 'supply-chain'], default='setup')
    parser.add_argument('--offline', action='store_true', help='Check local tools only; do not claim AWS readiness.')
    args = parser.parse_args()
    failures = []
    def result(ok, label, detail):
        print(('PASS' if ok else 'FAIL') + ' | ' + label + ' | ' + detail)
        if not ok:
            failures.append(label)
    tools = ['aws', 'kubectl', 'helm', 'docker', 'git']
    if args.stage == 'supply-chain':
        tools += ['cosign', 'trivy']
    for name in tools:
        result(bool(shutil.which(name)), name, 'Found on PATH' if shutil.which(name) else 'Install before this stage')
    for module in ['boto3', 'yaml']:
        result(importlib.util.find_spec(module) is not None, module, 'Python dependency; install requirements-lab.txt in .venv')
    if shutil.which('docker'):
        try:
            p = subprocess.run(['docker', 'info', '--format', '{{.OSType}}/{{.Architecture}}'], capture_output=True, text=True, timeout=15)
            result(p.returncode == 0, 'Docker daemon', p.stdout.strip() if p.returncode == 0 else 'Start Docker; check your docker group membership')
        except subprocess.TimeoutExpired:
            result(False, 'Docker daemon', 'No response within 15 seconds')
    if args.offline:
        print('SKIP | AWS readiness | Offline checks do not validate credentials, permissions, quotas or the lab')
    elif importlib.util.find_spec('boto3'):
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
        try:
            session = boto3.Session(profile_name=os.getenv('AWS_PROFILE', 'guru'), region_name=os.getenv('AWS_REGION', 'us-east-1'))
            identity = session.client('sts').get_caller_identity()
            result(True, 'AWS identity', f"Account {identity['Account']}; Region {session.region_name}")
            if args.stage != 'setup':
                cfg_path = ROOT / '.local/lab.json'
                result(cfg_path.exists(), 'Lab metadata', 'Run capture-config.py for this account before deployment')
                if cfg_path.exists():
                    cfg = json.loads(cfg_path.read_text())
                    saved = cfg.get('account_id') or cfg['image_repository'].split('.')[0]
                    result(saved == identity['Account'], 'Account matches metadata', 'Metadata and active profile must belong to the same account')
                    result(cfg['region'] == session.region_name, 'Region matches metadata', 'Use the same AWS_REGION as the lab')
                    cluster = session.client('eks').describe_cluster(name=cfg['cluster'])['cluster']
                    result(cluster['status'] == 'ACTIVE', 'EKS cluster', cluster['status'])
                    result((ROOT / '.local/image.txt').exists(), 'Pinned application image', 'Run build-push.sh before deploy')
        except (BotoCoreError, ClientError, ValueError, KeyError) as error:
            # Never dump credential files or an SDK response body.
            code = error.response['Error']['Code'] if isinstance(error, ClientError) else type(error).__name__
            result(False, 'AWS readiness', code + '; check profile, Region and the documented inputs')
    print(f"Readiness: {'BLOCKED' if failures else 'local checks passed' if args.offline else 'PASSED'} ({args.stage})")
    print('These checks do not guarantee creation permissions or service quotas; review Terraform plan or Console errors separately.')
    return bool(failures)

if __name__ == '__main__':
    sys.exit(main())
