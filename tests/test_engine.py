import sys
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import run, assess, analyze_inventory, analyze_dispatches, analyze_invoices, route_question, offline_answer

def test_sample_inputs_and_actions():
    r=run()
    assert r['inventory']['sku_count']==36
    assert r['dispatch']['shipment_count']==84
    assert r['invoices']['invoice_count']==28
    assert len(r['actions'])>10
    assert r['actions'][0]['priority']=='P0'
    assert r['invoices']['overdue_amount_inr']>0

def test_stock_risk_days_cover():
    row={'sku':'A','depot':'D','on_hand_units':'10','avg_daily_demand':'5','oldest_stock_days':'120',
         'damaged_units':'0','unit_value_inr':'100','critical_sku':'Yes'}
    x=analyze_inventory([row]);assert x['critical_stockout_risk'][0]['days_cover']==2
    assert x['old_stock_value_inr']==1000

def test_on_time_uses_only_delivered():
    base={'shipment_id':'T','depot':'D','transporter':'Vendor','dispatch_date':'2026-10-10',
          'planned_delivery_date':'2026-10-12','truck_in_time':'2026-10-10T10:00',
          'truck_out_time':'2026-10-10T12:00','qty_dispatched':'100','qty_damaged':'1','shipment_weight_mt':'1.5'}
    a={**base,'actual_delivery_date':'2026-10-11'}
    b={**base,'shipment_id':'T2','actual_delivery_date':''}
    x=analyze_dispatches([a,b],date(2026,10,24))
    assert x['on_time_delivery_pct']==100
    assert len(x['overdue_shipments'])==1
    assert x['damage_rate_pct']==1
    assert x['avg_truck_turnaround_minutes']==120

def test_invoice_only_unpaid_past_due():
    r={'invoice_id':'B','vendor':'Test','po_number':'P','amount_inr':'1200','due_date':'2026-10-20','payment_status':'Unpaid'}
    assert analyze_invoices([r],date(2026,10,24))['overdue_amount_inr']==1200
    assert analyze_invoices([{**r,'payment_status':'Paid'}],date(2026,10,24))['overdue_amount_inr']==0

def test_routing_is_transparent():
    assert route_question('how are our invoices?')==['invoices']
    assert route_question('which SKUs will stockout')==['inventory']
    assert route_question('what about truck turnaround')==['dispatch']
    assert 'Inventory:' in offline_answer('What should I do?',run())

def test_future_delivery_does_not_count_as_confirmed_on_as_of():
    row={'shipment_id':'T3','depot':'D','transporter':'Vendor','dispatch_date':'2026-10-20',
         'planned_delivery_date':'2026-10-22','actual_delivery_date':'2026-10-27',
         'truck_in_time':'2026-10-20T10:00','truck_out_time':'2026-10-20T11:00',
         'qty_dispatched':'100','qty_damaged':'0','shipment_weight_mt':'1.5'}
    results=analyze_dispatches([row],date(2026,10,24))
    assert results['delivered']==0
    assert len(results['overdue_shipments'])==1


def test_invalid_inventory_rejected():
    import pytest
    row={'sku':'A','depot':'D','on_hand_units':'-10','avg_daily_demand':'5','oldest_stock_days':'120',
         'damaged_units':'0','unit_value_inr':'100','critical_sku':'Yes'}
    with pytest.raises(ValueError): analyze_inventory([row])


def test_damaged_units_cannot_exceed_dispatch_quantity():
    import pytest
    row={'shipment_id':'T','depot':'D','transporter':'Vendor','dispatch_date':'2026-10-10',
         'planned_delivery_date':'2026-10-12','actual_delivery_date':'2026-10-12',
         'truck_in_time':'2026-10-10T10:00','truck_out_time':'2026-10-10T11:00',
         'qty_dispatched':'10','qty_damaged':'11','shipment_weight_mt':'1.5'}
    with pytest.raises(ValueError): analyze_dispatches([row],date(2026,10,24))
