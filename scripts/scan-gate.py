#!/usr/bin/env python3
"""Inspector gate: block incomplete coverage and active HIGH/CRITICAL findings."""
import json,os,pathlib,sys,datetime
from collections import Counter
import boto3
r=pathlib.Path(__file__).resolve().parents[1];image=(r/'.local/image.txt').read_text().strip();digest=image.split('@')[1]
s=boto3.Session(profile_name=os.getenv('AWS_PROFILE','guru'),region_name=os.getenv('AWS_REGION','us-east-1'));client=s.client('inspector2')
coverage=[]
for page in client.get_paginator('list_coverage').paginate(filterCriteria={'ecrRepositoryName':[{'comparison':'EQUALS','value':'eks-did/notes'}]}):coverage.extend(x for x in page['coveredResources'] if digest in x.get('resourceId',''))
findings=[]
for page in client.get_paginator('list_findings').paginate(filterCriteria={'ecrImageHash':[{'comparison':'EQUALS','value':digest}],'findingStatus':[{'comparison':'EQUALS','value':'ACTIVE'}]}):findings.extend(page['findings'])
complete=any(x.get('lastScannedAt') and x.get('scanStatus',{}).get('statusCode')=='ACTIVE' for x in coverage)
blocked=not complete or any(x['severity'] in ['HIGH','CRITICAL'] for x in findings)
report={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'image_digest':digest,'inspector_coverage_scanned':complete,'active_findings_by_severity':dict(Counter(x['severity'] for x in findings)),'release_gate':'BLOCK' if blocked else 'ALLOW','high_critical_findings':[{'title':x['title'],'severity':x['severity'],'fix_available':x.get('fixAvailable')} for x in findings if x['severity'] in ['HIGH','CRITICAL']],'note':'The sandbox application demonstrates network/identity controls; it is not approved for production release. No exception is silently granted for a missing fix.'}
(r/'evidence/image-scan.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(1 if blocked else 0)
