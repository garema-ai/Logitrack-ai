"""LogiTrack AI: inspect outbound logistics data and propose human-reviewed actions.

Offline default = auditable rule/tool routing; optional OpenAI API augments
narrative with a language model. All KPIs remain calculated by engine.py.
"""
import argparse
import json
import os
from pathlib import Path
from datetime import date
from engine import run, offline_answer, route_question

SYSTEM_RULES = '''You are LogiTrack AI, a supply-chain operations analyst working only with
synthetic training data. Use only the JSON evidence provided. Do not invent
numbers, sources, vendor policies, SAP access, or actions already performed.
Prioritize grounded, operationally useful recommendations, and separate facts
from proposals. Any payments, orders, or vendor messages require a human
reviewer. Limit answer to 220 words.'''

def llm_answer(question, report, model):
    if not os.environ.get('OPENAI_API_KEY'):
        raise RuntimeError('Set OPENAI_API_KEY for LLM mode; offline mode needs no API key.')
    from openai import OpenAI
    tools=route_question(question)
    evidence={'as_of':report['as_of'],'actions':report['actions'][:12]}
    for tool in tools:
        evidence[tool] = report[{'inventory':'inventory','dispatch':'dispatch','invoices':'invoices'}[tool]]
    client=OpenAI()
    result=client.responses.create(model=model,instructions=SYSTEM_RULES,
            input=f'User question: {question}\nSelected analytical tools: {tools}\nEvidence (JSON):\n{json.dumps(evidence,default=str)}')
    return result.output_text

def markdown_report(report):
    i,d,p=report['inventory'],report['dispatch'],report['invoices']
    lines=[f'# LogiTrack AI | Outbound Logistics Operations Brief',
           f'As of {report["as_of"]} | DEMONSTRATION: synthetic data only',
           '', '## Operating KPIs',
           f'- Inventory: {i["total_units"]:,} units across {i["sku_count"]} SKU/depot records.',
           f'- Critical SKUs below 5 days cover: {len(i["critical_stockout_risk"])}.',
           f'- Aging stock (oldest age >= 90 days): {len(i["old_stock"])} records, indicative value INR {i["old_stock_value_inr"]:,.0f}.',
           f'- On-time delivery: {d["on_time_delivery_pct"]}% of delivered shipments.',
           f'- Overdue in-transit shipments: {len(d["overdue_shipments"])}.',
           f'- Average truck turnaround: {d["avg_truck_turnaround_minutes"]} min (demo target: 180 min).',
           f'- Unit-based damage rate: {d["damage_rate_pct"]}% of dispatched units.',
           f'- Overdue unpaid invoices: {len(p["overdue_invoices"])} (INR {p["overdue_amount_inr"]:,.0f}).',
           '', '## Priority actions (human review required)',
           '| Priority | Issue | Evidence | Recommended next step |',
           '|---|---|---|---|']
    for a in report['actions'][:12]:
        vals=[a['priority'],a['title'],a['evidence'],a['recommendation']]
        lines.append('| '+' | '.join(str(s).replace('|','/') for s in vals)+' |')
    lines+=['','## Method and limitations',
            '- Stock cover = on-hand units / average daily demand. Zero demand is not classified as stockout risk.',
            '- Aging definition uses oldest-stock age >= 90 days; bucket value is an illustrative upper bound, not a batch-accurate inventory valuation.',
            '- On-time rate denominator includes only delivered shipments; overdue pending deliveries are tracked separately.',
            '- Truck turnaround uses exit timestamp minus entry timestamp.',
            '- Unit damage rate = damaged units / dispatched units. It is not volume-damage-per-MT.',
            '- No SAP, 3PL, transporter, invoice payment or messaging integrations exist in this demo.',
            '- Data are simulated and are not connected with Asian Paints or any employer.']
    return '\n'.join(lines)+'\n'

def main():
    ap=argparse.ArgumentParser(description='Explainable outbound logistics monitoring agent')
    ap.add_argument('--ask',default='What are the highest priority issues today?')
    ap.add_argument('--mode',choices=['offline','llm'],default='offline')
    ap.add_argument('--model',default=os.getenv('OPENAI_MODEL','gpt-4.1-mini'))
    ap.add_argument('--data-dir',default=str(Path(__file__).parent/'data'))
    ap.add_argument('--as-of',default='2026-10-24',help='YYYY-MM-DD')
    ap.add_argument('--write-report',default=None,help='Write Markdown report')
    ap.add_argument('--json-output',default=None,help='Write machine-readable evidence JSON')
    args=ap.parse_args()
    report=run(args.data_dir,date.fromisoformat(args.as_of))
    if args.write_report: Path(args.write_report).write_text(markdown_report(report),encoding='utf-8')
    if args.json_output: Path(args.json_output).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'LOGITRACK AI | {args.mode.upper()} MODE | as of {args.as_of}\n')
    if args.mode=='llm': print(llm_answer(args.ask,report,args.model))
    else: print(offline_answer(args.ask,report))
    print('\nNo actions executed. Recommendations require approval.')

if __name__=='__main__':main()
