#!/usr/bin/env python3
"""Real sandbox validation. No secret values or credentials are logged."""
import argparse, datetime, json, os, pathlib, re, subprocess, sys, time, urllib.request, urllib.error, uuid
import boto3
from botocore.exceptions import ClientError

R=pathlib.Path(__file__).resolve().parents[1]
os.environ.setdefault('AWS_PROFILE','guru');os.environ.setdefault('AWS_REGION','us-east-1')
os.environ['KUBECONFIG']=str(R/'.local/kubeconfig')
C=json.loads((R/'.local/lab.json').read_text());IMAGE=(R/'.local/image.txt').read_text().strip()
SESSION=boto3.Session(profile_name=os.environ['AWS_PROFILE'],region_name=C['region'])
RESULTS=[]
def run(cmd,timeout=90):
 p=subprocess.run(cmd,text=True,capture_output=True,timeout=timeout)
 if p.returncode:raise RuntimeError((p.stderr or p.stdout)[-1400:])
 return p.stdout

def k(*args,timeout=90):return run(['kubectl',*args],timeout)
def podexec(pod,code):return k('exec','-n','notes',pod,'--','python','-c',code,timeout=35)
def check(name,fn):
 print('TEST',name,flush=True)
 try:
  detail=fn()
  row={'test':name,'status':'PASS','detail':str(detail or 'Expected behavior observed')[:500]}
 except Exception as e:row={'test':name,'status':'FAIL','detail':str(e)[:1000]}
 RESULTS.append(row);print(row['status'],row['detail'],flush=True)

def expect(value,message):
 if not value:raise AssertionError(message)

def http(path,body=None,headers=None,expected=200):
 payload=None if body is None else json.dumps(body).encode()
 h={'Content-Type':'application/json',**(headers or {})}
 req=urllib.request.Request('https://'+C['hostname']+path,data=payload,headers=h)
 try:
  with urllib.request.urlopen(req,timeout=25) as response:code=response.status;data=response.read()
 except urllib.error.HTTPError as e:code=e.code;data=e.read()
 expect(code==expected,f'HTTP {code}; expected {expected}: {data[:180]}')
 return json.loads(data) if data.startswith((b'{',b'[')) else code

def make_probe(name,app):
 obj={'apiVersion':'v1','kind':'Pod','metadata':{'name':name,'namespace':'notes','labels':{'app':app}},'spec':{'serviceAccountName':'frontend','automountServiceAccountToken':False,'securityContext':{'runAsNonRoot':True,'runAsUser':10001,'seccompProfile':{'type':'RuntimeDefault'}},'containers':[{'name':'probe','image':IMAGE,'command':['sleep','1800'],'securityContext':{'allowPrivilegeEscalation':False,'readOnlyRootFilesystem':True,'capabilities':{'drop':['ALL']}},'resources':{'requests':{'cpu':'10m','memory':'32Mi'},'limits':{'cpu':'100m','memory':'96Mi'}}}]}}
 p=subprocess.run(['kubectl','apply','-f','-'],input=json.dumps(obj),text=True,capture_output=True)
 expect(p.returncode==0,p.stderr)
 k('wait','--for=condition=Ready','pod/'+name,'-n','notes','--timeout=120s',timeout=130)

def tcp(pod,host,port,allowed):
 code=f'''import socket
try:
 s=socket.create_connection(({host!r},{port}),timeout=4);s.close();ok=True
except OSError:ok=False
assert ok == {allowed!r}, "unexpected TCP connectivity"
print("TCP allowed" if ok else "TCP blocked")'''
 return podexec(pod,code)

def denied(code):return podexec('deployment/api',code)
def iam_deny(service,method,args,pod='deployment/api'):
 return podexec(pod,f'''import boto3
from botocore.exceptions import ClientError
try:
 boto3.client({service!r},region_name={C['region']!r}).{method}(**{args!r})
 raise AssertionError("unexpected authorization success")
except ClientError as e:
 code=e.response["Error"]["Code"]
 assert "AccessDenied" in code or "Unauthorized" in code, code
 print(code)''')

def observer():
 account=SESSION.client('sts').get_caller_identity()['Account']
 cfg=str(R/'.local/observer-kubeconfig')
 run(['aws','eks','update-kubeconfig','--name','eks-did','--role-arn',f'arn:aws:iam::{account}:role/eks-did-observer','--kubeconfig',cfg,'--alias','observer'])
 data=json.loads(run(['kubectl','--kubeconfig',cfg,'get','pods','-n','notes','-o','json']))
 expect(bool(data['items']),'observer cannot list pods')
 for action in [('get','secrets'),('patch','deployments'),('create','pods/exec')]:
  p=subprocess.run(['kubectl','--kubeconfig',cfg,'auth','can-i',*action,'-n','notes'],text=True,capture_output=True)
  expect(p.stdout.strip()=='no',f'observer unexpectedly allowed {action}: {p.stdout} {p.stderr}')
 p=subprocess.run(['kubectl','--kubeconfig',cfg,'get','secrets','-n','notes'],text=True,capture_output=True)
 expect(p.returncode!=0 and 'Forbidden' in p.stderr,'actual Secrets request not forbidden')
 return 'Real assumed IAM role: list pods allowed; secrets/patch/exec denied'

