from datetime import datetime
from pathlib import Path
import re
from fastapi import FastAPI, Depends, HTTPException, Response, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import Task, AuditLog, FileChange, Handoff, CallSession, TaskAttachment
from .schemas import TaskCreate, HandoffCreate, ChatRequest, CallCreate
from .services.roles import ROLES, BY_ROLE, BY_NAME, BY_EXTENSION
from .services.classifier import router
from .services.files import tree, safe_file, zip_project
from .services.rag import build_index, retrieve
from .services.nlp import analyze as nlp_analyze
from .services.workflow import create_role_artifact

Base.metadata.create_all(bind=engine)
app=FastAPI(title='Virtual Company OS',version='10.0.0')
app.mount('/static',StaticFiles(directory='app/static'),name='static')

def log(db, task_id, actor, action, details=''):
    db.add(AuditLog(task_id=task_id,actor=actor,action=action,details=details)); db.commit()

def resolve_employee(value, title='', description=''):
    if value:
        low=value.strip().lower()
        if low in BY_NAME: return BY_NAME[low]
        if value.strip() in BY_EXTENSION: return BY_EXTENSION[value.strip()]
        if low in BY_ROLE: return BY_ROLE[low]
    return BY_ROLE[router.classify(title+' '+description)]

def ser(t):
    return {'id':t.id,'title':t.title,'description':t.description,'assigned_role':t.assigned_role,'assigned_name':t.assigned_name,'status':t.status,'progress':getattr(t,'progress',0),'result':t.result,'created_at':t.created_at.isoformat()}

@app.head('/')
def root_head(): return Response(status_code=200)
@app.get('/')
def home(): return FileResponse('app/static/index.html')
@app.get('/api/health')
def health(): return {'status':'ok','version':'10.0.0','engine':'RAG+NLP+agent-workflow','llm':'provider-not-configured'}
@app.get('/api/roles')
def roles(): return ROLES

@app.post('/api/tasks')
def create_task(x:TaskCreate, db:Session=Depends(get_db)):
    meta=resolve_employee(getattr(x,'assigned_to',None),x.title,x.description)
    t=Task(title=x.title,description=x.description,assigned_role=meta['id'],assigned_name=meta['name'],status='assigned',progress=0)
    db.add(t);db.commit();db.refresh(t);log(db,t.id,'You','task_assigned',f"{meta['name']} ({meta.get('extension','')})")
    return ser(t)

@app.post('/api/tasks/with-files')
async def create_with_files(title:str=Form(...),description:str=Form(...),assigned_to:str=Form(''),files:list[UploadFile]=File(default=[]),db:Session=Depends(get_db)):
    meta=resolve_employee(assigned_to or None,title,description)
    t=Task(title=title,description=description,assigned_role=meta['id'],assigned_name=meta['name'],status='assigned',progress=0)
    db.add(t);db.commit();db.refresh(t)
    saved=[]
    for f in files:
        if not f.filename: continue
        raw=await f.read()
        if len(raw)>25*1024*1024: raise HTTPException(413,'Maximum 25 MB per file')
        name=re.sub(r'[^A-Za-z0-9._() -]+','_',Path(f.filename).name)[:180]
        rel=f'task_uploads/task_{t.id}/{name}'
        p=safe_file('demo-company',rel);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        a=TaskAttachment(task_id=t.id,project='demo-company',path=rel,original_name=f.filename,mime_type=f.content_type or 'application/octet-stream',size_bytes=len(raw),uploaded_by='You',assigned_to=meta['name'])
        db.add(a);db.add(FileChange(project='demo-company',path=rel,version=1,actor='You',action='uploaded',task_id=t.id,note=f'Attachment for {meta["name"]}'));saved.append({'name':f.filename,'path':rel})
    db.commit();build_index();log(db,t.id,'You','task_with_files',f"{meta['name']}; {len(saved)} files")
    return {'task':ser(t),'attachments':saved}

@app.get('/api/tasks')
def tasks(db:Session=Depends(get_db)): return [ser(x) for x in db.query(Task).order_by(Task.id.desc()).all()]

@app.post('/api/tasks/{tid}/run')
def run_task(tid:int, db:Session=Depends(get_db)):
    t=db.get(Task,tid)
    if not t: raise HTTPException(404,'Task not found')
    t.status='working';t.progress=35;db.commit();log(db,t.id,t.assigned_name,'working','Agent started task')
    ats=db.query(TaskAttachment).filter(TaskAttachment.task_id==tid).all()
    hits=retrieve(t.description,5)
    rel,filename=create_role_artifact(t,ats,hits)
    t.status='completed';t.progress=100;t.result=f'{t.assigned_name} created {filename}';t.updated_at=datetime.utcnow()
    db.add(FileChange(project='demo-company',path=rel,version=1,actor=t.assigned_name,action='created',task_id=t.id,note=t.result));db.commit();log(db,t.id,t.assigned_name,'completed',t.result)
    # deterministic inter-agent workflow
    if t.assigned_role=='developer':
        h=Handoff(project='demo-company',path=rel,from_agent=t.assigned_name,to_agent='Neha',purpose='Automatic QA review');db.add(h)
        qa=Task(title=f'QA review for task #{t.id}',description=f'Test developer output {rel} from {t.assigned_name}. Original: {t.description}',assigned_role='tester',assigned_name='Neha',status='assigned',progress=0)
        db.add(qa);db.commit();db.refresh(qa);log(db,qa.id,'Arjun','agent_message',f'Neha, please test {rel}. QA task #{qa.id} created.')
    elif t.assigned_role=='tester':
        h=Handoff(project='demo-company',path=rel,from_agent=t.assigned_name,to_agent='Arjun',purpose='QA result returned to developer');db.add(h);db.commit();log(db,t.id,'Neha','agent_message',f'Arjun, QA report ready: {rel}')
    build_index()
    return ser(t)

