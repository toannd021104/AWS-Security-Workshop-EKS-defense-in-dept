#!/usr/bin/env python3
"""Remove lab controller resources before Terraform destroy. Does not destroy AWS infrastructure."""
import json,os,pathlib,subprocess,time
import boto3
from botocore.exceptions import ClientError
r=pathlib.Path(__file__).resolve().parents[1];c=json.loads((r/'.local/lab.json').read_text())
assert c['cluster']=='eks-did','Refusing unexpected cluster'
os.environ['KUBECONFIG']=str(r/'.local/kubeconfig')
s=boto3.Session(profile_name=os.getenv('AWS_PROFILE','guru'),region_name=c['region'])
cluster=json.loads(subprocess.check_output(['kubectl','config','view','--minify','-o','json']))
endpoint=s.client('eks').describe_cluster(name='eks-did')['cluster']['endpoint']
assert cluster['clusters'][0]['cluster']['server']==endpoint,'Kubeconfig does not point to lab'
def command(args):
 p=subprocess.run(args,text=True,capture_output=True)
 if p.returncode and not any(x in p.stderr for x in ['not found','NotFound','no matches','resource type']):raise RuntimeError(p.stderr)
 print(p.stdout.strip() or 'Already absent')
command(['kubectl','delete','clusterpolicy','verify-notes-image','--ignore-not-found'])
command(['kubectl','delete','ingress','notes','-n','notes','--ignore-not-found','--timeout=240s'])
elb=s.client('elbv2')
for i in range(60):
 try:elb.describe_load_balancers(Names=['eks-did-notes'])
 except elb.exceptions.LoadBalancerNotFoundException:break
 time.sleep(5)
else:raise SystemExit('ALB still exists. Keep controller running and inspect finalizers before Terraform destroy.')
record_path=r/'.local/application-dns.json'
if record_path.exists():
 try:s.client('route53').change_resource_record_sets(HostedZoneId=c['zone_id'],ChangeBatch={'Changes':[{'Action':'DELETE','ResourceRecordSet':json.loads(record_path.read_text())}]})
 except ClientError as e:
  if 'not found' not in e.response['Error']['Message'].lower():raise
command(['kubectl','delete','namespace','notes','--ignore-not-found','--timeout=180s'])
command(['helm','uninstall','kyverno','-n','kyverno'])
command(['kubectl','delete','namespace','kyverno','--ignore-not-found','--timeout=180s'])
command(['helm','uninstall','aws-load-balancer-controller','-n','kube-system'])
print('Controller-owned resources removed. Review Terraform destroy plan next; VPC/RDS still exist.')
