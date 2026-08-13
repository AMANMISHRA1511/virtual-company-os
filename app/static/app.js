const $=s=>document.querySelector(s),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(u,o={}){const r=await fetch(u,{headers:{'Content-Type':'application/json'},...o});if(!r.ok)throw new Error(await r.text());return r.json()}
let roles=[],tasks=[],atts=[],files=[],audits=[],calls=[],scale=1,autoProcessing=false;

const zones={
 Reception:['email'],
 Director:['manager'],
 Engineering:['project_manager','product_manager','developer','code_reviewer','database','devops'],
 QA:['tester','security'],
 DataDesign:['ui_ux','ml_engineer','data_analyst','data_entry','researcher'],
 Growth:['sales','marketing','support','documentation'],
 HR:['hr'],
 Finance:['finance'],
 Operations:['operations'],
 Compliance:['compliance'],
 Server:['automation']
};

function switchTab(id){document.querySelectorAll('.tab,.sidebar nav button').forEach(x=>x.classList.remove('active'));$('#'+id)?.classList.add('active');document.querySelector(`[data-tab="${id}"]`)?.classList.add('active');$('#side').classList.remove('open')}
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>switchTab(b.dataset.tab));
document.querySelectorAll('[data-open]').forEach(b=>b.onclick=()=>switchTab(b.dataset.open));
$('#menu').onclick=()=>$('#side').classList.toggle('open');

function current(r){return tasks.find(t=>t.assigned_role===r.id&&t.status!=='completed')}
function statusClass(t,r){if(!t)return'';if(r.id==='tester')return'testing';return'working'}
function statusText(t,r){if(!t)return'ONLINE';if(r.id==='tester')return'TESTING';return String(t.status||'WORKING').toUpperCase()}

function employeeHTML(r){
 const t=current(r);
 return `<div class="employee ${statusClass(t,r)}" data-agent="${r.id}">
   <span class="ext">${r.extension||''}</span>
   <div class="desk-top"><span class="monitor"></span><span class="person-icon"></span></div>
   <div class="nameplate"><b>${esc(r.name)}</b><small>${esc(r.title)}</small><span class="work-state">${esc(statusText(t,r))}</span></div>
 </div>`;
}

function renderOffice(){
 for(const [zone,ids] of Object.entries(zones)){
   const el=document.querySelector(`[data-zone="${zone}"]`);if(!el)continue;
   el.innerHTML=ids.map(id=>roles.find(r=>r.id===id)).filter(Boolean).map(employeeHTML).join('');
 }
 document.querySelectorAll('[data-agent]').forEach(el=>el.onclick=()=>showAgent(el.dataset.agent));
}

function showAgent(id){
 const r=roles.find(x=>x.id===id);if(!r)return;const t=current(r);
 const related=tasks.filter(x=>x.assigned_role===r.id).slice(0,4);
 $('#drawerBody').innerHTML=`<h2>${esc(r.name)}</h2><p>${esc(r.title)} · Direct line ${esc(r.extension||'')}</p>
 <div class="card"><b>Current status</b><p>${t?`${esc(t.status)} — ${esc(t.title)} (${t.progress||0}%)`:'Available for work'}</p></div>
 <div class="actions"><button id="aTask">Assign Task</button><button class="call" id="aCall">☎ Call</button><button id="aMsg">Message</button><button id="aFile">Files</button></div>
 <h3>Recent work</h3>${related.map(x=>`<div class="taskrow"><b>#${x.id} ${esc(x.title)}</b><br><small>${esc(x.status)}</small></div>`).join('')||'<p>No tasks yet.</p>'}`;
 $('#drawer').classList.remove('hidden');
 $('#aTask').onclick=()=>{$('#drawer').classList.add('hidden');switchTab('tasks');$('#emp').value=r.name};
 $('#aCall').onclick=()=>callEmployee(r);
 $('#aMsg').onclick=()=>{const m=prompt(`Message ${r.name}:`);if(m){$('#chatInput').value=r.name+', '+m;$('#send').click()}};
 $('#aFile').onclick=()=>switchTab('files');
}
$('#close').onclick=()=>$('#drawer').classList.add('hidden');

