const OCCS = ["AI Engineer","Backend Developer","Cloud Engineer","Cybersecurity Analyst","Data Analyst","Data Engineer","Data Scientist","Database Administrator","DevOps Engineer","Frontend Developer","Full Stack Developer","Machine Learning Engineer","Mobile App Developer","Network Engineer","QA / Software Test Engineer","Software Developer"];
const SUGGEST = ["Python","SQL","Excel","Git","HTML","CSS","JavaScript","Java","Linux","Networking","Pandas","Statistics","Docker","AWS"];
const API = (location.protocol === "file:" || ["5500","5501"].includes(location.port)) ? "http://127.0.0.1:8000" : "";
let skills = ["Python","Git"], active = "BALANCED", pace = 10;
const $ = id => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";
function el(tag, attrs, ...kids){
  const e = document.createElement(tag);
  for (const [k,v] of Object.entries(attrs||{})){ if(k==="class") e.className=v; else if(k==="onclick") e.onclick=v; else e.setAttribute(k,v); }
  for (const k of kids.flat()) if (k!=null) e.append(k.nodeType?k:document.createTextNode(k));
  return e;
}
function sv(tag, attrs, ...kids){
  const e = document.createElementNS(NS, tag);
  for (const [k,v] of Object.entries(attrs||{})) e.setAttribute(k,v);
  for (const k of kids.flat()) if (k!=null) e.append(k.nodeType?k:document.createTextNode(k));
  return e;
}
OCCS.forEach(o => $("occ").append(el("option",{value:o},o)));
function updTotal(){ $("hpwV").textContent=$("hpw").value; $("wksV").textContent=$("wks").value; $("tot").textContent="Total budget: "+(+$("hpw").value * +$("wks").value)+" hours"; }
$("hpw").oninput = $("wks").oninput = updTotal;

function addSkill(s){ s=s.trim(); if(!s) return; if(!skills.some(x=>x.toLowerCase()===s.toLowerCase())) skills.push(s); drawSkills(); }
function drawSkills(){
  $("mine").replaceChildren(...skills.map(s=>el("button",{class:"chip",onclick:()=>{skills=skills.filter(x=>x!==s);drawSkills();}},s," ×")));
  const left = SUGGEST.filter(s=>!skills.some(x=>x.toLowerCase()===s.toLowerCase()));
  $("sug").replaceChildren(...left.map(s=>el("button",{class:"chip sug",onclick:()=>addSkill(s)},"+ "+s)));
}
$("skillIn").onkeydown = e => { if(e.key==="Enter"){ addSkill(e.target.value); e.target.value=""; } };
drawSkills();

function loadHistory(){
  fetch(API+"/history").then(r=>r.ok?r.json():Promise.reject()).then(rows=>{
    $("hist").classList.toggle("hide",!rows.length);
    $("histList").replaceChildren(...rows.map(h=>el("button",{class:"hrow",onclick:()=>openHistory(h.id)},
      el("b",{},h.occupation),el("div",{class:"meta"},h.budget_hours+" h • "+h.gap_count+" gaps • "+h.created_at.slice(0,16).replace("T"," ")))));
  }).catch(()=>$("hist").classList.add("hide"));
}
function openHistory(id){
  fetch(API+"/history/"+id).then(r=>r.json()).then(d=>{ active="BALANCED"; render(d,null); window.scrollTo({top:0,behavior:"smooth"}); });
}

function setStatus(ok, version){
  const s=$("status");
  if(!ok){ s.className="off"; s.textContent="API offline: sample mode"; return; }
  s.className = version ? "ok" : "off";
  s.textContent = version ? "API connected · engine v"+version : "API connected · OUTDATED engine";
}
fetch(API+"/health").then(r=>r.json()).then(h=>setStatus(true,h.engine_version)).catch(()=>setStatus(false));
loadHistory();
fetch(API+"/skills").then(r=>r.json()).then(list=>$("skillList").replaceChildren(...list.map(s=>el("option",{value:s})))).catch(()=>{});

