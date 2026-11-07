"""AWS network diagram, with shared SVG/draw.io geometry and vector assets."""
from pathlib import Path
import base64
from html import escape
import urllib.parse
import xml.etree.ElementTree as ET
from PIL import ImageFont

ICONS = Path('/home/ubuntu/devops-blog2/src/assets/icons')
NS = '{http://www.w3.org/2000/svg}'

class NetworkDiagram:
    def __init__(self):
        self.frames, self.nodes, self.edges, self.labels = [], [], [], []
        self.font = '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'

    def label(self, key, text, x, y, size=17, color='#233b50', center=True):
        # x/y locate the center or left edge, and the text baseline.
        font = ImageFont.truetype(self.font, size)
        width = round(font.getlength(text) + 12)
        self.labels.append((key, text, x-width/2 if center else x-6, y-size, width, size+8, size, color))

    def frame(self, key, x, y, w, h, text, color, asset=None, fill='none'):
        self.frames.append((key, x, y, w, h, color, fill, asset))
        self.label(key+'-title', text, x+42, y+26, 17, color, center=False)

    def node(self, key, x, y, text, asset):
        self.nodes.append((key, x, y, asset))
        for i, line in enumerate(text.split('\n')):
            self.label(key+'-text-'+str(i), line, x, y+61+i*22)

    def edge(self, key, source, target, points, text='', at=None, dashed=False):
        self.edges.append((key, source, target, points, dashed))
        if text:
            self.label(key+'-label', text, *at, size=17)

    @staticmethod
    def asset(path):
        data = (ICONS/path).read_bytes()
        return 'data:image/svg+xml;base64,'+base64.b64encode(data).decode()

    @staticmethod
    def corner(asset):
        # Extract the original vector corner from an AWS group. Exclude the
        # original frame and foreignObject/PNG text fallback; redraw text live.
        root = ET.parse(ICONS/'aws-architecture-group'/asset).getroot()
        for parent in list(root.iter()):
            for child in list(parent):
                if child.tag in (NS+'switch', NS+'foreignObject', NS+'image'):
                    parent.remove(child)
        paths = list(root.iter(NS+'path'))
        for parent in root.iter():
            if paths[0] in list(parent):
                parent.remove(paths[0]); break
        root.set('viewBox', '0 0 28 28')
        root.set('width', '28'); root.set('height', '28')
        return 'data:image/svg+xml;base64,'+base64.b64encode(ET.tostring(root)).decode()

    def save(self, out):
        out = Path(out)
        svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1840" height="1060" viewBox="0 0 1840 1060" role="img" aria-labelledby="title desc">',
               '<title id="title">Network architecture — Internet đến EKS workloads</title>',
               '<desc id="desc">HTTPS đi qua Internet Gateway đến ALB, HTTP đến frontend và API. API và worker kết nối RDS bằng TLS. Outbound đến SQS qua NAT và Internet Gateway. WAF và ACM được gắn với ALB.</desc>',
               '<defs><marker id="network-arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="none" stroke="#315675" stroke-width="1.5"/></marker></defs>']
        root = ET.Element('mxfile', host='app.diagrams.net')
        diagram = ET.SubElement(root, 'diagram', name='aws-architecture')
        model = ET.SubElement(diagram, 'mxGraphModel', pageWidth='1840', pageHeight='1060', background='none', grid='1', gridSize='10')
        cells = ET.SubElement(model, 'root')
        ET.SubElement(cells, 'mxCell', id='0')
        ET.SubElement(cells, 'mxCell', id='1', parent='0')
        def cell(key, x, y, w, h, style, value=''):
            c = ET.SubElement(cells, 'mxCell', id=key, value=value, style=style, vertex='1', parent='1')
            ET.SubElement(c, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), attrib={'as':'geometry'})
        def image(key, x, y, size, uri):
            svg.append(f'<image id="{key}" x="{x}" y="{y}" width="{size}" height="{size}" preserveAspectRatio="xMidYMid meet" href="{uri}"/>')
            drawio_uri = 'data:image/svg+xml,'+urllib.parse.quote(base64.b64decode(uri.split(',',1)[1]).decode(), safe='')
            cell(key, x, y, size, size, 'shape=image;imageAspect=1;aspect=fixed;image='+drawio_uri+';')
        for key,x,y,w,h,color,fill,asset in self.frames:
            is_dashed = key not in ('cloud', 'ec2-workers')
            dash = ' stroke-dasharray="8 5"' if is_dashed else ''
            svg.append(f'<rect id="{key}" x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{color}" stroke-width="1.5"{dash}/>')
            cell(key,x,y,w,h,f'fillColor={fill};strokeColor={color};dashed={int(is_dashed)};dashPattern=8 5;')
            if asset:
                uri = self.asset(asset) if '/' in asset else self.corner(asset)
                image(key+'-corner',x+1,y+1,28,uri)
            elif key=='cloud':
                image(key+'-corner',x+1,y+1,28,self.asset('aws/group/aws-cloud-logo-32.svg'))
        positions = {key:(x,y) for key,x,y,asset in self.nodes}
        for key,source,target,points,dashed in self.edges:
            path = 'M'+' L'.join(f'{x},{y}' for x,y in points)
            svg.append(f'<path id="{key}" d="{path}" stroke="#315675" stroke-width="2" fill="none" marker-end="url(#network-arrow)"'+(' stroke-dasharray="7 5"' if dashed else '')+'/>')
            sx,sy=positions[source];tx,ty=positions[target]
            anchors=f'exitX={(points[0][0]-sx+30)/60};exitY={(points[0][1]-sy+30)/60};entryX={(points[-1][0]-tx+30)/60};entryY={(points[-1][1]-ty+30)/60};exitPerimeter=0;entryPerimeter=0;'
            c=ET.SubElement(cells,'mxCell',id=key,edge='1',parent='1',source=source,target=target,style='edgeStyle=none;endArrow=open;strokeWidth=2;strokeColor=#315675;labelBackgroundColor=#ffffff;'+anchors+('dashed=1;' if dashed else ''))
            geo=ET.SubElement(c,'mxGeometry',relative='1',attrib={'as':'geometry'})
            array=ET.SubElement(geo,'Array',attrib={'as':'points'})
            for x,y in points[1:-1]:ET.SubElement(array,'mxPoint',x=str(x),y=str(y))
        # Nodes and every text background are above all connectors.
        for key,x,y,asset in self.nodes:
            image(key,x-30,y-30,60,self.asset(asset))
        for key,text,x,y,w,h,size,color in self.labels:
            svg.append(f'<g id="{key}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="white"/><text x="{x+w/2}" y="{y+size}" text-anchor="middle" font-family="Arial, sans-serif" font-size="{size}" fill="{color}">{escape(text)}</text></g>')
            cell(key,x,y,w,h,f'text;html=0;align=center;verticalAlign=top;whiteSpace=wrap;rounded=0;fillColor=#ffffff;labelBackgroundColor=#ffffff;strokeColor=none;fontFamily=Arial;fontSize={size};fontColor={color};spacing=0;',text)
        svg.append('</svg>')
        (out/'aws-architecture.svg').write_text(''.join(svg))
        ET.ElementTree(root).write(out/'aws-architecture.drawio',encoding='utf-8',xml_declaration=True)


