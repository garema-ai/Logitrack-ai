"""Transparent, testable decision tools for LogiTrack AI.

This module performs arithmetic and flags exceptions; it does not pretend that
predictions are verified facts or take actions in external business systems.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from datetime import date, datetime
from collections import defaultdict

AS_OF = date(2026, 10, 24)
LOW_COVER_DAYS = 5.0
OLD_STOCK_DAYS = 90
TRUCK_TAT_TARGET_MINUTES = 180

def load_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def safe_float(v, label):
    try: return float(v)
    except (TypeError, ValueError): raise ValueError(f'Invalid numeric value in {label}: {v!r}')

def parse_date(v): return date.fromisoformat(v)

def parse_dt(v): return datetime.fromisoformat(v)

def analyze_inventory(rows):
    low, old, total, damaged, old_value = [], [], 0, 0, 0
    for r in rows:
        sku=r['sku']; stock=safe_float(r['on_hand_units'],f'{sku}.on_hand_units')
        demand=safe_float(r['avg_daily_demand'],f'{sku}.avg_daily_demand')
        age=safe_float(r['oldest_stock_days'],f'{sku}.oldest_stock_days')
        n_damage=safe_float(r['damaged_units'],f'{sku}.damaged_units')
        unit_value=safe_float(r['unit_value_inr'],f'{sku}.unit_value_inr')
        if any(v<0 for v in [stock,demand,age,n_damage,unit_value]): raise ValueError('Negative stock / demand / age / damage / value')
        total += stock; damaged += n_damage
        cover=round(stock/demand,2) if demand>0 else None
        if (r['critical_sku'].strip().lower() in ['yes','true','1']) and cover is not None and cover < LOW_COVER_DAYS:
            low.append(dict(sku=sku,depot=r['depot'],stock=stock,days_cover=cover,avg_daily_demand=demand))
        if age>=OLD_STOCK_DAYS:
            cost=round(stock*unit_value,2); old_value+=cost
            old.append(dict(sku=sku,depot=r['depot'],age_days=int(age),units=stock,stock_value_inr=cost))
    low.sort(key=lambda x:x['days_cover']);old.sort(key=lambda x:(-x['age_days'],-x['stock_value_inr']))
    return dict(total_units=round(total),damaged_units=round(damaged),critical_stockout_risk=low,
                old_stock=old,old_stock_value_inr=round(old_value,2),sku_count=len(rows))

def analyze_dispatches(rows,as_of=AS_OF):
    delivered=0; on_time=0; turnaround=[]; overdue=[]; damage=0; units=0; weights=0
    for r in rows:
        shipped=safe_float(r['qty_dispatched'],f"{r['shipment_id']}.qty_dispatched")
        bad=safe_float(r['qty_damaged'],f"{r['shipment_id']}.qty_damaged")
        weight=safe_float(r['shipment_weight_mt'],f"{r['shipment_id']}.shipment_weight_mt")
        if min(shipped,bad,weight)<0: raise ValueError('Negative shipment values')
        if bad>shipped: raise ValueError('Damaged quantity exceeds dispatched quantity')
        units+=shipped;damage+=bad;weights+=weight
        plan=parse_date(r['planned_delivery_date'])
        actual=r['actual_delivery_date'].strip()
        if actual and parse_date(actual)<=as_of:
            delivered+=1
            if parse_date(actual)<=plan:on_time+=1
        elif plan<as_of:
            overdue.append(dict(shipment_id=r['shipment_id'],depot=r['depot'],transporter=r['transporter'],
                         days_late=(as_of-plan).days,planned_delivery_date=plan.isoformat()))
        in_time=r.get('truck_in_time','');out_time=r.get('truck_out_time','')
        if in_time and out_time:
            minutes=(parse_dt(out_time)-parse_dt(in_time)).total_seconds()/60
            if minutes<0: raise ValueError('Truck departure before arrival')
            turnaround.append(minutes)
    overdue.sort(key=lambda x:-x['days_late'])
    avg_tat=round(sum(turnaround)/len(turnaround),1) if turnaround else None
    on_time_pct=round(100*on_time/delivered,1) if delivered else None
    return dict(shipment_count=len(rows),delivered=delivered,on_time_delivery_pct=on_time_pct,
                avg_truck_turnaround_minutes=avg_tat,overdue_shipments=overdue,
                truck_tat_target_minutes=TRUCK_TAT_TARGET_MINUTES,damage_rate_pct=round(100*damage/units,2) if units else None,
                damaged_units=round(damage),dispatch_units=round(units),shipment_weight_mt=round(weights,2))

def analyze_invoices(rows,as_of=AS_OF):
    overdue=[]; total_unpaid=0
    for r in rows:
        value=safe_float(r['amount_inr'],f"{r['invoice_id']}.amount_inr")
        if value<0:raise ValueError('Negative invoice amount')
        if r['payment_status'].strip().lower() in ('paid','settled'): continue
        total_unpaid+=value
        due=parse_date(r['due_date'])
        if due<as_of:
            overdue.append(dict(invoice_id=r['invoice_id'],vendor=r['vendor'],
                                days_overdue=(as_of-due).days,amount_inr=value,po_number=r['po_number']))
    overdue.sort(key=lambda x:(-x['days_overdue'],-x['amount_inr']))
    return dict(invoice_count=len(rows),overdue_invoices=overdue,overdue_amount_inr=round(sum(x['amount_inr'] for x in overdue),2),
                unpaid_amount_inr=round(total_unpaid,2))

def make_actions(inventory,dispatches,invoices):
    actions=[]
    def add(priority,category,title,evidence,recommendation,owner):
        actions.append(dict(priority=priority,category=category,title=title,evidence=evidence,
                            recommendation=recommendation,suggested_owner=owner,status='Proposed - review required'))
    for x in inventory['critical_stockout_risk']:
        add('P0' if x['days_cover']<2 else 'P1','Inventory',f"Critical SKU {x['sku']} at {x['depot']}",
            f"{x['days_cover']} days of cover ({x['stock']:.0f} units on hand)",
            'Validate open orders and actual demand; request replenishment or approved stock transfer.',
            'Inventory planner')
    for x in dispatches['overdue_shipments'][:12]:
        add('P1' if x['days_late']>=3 else 'P2','Dispatch',f"Shipment {x['shipment_id']} overdue",
            f"{x['days_late']} days overdue; {x['transporter']}",
            'Verify transporter status, confirm revised ETA, and notify the receiving depot.', 'Logistics coordinator')
    for x in inventory['old_stock'][:12]:
        add('P1' if x['age_days']>=120 else 'P2','Inventory',f"Aging stock {x['sku']} at {x['depot']}",
            f"{x['age_days']} days; INR {x['stock_value_inr']:,.0f} indicative stock value",
            'Review demand, quality restrictions and approved redistribution or liquidation options.', 'Warehouse lead')
    for x in invoices['overdue_invoices'][:12]:
        add('P1' if x['days_overdue']>14 else 'P2','Payments',f"Vendor invoice {x['invoice_id']} overdue",
            f"{x['days_overdue']} days overdue; INR {x['amount_inr']:,.0f}",
            'Check invoice/PO documentation and follow up with finance and vendor.', 'Procurement / finance')
    if dispatches['avg_truck_turnaround_minutes'] is not None and dispatches['avg_truck_turnaround_minutes']>TRUCK_TAT_TARGET_MINUTES:
        add('P1','Dispatch','Average truck turnaround exceeds target',
            f"Average {dispatches['avg_truck_turnaround_minutes']} min; target {TRUCK_TAT_TARGET_MINUTES} min",
            'Review gate timestamps, loading bottlenecks, shift capacity and transporter slot adherence.', 'TL operations')
    order={'P0':0,'P1':1,'P2':2}
    actions.sort(key=lambda x:(order[x['priority']],x['category'],x['title']))
    return actions

def assess(inventory_rows,dispatch_rows,invoice_rows,as_of=AS_OF):
    inv=analyze_inventory(inventory_rows); dis=analyze_dispatches(dispatch_rows,as_of); pay=analyze_invoices(invoice_rows,as_of)
    return dict(as_of=as_of.isoformat(),inventory=inv,dispatch=dis,invoices=pay,actions=make_actions(inv,dis,pay),
                disclaimer='Synthetic example data. Recommendations require human review; no operational actions are executed.')

def run(data_dir=None,as_of=AS_OF):
    d=Path(data_dir) if data_dir else Path(__file__).resolve().parent/'data'
    return assess(load_csv(d/'inventory.csv'),load_csv(d/'dispatches.csv'),load_csv(d/'invoices.csv'),as_of)

def route_question(q):
    q=q.lower()
    if any(z in q for z in ('invoice','payment','vendor','bill','overdue payable')): return ['invoices']
    if any(z in q for z in ('truck','transport','dispatch','shipment','delivery','damage','turnaround','3pl')): return ['dispatch']
    if any(z in q for z in ('inventory','stock','sku','aging','ageing','replenishment','stockout')): return ['inventory']
    return ['inventory','dispatch','invoices']

def offline_answer(q, report):
    selected=route_question(q); lines=['Analysis tools selected: '+', '.join(selected)+'.']
    if 'inventory' in selected:
        i=report['inventory']; lines.append(f"Inventory: {i['total_units']:,} units across {i['sku_count']} SKU/depot records; {len(i['critical_stockout_risk'])} critical SKUs below {LOW_COVER_DAYS:g} days cover; {len(i['old_stock'])} old-stock records >= {OLD_STOCK_DAYS} days (INR {i['old_stock_value_inr']:,.0f} indicative value).")
        if i['critical_stockout_risk']: lines.append('Highest stockout risk: '+', '.join(f"{s['sku']} ({s['days_cover']}d)" for s in i['critical_stockout_risk'][:3])+'.')
        if i['old_stock']: lines.append('Oldest inventory records: '+', '.join(f"{s['sku']} ({s['age_days']} days)" for s in i['old_stock'][:3])+'.')
    if 'dispatch' in selected:
        d=report['dispatch']; lines.append(f"Dispatch: {d['shipment_count']} shipments; on-time delivery {d['on_time_delivery_pct']}% of delivered shipments; {len(d['overdue_shipments'])} in-transit shipments past due; truck turnaround {d['avg_truck_turnaround_minutes']} min; damage rate {d['damage_rate_pct']}% by units.")
        if d['overdue_shipments']: lines.append('Most delayed: '+', '.join(f"{s['shipment_id']} ({s['days_late']}d; {s['transporter']})" for s in d['overdue_shipments'][:3])+'.')
    if 'invoices' in selected:
        p=report['invoices']; lines.append(f"Vendor payments: {len(p['overdue_invoices'])} overdue unpaid invoices totaling INR {p['overdue_amount_inr']:,.0f}.")
        if p['overdue_invoices']: lines.append('Most overdue invoice: '+p['overdue_invoices'][0]['invoice_id']+'.')
    cats={'inventory':'Inventory','dispatch':'Dispatch','invoices':'Payments'}
    applicable=[a for a in report['actions'] if a['category'] in [cats[s] for s in selected]]
    if applicable:lines.append('Next action: '+applicable[0]['recommendation']+' ('+applicable[0]['evidence']+').')
    return '\n'.join(lines)
