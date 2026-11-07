#!/usr/bin/env python3
"""Discover an eks-did lab created via Console, CLI, or Terraform."""
import json, os, pathlib, shlex
import boto3
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
c={'cluster':'eks-did','region':s.region_name,'vpc_id':eks['resourcesVpcConfig']['vpcId'],'public_subnets':[x['SubnetId'] for x in public],'public_cidrs':[x['CidrBlock'] for x in public],'private_cidrs':[x['CidrBlock'] for x in private],'db_cidrs':[x['CidrBlock'] for x in db],'node_sg':eks['resourcesVpcConfig']['clusterSecurityGroupId'],'db_host':rds['Endpoint']['Address'],'db_secret_arn':rds['MasterUserSecret']['SecretArn'],'queue_url':s.client('sqs').get_queue_url(QueueName='eks-did-reports')['QueueUrl'],'image_repository':s.client('ecr').describe_repositories(repositoryNames=['eks-did/notes'])['repositories'][0]['repositoryUri'],'certificate_arn':cert,'hostname':hostname,'zone_id':zone['Id'].split('/')[-1],'waf_arn':'','kms_key_id':''}
try:
 for w in s.client('wafv2').list_web_acls(Scope='REGIONAL')['WebACLs']:
  if w['Name']=='eks-did':c['waf_arn']=w['ARN']
except s.client('wafv2').exceptions.ClientError as e:print('WAF discovery unavailable:',e.response['Error']['Code'])
try:
 for a in s.client('kms').list_aliases()['Aliases']:
  if a['AliasName']=='alias/eks-did':c['kms_key_id']=a['TargetKeyId']
except s.client('kms').exceptions.ClientError as e:print('KMS discovery unavailable:',e.response['Error']['Code'])
if not public or not private or not db:raise SystemExit('Subnet names must contain -public-, -private-, -database- as documented.')
(root/'.local').mkdir(exist_ok=True)
(root/'.local/lab.json').write_text(json.dumps(c,indent=2))
(root/'.local/lab.env').write_text('\n'.join('export '+key+'='+shlex.quote(str(c[field])) for key,field in {'DB_HOST':'db_host','QUEUE_URL':'queue_url','APP_HOST':'hostname','ZONE_ID':'zone_id','CERTIFICATE_ARN':'certificate_arn','DB_SECRET_ARN':'db_secret_arn','VPC_ID':'vpc_id','NODE_SG':'node_sg','ECR_REPO':'image_repository','WAF_ARN':'waf_arn','KMS_KEY_ID':'kms_key_id'}.items())+'\n')
print('Saved .local/lab.json and .local/lab.env; no secret values are fetched.')