def psa():
 p=subprocess.run(['kubectl','run','psa-negative','-n','notes','--image=nginx:1.28-alpine','--dry-run=server','-o','yaml'],text=True,capture_output=True)
 expect(p.returncode!=0 and 'violates PodSecurity' in p.stderr,p.stderr)
 return 'Restricted rejects noncompliant pod before creation'

def node_metadata():
 rs=SESSION.client('ec2').describe_instances(Filters=[{'Name':'tag:eks:cluster-name','Values':['eks-did']},{'Name':'instance-state-name','Values':['running']}])
 nodes=[i for r in rs['Reservations'] for i in r['Instances']]
 expect(len(nodes)==2,'Expected two running workers')
 for n in nodes:
  expect(not n.get('PublicIpAddress'),'worker has public IP')
  expect(n['MetadataOptions']['HttpTokens']=='required','IMDSv2 not required')
  expect(n['MetadataOptions']['HttpPutResponseHopLimit']==1,'hop limit not 1')
 return 'Two private workers; IMDSv2 required; hop limit 1'

def kms_roundtrip():
 kms=SESSION.client('kms');context={'Workshop':'eks-did'}
 encrypted=kms.encrypt(KeyId='alias/eks-did',Plaintext=b'eks-defense-in-depth-demo',EncryptionContext=context)['CiphertextBlob']
 expect(kms.decrypt(CiphertextBlob=encrypted,EncryptionContext=context)['Plaintext']==b'eks-defense-in-depth-demo','KMS roundtrip failed')
 try:kms.decrypt(CiphertextBlob=encrypted,EncryptionContext={'Workshop':'other'})
 except kms.exceptions.InvalidCiphertextException:return 'Roundtrip succeeds; mismatched encryption context rejected'
 raise AssertionError('KMS accepted incorrect context')

def note_flow():
 text='validation-'+str(uuid.uuid4())[:8]
 saved=http('/api/notes',{'body':text},expected=201)
 expect(any(x['id']==saved['id'] and x['body']==text for x in http('/api/notes')),'note not persisted')
 return 'HTTPS → frontend → API → RDS insert/read succeeds'

def report_flow():
 task=http('/api/reports',{},expected=202)['id']
 for _ in range(12):
  if any(r['id']==task for r in http('/api/reports')):return 'API SendMessage → worker Receive/Delete → RDS report persisted'
  time.sleep(3)
 raise AssertionError('Report not processed within 36 seconds')

