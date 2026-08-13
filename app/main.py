from datetime import datetime
from pathlib import Path
import re
from fastapi import FastAPI,Depends,HTTPException,Response,UploadFile,File,Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import Base,engine,get_db
from .models import Task,AuditLog,FileChange,Handoff,CallSession,TaskAttachment
from .schemas import TaskCreate,ApprovalRequest,FileWrite,HandoffCreate,ChatRequest,CallCreate
from .services.roles import ROLES,BY_ROLE,BY_NAME,BY_EXTENSION
from .services.classifier import router
from .services.agents import execute
from .services.files import tree,safe_file,snapshot,zip_project,project_root
Base.metadata.create_all(bind=engine)
app=FastAPI(title='Virtual Company OS',version='4.2.0');app.mount('/static',StaticFiles(directory='app/static'),name='static')
def log(db,task_id,actor,action,details=''):
 db.add(AuditLog(task_id=task_id,actor=actor,action=action,details=details));db.commit()
def ser(t): return {'id':t.id,'title':t.title,'description':t.description,'assigned_role':t.assigned_role,'assigned_name':t.assigned_name,'status':t.status,'result':t.result,'requires_approval':t.requires_approval,'approved':t.approved,'created_at':t.created_at.isoformat()}
@app.head('/')
def root_head(): return Response(status_code=200)
@app.get('/')
def home(): return FileResponse('app/static/index.html')
@app.get('/api/health')
def health(): return {'status':'ok','roles':len(ROLES),'version':'4.2.0'}
@app.get('/api/roles')
def roles(): return ROLES
def resolve_employee(value:str|None,title:str='',description:str=''):
 if value:
  low=value.strip().lower()
  if low in BY_NAME: return BY_NAME[low]
  if value.strip() in BY_EXTENSION: return BY_EXTENSION[value.strip()]
  if low in BY_ROLE: return BY_ROLE[low]
  for r in ROLES:
   if low==r['name'].lower() or low==r['id'].lower(): return r
 role=router.classify((title+' '+description).strip())
 return BY_ROLE[role]

@app.post('/api/tasks')
def create_task(x:TaskCreate,db:Session=Depends(get_db)):
 meta=resolve_employee(x.assigned_to,x.title,x.description)
 t=Task(title=x.title,description=x.description,assigned_role=meta['id'],assigned_name=meta['name'])
 db.add(t);db.commit();db.refresh(t)
 actor='You' if x.assigned_to else 'Aarav'
 action='task_direct_assigned' if x.assigned_to else 'task_routed'
 log(db,t.id,actor,action,f'Assigned to {meta["name"]} ({meta["title"]})')
 return ser(t)
@app.post('/api/tasks/{tid}/run')
def run_task(tid:int,db:Session=Depends(get_db)):
 t=db.get(Task,tid)
 if not t: raise HTTPException(404,'Task not found')
 t.status='running';db.commit();log(db,t.id,t.assigned_name,'work_started',t.title)
 attachments=db.query(TaskAttachment).filter(TaskAttachment.task_id==tid).all()
 attachment_paths=[safe_file(a.project,a.path) for a in attachments]
 path,summary,approval=execute(t,attachment_paths)
 t.result=f'{summary} File: {path}';t.requires_approval=approval;t.status='waiting_approval' if approval and not t.approved else 'completed';t.updated_at=datetime.utcnow();db.commit()
 version=db.query(FileChange).filter(FileChange.project=='demo-company',FileChange.path==path).count()+1
 db.add(FileChange(project='demo-company',path=path,version=version,actor=t.assigned_name,action='created',task_id=t.id,note=summary));db.commit()
 log(db,t.id,t.assigned_name,'work_completed',t.result);return ser(t)
@app.get('/api/tasks')
def tasks(db:Session=Depends(get_db)): return [ser(t) for t in db.query(Task).order_by(Task.id.desc()).all()]
@app.post('/api/tasks/{tid}/approval')
def approval(tid:int,x:ApprovalRequest,db:Session=Depends(get_db)):
 t=db.get(Task,tid)
 if not t: raise HTTPException(404,'Task not found')
 t.approved=x.approved
 if x.approved and t.status=='waiting_approval': t.status='completed';t.result+=' Human approval granted; external action remains simulated in this demo.'
 db.commit();log(db,t.id,'Human','approval_changed',str(x.approved));return ser(t)
@app.post('/api/chat')
def chat(x:ChatRequest):
 low=x.message.lower();target=None
 for name,r in BY_NAME.items():
  if name in low: target=r;break
 if not target: target=BY_ROLE['manager']
 return {'agent':target['name'],'title':target['title'],'reply':f'{target["name"]}: Aapka message mila — “{x.message}”. Is request ko {target["title"]} workflow me handle kiya jayega.'}
