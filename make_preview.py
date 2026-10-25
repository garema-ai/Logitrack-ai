"""Build a standalone read-only GitHub Pages preview from the analysis JSON.
No Streamlit server, API key, or personal data needed.
"""
from pathlib import Path
import json
from html import escape

root=Path(__file__).resolve().parent
report=json.loads((root/'data'/'sample_analysis.json').read_text(encoding='utf-8'))
report_payload=json.dumps(report,ensure_ascii=False).replace('</','<\\/')

page=r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>LogiTrack AI — Outbound Logistics Control Tower</title>
<style>
:root{--bg:#09121e;--surface:#101f2d;--panel:#132637;--line:#284153;--mint:#5de1bc;--teal:#3bbca7;--text:#eff7fb;--muted:#9eb2bf;--amber:#ffcb7b;--red:#ff8f9a;--blue:#86c6ff}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:radial-gradient(circle at 75% 0%,#173249 0%,#09121e 53%);color:var(--text)}
header{border-bottom:1px solid #29404f;background:#091523db;position:sticky;top:0;z-index:3;backdrop-filter:blur(14px)}.shell{max-width:1210px;padding:0 24px;margin:auto}
nav{display:flex;align-items:center;justify-content:space-between;padding:15px 0}.brand{font-size:19px;font-weight:750;letter-spacing:-.5px}.brand span{color:var(--mint)}.top-label{font-size:12px;color:var(--muted)}
.hero{display:flex;justify-content:space-between;gap:20px;align-items:center;padding:42px 0 24px}.eyebrow{font-size:11px;color:var(--mint);font-weight:800;letter-spacing:1.5px}.hero h1{margin:7px 0 4px;font-size:clamp(26px,4vw,43px);line-height:1.1;letter-spacing:-1.4px}.hero p{margin:9px 0;color:var(--muted);max-width:700px}.pill{border:1px solid #306354;border-radius:20px;padding:7px 13px;color:#89edd0;background:#13382f;font-weight:650;font-size:11px;white-space:nowrap}
.banner{border:1px solid #395d71;background:#11293a;border-radius:10px;padding:12px 16px;color:#b6cad6;font-size:12px;margin:0 0 22px}
.kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin-bottom:24px}.kpi{background:linear-gradient(165deg,#142a39,#10202f);border:1px solid #294454;border-radius:14px;padding:20px 15px;min-height:128px}.kpi h3{font-size:11px;font-weight:650;color:#b3cad4;margin:0 0 12px}.kpi strong{font-size:31px;letter-spacing:-1px}.kpi small{display:block;color:var(--muted);margin-top:4px;font-size:11px}
.main{background:#102130;border:1px solid #294455;border-radius:16px;overflow:hidden;margin-bottom:20px}.mainhead{padding:20px 22px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:16px}.mainhead h2{margin:0;font-size:18px}.sub{font-size:12px;color:var(--muted);margin:3px 0 0}
.tabs{display:flex;gap:6px;flex-wrap:wrap;padding:13px 20px;border-bottom:1px solid var(--line)}button{border:none;cursor:pointer}button.tab{background:transparent;color:var(--muted);padding:9px 12px;border-radius:8px;font-weight:700}button.tab.active{color:#051816;background:var(--mint)}
.tools{display:flex;gap:9px;align-items:center;justify-content:space-between;flex-wrap:wrap;padding:16px 20px}input,select{background:#0b1c2a;color:var(--text);padding:11px 12px;border:1px solid #2b4b61;border-radius:8px;outline:0;font:inherit}input{min-width:250px;flex:1}input:focus,select:focus{border-color:var(--mint)}
.scroll{overflow:auto}table{width:100%;border-collapse:collapse;font-size:12px}thead{background:#172d3c;color:#cde1e7}th{text-transform:uppercase;letter-spacing:.6px;font-size:10px;text-align:left;padding:11px 16px;white-space:nowrap}td{padding:11px 16px;border-top:1px solid #223b4c;color:#d4e6ea}tr:hover td{background:#183346}.sev{padding:3px 8px;font-weight:800;border-radius:6px;font-size:11px}.p0{background:#532a35;color:#ff9cad}.p1{background:#4b402c;color:#ffdb9f}.p2{background:#244153;color:#b5ddfb}
.foot{color:#92aebc;font-size:12px;display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;margin:24px 0 35px}a{color:#91efda;text-decoration:none}a:hover{text-decoration:underline}.empty{padding:30px;color:var(--muted)}.about{padding:19px 21px;color:#b9ced8}.about strong{color:#e4f4f8}
@media(max-width:950px){.kpis{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:640px){.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.hero{flex-direction:column;align-items:start}.shell{padding:0 14px}.mainhead{padding:17px}.kpi strong{font-size:26px}.top-label{display:none}.tools input{min-width:0;width:100%}}
</style></head>
<body><header><div class="shell"><nav><div class="brand">▣ Logi<span>Track AI</span></div><div class="top-label">OUTBOUND LOGISTICS CONTROL TOWER · DEMO</div></nav></div></header>
<main class="shell">
<section class="hero"><div><div class="eyebrow">INDEPENDENT PORTFOLIO PROJECT</div><h1>From logistics data to<br>decisions that move goods.</h1><p>Detect stockout risks, monitor dispatch delays, review vendor payments, and prioritize operational follow-ups.</p></div><span class="pill">● SIMULATED DATA</span></section>
<div class="banner">This is a synthetic, read-only demonstration. All numbers are invented for training. No SAP, vendor, transporter, or employer system is connected. Actions require human approval.</div>
<div class="kpis" id="kpis"></div>
<section class="main"><div class="mainhead"><div><h2>Operations exception explorer</h2><p class="sub">Analysis as of <span id="asof"></span> · Search evidence, identify risk, prioritize action</p></div><span class="pill" id="count"></span></div>
<div class="tabs" id="tabs"><button class="tab active" data-view="actions">Priority queue</button><button class="tab" data-view="inventory">Stockout risk</button><button class="tab" data-view="aging">Aging inventory</button><button class="tab" data-view="dispatch">Late dispatches</button><button class="tab" data-view="payments">Vendor payments</button></div>
<div class="tools"><input type="search" id="search" placeholder="Search an SKU, shipment, vendor, issue..." aria-label="Search results"/><select id="priority" aria-label="Priority filter"><option value="all">All priorities</option><option>P0</option><option>P1</option><option>P2</option></select></div><div class="scroll" id="table"></div>
</section>
<section class="main"><div class="mainhead"><div><h2>What this agent actually does</h2><p class="sub">Explainable analysis rules, prioritized actions, optional LLM-assisted explanations</p></div></div>
<div class="about"><strong>Decision pipeline:</strong> CSV records → validation → KPI calculations → exception rules → P0/P1/P2 suggested actions → human review.<br><br><strong>Definitions:</strong> Critical stockout risk = marked-critical item with &lt;5 days of cover. Aging inventory = oldest unit age ≥90 days. Pending overdue shipment = planned delivery date is earlier than analysis date, with no confirmed delivery by that date. Vendor overdue = unpaid and past due.<br><br><strong>Not included:</strong> Autonomous purchase ordering, real-time tracking, SAP integration, live warehouse or transporter data, predictive machine learning, or business-approved controls. For CSV upload, dynamic calculations, and an optional LLM explanation mode, run the Python Streamlit application included in this repository.</div>
</section><div class="foot"><span>© 2026 Garema Dogra · Independent educational project</span><span>Pure browser preview · No API calls · Not affiliated with Asian Paints</span></div>
</main>
<script id="report-json" type="application/json">__DATA__</script>
<script>
const report=JSON.parse(document.getElementById('report-json').textContent);
const inventory=report.inventory, dispatch=report.dispatch, invoices=report.invoices;
function esc(v){return String(v??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));}
function nr(v){return Number(v).toLocaleString('en-IN')}
const kpis=[['Critical SKUs',inventory.critical_stockout_risk.length,'Below 5 days cover'],['Overdue shipments',dispatch.overdue_shipments.length,'Past expected date'],['On-time delivery',dispatch.on_time_delivery_pct+'%','Of confirmed deliveries'],['Truck turnaround',dispatch.avg_truck_turnaround_minutes+' min','Demo target: 180 min'],['Overdue invoices',invoices.overdue_invoices.length,'₹'+nr(invoices.overdue_amount_inr)+' outstanding']];
document.getElementById('kpis').innerHTML=kpis.map(k=>`<article class="kpi"><h3>${esc(k[0])}</h3><strong>${esc(k[1])}</strong><small>${esc(k[2])}</small></article>`).join('');
document.getElementById('asof').textContent=report.as_of;
const schemas={actions:[['priority','Priority'],['category','Area'],['title','Exception'],['evidence','Evidence'],['recommendation','Recommended follow-up'],['suggested_owner','Suggested owner']],inventory:[['sku','SKU'],['depot','Depot'],['stock','Units'],['days_cover','Days cover'],['avg_daily_demand','Daily demand']],aging:[['sku','SKU'],['depot','Depot'],['age_days','Oldest age (days)'],['units','On hand'],['stock_value_inr','Indicative value (₹)']],dispatch:[['shipment_id','Shipment'],['depot','Depot'],['transporter','Transporter'],['days_late','Days late'],['planned_delivery_date','Planned delivery']],payments:[['invoice_id','Invoice'],['vendor','Vendor'],['po_number','PO'],['days_overdue','Days overdue'],['amount_inr','Amount (₹)']]};
const datasets={actions:report.actions,inventory:inventory.critical_stockout_risk,aging:inventory.old_stock,dispatch:dispatch.overdue_shipments,payments:invoices.overdue_invoices};
let view='actions';
function render(){const q=document.getElementById('search').value.trim().toLowerCase(),prio=document.getElementById('priority').value;
const rows=datasets[view].filter(x=>(view!=='actions'||prio==='all'||x.priority===prio)&&(!q||Object.values(x).some(v=>String(v).toLowerCase().includes(q))));document.getElementById('count').textContent=rows.length+' records';const cols=schemas[view];
if(!rows.length){document.getElementById('table').innerHTML='<div class="empty">No matching records.</div>';return;}
const head='<thead><tr>'+cols.map(([,label])=>`<th>${esc(label)}</th>`).join('')+'</tr></thead>';
const body=rows.map(x=>'<tr>'+cols.map(([key])=>{let value=x[key];if(view==='actions'&&key==='priority'){value=`<span class="sev ${esc(String(value).toLowerCase())}">${esc(value)}</span>`;} else if((key==='stock_value_inr'||key==='amount_inr')&&Number.isFinite(Number(value))){value='₹'+nr(value);}else{value=esc(value);}return `<td>${value}</td>`}).join('')+'</tr>').join('');
document.getElementById('table').innerHTML='<table>'+head+'<tbody>'+body+'</tbody></table>';}
document.querySelectorAll('button.tab').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('button.tab').forEach(x=>x.classList.remove('active'));b.classList.add('active');view=b.dataset.view;document.getElementById('priority').style.display=view==='actions'?'block':'none';render()}));
document.getElementById('search').addEventListener('input',render);document.getElementById('priority').addEventListener('change',render);render();
</script></body></html>'''
(root/'docs'/'index.html').write_text(page.replace('__DATA__',report_payload),encoding='utf-8')
print('Wrote docs/index.html')