@app.get('/api/attachments')
def attachments(db:Session=Depends(get_db)):
    rs=db.query(TaskAttachment).order_by(TaskAttachment.id.desc()).all();return [{'id':a.id,'task_id':a.task_id,'path':a.path,'original_name':a.original_name,'size_bytes':a.size_bytes} for a in rs]
@app.get('/api/files/{project}')
def files(project:str): return tree(project)
@app.get('/api/files/{project}/file')
def file_download(project:str,path:str):
    p=safe_file(project,path)
    if not p.exists() or not p.is_file(): raise HTTPException(404,'File not found')
    return FileResponse(p,filename=p.name)
@app.get('/api/files/{project}/download')
def project_zip(project:str): return FileResponse(zip_project(project),filename=f'{project}-latest.zip',media_type='application/zip')
@app.get('/api/file-changes')
def changes(db:Session=Depends(get_db)):
    rs=db.query(FileChange).order_by(FileChange.id.desc()).limit(300).all();return [{'id':r.id,'path':r.path,'actor':r.actor,'action':r.action,'task_id':r.task_id,'note':r.note,'created_at':r.created_at.isoformat()} for r in rs]
@app.get('/api/handoffs')
def handoffs(db:Session=Depends(get_db)):
    rs=db.query(Handoff).order_by(Handoff.id.desc()).limit(200).all();return [{'id':r.id,'path':r.path,'from':r.from_agent,'to':r.to_agent,'purpose':r.purpose,'status':r.status} for r in rs]
@app.post('/api/handoffs')
def handoff(x:HandoffCreate,db:Session=Depends(get_db)):
    p=safe_file(x.project,x.path)
    if not p.exists(): raise HTTPException(404,'File not found')
    h=Handoff(project=x.project,path=x.path,from_agent=x.from_agent,to_agent=x.to_agent,purpose=x.purpose);db.add(h);db.commit();log(db,0,x.from_agent,'handoff',f'{x.path} → {x.to_agent}');return {'id':h.id,'status':'shared'}

@app.post('/api/chat')
def chat(x:ChatRequest):
    low=x.message.lower();target=None
    for name,r in BY_NAME.items():
        if name in low: target=r;break
    target=target or BY_ROLE['manager'];nlp=nlp_analyze(x.message);hits=retrieve(x.message,4)
    src=', '.join(h['path'] for h in hits[:3]) or 'no indexed project source'
    return {'agent':target['name'],'reply':f"{target['name']}: NLP={nlp.get('intent',nlp.get('role'))}; RAG={src}. Assign a task to execute my supported workflow.",'mode':'RAG+NLP','sources':hits,'nlp':nlp}

@app.post('/api/calls')
def call(x:CallCreate,db:Session=Depends(get_db)):
    r=resolve_employee(x.to_agent);task_id=None
    if x.create_task and x.message.strip():
        t=Task(title=f'Call task for {r["name"]}',description=x.message,assigned_role=r['id'],assigned_name=r['name'],status='assigned',progress=0);db.add(t);db.commit();db.refresh(t);task_id=t.id
    response=f"{r['name']}: Direct internal line {r.get('extension','')} connected. Instruction recorded."
    c=CallSession(from_agent='You',to_agent=r['name'],extension=r.get('extension',''),channel='internal',message=x.message,response=response,status='completed');db.add(c);db.commit();log(db,task_id or 0,'You','call',f"{r['name']} {r.get('extension','')}");return {'to':r['name'],'extension':r.get('extension',''),'response':response,'task_id':task_id}
@app.get('/api/calls')
def calls(db:Session=Depends(get_db)):
    rs=db.query(CallSession).order_by(CallSession.id.desc()).limit(100).all();return [{'id':r.id,'from':r.from_agent,'to':r.to_agent,'extension':r.extension,'message':r.message,'response':r.response} for r in rs]
@app.get('/api/audit')
def audit(db:Session=Depends(get_db)):
    rs=db.query(AuditLog).order_by(AuditLog.id.desc()).limit(300).all();return [{'id':r.id,'task_id':r.task_id,'actor':r.actor,'action':r.action,'details':r.details,'created_at':r.created_at.isoformat()} for r in rs]
@app.post('/api/rag/reindex')
def reindex(): return build_index()
@app.get('/api/rag/search')
def rag_search(q:str): return retrieve(q,6)
@app.get('/api/nlp')
def nlp(q:str): return nlp_analyze(q)
