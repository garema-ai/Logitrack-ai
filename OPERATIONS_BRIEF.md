# LogiTrack AI | Outbound Logistics Operations Brief
As of 2026-10-24 | DEMONSTRATION: synthetic data only

## Operating KPIs
- Inventory: 3,343 units across 36 SKU/depot records.
- Critical SKUs below 5 days cover: 4.
- Aging stock (oldest age >= 90 days): 15 records, indicative value INR 1,459,850.
- On-time delivery: 63.1% of delivered shipments.
- Overdue in-transit shipments: 12.
- Average truck turnaround: 177.0 min (demo target: 180 min).
- Unit-based damage rate: 0.19% of dispatched units.
- Overdue unpaid invoices: 10 (INR 1,111,000).

## Priority actions (human review required)
| Priority | Issue | Evidence | Recommended next step |
|---|---|---|---|
| P0 | Critical SKU PAINT-003 at Surat Depot | 0.75 days of cover (3 units on hand) | Validate open orders and actual demand; request replenishment or approved stock transfer. |
| P0 | Critical SKU PAINT-008 at Nagpur Depot | 1.0 days of cover (12 units on hand) | Validate open orders and actual demand; request replenishment or approved stock transfer. |
| P1 | Shipment SHP-0017 overdue | 5 days overdue; Western Freight | Verify transporter status, confirm revised ETA, and notify the receiving depot. |
| P1 | Shipment SHP-0018 overdue | 15 days overdue; Marigold Logistics | Verify transporter status, confirm revised ETA, and notify the receiving depot. |
| P1 | Shipment SHP-0034 overdue | 8 days overdue; Marigold Logistics | Verify transporter status, confirm revised ETA, and notify the receiving depot. |
| P1 | Shipment SHP-0036 overdue | 5 days overdue; Coastal Carriers | Verify transporter status, confirm revised ETA, and notify the receiving depot. |
| P1 | Shipment SHP-0045 overdue | 8 days overdue; Western Freight | Verify transporter status, confirm revised ETA, and notify the receiving depot. |
| P1 | Shipment SHP-0051 overdue | 6 days overdue; Blue Route Transport | Verify transporter status, confirm revised ETA, and notify the receiving depot. |
| P1 | Shipment SHP-0054 overdue | 14 days overdue; Marigold Logistics | Verify transporter status, confirm revised ETA, and notify the receiving depot. |
| P1 | Shipment SHP-0068 overdue | 4 days overdue; Coastal Carriers | Verify transporter status, confirm revised ETA, and notify the receiving depot. |
| P1 | Shipment SHP-0072 overdue | 24 days overdue; Coastal Carriers | Verify transporter status, confirm revised ETA, and notify the receiving depot. |
| P1 | Shipment SHP-0081 overdue | 3 days overdue; Western Freight | Verify transporter status, confirm revised ETA, and notify the receiving depot. |

## Method and limitations
- Stock cover = on-hand units / average daily demand. Zero demand is not classified as stockout risk.
- Aging definition uses oldest-stock age >= 90 days; bucket value is an illustrative upper bound, not a batch-accurate inventory valuation.
- On-time rate denominator includes only delivered shipments; overdue pending deliveries are tracked separately.
- Truck turnaround uses exit timestamp minus entry timestamp.
- Unit damage rate = damaged units / dispatched units. It is not volume-damage-per-MT.
- No SAP, 3PL, transporter, invoice payment or messaging integrations exist in this demo.
- Data are simulated and are not connected with Asian Paints or any employer.