function callEmployee(r){
 const m=prompt(`Direct call ${r.name} (${r.extension||''}) — instruction:`);
 if(m===null)return;
 api('/api/calls',{method:'POST',body:JSON.stringify({to_agent:r.name,message:m,create_task:!!m})}).then(async o=>{
   alert(o.response+(o.task_id?` Task #${o.task_id} created and will start automatically.`:''));
   await loadAll(); if(o.task_id) await processAssignedQueue();
 });
}

async function loadHealth(){
 try{
  const h=await api('/api/health');
  $('#engineStatus').textContent=h.llm&&h.llm!=='provider-not-configured'?`LLM ${h.llm} active`:'LLM provider pending · local workflow active';
  $('#health').textContent='● Company Online';
 }catch(e){$('#health').textContent='● Offline'}
}

async function loadRoles(){
 roles=await api('/api/roles');$('#rc').textContent=roles.length;$('#sumActive').textContent=roles.length;
 $('#emp').innerHTML='<option value="">Auto route</option>'+roles.map(r=>`<option value="${r.name}">${r.name} — ${r.title} (${r.extension||''})</option>`).join('');
 $('#directory').innerHTML=roles.map(r=>`<div class="person"><b>${esc(r.name)}</b><small>${esc(r.title)}</small><small>Line ${esc(r.extension||'')}</small><button data-call="${r.id}">☎ Call directly</button></div>`).join('');
 document.querySelectorAll('[data-call]').forEach(b=>b.onclick=()=>callEmployee(roles.find(r=>r.id===b.dataset.call)));
 renderOffice();
}

async function loadTasks(){
 [tasks,atts]=await Promise.all([api('/api/tasks'),api('/api/attachments')]);
 const working=tasks.filter(t=>t.status!=='completed').length,completed=tasks.filter(t=>t.status==='completed').length,pending=tasks.filter(t=>t.status==='assigned').length;
 $('#wc').textContent=working;$('#cc').textContent=completed;$('#pc').textContent=pending;$('#sumCompleted').textContent=completed;$('#sumWorking').textContent=working;
 $('#taskList').innerHTML=tasks.map(t=>{const aa=atts.filter(a=>a.task_id===t.id);return `<div class="taskrow">
 <b>#${t.id} ${esc(t.title)}</b> <span class="badge">${esc(t.assigned_name)}</span> <span class="badge">${esc(t.status)}</span>
 <div class="progress"><i style="width:${t.progress||0}%"></i></div><div>${esc(t.description)}</div>
 ${aa.length?`<div class="attachments">${aa.map(a=>`<a href="/api/files/demo-company/file?path=${encodeURIComponent(a.path)}">📎 ${esc(a.original_name)}</a>`).join('')}</div>`:''}
 ${t.result?`<p>${esc(t.result)}</p>`:''}${t.status==='assigned'?`<button data-run="${t.id}">▶ Start now</button>`:''}</div>`}).join('')||'No tasks yet.';
 document.querySelectorAll('[data-run]').forEach(b=>b.onclick=async()=>{b.disabled=true;b.textContent='Working…';await api('/api/tasks/'+b.dataset.run+'/run',{method:'POST'});await loadAll();await processAssignedQueue()});
 renderOffice();
}

async function processAssignedQueue(){
 if(autoProcessing)return;autoProcessing=true;
 try{
   for(let round=0;round<6;round++){
     const fresh=await api('/api/tasks');
     const next=fresh.find(t=>t.status==='assigned');
     if(!next)break;
     await api('/api/tasks/'+next.id+'/run',{method:'POST'});
   }
 }catch(e){console.error('auto queue',e)}
 autoProcessing=false;await loadAll();
}

async function loadFiles(){
 files=await api('/api/files/demo-company');const count=files.filter(f=>f.type==='file').length;$('#fc').textContent=count;$('#sumFiles').textContent=count;
 $('#fileTree').innerHTML=files.map(f=>`<div class="file"><span>${f.type==='dir'?'📁':'📄'} ${esc(f.path)}</span>${f.type==='file'?`<a href="/api/files/demo-company/file?path=${encodeURIComponent(f.path)}">Download</a>`:''}</div>`).join('');
 const h=await api('/api/handoffs');$('#handoffs').innerHTML=h.map(x=>`<div class="handoff">📄 ${esc(x.path)} · <b>${esc(x.from)}</b> → <b>${esc(x.to)}</b><br><small>${esc(x.purpose)}</small></div>`).join('');
}

