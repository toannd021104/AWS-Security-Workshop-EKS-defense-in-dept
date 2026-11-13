#!/usr/bin/env python3
"""Discover an eks-did lab created via Console, CLI, or Terraform."""
import argparse, json, os, pathlib, shlex
from botocore.exceptions import ClientError
import boto3
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--without-waf',action='store_true',help='Explicitly skip WAF; the edge security exercise is not validated.')
parser.add_argument('--without-kms',action='store_true',help='Explicitly skip the demonstration KMS key; the KMS exercise is not validated.')
args=parser.parse_args()
root=pathlib.Path(__file__).resolve().parents[1]
s=boto3.Session(profile_name=os.getenv('AWS_PROFILE','guru'),region_name=os.getenv('AWS_REGION','us-east-1'))
eks=s.client('eks').describe_cluster(name='eks-did')['cluster']
rds=s.client('rds').describe_db_instances(DBInstanceIdentifier='eks-did')['DBInstances'][0]
subnets=s.client('ec2').describe_subnets(Filters=[{'Name':'vpc-id','Values':[eks['resourcesVpcConfig']['vpcId']]}])['Subnets']
def tagged(subnet,part):return any(t['Key']=='Name' and part in t['Value'] for t in subnet.get('Tags',[]))
public=[x for x in subnets if tagged(x,'-public-')]; private=[x for x in subnets if tagged(x,'-private-')]; db=[x for x in subnets if tagged(x,'-database-')]
zones=s.client('route53').list_hosted_zones()['HostedZones']
zone_name=os.getenv('DNS_ZONE_NAME')
zones=[z for z in zones if not z['Config']['PrivateZone'] and (not zone_name or z['Name']==zone_name)]
if len(zones)!=1:raise SystemExit('Set DNS_ZONE_NAME to your public Route 53 zone (including trailing dot).')
zone=zones[0];hostname='notes.'+zone['Name'].rstrip('.')
certs=s.client('acm').list_certificates(CertificateStatuses=['ISSUED'])['CertificateSummaryList']
cert=next(c['CertificateArn'] for c in certs if c['DomainName']==hostname)
c={'account_id':s.client('sts').get_caller_identity()['Account'],'cluster':'eks-did','region':s.region_name,'vpc_id':eks['resourcesVpcConfig']['vpcId'],'public_subnets':[x['SubnetId'] for x in public],'public_cidrs':[x['CidrBlock'] for x in public],'private_cidrs':[x['CidrBlock'] for x in private],'db_cidrs':[x['CidrBlock'] for x in db],'node_sg':eks['resourcesVpcConfig']['clusterSecurityGroupId'],'db_host':rds['Endpoint']['Address'],'db_secret_arn':rds['MasterUserSecret']['SecretArn'],'queue_url':s.client('sqs').get_queue_url(QueueName='eks-did-reports')['QueueUrl'],'image_repository':s.client('ecr').describe_repositories(repositoryNames=['eks-did/notes'])['repositories'][0]['repositoryUri'],'certificate_arn':cert,'hostname':hostname,'zone_id':zone['Id'].split('/')[-1],'waf_arn':'','kms_key_id':''}
if not args.without_waf:
 try:
  response=s.client('wafv2').list_web_acls(Scope='REGIONAL')
  c['waf_arn']=next((w['ARN'] for w in response['WebACLs'] if w['Name']=='eks-did'),'')
 except ClientError as error:raise SystemExit('Cannot read WAF configuration: '+error.response['Error']['Code']+'. No metadata was saved. Use --without-waf only when deliberately skipping that exercise.')
 if not c['waf_arn']:raise SystemExit('WAF Web ACL eks-did is missing. Create it, or explicitly use --without-waf and record that the edge exercise is skipped.')
else:print('SKIPPED: WAF discovery and its edge-security exercise')
if not args.without_kms:
 try:
  aliases=[a for page in s.client('kms').get_paginator('list_aliases').paginate() for a in page['Aliases']]
  c['kms_key_id']=next((a['TargetKeyId'] for a in aliases if a['AliasName']=='alias/eks-did'),'')
 except ClientError as error:print('DEFERRED: KMS discovery '+error.response['Error']['Code']+'; demo key must be checked in chapter 5.4.')
 if not c['kms_key_id']:print('DEFERRED: demonstration KMS key is not configured yet; create/check alias eks-did in chapter 5.4. It is not required for the Notes baseline.')
else:print('SKIPPED: KMS key discovery and its encryption exercise')
if not public or not private or not db:raise SystemExit('Subnet names must contain -public-, -private-, -database- as documented.')
(root/'.local').mkdir(exist_ok=True)
(root/'.local/lab.json').write_text(json.dumps(c,indent=2))
(root/'.local/lab.env').write_text('\n'.join('export '+key+'='+shlex.quote(str(c[field])) for key,field in {'DB_HOST':'db_host','QUEUE_URL':'queue_url','APP_HOST':'hostname','ZONE_ID':'zone_id','CERTIFICATE_ARN':'certificate_arn','DB_SECRET_ARN':'db_secret_arn','VPC_ID':'vpc_id','NODE_SG':'node_sg','ECR_REPO':'image_repository','WAF_ARN':'waf_arn','KMS_KEY_ID':'kms_key_id'}.items())+'\n')
print('Saved .local/lab.json and .local/lab.env; no secret values are fetched.')
