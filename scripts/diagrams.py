#!/usr/bin/env python3
"""Generate matching SVG and editable diagrams.net diagrams using the supplied icons."""
from pathlib import Path
from html import escape
import argparse, base64, urllib.parse, xml.etree.ElementTree as ET
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--only", nargs="+", help="Regenerate only the named diagrams")
args=parser.parse_args()
R=Path(__file__).resolve().parents[1]; OUT=R/'workshop/static/images'; OUT.mkdir(parents=True,exist_ok=True)
ICONS=Path('/home/ubuntu/devops-blog2/src/assets/icons')
MAP={'alb':'aws/elastic-load-balancing-application-load-balancer.svg','eks':'aws/amazon-elastic-kubernetes-service.svg','rds':'aws/amazon-rds.svg','sqs':'aws/amazon-simple-queue-service.svg','nat':'aws/amazon-vpc-nat-gateway.svg','igw':'aws/amazon-vpc-internet-gateway.svg','iam':'aws/aws-identity-and-access-management.svg','acm':'aws/aws-certificate-manager.svg','waf':'aws/aws-waf.svg','ecr':'aws/amazon-elastic-container-registry.svg','kms':'aws/aws-key-management-service.svg','pod':'kubernetes/pod.svg','svc':'kubernetes/svc.svg','ing':'kubernetes/ing.svg','sa':'kubernetes/sa.svg','netpol':'kubernetes/netpol.svg','user':'kubernetes/user.svg','role':'kubernetes/role.svg','node':'kubernetes/node.svg','secret':'kubernetes/secret.svg'}
class Diagram:
 def __init__(self,title,width,height,transparent=False,cards=True):
  self.transparent=transparent;self.cards=cards
  self.w=width;self.h=height;self.shapes=[];self.edges=[];self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="none" stroke="#315675" stroke-width="1.5"/></marker></defs>'+('' if transparent else '<rect width="100%" height="100%" fill="white"/>')+'<g font-family="Arial, sans-serif">',f'<text x="32" y="39" font-size="23" font-weight="bold" fill="#173c60">{escape(title)}</text>']
 def box(self,id,x,y,w,h,label,color='#148a98',fill='#f0f9fa'):
  self.svg.extend([f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="{color}" stroke-dasharray="7 5" stroke-width="1.5"/>',f'<text x="{x+14}" y="{y+24}" font-size="14" font-weight="bold" fill="{color}">{escape(label)}</text>']);self.shapes.append((id,label,x,y,w,h,f'rounded=0;dashed=1;fillColor={fill};strokeColor={color};verticalAlign=top;align=left;spacing=12;'))
 def node(self,id,x,y,label,icon=None,w=160,h=100):
  if self.cards:self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="white" stroke="#d0dce6"/>')
  text_y=y+39
  if icon:
   p=ICONS/MAP[icon];data=p.read_bytes();b64=base64.b64encode(data).decode()
   self.svg.append(f'<image x="{x+(w-44)/2}" y="{y+9}" width="44" height="44" xlink:href="data:image/svg+xml;base64,{b64}"/>');text_y=y+73
   self.shapes.append((id+'-icon','',x+(w-44)/2,y+9,44,44,'shape=image;image=data:image/svg+xml,'+urllib.parse.quote(data.decode(),safe='')+';'))
  for i,line in enumerate(label.split('\n')):self.svg.append(f'<text x="{x+w/2}" y="{text_y+i*17}" text-anchor="middle" fill="#173c60" font-size="13">{escape(line)}</text>')
  self.shapes.append((id,label,x,y,w,h,('rounded=1;fillColor=#ffffff;strokeColor=#d0dce6;' if self.cards else 'fillColor=none;strokeColor=none;')+'verticalAlign=bottom;spacingBottom=8;'))
 def edge(self,a,b,points,label='',dashed=False):
  path='M'+' L'.join(f'{x},{y}' for x,y in points)
  self.svg.append(f'<path d="{path}" fill="none" stroke="#315675" stroke-width="1.7" marker-end="url(#arrow)"'+(' stroke-dasharray="6 4"' if dashed else '')+'/>')
  if label:
   halo="none" if self.transparent else "white"
   start,end=max(zip(points,points[1:]),key=lambda v:abs(v[1][0]-v[0][0])+abs(v[1][1]-v[0][1]));x,y=(start[0]+end[0])/2,(start[1]+end[1])/2
   anchor="middle" if start[1] == end[1] else "start"
   self.svg.append(f'<text x="{x if start[1] == end[1] else x+12}" y="{y-12 if start[1] == end[1] else y}" text-anchor="{anchor}" font-size="15" fill="#315675" paint-order="stroke" stroke="{halo}" stroke-width="4">{escape(label)}</text>')
  self.edges.append((a,b,points,label,dashed))
 def save(self,name):
  if args.only and name not in args.only:return
  self.svg.append('</g></svg>');(OUT/(name+'.svg')).write_text(''.join(self.svg))
  root=ET.Element('mxfile',host='app.diagrams.net');dia=ET.SubElement(root,'diagram',name=name);model=ET.SubElement(dia,'mxGraphModel',pageWidth=str(self.w),pageHeight=str(self.h),grid='1',gridSize='10',background='none' if self.transparent else '#ffffff'); rr=ET.SubElement(model,'root');ET.SubElement(rr,'mxCell',id='0');ET.SubElement(rr,'mxCell',id='1',parent='0')
  # Containers first, then node cards, then icons, so icons remain visible.
  for id,label,x,y,w,h,style in sorted(self.shapes,key=lambda z:0 if 'dashed=1' in z[-1] else 2 if 'shape=image' in z[-1] else 1):
   c=ET.SubElement(rr,'mxCell',id=id,value=label,style=style,vertex='1',parent='1');ET.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
  bounds={id:(x,y,w,h) for id,label,x,y,w,h,style in self.shapes}
  for i,(a,b,pts,label,dash) in enumerate(self.edges):
   sx,sy,sw,sh=bounds[a];tx,ty,tw,th=bounds[b]
   anchors=f'exitX={(pts[0][0]-sx)/sw};exitY={(pts[0][1]-sy)/sh};exitPerimeter=0;entryX={(pts[-1][0]-tx)/tw};entryY={(pts[-1][1]-ty)/th};entryPerimeter=0;'
   c=ET.SubElement(rr,'mxCell',id=f'edge{i}',value=label,style='edgeStyle=orthogonalEdgeStyle;endArrow=open;fontSize=15;strokeColor=#315675;'+anchors+('dashed=1;' if dash else ''),edge='1',parent='1',source=a,target=b);g=ET.SubElement(c,'mxGeometry',relative='1',attrib={'as':'geometry'});arr=ET.SubElement(g,'Array',attrib={'as':'points'})
   for x,y in pts[1:-1]:ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
  ET.ElementTree(root).write(OUT/(name+'.drawio'),encoding='utf-8',xml_declaration=True)

d=Diagram('High-level architecture · ba luồng, ba loại quyền',1320,620,transparent=True,cards=False)
for id,x,y,label,icon in [('client',35,110,'Người dùng','user'),('edge',255,110,'Điểm vào công khai\nHTTPS / WAF','alb'),('front',475,110,'Frontend\nNginx','pod'),('api',695,110,'Backend\nAPI','pod'),('db',1085,110,'Dữ liệu\nRDS PostgreSQL','rds'),('queue',695,340,'Hàng đợi\nSQS','sqs'),('worker',1085,340,'Xử lý nền\nWorker','pod'),('admin',35,340,'Quản trị cluster\nIAM → EKS access → RBAC','iam')]:d.node(id,x,y,label,icon,w=190 if id=='admin' else 160)
for a,b,p,l in [('client','edge',[(147,141),(303,141)],'①'),('edge','front',[(367,141),(523,141)],'②'),('front','api',[(587,141),(743,141)],'③'),('api','db',[(807,141),(1133,141)],'④ SQL / TLS'),('api','queue',[(775,214),(775,339)],'⑤ SendMessage'),('worker','queue',[(1133,371),(807,371)],'⑥ ReceiveMessage'),('worker','db',[(1165,339),(1165,214)],'⑦ SQL / TLS')]:d.edge(a,b,p,l)
d.box('legend',270,500,970,80,'Network: ai kết nối được?  |  RBAC: ai sửa Kubernetes?  |  IAM: pod gọi AWS API nào?',fill='none')
d.save('high-level')
d=Diagram('AWS architecture · ALB target type IP / private EKS / managed database',1440,1030)
d.box('cloud',180,65,1220,925,'AWS Cloud · us-east-1','#323e4b','#fff')
d.box('vpc',205,145,965,815,'VPC 10.20.0.0/16','#8355c4','#fcfaff')
d.box('public',230,195,910,190,'Public subnets · AZ A: 10.20.0.0/20  |  AZ B: 10.20.16.0/20','#198d9c','#eefafb')
d.box('private',230,410,910,310,'Private application subnets · AZ A: 10.20.32.0/20  |  AZ B: 10.20.48.0/20','#267bb3','#eff6fc')
d.box('cluster',250,455,870,240,'EKS managed nodes · VPC CNI + NetworkPolicy','#327de2','#f9fcff')
d.box('database',230,750,910,180,'Isolated database subnets · 10.20.64.0/24 + 10.20.65.0/24','#4f8c41','#f4fbf0')
for id,x,y,label,icon in [('user',15,240,'Internet client','user'),('alb',290,245,'ALB :443\nIP target → pod :8080','alb'),('nat',900,245,'NAT Gateway\noutbound only','nat'),('front',290,520,'Frontend ×2\nNginx :8080','pod'),('api',550,520,'API ×2\nHTTP :8080','pod'),('worker',880,520,'Worker ×1\nno public listener','pod'),('rds',550,805,'RDS PostgreSQL :5432\nTLS + SQL roles','rds'),('sqs',1200,520,'SQS reports\nHTTPS :443','sqs'),('acm',1200,245,'ACM + WAF\nassociated with ALB','acm'),('control',1200,805,'EKS control plane\nAPI endpoint / IAM / RBAC','eks')]:d.node(id,x,y,label,icon,w=180)
for a,b,p,l,da in [('user','alb',[(195,290),(290,290)],'HTTPS',False),('alb','front',[(380,345),(380,520)],'① target pod IP',False),('front','api',[(470,570),(550,570)],'② ClusterIP Service',False),('api','rds',[(640,620),(640,805)],'③ SQL / TLS',False),('api','sqs',[(730,550),(800,550),(800,435),(1290,435),(1290,520)],'④ SendMessage via NAT',True),('worker','sqs',[(1060,570),(1200,570)],'⑤ long poll via NAT',False),('worker','rds',[(970,620),(970,785),(730,785),(730,850)],'⑥ SQL / TLS',False),('acm','alb',[(1200,290),(1100,290),(1100,175),(380,175),(380,245)],'certificate / Web ACL association',True),('worker','nat',[(1060,540),(1110,540),(1110,390),(990,390),(990,345)],'outbound route',True)]:d.edge(a,b,p,l,da)
d.save('aws-architecture')

def chain(name,title,items,labels=None):
 w=max(1150,230*len(items)+80);d=Diagram(title,w,360)
 for i,(key,label,icon) in enumerate(items):d.node(key,40+i*230,110,label,icon,w=180,h=110)
 for i in range(len(items)-1):d.edge(items[i][0],items[i+1][0],[(220+i*230,165),(270+i*230,165)],labels[i] if labels else '')
 d.save(name)
chain('request-path','Request path · solid arrows = traffic, not configuration',[('client','Client / DNS lookup','user'),('alb','ALB HTTPS :443','alb'),('front','Frontend pod :8080','pod'),('api','API Service → pod :8080','svc'),('rds','RDS TLS :5432','rds')],['① TLS','② target IP','③ /api proxy','④ SQL'])
chain('workload-identity','Workload identity · credential path, separate from application traffic',[('pod','API / Worker pod','pod'),('sa','ServiceAccount','sa'),('agent','Pod Identity Agent','eks'),('iam','Temporary IAM role','iam'),('sqs','One SQS queue','sqs')],['association','credential request','EKS Auth','scoped permission'])
chain('human-access','Management access · this request does not pass through the application ALB',[('user','Operator / kubectl','user'),('iam','AWS IAM identity','iam'),('api','EKS API endpoint','eks'),('rbac','Access entry + RBAC','role'),('pod','Kubernetes resources','pod')],['token','network reachability','authorization','allowed verbs'])
chain('supply-chain','Supply chain · verification must happen before release',[('source','Source + dependencies',None),('build','Build / SBOM / scan','ecr'),('sign','Sign immutable digest','iam'),('registry','ECR image + signature','ecr'),('admission','Verify / admission','pod')],['build','decision gate','publish','deploy'])
d=Diagram('NetworkPolicy · default deny, then allow the exact application flows',1220,580)
for id,x,y,label,icon in [('alb',35,120,'ALB subnets','alb'),('front',285,120,'Frontend\nno AWS IAM role','pod'),('api',535,120,'API :8080','pod'),('db',995,120,'RDS :5432','rds'),('other',285,350,'Untrusted pod','pod'),('dns',535,350,'CoreDNS :53\nTCP + UDP','svc'),('agent',995,350,'Identity Agent :80\n169.254.170.23','iam')]:d.node(id,x,y,label,icon,w=180)
for a,b,p,l in [('alb','front',[(215,170),(285,170)],'ALLOW :8080'),('front','api',[(465,170),(535,170)],'ALLOW :8080'),('api','db',[(715,170),(995,170)],'ALLOW :5432 + SG + SQL'),('front','dns',[(375,220),(375,320),(625,320),(625,350)],'ALLOW DNS'),('api','agent',[(625,220),(625,280),(1085,280),(1085,350)],'ALLOW credentials')]:d.edge(a,b,p,l)
d.box('deny',35,490,1140,55,'DENY: untrusted → API · frontend → RDS · frontend → Internet · API → unrelated private pods','#ba3f4f','#fff5f5');d.save('network-policy')
chain('encryption','Data protection · separate keys and separate responsibilities',[('client','Client → ALB\nACM TLS','acm'),('pod','Pod → RDS\nverify-full TLS','pod'),('db','RDS storage\nAWS-managed key','rds'),('secret','Master password\nSecrets Manager','secret'),('cmk','Demo CMK\nexplicit KMS encrypt/decrypt','kms')])
print('Generated',len(list(OUT.glob('*.svg'))),'SVG diagrams and matching drawio files.')
