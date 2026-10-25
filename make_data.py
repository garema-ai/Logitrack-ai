"""Generate realistic-looking, fully synthetic outbound logistics demo records."""
from __future__ import annotations
import csv
import random
from datetime import datetime, timedelta, date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data'
TODAY = date(2026, 10, 24)
RNG = random.Random(15474)
DEPOTS = ['Mumbai TL', 'Pune Depot', 'Surat Depot', 'Nagpur Depot']
VENDORS = ['Coastal Carriers', 'Western Freight', 'Marigold Logistics', 'Blue Route Transport']
PRODUCTS = ['Interior Emulsion', 'Exterior Weathercoat', 'Primer', 'Wall Putty', 'Enamel', 'Wood Finish', 'Waterproofing', 'Texture Coat']

def write(name, fields, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

inv = []
for i in range(1, 37):
    critical = i % 4 == 0 or i in (3, 7, 17)
    daily = RNG.choice([2, 4, 6, 8, 10, 12, 16, 20])
    stock = RNG.choice([3, 4, 5, 9, 12, 18, 24, 30, 45, 60, 75, 90, 120]) * daily // 4
    age = RNG.choice([12, 19, 23, 35, 43, 60, 74, 91, 104, 118, 132, 155])
    damaged = RNG.choice([0, 0, 0, 1, 2, 3, 5])
    inv.append(dict(sku=f'PAINT-{i:03d}', product=PRODUCTS[(i-1)%len(PRODUCTS)], depot=DEPOTS[(i-1)%4],
                    on_hand_units=stock, avg_daily_demand=daily, oldest_stock_days=age, damaged_units=min(damaged,stock),
                    unit_value_inr=RNG.choice([480, 650, 920, 1250, 1700, 2200]), critical_sku='Yes' if critical else 'No'))
write('inventory.csv', list(inv[0]), inv)

ships = []
for i in range(1, 85):
    departure_day = TODAY-timedelta(days=RNG.randrange(1,29))
    arrival = datetime.combine(departure_day, datetime.min.time()).replace(hour=RNG.randrange(5,21), minute=RNG.choice([0,15,30,45]))
    tat = RNG.randrange(60,310)
    exit_time = arrival + timedelta(minutes=tat)
    plan = departure_day + timedelta(days=RNG.choice([2,3,4,5,6]))
    is_pending = (i % 9 == 0 or i % 17 == 0)
    actual = None if is_pending else plan + timedelta(days=RNG.choice([-1,0,0,0,1,2,4]))
    qty = RNG.randrange(80,800,20)
    damage = 0 if i%7 else RNG.choice([1,2,3,7,10])
    ships.append(dict(shipment_id=f'SHP-{i:04d}', sku=inv[(i*7)%len(inv)]['sku'], depot=DEPOTS[i%4], transporter=VENDORS[i%4],
                      dispatch_date=departure_day.isoformat(), planned_delivery_date=plan.isoformat(),
                      actual_delivery_date=actual.isoformat() if actual else '', truck_in_time=arrival.isoformat(timespec='minutes'),
                      truck_out_time=exit_time.isoformat(timespec='minutes'), qty_dispatched=qty, qty_damaged=damage,
                      shipment_weight_mt=round(qty * 0.015, 2), status='In transit' if is_pending else 'Delivered'))
write('dispatches.csv', list(ships[0]), ships)

invoices=[]
for i in range(1,29):
    invdate=TODAY-timedelta(days=RNG.randrange(7,76))
    due=invdate+timedelta(days=RNG.choice([15,30,45]))
    paid = i%5==0 or (due<TODAY and i%7==0)
    invoices.append(dict(invoice_id=f'INV-{i:04d}', vendor=VENDORS[i%4], po_number=f'PO-{1000+i}',
                         invoice_date=invdate.isoformat(), due_date=due.isoformat(),
                         amount_inr=RNG.randrange(8,200)*1000, payment_status='Paid' if paid else 'Unpaid'))
write('invoices.csv',list(invoices[0]), invoices)
print(f'Generated {len(inv)} inventory rows, {len(ships)} dispatches, {len(invoices)} invoices')