def generate(out):
    d=NetworkDiagram()
    # Exact golden ratio applies to the actual Cloud frame, not just the canvas.
    d.frame('cloud',190,30,1618,1000,'AWS Cloud','#526575')
    d.frame('region',215,75,1568,930,'Region · us-east-1','#00a4a6','region-group.svg')
    d.frame('vpc',240,120,1280,855,'VPC · 10.20.0.0/16','#8c4fff','vpc-group.svg')
    d.frame('public',335,205,1160,185,'Public subnets · 2 Availability Zones','#7aa116','public-subnet-group.svg')
    d.frame('private',285,465,1210,300,'Private subnets · 2 AZ','#00a4a6','private-subnet-group.svg')
    d.frame('managed-nodes',310,510,1115,230,'EKS Managed Node Group','#ed7100','aws/group/amazon-eks-cloud.svg')
    d.frame('ec2-workers',335,555,1065,170,'EC2 worker nodes ×2','#d86613','ec2-instance-contents-group.svg')
    d.label('scheduler-note','Vị trí pod minh họa; scheduler phân bố replicas trên các node.',850,755,15)
    d.frame('database',285,790,1210,160,'Database subnets · RDS private / Single-AZ trong lab','#00a4a6','private-subnet-group.svg')
    for args in [
      ('client',80,290,'Người dùng\nInternet','kubernetes/user.svg'),
      ('igw',280,290,'Internet\nGateway','aws/resource/amazon-vpc-internet-gateway.svg'),
      ('alb',600,290,'Application Load Balancer\nHTTPS :443 · IP targets','aws/resource/elastic-load-balancing-application-load-balancer.svg'),
      ('nat',1320,290,'NAT Gateway\nChỉ outbound','aws/resource/amazon-vpc-nat-gateway.svg'),
      ('front',600,625,'Frontend ×2\nNginx · HTTP :8080','kubernetes/pod.svg'),
      ('api',910,625,'API ×2\nService → pod :8080','kubernetes/pod.svg'),
      ('worker',1320,625,'Worker ×1\nXử lý báo cáo','kubernetes/pod.svg'),
      ('db',910,845,'RDS PostgreSQL\nTLS :5432','aws/group/amazon-rds.svg'),
      ('controls',1650,290,'AWS WAF + ACM\nWeb ACL / certificate','aws/group/aws-waf.svg'),
      ('sqs',1650,670,'Amazon SQS\nHàng đợi báo cáo','aws/group/amazon-simple-queue-service.svg'),
    ]:d.node(*args)
    d.edge('internet-ingress','client','igw',[(120,290),(240,290)])
    d.edge('https-ingress','igw','alb',[(320,290),(560,290)],'HTTPS :443',(425,274))
    d.edge('controls-association','controls','alb',[(1610,290),(1555,290),(1555,180),(600,180),(600,250)],'Gắn Web ACL / certificate với ALB',(1080,169),True)
    d.edge('alb-frontend','alb','front',[(600,390),(600,585)],'HTTP :8080 · IP target',(730,432))
    d.edge('frontend-api','front','api',[(640,625),(870,625)],'Proxy /api',(755,609))
    d.edge('api-db','api','db',[(910,725),(910,805)],'SQL / TLS',(973,783))
    d.edge('worker-db','worker','db',[(1320,725),(1320,775),(1070,775),(1070,845),(950,845)],'SQL / TLS',(1190,799))
    d.edge('api-nat','api','nat',[(950,625),(1095,625),(1095,290),(1280,290)],'Gửi yêu cầu · HTTPS',(1117,420))
    d.edge('worker-nat','worker','nat',[(1320,585),(1320,390)],'Poll SQS · HTTPS',(1350,445))
    d.edge('nat-sqs','nat','sqs',[(1360,290),(1450,290),(1450,670),(1610,670)],'Qua IGW · HTTPS :443',(1575,610))
    d.save(out)
