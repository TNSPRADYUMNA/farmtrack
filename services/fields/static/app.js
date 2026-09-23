const $ = s => document.querySelector(s);
let fields = [], activities = [];
const escapeHTML = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
function notice(message, error=false) { $('#notice').textContent=message; $('#notice').className='notice'+(error?' error':''); }
async function api(path, options={}) {
  const controller=new AbortController(); const timer=setTimeout(()=>controller.abort(),10000);
  try { const response=await fetch(path,{...options,signal:controller.signal,headers:{'Content-Type':'application/json'}});
    const data=await response.json(); if(!response.ok) throw Error(typeof data.detail==='string'?data.detail:'Please check the entered values.'); return data;
  } catch(error) { if(error.name==='AbortError') throw Error('The request timed out. Refresh before trying again.'); throw error; }
  finally { clearTimeout(timer); }
}
function render() {
  $('#field-count').textContent=fields.length;
  $('#area-total').textContent=fields.reduce((sum,f)=>sum+f.area_hectares,0).toLocaleString(undefined,{maximumFractionDigits:2});
  $('#pending-count').textContent=activities.filter(a=>a.status==='pending').length;
  $('#done-count').textContent=activities.filter(a=>a.status==='completed').length;
  $('#field-list').innerHTML=fields.length?fields.map(f=>`<article class="field-card"><div class="landscape" aria-hidden="true"></div><div class="field-body"><h3>${escapeHTML(f.name)}</h3><div class="field-meta"><span class="crop-tag">${escapeHTML(f.crop)}</span><span>${escapeHTML(f.area_hectares)} ha</span></div></div></article>`).join(''):'<div class="empty">Your next season starts here. Add your first field.</div>';
  const selected=$('#field-filter').value;
  const options=fields.map(f=>`<option value="${f.id}">${escapeHTML(f.name)}</option>`).join('');
  $('#field-filter').innerHTML='<option value="">All fields</option>'+options;
  $('#field-filter').value=selected; $('#activity-field').innerHTML=options;
  renderActivities();
}
function renderActivities() {
  const fieldId=$('#field-filter').value,status=$('#status-filter').value;
  const filtered=activities.filter(a=>(!fieldId||a.field_id===fieldId)&&(!status||a.status===status));
  $('#activity-list').innerHTML=filtered.length?filtered.map(a=>{
    const field=fields.find(f=>f.id===a.field_id); const icon={watering:'◉',fertilizing:'♧',harvesting:'✳'}[a.kind];
    return `<article class="task"><div class="task-icon" aria-hidden="true">${icon}</div><div class="task-info"><strong>${escapeHTML(a.kind[0].toUpperCase()+a.kind.slice(1))} · ${escapeHTML(field?field.name:'Unknown field')}</strong><p>${escapeHTML(a.notes||'No additional notes')}</p></div><span class="task-date">Due ${escapeHTML(a.due_date)}</span>${a.status==='completed'?'<span class="status">✓ Completed</span>':`<button class="secondary" data-complete="${a.id}">Mark complete</button>`}</article>`;
  }).join(''):'<div class="empty">No activities here yet. Schedule a task to keep your farm moving.</div>';
}
async function refresh() { const results=await Promise.all([api('/api/fields'),api('/api/activities')]); [fields,activities]=results; render(); }
$('#add-field').onclick=()=>$('#field-dialog').showModal();
$('#add-activity').onclick=()=>{if(!fields.length){notice('Add a field before scheduling an activity.');return;} $('#activity-dialog').showModal();};
for(const b of document.querySelectorAll('[data-close]')) b.onclick=()=>document.getElementById(b.dataset.close).close();
for(const name of ['field','activity']) $('#'+name+'-form').onsubmit=async event=>{
  event.preventDefault(); const form=event.target,button=form.querySelector('[type=submit]'); button.disabled=true;
  try { const payload=Object.fromEntries(new FormData(form)); if(name==='field') payload.area_hectares=Number(payload.area_hectares);
    await api('/api/'+(name==='field'?'fields':'activities'),{method:'POST',body:JSON.stringify(payload)});
    $('#'+name+'-dialog').close(); form.reset(); notice(name==='field'?'Field added. Ready to grow.':'Activity scheduled.'); await refresh();
  } catch(error) { notice(error.message,true); $('#'+name+'-dialog').close(); } finally {button.disabled=false;}
};
$('#activity-list').onclick=async event=>{const button=event.target.closest('[data-complete]');if(!button)return;button.disabled=true;
  try {await api('/api/activities/'+button.dataset.complete,{method:'PATCH',body:JSON.stringify({status:'completed'})});await refresh();notice('Activity completed. Good work!');}
  catch(error){notice(error.message,true);button.disabled=false;}
};
$('#field-filter').onchange=renderActivities;$('#status-filter').onchange=renderActivities;
$('#refresh').onclick=()=>refresh().then(()=>notice('Farm updated.')).catch(e=>notice(e.message,true));
refresh().catch(error=>notice('Could not load your farm. '+error.message,true));