async function loadCalls(){
 calls=await api('/api/calls');$('#calls').innerHTML=calls.map(x=>`<div class="callrow"><b>${esc(x.to)} · ${esc(x.extension)}</b><br>${esc(x.message||'Connected')}</div>`).join('');
 $('#liveCalls').innerHTML=calls.slice(0,4).map(x=>`<div class="callrow"><b>${esc(x.to)}</b> · ${esc(x.extension)}<br><small>${esc(x.message||'Connected')}</small></div>`).join('')||'<div class="callrow">No recent calls</div>';
}

async function loadAudit(){
 audits=await api('/api/audit');$('#audit').innerHTML=audits.map(x=>`<div class="auditrow"><b>${esc(x.actor)}</b> · ${esc(x.action)}<br><small>${esc(x.details)}</small></div>`).join('');
 $('#mini').innerHTML=audits.slice(0,8).map(x=>`<div class="auditrow"><b>${esc(x.actor)}</b><br>${esc(x.details||x.action)}</div>`).join('')||'<div class="auditrow">No recent activity</div>';
}

$('#uploads').onchange=()=>$('#picked').innerHTML=[...$('#uploads').files].map(f=>`<span class="badge">📎 ${esc(f.name)}</span>`).join('');

$('#assign').onclick=async()=>{
 const title=$('#title').value.trim(),description=$('#desc').value.trim(),emp=$('#emp').value,fs=[...$('#uploads').files];
 if(!title||!description)return alert('Title and description required');
 let created;
 if(fs.length){
   const fd=new FormData();fd.append('title',title);fd.append('description',description);fd.append('assigned_to',emp);fs.forEach(f=>fd.append('files',f));
   const r=await fetch('/api/tasks/with-files',{method:'POST',body:fd});if(!r.ok)throw new Error(await r.text());created=await r.json();
 }else created=await api('/api/tasks',{method:'POST',body:JSON.stringify({title,description,assigned_to:emp||null})});
 $('#title').value='';$('#desc').value='';$('#uploads').value='';$('#picked').innerHTML='';await loadAll();
 if($('#autoRun').checked)await processAssignedQueue();
 switchTab('office');
};

$('#send').onclick=async()=>{
 const m=$('#chatInput').value.trim();if(!m)return;
 $('#chat').innerHTML+=`<div class="msg you"><b>You</b><br>${esc(m)}</div>`;
 const o=await api('/api/chat',{method:'POST',body:JSON.stringify({message:m})});
 const src=(o.sources||[]).slice(0,3).map(s=>`<span class="rag">RAG: ${esc(s.path)} · ${(s.score||0).toFixed(2)}</span>`).join('');
 $('#chat').innerHTML+=`<div class="msg"><b>${esc(o.agent)} · ${esc(o.mode||'')}</b><br>${esc(o.reply)}${src}</div>`;
 $('#chatInput').value='';$('#chat').scrollTop=$('#chat').scrollHeight;
};
$('#chatInput').onkeydown=e=>{if(e.key==='Enter')$('#send').click()};

$('#globalSearch').oninput=e=>{
 const q=e.target.value.trim().toLowerCase();
 document.querySelectorAll('.employee').forEach(el=>{const id=el.dataset.agent,r=roles.find(x=>x.id===id);el.style.opacity=!q||`${r.name} ${r.title}`.toLowerCase().includes(q)?'1':'.22'});
};

function applyZoom(){document.getElementById('officeMap').style.transform=`scale(${scale})`;$('#zoomLabel').textContent=Math.round(scale*100)+'%'}
$('#zoomIn').onclick=()=>{scale=Math.min(1.5,scale+.1);applyZoom()};$('#zoomOut').onclick=()=>{scale=Math.max(.65,scale-.1);applyZoom()};$('#zoomReset').onclick=()=>{scale=1;applyZoom()};

async function loadAll(){
 try{await Promise.all([loadHealth(),loadRoles(),loadTasks(),loadFiles(),loadCalls(),loadAudit()])}catch(e){console.error(e);$('#health').textContent='● Error'}
}
loadAll();setInterval(loadAll,8000);