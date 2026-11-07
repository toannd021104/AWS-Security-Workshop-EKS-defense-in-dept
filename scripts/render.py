#!/usr/bin/env python3
"""Render manifests from non-secret Terraform outputs. No credentials are written."""
import json
import pathlib
import subprocess
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
config = json.loads((ROOT / '.local/lab.json').read_text())
image = (ROOT / '.local/image.txt').read_text().strip()
manifest = []
def add(kind, name, spec=None, **fields):
    version = {'Deployment':'apps/v1', 'Job':'batch/v1', 'Ingress':'networking.k8s.io/v1', 'NetworkPolicy':'networking.k8s.io/v1','Role':'rbac.authorization.k8s.io/v1','RoleBinding':'rbac.authorization.k8s.io/v1'}.get(kind,'v1')
    obj={'apiVersion':version,'kind':kind,'metadata':{'name':name,'namespace':'notes'}}
    if spec is not None: obj['spec']=spec
    obj.update(fields); manifest.append(obj); return obj
manifest.append({'apiVersion':'v1','kind':'Namespace','metadata':{'name':'notes','labels':{'pod-security.kubernetes.io/enforce':'restricted','pod-security.kubernetes.io/enforce-version':'v1.35','pod-security.kubernetes.io/warn':'restricted','pod-security.kubernetes.io/audit':'restricted'}}})
for name in ['frontend','api','worker','db-init']:
    add('ServiceAccount',name,automountServiceAccountToken=False)
nginx='''pid /tmp/nginx.pid;
events { worker_connections 256; }
http {
  include /etc/nginx/mime.types;
  client_body_temp_path /tmp/client_temp;
  proxy_temp_path /tmp/proxy_temp;
  fastcgi_temp_path /tmp/fastcgi_temp;
  uwsgi_temp_path /tmp/uwsgi_temp;
  scgi_temp_path /tmp/scgi_temp;
  server {
    listen 8080;
    server_tokens off;
    root /usr/share/nginx/html;
    location = /healthz { return 200 'ok'; add_header Content-Type text/plain; }
    location /api/ { proxy_pass http://api.notes.svc.cluster.local:8080/; proxy_connect_timeout 5s; proxy_read_timeout 15s; }
    location / { try_files $uri /index.html; }
  }
}
'''
add('ConfigMap','frontend',data={'nginx.conf':nginx,'index.html':(ROOT/'app/index.html').read_text()})
add('ConfigMap','application',data={'AWS_REGION':config['region'],'DB_HOST':config['db_host'],'QUEUE_URL':config['queue_url'],'DB_SECRET_ARN':config['db_secret_arn']})
security={'runAsNonRoot':True,'runAsUser':10001,'runAsGroup':10001,'seccompProfile':{'type':'RuntimeDefault'}}
container_security={'allowPrivilegeEscalation':False,'readOnlyRootFilesystem':True,'capabilities':{'drop':['ALL']}}
for name in ['frontend','api','worker','db-init']:
    c={'name':name,'image':'nginxinc/nginx-unprivileged:1.28-alpine' if name=='frontend' else image,'securityContext':container_security,'resources':{'requests':{'cpu':'50m','memory':'96Mi'},'limits':{'cpu':'500m','memory':'256Mi'}}}
    pod={'serviceAccountName':name,'automountServiceAccountToken':False,'securityContext':security,'containers':[c]}
    if name=='frontend':
        c['args']=['nginx','-c','/etc/workshop/nginx.conf','-g','daemon off;']
        c['volumeMounts']=[{'name':'config','mountPath':'/etc/workshop','readOnly':True},{'name':'config','mountPath':'/usr/share/nginx/html/index.html','subPath':'index.html','readOnly':True},{'name':'tmp','mountPath':'/tmp'}]
        pod['volumes']=[{'name':'config','configMap':{'name':'frontend'}},{'name':'tmp','emptyDir':{'sizeLimit':'32Mi'}}]
    else:
        c['envFrom']=[{'configMapRef':{'name':'application'}}]
        c['env']=[{'name':'MODE','value':name}]
    if name in ['frontend','api']:
        c['ports']=[{'containerPort':8080,'name':'http'}]
        c['readinessProbe']={'httpGet':{'path':'/healthz','port':8080},'initialDelaySeconds':3,'periodSeconds':5}
        c['livenessProbe']={'httpGet':{'path':'/healthz','port':8080},'initialDelaySeconds':15,'periodSeconds':10}
    template={'metadata':{'labels':{'app':name}},'spec':pod}
    if name=='db-init':
        pod['restartPolicy']='Never'
        add('Job','db-init',{'backoffLimit':3,'activeDeadlineSeconds':300,'template':template})
    else:
        add('Deployment',name,{'replicas':2 if name in ['frontend','api'] else 1,'selector':{'matchLabels':{'app':name}},'template':template})
    if name in ['frontend','api']:
        add('Service',name,{'type':'ClusterIP','selector':{'app':name},'ports':[{'name':'http','port':8080,'targetPort':8080}]})