@app.get('/api/files/{project}')
def files(project:str): return tree(project)
@app.get('/api/files/{project}/download')
def download_project(project:str): return FileResponse(zip_project(project),filename=f'{project}-latest.zip',media_type='application/zip')
@app.get('/api/files/{project}/file')
def download_file(project:str,path:str):
 p=safe_file(project,path)
 if not p.exists() or not p.is_file(): raise HTTPException(404,'File not found')
 return FileResponse(p,filename=p.name)
@app.post('/api/files/write')
def write_file(x:FileWrite,db:Session=Depends(get_db)):
 p=safe_file(x.project,x.path);p.parent.mkdir(parents=True,exist_ok=True);old=p.exists();version=db.query(FileChange).filter(FileChange.project==x.project,FileChange.path==x.path).count()+1
 if old: snapshot(x.project,x.path,version-1)
 p.write_text(x.content,encoding='utf-8');db.add(FileChange(project=x.project,path=x.path,version=version,actor=x.actor,action='updated' if old else 'created',task_id=x.task_id,note=x.note));db.commit();log(db,x.task_id,x.actor,'file_changed',f'{x.path} v{version}');return {'ok':True,'path':x.path,'version':version}
@app.get('/api/file-changes')
def changes(db:Session=Depends(get_db)):
 rows=db.query(FileChange).order_by(FileChange.id.desc()).limit(200).all();return [{'id':r.id,'path':r.path,'version':r.version,'actor':r.actor,'action':r.action,'task_id':r.task_id,'note':r.note,'created_at':r.created_at.isoformat()} for r in rows]
@app.post('/api/handoffs')
def handoff(x:HandoffCreate,db:Session=Depends(get_db)):
 p=safe_file(x.project,x.path)
 if not p.exists(): raise HTTPException(404,'File not found')
 h=Handoff(project=x.project,path=x.path,from_agent=x.from_agent,to_agent=x.to_agent,purpose=x.purpose);db.add(h);db.commit();db.refresh(h);log(db,0,x.from_agent,'file_handoff',f'{x.path} → {x.to_agent}: {x.purpose}');return {'id':h.id,'status':'shared','path':x.path,'from':x.from_agent,'to':x.to_agent}
@app.get('/api/handoffs')
def handoffs(db:Session=Depends(get_db)):
 rs=db.query(Handoff).order_by(Handoff.id.desc()).limit(100).all();return [{'id':r.id,'path':r.path,'from':r.from_agent,'to':r.to_agent,'purpose':r.purpose,'status':r.status,'created_at':r.created_at.isoformat()} for r in rs]
@app.get('/api/audit')
def audit(db:Session=Depends(get_db)):
 rs=db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all();return [{'id':r.id,'task_id':r.task_id,'actor':r.actor,'action':r.action,'details':r.details,'created_at':r.created_at.isoformat()} for r in rs]

def _call_reply(agent, message):
    role=agent['id']
    base={
      'manager':'Main request ko analyze karke sahi team ko assign kar raha hoon.',
      'developer':'Main requirement samajh gaya. Main implementation plan aur code work start kar raha hoon.',
      'tester':'Main build ko test cases, regression aur bug checks ke saath verify karunga.',
      'ui_ux':'Main interface ko user flow, responsive layout aur usability ke hisaab se design karungi.',
      'database':'Main schema, queries aur data integrity check kar raha hoon.',
      'devops':'Main deployment, environment aur release workflow check kar raha hoon.',
      'hr':'Main candidate ya HR workflow ko handle kar rahi hoon.',
      'email':'Main communication draft aur delivery workflow prepare kar rahi hoon.',
      'security':'Main access, secrets aur common security risks review kar raha hoon.',
    }.get(role, f"Main {agent['title']} workflow me is request par kaam kar raha hoon.")
    if message:
        return f"{agent['name']}: {base} Aapne kaha: {message}"
    return f"{agent['name']}: Hello, main {agent['title']} hoon. Bataiye kya kaam karna hai."

@app.post('/api/calls')
def create_call(x:CallCreate,db:Session=Depends(get_db)):
    target=None
    low=x.to_agent.lower().strip()
    if low in BY_NAME: target=BY_NAME[low]
    elif x.to_agent in BY_EXTENSION: target=BY_EXTENSION[x.to_agent]
    else:
        for r in ROLES:
            if r['name'].lower()==low or r['extension']==x.to_agent:
                target=r;break
    if not target: raise HTTPException(404,'Employee not found')
    response=_call_reply(target,x.message)
    c=CallSession(from_agent=x.from_agent,to_agent=target['name'],extension=target['extension'],channel=x.channel,message=x.message,response=response,status='completed')
    db.add(c);db.commit();db.refresh(c)
    task_id=None
    if x.create_task and x.message.strip():
        t=Task(title=f"Call request for {target['name']}",description=x.message,assigned_role=target['id'],assigned_name=target['name'],status='queued')
        db.add(t);db.commit();db.refresh(t);task_id=t.id
        log(db,t.id,x.from_agent,'task_created_from_call',f"Direct call → {target['name']} ext {target['extension']}")
    log(db,task_id or 0,x.from_agent,'internal_call',f"Called {target['name']} ext {target['extension']}")
    return {'id':c.id,'to':target['name'],'title':target['title'],'extension':target['extension'],'response':response,'task_id':task_id,'channel':x.channel}