async function run(){
  const body = {target_occupation:$("occ").value, current_skills:skills, time_budget_hours:+$("hpw").value * +$("wks").value};
  pace = +$("hpw").value;
  $("go").disabled = true; $("go").textContent = "Analyzing...";
  let data, reason = null;
  try{
    const r = await fetch(API+"/recommend",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    if(!r.ok){ let d=""; try{ const j=await r.json(); d=Array.isArray(j.detail)?j.detail.map(x=>x.msg).join("; "):(j.detail||""); }catch(e){} throw new Error("HTTP "+r.status+(d?": "+d:" (see the uvicorn terminal for the traceback)")); }
    data = await r.json(); setStatus(true, data.engine_version); loadHistory();
  }catch(err){
    reason = (err instanceof TypeError) ? "could not reach the API at "+(API||location.origin)+" (is uvicorn running?)" : err.message;
    data = DEMO[body.target_occupation]; setStatus(!(err instanceof TypeError));
  }
  $("go").disabled = false; $("go").textContent = "Analyze my skill gap";
  active = "BALANCED"; render(data, reason);
}
$("go").onclick = run;

function stat(v,l){ return el("div",{class:"stat"},el("b",{},String(v)),el("span",{},l)); }
function lab(d,id){ return (d.skill_labels&&d.skill_labels[id]) || id; }

function render(d, reason){
  const out = $("out"); out.replaceChildren();
  if (reason) out.append(el("div",{class:"banner demo"},"Your inputs were NOT applied: "+reason+". Showing a saved sample for "+d.candidate.target_occupation+" ("+d.candidate.time_budget_hours+" h budget, skills: "+d.candidate.current_skills.join(", ")+")."));
  if (!reason && !d.engine_version) out.append(el("div",{class:"banner demo"},"Your backend is running an OUTDATED recommendation_engine.py (no engine version in the response). Replace backend/recommendation_engine.py with the one from the latest zip and restart uvicorn. Until then the dependency graph, skill matching and label fixes will not work."));
  if (d.skills_interpreted && d.skills_interpreted.length) out.append(el("div",{class:"note"},"We matched your skills: "+d.skills_interpreted.map(x=>"“"+x.typed+"” → "+x.matched).join(", ")+"."));
  if (d.skills_unrecognized && d.skills_unrecognized.length) out.append(el("div",{class:"banner demo"},"Not recognised, so ignored: "+d.skills_unrecognized.join(", ")+". Pick skills from the suggestions that appear while you type."));
  const gaps = d.skill_gaps, ev = d.evaluations||{}, names = Object.keys(d.pathways);
  const bestKey = names.slice().sort((a,b)=>(ev[b]?.quality_score||0)-(ev[a]?.quality_score||0))[0];
  out.append(el("div",{class:"stats"},
    stat(d.candidate.target_occupation,"Target career"), stat(gaps.length,"Skills to learn"),
    stat(d.candidate.current_skills.length,"Skills you have"), stat(d.candidate.time_budget_hours+" h","Time budget"),
    stat(bestKey||"-","Highest-scoring pathway")));
  const g = el("div",{class:"card"},el("h2",{},"Skill gaps (ranked by job demand)"));
  if(!gaps.length) g.append("No gaps found for this career.");
  gaps.forEach(s=>g.append(el("div",{class:"gap"},
    el("span",{},s.skill), el("div",{class:"bar"},el("i",{style:"width:"+Math.min(100,s.demand_percentage*1.8)+"%"})),
    el("span",{class:"meta"},s.demand_percentage+"%"), el("span",{class:"tag "+s.priority},s.priority))));
  out.append(g);
  const p = el("div",{class:"card",id:"pw"}); out.append(p);
  const gr = el("div",{class:"card",id:"gr"}); out.append(gr);
  const redraw = () => { drawPathways(d,p,redraw); drawGraph(d,gr); };
  redraw();
  if (d.analysis_id) out.append(feedbackCard(d.analysis_id));
}


function feedbackCard(analysisId){
  const score = {relevance:0, clarity:0};
  const card = el("div",{class:"card fb"},el("h2",{},"Rate this result (helps our evaluation)"));
  function rating(key,label){
    const row = el("div",{class:"rate"});
    [1,2,3,4,5].forEach(n=>row.append(el("button",{onclick:()=>{ score[key]=n; [...row.children].forEach((b,i)=>b.className=(i+1===n?"on":"")); }},String(n))));
    card.append(el("label",{},label+" (1 = poor, 5 = excellent)"),row);
  }
  rating("relevance","Are the skill gaps and courses relevant to the career?");
  rating("clarity","Are the pathway explanations clear?");
  const role = el("select",{},["Student","Faculty / expert","Industry professional","Other"].map(r=>el("option",{value:r},r)));
  const comment = el("textarea",{rows:"2",maxlength:"500",placeholder:"Optional comment"});
  const msg = el("p",{class:"meta"});
  card.append(el("label",{},"You are a"),role,el("label",{},"Comment"),comment,
    el("button",{class:"send",onclick:async()=>{
      if(!score.relevance||!score.clarity){ msg.textContent="Please give both ratings."; return; }
      try{
        const r = await fetch(API+"/feedback",{method:"POST",headers:{"Content-Type":"application/json"},
          body:JSON.stringify({analysis_id:analysisId,relevance:score.relevance,clarity:score.clarity,role:role.value,comment:comment.value||null})});
        msg.textContent = r.ok ? "Thank you, your feedback was saved." : "Could not save feedback.";
      }catch(e){ msg.textContent="Could not reach the API."; }
    }},"Submit"),msg);
  return card;
}

function drawPathways(d, box, redraw){
  box.replaceChildren(el("h2",{},"Learning pathways"));
  const names = Object.keys(d.pathways);
  box.append(el("div",{class:"tabs"},names.map(n=>el("button",{class:"tab"+(n===active?" on":""),onclick:()=>{active=n;redraw();}},n[0]+n.slice(1).toLowerCase()))));
  const ev = d.evaluations[active]||{}, ex = d.explanations[active]||{};
  box.append(el("div",{class:"stats"},
    stat(ev.total_time_hours+" h","Total time"), stat(Math.max(1,Math.ceil(ev.total_time_hours/pace))+" wk","At "+pace+" h/week"), stat(ev.skill_coverage_percentage+"%","Gap skills covered"),
    stat(ev.demand_coverage_percentage+"%","Job demand covered"), stat(ev.average_course_rating,"Avg. rating"), stat(ev.quality_score,"Quality score")));
  if(ex.explanation) box.append(el("div",{class:"why"},ex.explanation));
  const sig = n => d.pathways[n].map(c=>c.course_id).join("|");
  const twin = names.slice(0,names.indexOf(active)).find(n=>sig(n)===sig(active));
  if(twin) box.append(el("div",{class:"note"},"Same courses as "+twin[0]+twin.slice(1).toLowerCase()+": within your time budget the quickest route is also the best one, so the pathways coincide."));
  const ok = ev.strict_prerequisites_valid && ev.time_feasible;
  box.append(el("p",{class:ok?"":"warn",style:"margin:0 0 8px"},
    (ev.strict_prerequisites_valid?"Prerequisite order valid":"Prerequisite violations: "+(ev.prerequisite_violations||[]).join(", "))+"  •  "+(ev.time_feasible?"Fits your time budget":"Exceeds your time budget")));
  d.pathways[active].forEach((c,i)=>box.append(el("div",{class:"course"},
    el("div",{class:"num"},String(i+1)),
    el("div",{},
      el("h3",{},el("a",{href:c.url,target:"_blank",rel:"noopener"},c.course_name)),
      el("div",{class:"meta"},[c.provider,c.duration_hours+" h",c.level,"rating "+c.rating].filter(Boolean).join(" • ")),
      el("div",{},"Covers: ",(c.covers||[]).map(s=>el("span",{class:"mini g"},lab(d,s)))),
      c.description?el("div",{class:"meta"},c.description):null))));
  if(ex.course_reason) box.append(el("p",{class:"meta"},ex.course_reason));
  const rows = names.map(n=>[n,d.evaluations[n]||{}]);
  const top = Math.max(...rows.map(r=>r[1].quality_score||0));
  box.append(el("h2",{style:"margin-top:20px"},"Compare pathways"),
    el("div",{style:"overflow-x:auto"},el("table",{},
      el("tr",{},["Pathway","Courses","Hours","Skill cov.","Demand cov.","Quality"].map(h=>el("th",{},h))),
      rows.map(([n,e])=>el("tr",{},el("td",{},n),el("td",{},String(e.course_count)),el("td",{},String(e.total_time_hours)),
        el("td",{},e.skill_coverage_percentage+"%"),el("td",{},e.demand_coverage_percentage+"%"),
        el("td",{class:e.quality_score===top?"best":""},String(e.quality_score)))))));
}

function drawGraph(d, box){
  box.replaceChildren(el("h2",{},"Skill dependency graph: courses, skills and occupation"));
  const g = d.skill_graph;
  if(!g){ box.append(el("p",{class:"warn"},"This API response has no skill_graph: the backend recommendation_engine.py is outdated. Replace it with the latest version and restart.")); return; }
  if(!g.nodes.length){ box.append("No dependency data for this result."); return; }
  const covered = new Set((d.evaluations[active]||{}).covered_skills||[]);
  const courses = d.pathways[active]||[];
  const demand = Object.fromEntries(d.skill_gaps.map(s=>[s.normalized_skill,s.demand_percentage]));
  const preds = {}; g.edges.forEach(e=>(preds[e.to]=preds[e.to]||[]).push(e.from));
  const level = {};
  const lv = id => { if(level[id]!==undefined) return level[id]; level[id]=0; level[id]=(preds[id]||[]).reduce((m,p)=>Math.max(m,lv(p)+1),0); return level[id]; };
  g.nodes.forEach(n=>lv(n.id));
  const firstCourse = id => { const i=courses.findIndex(c=>(c.covers||[]).includes(id)); return i<0?99:i; };
  const short = s => s.length>32 ? s.slice(0,31)+"…" : s;
  const nLev = Math.max(...g.nodes.map(n=>level[n.id]))+1;
  const cols = [courses.map((c,i)=>({kind:"course",id:"c"+i,label:(i+1)+". "+short(c.course_name),tip:c.course_name+" ("+c.duration_hours+" h)"}))];
  for(let l=0;l<nLev;l++) cols.push(g.nodes.filter(n=>level[n.id]===l)
    .sort((a,b)=>firstCourse(a.id)-firstCourse(b.id)||a.label.localeCompare(b.label)).map(n=>({kind:"skill",id:n.id,label:n.label,status:n.status})));
  cols.push([{kind:"occ",id:"occ",label:d.candidate.target_occupation}]);
  const widths = cols.map((c,i)=>i===0?230:170), H=34, GX=80, GY=14, PAD=20;
  const tallest = Math.max(...cols.map(c=>c.length));
  const height = PAD*2 + tallest*(H+GY) - GY;
  const xs = []; let x = PAD; widths.forEach(w=>{ xs.push(x); x += w+GX; });
  const width = x - GX + PAD;
  const pos = {};
  cols.forEach((c,ci)=>{ const top=(height-(c.length*(H+GY)-GY))/2; c.forEach((n,i)=>pos[n.id]={x:xs[ci],y:top+i*(H+GY),w:widths[ci]}); });
  const svg = sv("svg", {
    width,
    height,
    viewBox: "0 0 " + width + " " + height,
    preserveAspectRatio: "xMinYMin meet"
});
  const curve = (a,b,attrs,tip)=>{
    const x1=a.x+a.w,y1=a.y+H/2,x2=b.x,y2=b.y+H/2,mx=(x1+x2)/2;
    const p=sv("path",Object.assign({d:`M${x1} ${y1} C${mx} ${y1} ${mx} ${y2} ${x2} ${y2}`,fill:"none"},attrs));
    if(tip) p.append(sv("title",{},tip)); svg.append(p);
  };
  g.nodes.forEach(n=>curve(pos[n.id],pos.occ,{stroke:covered.has(n.id)?"#16a34a":"#cbd5e1","stroke-width":covered.has(n.id)?"1.8":"1","opacity":covered.has(n.id)?"0.9":"0.45"},n.label+" is required by "+d.candidate.target_occupation+" ("+(demand[n.id]||0)+"% of job postings)"));
  g.edges.forEach(e=>{ if(pos[e.from]&&pos[e.to]) curve(pos[e.from],pos[e.to],{stroke:"#64748b","stroke-width":e.strength==="STRICT"?"2":"1.5","stroke-dasharray":e.strength==="STRICT"?"":"5 4"},d.skill_labels[e.from]+" → "+d.skill_labels[e.to]+" ("+e.strength.toLowerCase()+"): "+(e.rationale||"")); });
  courses.forEach((c,i)=>(c.covers||[]).forEach(s=>{ if(pos[s]) curve(pos["c"+i],pos[s],{stroke:"#4f46e5","stroke-width":"2"},c.course_name+" teaches "+lab(d,s)); }));
  const fills = {have:["#dcfce7","#16a34a"],gap:["#eef0ff","#4f46e5"],prerequisite:["#fef3c7","#d97706"]};
  cols.flat().forEach(n=>{
    const p=pos[n.id], grp=sv("g",{});
    let fill,stroke,tc="#1c2333",sw="1.5",label=n.label;
    if(n.kind==="course"){ fill="#fff7ed"; stroke="#ea580c"; }
    else if(n.kind==="occ"){ fill="#4f46e5"; stroke="#4338ca"; tc="#fff"; }
    else { [fill,stroke]=fills[n.status]; if(covered.has(n.id)){ stroke="#111827"; sw="3"; label="✓ "+label; } }
    grp.append(sv("rect",{x:p.x,y:p.y,width:p.w,height:H,rx:9,fill,stroke,"stroke-width":sw}));
    grp.append(sv("text",{x:p.x+10,y:p.y+H/2+4,fill:tc},label));
    grp.append(sv("title",{},n.tip||label));
    svg.append(grp);
  });
  const sw = (bg,bd,t)=>el("span",{},el("i",{style:"background:"+bg+";border:1.5px solid "+bd}),t);
  box.append(
    el("div",{class:"legend"},sw("#fff7ed","#ea580c","Course in the "+active.toLowerCase()+" pathway"),sw("#dcfce7","#16a34a","Skill you have"),
      sw("#eef0ff","#4f46e5","Skill gap"),sw("#fef3c7","#d97706","Prerequisite you still need"),sw("#4f46e5","#4338ca","Target occupation")),
    el("div",{class:"legend"},el("span",{},"indigo line = course teaches skill"),el("span",{},"grey solid/dashed = strict/recommended prerequisite"),
      el("span",{},"green line and ✓ bold outline = covered by this pathway")),
    el("div",{id:"graph"},svg));
}