def signature_test(image,allowed):
 obj={'apiVersion':'v1','kind':'Pod','metadata':{'name':'signature-probe','namespace':'notes'},'spec':{'serviceAccountName':'frontend','automountServiceAccountToken':False,'securityContext':{'runAsNonRoot':True,'runAsUser':10001,'seccompProfile':{'type':'RuntimeDefault'}},'containers':[{'name':'test','image':image,'command':['sleep','60'],'securityContext':{'allowPrivilegeEscalation':False,'capabilities':{'drop':['ALL']}}}]}}
 p=subprocess.run(['kubectl','create','--dry-run=server','-f','-'],input=json.dumps(obj),text=True,capture_output=True,timeout=60)
 expect((p.returncode==0)==allowed,p.stderr or p.stdout)
 if not allowed:expect('signature' in p.stderr.lower() or 'verify' in p.stderr.lower(),'Denied for a reason other than image verification: '+p.stderr)
 return 'Signed digest accepted' if allowed else 'Unsigned digest rejected by verifier admission'

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--supply-chain',action='store_true');args=parser.parse_args()
 check('HTTPS frontend',lambda:http('/'))
 check('API health',lambda:http('/api/healthz'))
 check('WAF negative header',lambda:http('/',headers={'x-workshop-test':'block-me'},expected=403))
 check('Database note flow',note_flow)
 check('Queue and worker report flow',report_flow)
 check('Node private placement and IMDS options',node_metadata)
 check('IMDS token blocked from ordinary pod',lambda:podexec('deployment/api','''import urllib.request
try:
 urllib.request.urlopen(urllib.request.Request("http://169.254.169.254/latest/api/token",method="PUT",headers={"X-aws-ec2-metadata-token-ttl-seconds":"60"}),timeout=3)
 raise AssertionError("IMDS reached")
except (OSError,TimeoutError):print("IMDS token unreachable from ordinary pod")'''))
 check('VPC CNI policy agent',lambda:expect(all(any(c['name'] in ['aws-eks-nodeagent','aws-network-policy-agent'] for c in p['spec']['containers']) for p in json.loads(k('get','pods','-n','kube-system','-l','k8s-app=aws-node','-o','json'))['items']),'Missing policy agent'))
 try:
  make_probe('probe-frontend','frontend');make_probe('probe-untrusted','untrusted')
  service=json.loads(k('get','svc','api','-n','notes','-o','json'))['spec']['clusterIP']
  policies=json.loads(k('get','networkpolicy','-n','notes','-o','json'))['items']
  if not policies:check('Before isolation: untrusted can reach API',lambda:tcp('probe-untrusted',service,8080,True))
  k('apply','-f',str(R/'k8s/network-policies.yaml'));time.sleep(6)
  check('NetworkPolicy frontend to API allowed',lambda:tcp('probe-frontend',service,8080,True))
  check('NetworkPolicy untrusted to API denied',lambda:tcp('probe-untrusted',service,8080,False))
  # Resolve externally on the workstation, so this negative test does not merely test DNS denial.
  import socket
  db_ip=socket.gethostbyname(C['db_host'])
  check('NetworkPolicy frontend to RDS denied',lambda:tcp('probe-frontend',db_ip,5432,False))
  check('After isolation: API DB still works',lambda:http('/api/notes'))
  check('After isolation: SQS and worker still work',report_flow)
  check('Frontend has no injected AWS application credentials',lambda:podexec('probe-frontend','import os,boto3; assert "AWS_CONTAINER_CREDENTIALS_FULL_URI" not in os.environ; assert boto3.Session().get_credentials() is None; print("No application or fallback node credentials")'))
 finally:
  k('delete','pod','probe-frontend','probe-untrusted','-n','notes','--ignore-not-found','--wait=false')
 check('API Pod Identity role',lambda:podexec('deployment/api','import boto3; a=boto3.client("sts").get_caller_identity()["Arn"]; assert ":assumed-role/eks-did-api/" in a; print("API uses its dedicated role")'))
 check('API cannot receive SQS',lambda:iam_deny('sqs','receive_message',{'QueueUrl':C['queue_url'],'WaitTimeSeconds':0}))
 check('Worker cannot send SQS',lambda:iam_deny('sqs','send_message',{'QueueUrl':C['queue_url'],'MessageBody':'negative-permission-test'},'deployment/worker'))
 check('API cannot read master secret',lambda:iam_deny('secretsmanager','get_secret_value',{'SecretId':C['db_secret_arn']}))
 check('API SQL cannot write reports',lambda:podexec('deployment/api','''import main,psycopg
try:
 with main.connect() as conn: conn.execute("INSERT INTO notes.reports(id,note_count) VALUES(gen_random_uuid(),0)")
 raise AssertionError("API unexpectedly inserted report")
except psycopg.errors.InsufficientPrivilege:print("SQL privilege denied as expected")'''))
 check('Real observer authorization',observer)
 check('Restricted Pod Security Admission',psa)
 check('Container nonroot and read-only filesystem',lambda:podexec('deployment/api','''import os,pathlib
assert os.getuid()==10001
try:pathlib.Path("/app/unexpected-write").write_text("test")
except OSError:print("UID 10001; root filesystem write rejected")
else:raise AssertionError("root filesystem writable")'''))
 check('KMS encryption and context binding',kms_roundtrip)
 if args.supply_chain:
  check('Admission signed image allowed',lambda:signature_test(IMAGE,True))
  unsigned=(R/'.local/unsigned-image.txt').read_text().strip()
  check('Admission unsigned image denied',lambda:signature_test(unsigned,False))
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 results={'timestamp_utc':now,'results':RESULTS,'limitations':['Single NAT, Single-AZ RDS and single admission/controller replicas are lab cost tradeoffs.','ALB→frontend→API uses private HTTP, not end-to-end TLS.','NetworkPolicy standard startup mode; HTTPS egress is not restricted by hostname.','Signing policy covers app repository, not all images; registry verification token expires.','Console instructions are documented; actual provisioning was performed with Terraform/CLI.']}
 # Redact account IDs from public diagnostics while keeping local logs for investigation.
 public=json.loads(re.sub(r'\b\d{12}\b','ACCOUNT',json.dumps(results,ensure_ascii=False)))
 (R/'.local/verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
 (R/'evidence/verification.json').write_text(json.dumps(public,ensure_ascii=False,indent=2))
 rows=['| Phép thử | Kết quả | Chi tiết |','|---|---|---|']+[f"| {x['test']} | {x['status']} | {x['detail'].replace('|','/').replace(chr(10),' ')[:240]} |" for x in public['results']]
 p=R/'workshop/content/validation/results/_index.md';p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text('---\ntitle: "Kết quả kiểm chứng thực tế"\nweight: 1\n---\n\nThời điểm UTC: '+now+'\n\n'+'\n'.join(rows)+'\n\n### Giới hạn\n\n'+'\n'.join('- '+l for l in public['limitations'])+'\n')
 failed=sum(x['status']=='FAIL' for x in RESULTS);print(f'{len(RESULTS)-failed}/{len(RESULTS)} passed')
 return bool(failed)
if __name__=='__main__':sys.exit(main())
