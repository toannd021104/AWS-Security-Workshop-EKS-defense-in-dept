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
MAP={'source':'aws/source-code.svg','secretsmanager':'aws/aws-secrets-manager.svg','alb':'aws/elastic-load-balancing-application-load-balancer.svg','eks':'aws/amazon-elastic-kubernetes-service.svg','rds':'aws/amazon-rds.svg','sqs':'aws/amazon-simple-queue-service.svg','nat':'aws/amazon-vpc-nat-gateway.svg','igw':'aws/amazon-vpc-internet-gateway.svg','iam':'aws/aws-identity-and-access-management.svg','acm':'aws/aws-certificate-manager.svg','waf':'aws/aws-waf.svg','ecr':'aws/amazon-elastic-container-registry.svg','kms':'aws/aws-key-management-service.svg','pod':'kubernetes/pod.svg','svc':'kubernetes/svc.svg','ing':'kubernetes/ing.svg','sa':'kubernetes/sa.svg','netpol':'kubernetes/netpol.svg','user':'kubernetes/user.svg','role':'kubernetes/role.svg','node':'kubernetes/node.svg','secret':'kubernetes/secret.svg'}
class Diagram:
 def __init__(self,title,width,height,transparent=False,cards=True):
  self.transparent=transparent;self.cards=cards
  self.w=width;self.h=height;self.shapes=[];self.edges=[];self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="none" stroke="#315675" stroke-width="1.5"/></marker></defs>'+('' if transparent else '<rect width="100%" height="100%" fill="white"/>')+'<g font-family="Arial, sans-serif">',f'<text x="32" y="39" font-size="23" font-weight="bold" fill="#173c60">{escape(title)}</text>' if title else '']
 def box(self,id,x,y,w,h,label,color='#148a98',fill='#f0f9fa'):
  self.svg.extend([f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="{color}" stroke-dasharray="7 5" stroke-width="1.5"/>',f'<text x="{x+14}" y="{y+24}" font-size="14" font-weight="bold" fill="{color}">{escape(label)}</text>']);self.shapes.append((id,label,x,y,w,h,f'rounded=0;dashed=1;fillColor={fill};strokeColor={color};verticalAlign=top;align=left;spacing=12;'))
 def node(self,id,x,y,label,icon=None,w=160,h=100,icon_size=44,font_size=13):
  if self.cards:self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="white" stroke="#d0dce6"/>')
  text_y=y+39
  if icon:
   p=ICONS/MAP[icon];data=p.read_bytes();b64=base64.b64encode(data).decode()
   self.svg.append(f'<image x="{x+(w-icon_size)/2}" y="{y+9}" width="{icon_size}" height="{icon_size}" xlink:href="data:image/svg+xml;base64,{b64}"/>');text_y=y+icon_size+29
   self.shapes.append((id+'-icon','',x+(w-icon_size)/2,y+9,icon_size,icon_size,'shape=image;image=data:image/svg+xml,'+urllib.parse.quote(data.decode(),safe='')+';'))
  for i,line in enumerate(label.split('\n')):self.svg.append(f'<text x="{x+w/2}" y="{text_y+i*(font_size+4)}" text-anchor="middle" fill="#173c60" font-size="{font_size}">{escape(line)}</text>')
  self.shapes.append((id,label,x,y,w,h,('rounded=1;fillColor=#ffffff;strokeColor=#d0dce6;' if self.cards else 'fillColor=none;strokeColor=none;')+f'fontSize={font_size};verticalAlign=bottom;spacingBottom=8;'))
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

# Keep this overview focused on application traffic; detailed controls live in
# their own diagrams and lessons. No visible title, cards, or legend.
d=Diagram('',1220,390,transparent=True,cards=False)
for id,x,y,label,icon in [
 ('client',10,55,'Người dùng','user'),
 ('edge',220,55,'ALB + WAF\nĐiểm vào ứng dụng','alb'),
 ('front',430,55,'Frontend\nNginx','pod'),
 ('api',650,55,'API\nXử lý nghiệp vụ','pod'),
 ('db',1010,55,'RDS PostgreSQL\nDữ liệu','rds'),
 ('queue',650,260,'Amazon SQS\nHàng đợi','sqs'),
 ('worker',1010,260,'Worker\nTạo báo cáo','pod'),
]:d.node(id,x,y,label,icon,h=110,icon_size=56,font_size=15)
for a,b,points,label in [
 ('client','edge',[(128,92),(262,92)],'HTTPS'),
 ('edge','front',[(338,92),(472,92)],'HTTP'),
 ('front','api',[(548,92),(692,92)],'HTTP'),
 ('api','db',[(768,92),(1052,92)],'SQL / TLS'),
 ('api','queue',[(730,176),(730,259)],'Gửi yêu cầu'),
 ('worker','queue',[(1052,297),(768,297)],'Nhận yêu cầu'),
 ('worker','db',[(1090,259),(1090,176)],'SQL / TLS'),
]:d.edge(a,b,points,label)
d.save('high-level')
# Detailed network layout: dashed containers represent network boundaries.
d=Diagram('',1440,1120,transparent=True,cards=False)
d.box('cloud',180,20,1235,1080,'AWS Cloud · us-east-1','#526575','none')
d.box('vpc',205,70,950,1000,'VPC · 10.20.0.0/16','#8355c4','none')
d.box('public',230,120,900,205,'Public subnets · 2 Availability Zones','#198d9c','none')
d.box('private',230,365,900,405,'Private application subnets · 2 Availability Zones','#267bb3','none')
d.box('cluster',250,410,860,335,'Amazon EKS · managed nodes / VPC CNI','#327de2','none')
d.box('database',230,815,900,225,'Database subnets · RDS không có public access','#4f8c41','none')
for id,x,y,label,icon in [
 ('user',0,175,'Người dùng','user'),('alb',280,175,'ALB :443\nIP targets','alb'),
 ('nat',920,175,'NAT Gateway\nChỉ outbound','nat'),
 ('front',280,470,'Frontend ×2\nNginx :8080','pod'),('api',560,470,'API ×2\nHTTP :8080','pod'),
 ('worker',920,470,'Worker ×1\nTạo báo cáo','pod'),('rds',560,880,'RDS PostgreSQL\nTLS :5432','rds'),
 ('sqs',1205,470,'Amazon SQS\nHTTPS :443','sqs'),('waf',1205,175,'AWS WAF + ACM\nWeb ACL / certificate','waf')
]:d.node(id,x,y,label,icon,h=115,icon_size=56,font_size=15)
for a,b,points,label,dash in [
 ('user','alb',[(118,212),(322,212)],'HTTPS',False),
 ('waf','alb',[(1247,212),(1175,212),(1175,350),(435,350),(435,212),(398,212)],'Gắn Web ACL / certificate với ALB',True),
 ('alb','front',[(360,296),(360,469)],'',False),
 ('front','api',[(398,507),(602,507)],'Service :8080',False),
 ('api','rds',[(640,590),(640,879)],'SQL / TLS',False),
 ('worker','rds',[(1000,590),(1000,857),(760,857),(760,917),(678,917)],'SQL / TLS',False),
 ('api','sqs',[(678,507),(780,507),(780,690),(1185,690),(1185,507),(1247,507)],'Gửi yêu cầu · HTTPS qua NAT',True),
 ('worker','sqs',[(1038,507),(1247,507)],'Nhận qua NAT',False),
 ('worker','nat',[(1000,469),(1000,296)],'Default route',True),
]:d.edge(a,b,points,label,dash)
d.save('aws-architecture')

def chain(name,items,labels):
 d=Diagram('',len(items)*250,225,transparent=True,cards=False)
 for i,(key,label,icon) in enumerate(items):d.node(key,15+i*250,65,label,icon,h=115,icon_size=56,font_size=15)
 for i in range(len(items)-1):d.edge(items[i][0],items[i+1][0],[(133+i*250,102),(307+i*250,102)],labels[i])
 d.save(name)
chain('request-path',[
 ('client','Người dùng\nDNS → địa chỉ ALB','user'),('alb','ALB\nKết thúc TLS','alb'),
 ('front','Frontend pod\nNginx :8080','pod'),('api','API Service → pod\nHTTP :8080','svc'),
 ('rds','RDS PostgreSQL\nTLS :5432','rds')],['HTTPS :443','HTTP · IP target','Proxy /api','SQL / TLS'])

# Workload credentials: ServiceAccount association is configuration, not traffic.
d=Diagram('',1250,480,transparent=True,cards=False)
for id,x,y,label,icon in [
 ('pod',15,65,'API / Worker pod\nAWS SDK','pod'),('agent',385,65,'Pod Identity Agent\nCredentials endpoint','eks'),
 ('auth',755,65,'EKS Auth\nTemporary credentials','eks'),('sqs',15,335,'Amazon SQS\nQueue của workload','sqs'),
 ('sa',385,335,'ServiceAccount\nNamespace + tên SA','sa'),('role',755,335,'IAM role\nQuyền trên queue','iam')
]:d.node(id,x,y,label,icon,h=115,icon_size=56,font_size=15)
d.edge('pod','agent',[(133,102),(427,102)],'Yêu cầu credentials')
d.edge('agent','auth',[(503,102),(797,102)],'EKS Auth API')
d.edge('auth','pod',[(835,186),(835,235),(95,235),(95,186)],'Trả temporary credentials')
d.edge('pod','sqs',[(57,186),(57,334)],'HTTPS ký SigV4')
d.edge('sa','role',[(503,372),(797,372)],'Pod Identity association',True)
d.edge('auth','role',[(873,102),(1095,102),(1095,334),(873,334)],'Assume role',True)
d.save('workload-identity')
chain('human-access',[
 ('user','Người quản trị\nkubectl','user'),('iam','AWS IAM identity\nToken xác thực','iam'),
 ('api','EKS API endpoint\nKiểm tra identity','eks'),('rbac','Access entry + RBAC\nKiểm tra quyền','role'),
 ('pod','Kubernetes resources\nPod / Deployment','pod')],['aws eks get-token','Gửi request','Ánh xạ / cấp quyền','Cho phép thao tác'])
chain('supply-chain',[
 ('source','Source code\nDependencies','source'),('build','Build image\nSBOM + scan','ecr'),
 ('sign','Ký image digest\nSau khi đạt gate','iam'),('registry','Amazon ECR\nImage + signature','ecr'),
 ('admission','Admission policy\nKiểm tra trước chạy','pod')],['Build','Đánh giá kết quả','Push digest','Verify signature'])

d=Diagram('',1250,525,transparent=True,cards=False)
for id,x,y,label,icon in [
 ('alb',15,65,'ALB','alb'),('front',285,65,'Frontend\nNginx :8080','pod'),
 ('api',555,65,'API\nHTTP :8080','pod'),('db',1035,65,'RDS PostgreSQL\nTLS :5432','rds'),
 ('other',555,335,'Pod không tin cậy\nKhông được gọi API','pod'),
 ('dns',285,335,'CoreDNS\nTCP / UDP :53','svc'),
 ('agent',1035,335,'Pod Identity Agent\n169.254.170.23 :80','iam')
]:d.node(id,x,y,label,icon,h=115,icon_size=56,font_size=15)
for a,b,points,label,dash in [
 ('alb','front',[(133,102),(327,102)],'ALLOW :8080',False),
 ('front','api',[(403,102),(597,102)],'ALLOW :8080',False),
 ('api','db',[(673,102),(1077,102)],'ALLOW :5432 · SG + SQL roles',False),
 ('front','dns',[(365,186),(365,334)],'ALLOW DNS',False),
 ('api','agent',[(673,139),(860,139),(860,290),(1115,290),(1115,334)],'ALLOW credentials',False),
 ('other','api',[(635,334),(635,186)],'DENY',True),
]:d.edge(a,b,points,label,dash)
d.save('network-policy')

# Independent protection boundaries, deliberately not drawn as a request chain.
d=Diagram('',1250,425,transparent=True,cards=False)
for id,x,y,label,icon in [
 ('client',15,50,'Client → ALB\nHTTPS · ACM certificate','acm'),
 ('pod',435,50,'Pod → RDS\nTLS · verify-full','pod'),
 ('db',855,50,'RDS storage\nEncryption at rest','rds'),
 ('secret',225,270,'Master password\nAWS Secrets Manager','secretsmanager'),
 ('cmk',645,270,'KMS customer managed key\nBài thực hành encrypt / decrypt','kms')
]:d.node(id,x,y,label,icon,w=300,h=115,icon_size=56,font_size=15)
d.save('encryption')
print('Generated',len(list(OUT.glob('*.svg'))),'SVG diagrams and matching drawio files.')
