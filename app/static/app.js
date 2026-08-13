const POS={"manager": [135, 315], "project_manager": [280, 315], "developer": [450, 315], "code_reviewer": [605, 315], "product_manager": [120, 455], "database": [440, 455], "tester": [830, 340], "security": [970, 340], "hr": [105, 600], "finance": [325, 600], "operations": [530, 600], "compliance": [740, 600], "devops": [610, 455], "ui_ux": [250, 455], "ml_engineer": [340, 455], "automation": [880, 635], "data_analyst": [250, 475], "data_entry": [330, 475], "researcher": [180, 475], "email": [150, 115], "sales": [860, 130], "marketing": [980, 130], "support": [995, 475], "documentation": [670, 600]};
const $=s=>document.querySelector(s),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(u,o={}){const r=await fetch(u,{headers:{'Content-Type':'application/json'},...o});if(!r.ok)throw new Error(await r.text());return r.json()}
let roles=[],tasks=[],atts=[],files=[],audits=[],calls=[],handoffs=[],scale=1,processing=false;

function tab(id){document.querySelectorAll('.tab,.sidebar nav button').forEach(x=>x.classList.remove('active'));$('#'+id)?.classList.add('active');document.querySelector(`[data-tab="${id}"]`)?.classList.add('active');$('#sidebar').classList.remove('open')}
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>tab(b.dataset.tab));
document.querySelectorAll('[data-open]').forEach(b=>b.onclick=()=>tab(b.dataset.open));
$('#menu').onclick=()=>$('#sidebar').classList.toggle('open');

function current(r){return tasks.find(t=>t.assigned_role===r.id&&t.status!=='completed')}
function fallbackPos(i){const cols=6;return [120+(i%cols)*160,210+Math.floor(i/cols)*135]}
function renderHotspots(){
 const el=$('#hotspots');
 el.innerHTML=roles.map((r,i)=>{const p=POS[r.id]||fallbackPos(i),t=current(r),cls=t?(r.id==='tester'?'testing':'working'):'',state=t?(r.id==='tester'?'TESTING':String(t.status||'WORKING').toUpperCase()):'ONLINE';return `<div class="employee-hotspot ${cls}" data-agent="${r.id}" style="left:${p[0]}px;top:${p[1]}px"><span class="ext">${esc(r.extension||'')}</span><div class="hit">${esc(r.name[0])}</div><div class="plate"><b>${esc(r.name)}</b><small>${esc(r.title)}</small><span class="state">${esc(state)}</span></div></div>`}).join('');
 document.querySelectorAll('[data-agent]').forEach(x=>x.onclick=()=>showEmployee(x.dataset.agent));
 renderTransfers();
}
function renderTransfers(){
 const layer=$('#transferLayer');layer.innerHTML='';
 handoffs.slice(0,3).forEach(h=>{const from=roles.find(r=>r.name===h.from),to=roles.find(r=>r.name===h.to);if(!from||!to)return;const a=POS[from.id],b=POS[to.id];if(!a||!b)return;const dx=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dx,dy),ang=Math.atan2(dy,dx)*180/Math.PI;layer.innerHTML+=`<div class="transfer" style="left:${a[0]}px;top:${a[1]}px;width:${len}px;transform:rotate(${ang}deg)"></div>`});
}
function showEmployee(id){
 const r=roles.find(x=>x.id===id);if(!r)return;const t=current(r),recent=tasks.filter(x=>x.assigned_role===r.id).slice(0,5);
 $('#drawerBody').innerHTML=`<h2>${esc(r.name)}</h2><p>${esc(r.title)} · Direct line ${esc(r.extension||'')}</p><div class="card"><b>Status</b><p>${t?`${esc(t.status)} — ${esc(t.title)} (${t.progress||0}%)`:'Available'}</p></div><div class="drawer-actions"><button id="dTask">Assign Task</button><button class="call" id="dCall">☎ Call</button><button id="dMsg">Message</button><button id="dFiles">Files</button></div><h3>Recent Work</h3>${recent.map(x=>`<div class="taskrow"><b>#${x.id} ${esc(x.title)}</b><br><small>${esc(x.status)}</small></div>`).join('')||'<p>No tasks yet.</p>'}`;
 $('#drawer').classList.remove('hidden');
 $('#dTask').onclick=()=>{$('#drawer').classList.add('hidden');tab('tasks');$('#employeeSelect').value=r.name};
 $('#dCall').onclick=()=>callEmployee(r);
 $('#dMsg').onclick=()=>{const m=prompt(`Message ${r.name}:`);if(m){tab('assistant');$('#bigChatInput').value=r.name+', '+m;sendChat()}};
 $('#dFiles').onclick=()=>tab('files');
}
$('#drawerClose').onclick=()=>$('#drawer').classList.add('hidden');

