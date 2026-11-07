#!/usr/bin/env python3
"""Observe connectivity before/after NetworkPolicy without changing policies."""
import argparse
import importlib.util
import json
import socket
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--stage', choices=['before', 'after'], required=True)
args = parser.parse_args()
spec = importlib.util.spec_from_file_location('lab_verify', Path(__file__).with_name('verify.py'))
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)
policies = json.loads(lab.k('get', 'networkpolicy', '-n', 'notes', '-o', 'json'))['items']
if args.stage == 'before' and policies:
    raise SystemExit('NetworkPolicy already exists. Use --stage after; this script never removes policies.')
if args.stage == 'after' and not policies:
    raise SystemExit('Apply the workshop NetworkPolicies before testing --stage after.')
prefix = 'network-proof-'
try:
    lab.make_probe(prefix + 'frontend', 'frontend')
    lab.make_probe(prefix + 'untrusted', 'untrusted')
    service = json.loads(lab.k('get', 'svc', 'api', '-n', 'notes', '-o', 'json'))['spec']['clusterIP']
    lab.check('Frontend to API allowed', lambda: lab.tcp(prefix + 'frontend', service, 8080, True))
    lab.check('Untrusted to API ' + ('allowed before policy' if args.stage == 'before' else 'denied after policy'),
              lambda: lab.tcp(prefix + 'untrusted', service, 8080, args.stage == 'before'))
    if args.stage == 'after':
        db_ip = socket.gethostbyname(lab.C['db_host'])
        lab.check('Frontend to RDS denied', lambda: lab.tcp(prefix + 'frontend', db_ip, 5432, False))
    lab.check('Application note flow', lab.note_flow)
    lab.check('Application report flow', lab.report_flow)
finally:
    lab.k('delete', 'pod', prefix + 'frontend', prefix + 'untrusted', '-n', 'notes',
          '--ignore-not-found', '--wait=false')
if not lab.RESULTS or any(row['status'] != 'PASS' for row in lab.RESULTS):
    raise SystemExit(1)
print('Connectivity checks passed; existing NetworkPolicies were left unchanged.')
