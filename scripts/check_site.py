#!/usr/bin/env python3
"""Check built Hugo HTML, image/download links, and accidental sensitive artifacts."""
import argparse,pathlib,re,sys,urllib.parse,xml.etree.ElementTree as ET
from html.parser import HTMLParser
R=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--site',type=pathlib.Path,default=R/'.local/site');a=p.parse_args();site=a.site.resolve()
xml=ET.parse(site/'sitemap.xml');loc=next(x.text for x in xml.iter() if x.tag.endswith('loc'));u=urllib.parse.urlsplit(loc)
# Hugo sitemap can begin with a nested page; use base URL from home canonical URLs in index.json if needed.
all_urls=[x.text for x in xml.iter() if x.tag.endswith('loc')]
base_path=min((urllib.parse.urlsplit(x).path for x in all_urls),key=len).rstrip('/')+'/'
errors=[];checked=0
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=set()
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if 'id' in attrs:self.ids.add(attrs['id'])
  for k in ['href','src']:
   if k in attrs and tag in ['a','img','script','link']:self.links.append((tag,attrs[k]))
parsed={}
for f in site.rglob('*.html'):
 h=Links();h.feed(f.read_text());parsed[f]=h
for f,h in parsed.items():
 for tag,link in h.links:
  v=urllib.parse.urlsplit(link)
  if v.scheme in ['mailto','data','javascript','tel'] or (v.netloc and v.netloc!=u.netloc):continue
  path=urllib.parse.unquote(v.path)
  if path.startswith('/'):
   if base_path!='/' and path.startswith(base_path):path=path[len(base_path):]
   target=site/path.lstrip('/')
  else:target=f.parent/path if path else f
  if target.is_dir():target=target/'index.html'
  checked+=1
  if not target.exists():errors.append(f'{f.relative_to(site)} → missing {link}')
  elif tag=='a' and v.fragment and target.suffix=='.html' and v.fragment not in ['', 'top']:
   if target not in parsed:continue
   # Theme-only '#' controls and dynamically-created history anchors are excluded.
   if v.fragment not in parsed[target].ids and not link.startswith('#'):errors.append(f'{f.relative_to(site)} → missing anchor {link}')
for f in site.rglob('*'):
 if not f.is_file():continue
 rel=f.relative_to(site)
 if any(x in rel.parts for x in ['.local','.terraform','.git','__pycache__']) or f.name in ['terraform.tfvars','cosign.key','kubeconfig','console-session.json'] or '.tfstate' in f.name or f.suffix=='.tfplan':errors.append('Sensitive artifact: '+str(rel))
 if f.suffix in ['.html','.json','.py','.sh','.tf','.yaml','.toml']:
  t=f.read_text(errors='ignore')
  if re.search(r'(?:AKIA|ASIA)[A-Z0-9]{16}',t):errors.append('Possible real AWS access key: '+str(rel))
print(f'{len(parsed)} HTML pages, {checked} local references checked, {len(errors)} errors')
for e in errors[:40]:print(e)
sys.exit(bool(errors))