function callEmployee(r){
 const m=prompt(`Direct call ${r.name} (${r.extension||''}) — instruction:`);
 if(m===null)return;
 api('/api/calls',{method:'POST',body:JSON.stringify({to_agent:r.name,message:m,create_task:!!m})}).then(async o=>{alert(o.response+(o.task_id?` Task #${o.task_id} created.`:''));await loadAll();if(o.task_id)await processQueue()});
}

async function loadHealth(){
 try{const h=await api('/api/health');$('#engineStatus').textContent=(h.llm&&h.llm!=='provider-not-configured')?`LLM ${h.llm} active`:'Local workflow active · LLM pending';$('#online').textContent='● Company Online'}catch(e){$('#online').textContent='● Offline'}
}
async function loadRoles(){
 roles=await api('/api/roles');$('#mEmployees').textContent=roles.length;$('#sActive').textContent=roles.length;
 $('#employeeSelect').innerHTML='<option value="">Auto route</option>'+roles.map(r=>`<option value="${r.name}">${esc(r.name)} — ${esc(r.title)} (${esc(r.extension||'')})</option>`).join('');
 $('#directory').innerHTML=roles.map(r=>`<div class="person"><b>${esc(r.name)}</b><small>${esc(r.title)}</small><small>Line ${esc(r.extension||'')}</small><button data-call="${r.id}">☎ Call directly</button></div>`).join('');
 document.querySelectorAll('[data-call]').forEach(b=>b.onclick=()=>callEmployee(roles.find(r=>r.id===b.dataset.call)));
 renderHotspots();
}
async function loadTasks(){
 [tasks,atts]=await Promise.all([api('/api/tasks'),api('/api/attachments')]);
 const working=tasks.filter(t=>t.status!=='completed').length,done=tasks.filter(t=>t.status==='completed').length,pending=tasks.filter(t=>t.status==='assigned').length;
 $('#mWorking').textContent=working;$('#mDone').textContent=done;$('#mPending').textContent=pending;$('#sDone').textContent=done;$('#sWorking').textContent=working;
 $('#taskList').innerHTML=tasks.map(t=>{const aa=atts.filter(a=>a.task_id===t.id);return `<div class="taskrow"><b>#${t.id} ${esc(t.title)}</b> <span class="badge">${esc(t.assigned_name)}</span> <span class="badge">${esc(t.status)}</span><div class="progress"><i style="width:${t.progress||0}%"></i></div><div>${esc(t.description)}</div>${aa.length?`<div class="attachments">${aa.map(a=>`<a href="/api/files/demo-company/file?path=${encodeURIComponent(a.path)}">📎 ${esc(a.original_name)}</a>`).join('')}</div>`:''}${t.result?`<p>${esc(t.result)}</p>`:''}${t.status==='assigned'?`<button data-run="${t.id}">▶ Start now</button>`:''}</div>`}).join('')||'No tasks.';
 document.querySelectorAll('[data-run]').forEach(b=>b.onclick=async()=>{await api('/api/tasks/'+b.dataset.run+'/run',{method:'POST'});await loadAll();await processQueue()});
 renderHotspots();
}
async function processQueue(){
 if(processing)return;processing=true;
 try{for(let i=0;i<8;i++){const q=await api('/api/tasks');const n=q.find(t=>t.status==='assigned');if(!n)break;await api('/api/tasks/'+n.id+'/run',{method:'POST'})}}catch(e){console.error(e)}
 processing=false;await loadAll();
}
async function loadFiles(){
 files=await api('/api/files/demo-company');const n=files.filter(f=>f.type==='file').length;$('#mFiles').textContent=n;$('#sFiles').textContent=n;
 $('#fileTree').innerHTML=files.map(f=>`<div class="file"><span>${f.type==='dir'?'📁':'📄'} ${esc(f.path)}</span>${f.type==='file'?`<a href="/api/files/demo-company/file?path=${encodeURIComponent(f.path)}">Download</a>`:''}</div>`).join('');
 handoffs=await api('/api/handoffs');$('#handoffs').innerHTML=handoffs.map(h=>`<div class="handoff">📄 ${esc(h.path)} · <b>${esc(h.from)}</b> → <b>${esc(h.to)}</b><br><small>${esc(h.purpose)}</small></div>`).join('');renderTransfers();
}
async function loadCalls(){
 calls=await api('/api/calls');$('#callHistory').innerHTML=calls.map(c=>`<div class="callrow"><b>${esc(c.to)} · ${esc(c.extension)}</b><br>${esc(c.message||'Connected')}</div>`).join('');
 $('#recentCalls').innerHTML=calls.slice(0,4).map(c=>`<div class="callrow"><b>${esc(c.to)}</b> · ${esc(c.extension)}<br><small>${esc(c.message||'Connected')}</small></div>`).join('')||'<div class="callrow">No recent calls</div>';
}
async function loadActivity(){
 audits=await api('/api/audit');$('#activityList').innerHTML=audits.map(a=>`<div class="activity-row"><b>${esc(a.actor)}</b> · ${esc(a.action)}<br><small>${esc(a.details)}</small></div>`).join('');
 $('#recentActivity').innerHTML=audits.slice(0,7).map(a=>`<div class="activity-row"><b>${esc(a.actor)}</b><br><small>${esc(a.details||a.action)}</small></div>`).join('')||'<div class="activity-row">No recent activity</div>';
}
$('#taskFiles').onchange=()=>$('#pickedFiles').innerHTML=[...$('#taskFiles').files].map(f=>`<span class="badge">📎 ${esc(f.name)}</span>`).join('');
$('#assignTask').onclick=async()=>{const title=$('#taskTitle').value.trim(),description=$('#taskDescription').value.trim(),emp=$('#employeeSelect').value,fs=[...$('#taskFiles').files];if(!title||!description)return alert('Title and description required');if(fs.length){const fd=new FormData();fd.append('title',title);fd.append('description',description);fd.append('assigned_to',emp);fs.forEach(f=>fd.append('files',f));const r=await fetch('/api/tasks/with-files',{method:'POST',body:fd});if(!r.ok)throw new Error(await r.text())}else await api('/api/tasks',{method:'POST',body:JSON.stringify({title,description,assigned_to:emp||null})});$('#taskTitle').value='';$('#taskDescription').value='';$('#taskFiles').value='';$('#pickedFiles').innerHTML='';await loadAll();if($('#autoRun').checked)await processQueue();tab('office')};

