from pathlib import Path
import shutil, zipfile, re
ROOT=Path('workspace/projects'); ROOT.mkdir(parents=True,exist_ok=True)
def safe_part(v): return re.sub(r'[^a-zA-Z0-9_.-]+','-',v.strip())[:100] or 'project'
def project_root(project):
 p=ROOT/safe_part(project)/'current';p.mkdir(parents=True,exist_ok=True);return p
def safe_file(project,path):
 base=project_root(project).resolve();target=(base/path).resolve()
 if base!=target and base not in target.parents: raise ValueError('Unsafe path')
 return target
def tree(project):
 base=project_root(project);out=[]
 for p in sorted(base.rglob('*')):
  out.append({'path':str(p.relative_to(base)),'type':'dir' if p.is_dir() else 'file','size':p.stat().st_size if p.is_file() else 0})
 return out
def snapshot(project,path,version):
 src=safe_file(project,path)
 if not src.exists() or not src.is_file(): return None
 dst=ROOT/safe_part(project)/'versions'/f'v{version}'/path;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);return str(dst)
def zip_project(project):
 base=project_root(project);out=Path('workspace')/f'{safe_part(project)}-latest.zip'
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for p in base.rglob('*'):
   if p.is_file(): z.write(p,p.relative_to(base))
 return out
