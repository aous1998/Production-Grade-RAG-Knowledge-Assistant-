// =============================================================================
// static/js/app.js: browser logic for the chat page (templates/index.html)
// -----------------------------------------------------------------------------
// - Sends questions to POST /api/chat and shows the answer, sources and the
//   agent's step-by-step trace.
// - Handles the "Add Company Document" upload dialog (POST /api/ingest).
// =============================================================================

// References to page elements defined in templates/index.html.
const chat = document.getElementById('chat');             // message list
const form = document.getElementById('chatForm');         // question form
const question = document.getElementById('question');     // text input
const trace = document.getElementById('trace');           // decision-path panel
const sourceUsed = document.getElementById('sourceUsed'); // "source used" badge

// Escape HTML special characters so text from the server or user can never
// inject HTML/JavaScript into the page (protection against XSS).
function escapeHtml(s=''){return s.replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
// Escape, then keep line breaks visible.
function formatText(s=''){return escapeHtml(s).replace(/\n/g,'<br>');}
// Append one chat bubble. role = 'user' or 'assistant'. Assistant bubbles can
// show the source used and a list of citations (web ones become links).
function addMessage(role, text, source='', citations=[]){
  const wrap=document.createElement('div'); wrap.className=`message ${role}`;
  const citeHtml=citations.length?`<div class="citations"><strong>Sources</strong><br>${citations.map(c=>c.url?`<a href="${escapeHtml(c.url)}" target="_blank" rel="noopener">${escapeHtml(c.title)}</a>`:escapeHtml(c.title)).join('<br>')}</div>`:'';
  wrap.innerHTML=`<div class="avatar">AI</div><div class="bubble">${formatText(text)}${source?`<div class="answer-source">Source: ${escapeHtml(source)}</div>`:''}${citeHtml}</div>`;
  chat.appendChild(wrap); chat.scrollTop=chat.scrollHeight;  // scroll to newest message
}
// Show the agent's trace, e.g. ["Router → KB", "KB evidence grade → GOOD", ...].
function renderTrace(items=[]){trace.innerHTML=items.length?items.map(x=>`<div class="trace-item">${escapeHtml(x)}</div>`).join(''):'<div class="empty">No trace.</div>';}
// Send one question to the backend and display the result.
async function askAgent(q){
  // Show the question immediately and lock the button while the agent runs.
  addMessage('user',q); question.value=''; renderTrace(['Running LangGraph workflow...']); sourceUsed.textContent='Running';
  const btn=form.querySelector('button'); btn.disabled=true;
  try{
    const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});
    const data=await res.json(); if(!res.ok) throw new Error(data.detail||'Request failed');  // server error -> show its message
    addMessage('assistant',data.answer,data.source_used,data.citations||[]); renderTrace(data.trace||[]); sourceUsed.textContent=data.source_used;
  }catch(e){addMessage('assistant',`Error: ${e.message}`); renderTrace(['Request failed']); sourceUsed.textContent='Error';}
  finally{btn.disabled=false;}
}
// Submit with Enter or the Send button (preventDefault stops a page reload).
form.addEventListener('submit',e=>{e.preventDefault(); const q=question.value.trim(); if(q) askAgent(q);});
// The example-question buttons send their own text as the question.
document.querySelectorAll('.example').forEach(b=>b.addEventListener('click',()=>askAgent(b.textContent.trim())));

// ---- Document upload dialog --------------------------------------------------
const modal=document.getElementById('uploadModal');
document.getElementById('openUpload').onclick=()=>modal.classList.remove('hidden');
document.getElementById('closeUpload').onclick=()=>modal.classList.add('hidden');
// Upload the chosen file with the admin key in the X-Admin-Key header.
// The backend saves it, chunks it, embeds it and adds it to Pinecone.
document.getElementById('uploadBtn').onclick=async()=>{
  const file=document.getElementById('fileInput').files[0]; const key=document.getElementById('adminKey').value; const status=document.getElementById('uploadStatus');
  if(!file){status.textContent='Choose a file first.'; return;}
  status.textContent='Indexing document...'; const fd=new FormData(); fd.append('file',file);
  try{const r=await fetch('/api/ingest',{method:'POST',headers:{'X-Admin-Key':key},body:fd}); const d=await r.json(); if(!r.ok) throw new Error(d.detail||'Upload failed'); status.textContent=`Indexed ${d.file}: ${d.chunks} chunks.`;}catch(e){status.textContent=`Error: ${e.message}`;}
};