async function sendChat(){
 const input=$('#bigChatInput'),m=input.value.trim();if(!m)return;$('#bigChat').innerHTML+=`<div class="chat-msg you"><b>You</b><br>${esc(m)}</div>`;const o=await api('/api/chat',{method:'POST',body:JSON.stringify({message:m})});const src=(o.sources||[]).slice(0,3).map(s=>`<span class="rag">RAG: ${esc(s.path)} · ${(s.score||0).toFixed(2)}</span>`).join('');$('#bigChat').innerHTML+=`<div class="chat-msg"><b>${esc(o.agent)} · ${esc(o.mode||'')}</b><br>${esc(o.reply)}${src}</div>`;input.value='';$('#bigChat').scrollTop=$('#bigChat').scrollHeight}
$('#bigSend').onclick=sendChat;$('#bigChatInput').onkeydown=e=>{if(e.key==='Enter')sendChat()};
$('#globalSearch').oninput=e=>{const q=e.target.value.toLowerCase().trim();document.querySelectorAll('.employee-hotspot').forEach(el=>{const r=roles.find(x=>x.id===el.dataset.agent);el.style.opacity=!q||`${r.name} ${r.title}`.toLowerCase().includes(q)?'1':'.2'})};

function zoom(){document.getElementById('officeStage').style.transform=`scale(${scale})`;$('#zoomPct').textContent=Math.round(scale*100)+'%'}
$('#zoomIn').onclick=()=>{scale=Math.min(1.5,scale+.1);zoom()};$('#zoomOut').onclick=()=>{scale=Math.max(.65,scale-.1);zoom()};$('#zoomReset').onclick=()=>{scale=1;zoom()};

async function loadAll(){try{await Promise.all([loadHealth(),loadRoles(),loadTasks(),loadFiles(),loadCalls(),loadActivity()])}catch(e){console.error(e);$('#online').textContent='● Error'}}
loadAll();setInterval(loadAll,8000);