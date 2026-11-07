#!/usr/bin/env python3
import json, pathlib, subprocess, boto3
root=pathlib.Path(__file__).resolve().parents[1]
c=json.loads((root/'.local/lab.json').read_text())
ing=json.loads(subprocess.check_output(['kubectl','--kubeconfig',str(root/'.local/kubeconfig'),'-n','notes','get','ingress','notes','-o','json']))
alb=ing['status']['loadBalancer']['ingress'][0]['hostname']
record={'Name':c['hostname'],'Type':'CNAME','TTL':60,'ResourceRecords':[{'Value':alb}]}
response=boto3.Session(profile_name='guru',region_name=c['region']).client('route53').change_resource_record_sets(HostedZoneId=c['zone_id'],ChangeBatch={'Changes':[{'Action':'UPSERT','ResourceRecordSet':record}]})
(root/'.local/application-dns.json').write_text(json.dumps(record))
print('https://'+c['hostname']);print(response['ChangeInfo']['Status'])