@app.get('/api/calls')
def list_calls(db:Session=Depends(get_db)):
    rs=db.query(CallSession).order_by(CallSession.id.desc()).limit(100).all()
    return [{'id':r.id,'from':r.from_agent,'to':r.to_agent,'extension':r.extension,'channel':r.channel,'message':r.message,'response':r.response,'status':r.status,'created_at':r.created_at.isoformat()} for r in rs]

@app.post('/api/internal-call/{from_name}/{to_name}')
def internal_call(from_name:str,to_name:str,x:ChatRequest,db:Session=Depends(get_db)):
    f=BY_NAME.get(from_name.lower());t=BY_NAME.get(to_name.lower())
    if not f or not t: raise HTTPException(404,'Employee not found')
    response=_call_reply(t,x.message)
    c=CallSession(from_agent=f['name'],to_agent=t['name'],extension=t['extension'],channel='employee_to_employee',message=x.message,response=response,status='completed')
    db.add(c);db.commit();db.refresh(c)
    log(db,0,f['name'],'employee_call',f"{f['name']} → {t['name']}: {x.message}")
    return {'id':c.id,'from':f['name'],'to':t['name'],'extension':t['extension'],'response':response}


def _safe_upload_name(name:str)->str:
 name=Path(name or 'file').name
 name=re.sub(r'[^A-Za-z0-9._() -]+','_',name).strip()
 return name[:180] or 'file'

@app.post('/api/tasks/assign-with-files')
async def assign_with_files(
 title:str=Form(...),
 description:str=Form(...),
 assigned_to:str=Form(''),
 uploaded_by:str=Form('You'),
 save_to_library:bool=Form(True),
 files:list[UploadFile]=File(default=[]),
 db:Session=Depends(get_db)
):
 meta=resolve_employee(assigned_to or None,title,description)
 t=Task(title=title,description=description,assigned_role=meta['id'],assigned_name=meta['name'])
 db.add(t);db.commit();db.refresh(t)
 saved=[]
 for upload in files:
  if not upload.filename: continue
  raw=await upload.read()
  if len(raw)>25*1024*1024:
   raise HTTPException(413,f'{upload.filename}: maximum 25 MB per file')
  name=_safe_upload_name(upload.filename)
  rel=f'task_uploads/task_{t.id}/{name}'
  target=safe_file('demo-company',rel)
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(raw)
  a=TaskAttachment(task_id=t.id,project='demo-company',path=rel,original_name=upload.filename,mime_type=upload.content_type or 'application/octet-stream',size_bytes=len(raw),uploaded_by=uploaded_by,assigned_to=meta['name'])
  db.add(a)
  version=db.query(FileChange).filter(FileChange.project=='demo-company',FileChange.path==rel).count()+1
  db.add(FileChange(project='demo-company',path=rel,version=version,actor=uploaded_by,action='uploaded',task_id=t.id,note=f'Attached to task #{t.id} for {meta["name"]}'))
  saved.append({'name':upload.filename,'path':rel,'size_bytes':len(raw)})
 db.commit()
 log(db,t.id,uploaded_by,'task_assigned_with_files',f'Assigned to {meta["name"]}; {len(saved)} attachment(s)')
 return {'task':ser(t),'attachments':saved}

@app.get('/api/attachments')
def attachments(db:Session=Depends(get_db)):
 rs=db.query(TaskAttachment).order_by(TaskAttachment.id.desc()).limit(500).all()
 return [{'id':r.id,'task_id':r.task_id,'project':r.project,'path':r.path,'original_name':r.original_name,'mime_type':r.mime_type,'size_bytes':r.size_bytes,'uploaded_by':r.uploaded_by,'assigned_to':r.assigned_to,'created_at':r.created_at.isoformat()} for r in rs]

@app.get('/api/tasks/{tid}/attachments')
def task_attachments(tid:int,db:Session=Depends(get_db)):
 rs=db.query(TaskAttachment).filter(TaskAttachment.task_id==tid).order_by(TaskAttachment.id.asc()).all()
 return [{'id':r.id,'task_id':r.task_id,'path':r.path,'original_name':r.original_name,'mime_type':r.mime_type,'size_bytes':r.size_bytes,'uploaded_by':r.uploaded_by,'assigned_to':r.assigned_to} for r in rs]

@app.get('/api/attachments/{attachment_id}/download')
def download_attachment(attachment_id:int,db:Session=Depends(get_db)):
 r=db.get(TaskAttachment,attachment_id)
 if not r: raise HTTPException(404,'Attachment not found')
 p=safe_file(r.project,r.path)
 if not p.exists(): raise HTTPException(404,'Attachment file not found')
 return FileResponse(p,filename=r.original_name,media_type=r.mime_type)
