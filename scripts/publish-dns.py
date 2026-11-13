#!/usr/bin/env python3
"""Publish the application hostname after the controller reports its ALB."""
import json
import os
from pathlib import Path
import subprocess
import time
import boto3

root = Path(__file__).resolve().parents[1]
config = json.loads((root / '.local/lab.json').read_text())
session = boto3.Session(profile_name=os.getenv('AWS_PROFILE', 'guru'), region_name=config['region'])
account = session.client('sts').get_caller_identity()['Account']
expected = config.get('account_id') or config['image_repository'].split('.')[0]
if account != expected:
    raise SystemExit('Active AWS account differs from lab metadata. Capture configuration for this account first.')
print('Waiting for the Ingress controller to report the application ALB...', flush=True)
for _ in range(60):
    ingress = json.loads(subprocess.check_output([
        'kubectl', '--kubeconfig', str(root / '.local/kubeconfig'), '-n', 'notes',
        'get', 'ingress', 'notes', '-o', 'json']))
    targets = ingress.get('status', {}).get('loadBalancer', {}).get('ingress', [])
    alb = next((target['hostname'] for target in targets if target.get('hostname')), None)
    if alb:
        break
    time.sleep(5)
else:
    raise SystemExit('Ingress has no ALB hostname after 5 minutes. Inspect Ingress events and controller logs; no DNS record changed.')
record = {'Name': config['hostname'], 'Type': 'CNAME', 'TTL': 60, 'ResourceRecords': [{'Value': alb}]}
response = session.client('route53').change_resource_record_sets(
    HostedZoneId=config['zone_id'], ChangeBatch={'Changes': [{'Action': 'UPSERT', 'ResourceRecordSet': record}]})
(root / '.local/application-dns.json').write_text(json.dumps(record))
print('https://' + config['hostname'])
print(response['ChangeInfo']['Status'])