annotations={'alb.ingress.kubernetes.io/scheme':'internet-facing','alb.ingress.kubernetes.io/target-type':'ip','alb.ingress.kubernetes.io/subnets':','.join(config['public_subnets']),'alb.ingress.kubernetes.io/listen-ports':'[{"HTTP":80},{"HTTPS":443}]','alb.ingress.kubernetes.io/ssl-redirect':'443','alb.ingress.kubernetes.io/certificate-arn':config['certificate_arn'],'alb.ingress.kubernetes.io/healthcheck-path':'/healthz','alb.ingress.kubernetes.io/load-balancer-name':'eks-did-notes','alb.ingress.kubernetes.io/tags':'Project=eks-did,ManagedBy=aws-load-balancer-controller'}
if config['waf_arn']: annotations['alb.ingress.kubernetes.io/wafv2-acl-arn']=config['waf_arn']
add('Ingress','notes',{'ingressClassName':'alb','rules':[{'host':config['hostname'],'http':{'paths':[{'path':'/','pathType':'Prefix','backend':{'service':{'name':'frontend','port':{'number':8080}}}}]}}]})['metadata']['annotations']=annotations
add('Role','observer',rules=[{'apiGroups':[''],'resources':['pods','services'],'verbs':['get','list','watch']},{'apiGroups':['apps'],'resources':['deployments'],'verbs':['get','list','watch']}])
add('RoleBinding','observer',subjects=[{'kind':'Group','name':'notes-observers','apiGroup':'rbac.authorization.k8s.io'}],roleRef={'kind':'Role','name':'observer','apiGroup':'rbac.authorization.k8s.io'})
(ROOT/'k8s/application.yaml').write_text(yaml.safe_dump_all(manifest,sort_keys=False,allow_unicode=True))
manifest.clear()
add('NetworkPolicy','default-deny',{'podSelector':{},'policyTypes':['Ingress','Egress']})
def rule_policy(name,selector,ingress=None,egress=None):
    spec={'podSelector':{'matchLabels':{'app':selector}},'policyTypes':[]}
    for key,value in [('ingress',ingress),('egress',egress)]:
        if value is not None: spec['policyTypes'].append(key.capitalize()); spec[key]=value
    add('NetworkPolicy',name,spec)
def pods(app): return {'podSelector':{'matchLabels':{'app':app}}}
def port(n,protocol='TCP'): return {'port':n,'protocol':protocol}
# DNS is cluster infrastructure, scoped by namespace and pod labels.
add('NetworkPolicy','allow-dns',{'podSelector':{},'policyTypes':['Egress'],'egress':[{'to':[{'namespaceSelector':{'matchLabels':{'kubernetes.io/metadata.name':'kube-system'}},'podSelector':{'matchLabels':{'k8s-app':'kube-dns'}}}],'ports':[port(53),port(53,'UDP')]}]})
rule_policy('frontend','frontend',ingress=[{'from':[{'ipBlock':{'cidr':x}} for x in config['public_cidrs']],'ports':[port(8080)]}],egress=[{'to':[pods('api')],'ports':[port(8080)]}])
for name in ['api','worker','db-init']:
    egress=[{'to':[{'ipBlock':{'cidr':x}} for x in config['db_cidrs']],'ports':[port(5432)]},{'to':[{'ipBlock':{'cidr':'169.254.170.23/32'}}],'ports':[port(80)]},{'to':[{'ipBlock':{'cidr':'0.0.0.0/0','except':['10.0.0.0/8','172.16.0.0/12','192.168.0.0/16','169.254.0.0/16']}}],'ports':[port(443)]}]
    rule_policy(name,name,ingress=[{'from':[pods('frontend')],'ports':[port(8080)]}] if name=='api' else [],egress=egress)
(ROOT/'k8s/network-policies.yaml').write_text(yaml.safe_dump_all(manifest,sort_keys=False))
print('Rendered application.yaml and network-policies.yaml (no secret values).')
