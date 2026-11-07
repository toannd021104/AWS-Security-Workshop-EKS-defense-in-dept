#!/usr/bin/env python3
import pathlib,zipfile
r=pathlib.Path(__file__).resolve().parents[1];out=r/'workshop/static/downloads';out.mkdir(parents=True,exist_ok=True)
files=[r/'README.md',r/'.gitignore']
for folder,extensions in [('app',{'.py','.txt','.html',''}),('scripts',{'.py','.sh'}),('k8s',{'.yaml','.pub'}),('infrastructure/terraform',{'.tf','.json','.example','.hcl'})]:
 for f in (r/folder).iterdir():
  if f.is_file() and f.suffix in extensions and f.name!='terraform.tfvars':files.append(f)
with zipfile.ZipFile(out/'eks-defense-in-depth-lab.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
 for f in sorted(files):z.write(f,f.relative_to(r))
print('Packaged',len(files),'source files; no state, credentials or signing private key.')
