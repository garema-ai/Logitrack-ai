# LogiTrack AI — Outbound Logistics Operations Agent

**An independent supply-chain analytics portfolio project by Garema Dogra**  
*Inventory health • Dispatch tracking • Vendor payments • Priority actions*

> **DEMO / SYNTHETIC DATA ONLY.** This project is inspired by common outbound logistics responsibilities. It is **not affiliated with Asian Paints** and does not connect to any company's systems. It never releases purchase orders, pays bills, or contacts transporters.

## View the demo
App link : https://logitrack-ai-garema.streamlit.app/

**No-code browser preview:** Open [`docs/index.html`](docs/index.html) in a browser. After publishing to GitHub, enable **GitHub Pages** for a public demo link (see below). The preview is read-only and uses the packaged sample analysis.

**Interactive Python app:** Run the Streamlit dashboard to upload CSVs, inspect dynamic KPIs, ask the agent questions, and download audit-friendly reports.

## What problem does it solve?

Outbound logistics teams often review stock reports, transporter updates, delivery performance and vendor payment trackers separately. This prototype combines them into **one exception-based daily operating brief**, flags urgent risks, and proposes next steps for a human reviewer.

### Capabilities

| Operational task | Prototype implementation | Business relevance |
|---|---|---|
| Critical SKU compliance | Flags critical SKUs with less than 5 days of cover | Stockout prevention |
| STO / old stock review | Flags SKUs with oldest-stock age ≥ 90 days | Review stock liquidation or redistribution |
| Dispatch monitoring | Flags pending shipments past the expected delivery date | Escalate delivery risks |
| Truck turnaround | Uses gate-in and gate-out timestamps | Identify loading/yard bottlenecks |
| Dispatch quality | Calculates unit-based damage rate | Track damages (not a certified damage-per-MT measure) |
| Vendor payment follow-up | Finds unpaid invoices past due | Support invoice follow-up |
| Operations reporting | Exports an action queue and Markdown brief | Daily operations and follow-up meetings |
| Agent-style interaction | Routes questions to analytical tools; optional LLM explanations | Faster interpretation of structured evidence |

## Example outputs (as-of 24 October 2026)

The sample generator seeds **36 inventory rows, 84 shipments, and 28 invoices**. Results can change if you regenerate with a different seed or alter the rules. All figures are simulated.

- 4 critical SKU records below 5 days of cover
- 12 overdue, not-yet-delivered shipments
- 10 overdue unpaid vendor invoices
- 177.0-minute average truck turnaround (illustrative threshold: 180 minutes)

The interactive dashboard and `OPERATIONS_BRIEF.md` show the detailed evidence and suggested actions.

## Quick start — local dashboard

Python **3.10+** recommended.

```bash
# From the downloaded repository folder
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit, typically `http://localhost:8501`.

The default demo works **without an API key**. Optional CSV upload uses the data dictionary below.

## Command-line analysis (no third-party packages required)

```bash
python agent.py --ask "Which shipments are overdue?"
python agent.py --ask "Which SKUs risk stocking out?"
python agent.py --write-report OPERATIONS_BRIEF.md --json-output data/sample_analysis.json
```

### Optional LLM explanation mode

To generate natural-language explanations grounded in the computed evidence, install requirements and provide your own OpenAI API key as an environment variable:

```bash
# macOS/Linux example (never commit real values):
export OPENAI_API_KEY="YOUR_PRIVATE_KEY"
python agent.py --mode llm --ask "Summarize the urgent logistics risks"
```

Or enable LLM mode in the Streamlit sidebar after setting `OPENAI_API_KEY`. `OPENAI_MODEL` can be customized. This mode **sends the selected simulated evidence and question to the API**; do not use confidential company data without authorization.

**Architecture note:** KPI calculations and prioritization are deterministic, auditable Python rules. In offline mode, the agent uses transparent keyword-based tool routing. Optional LLM mode provides language generation over the selected evidence; it does not autonomously call external business systems. This is a prototype decision-support agent, not an autonomous supply-chain execution system.

## Data dictionary / CSV input schema

Three files are included in `/data`. Upload replacements using the same required headers; additional columns are permitted.

| File | Required columns |
|---|---|
| `inventory.csv` | `sku`, `depot`, `on_hand_units`, `avg_daily_demand`, `oldest_stock_days`, `damaged_units`, `unit_value_inr`, `critical_sku` |
| `dispatches.csv` | `shipment_id`, `depot`, `transporter`, `planned_delivery_date`, `actual_delivery_date`, `qty_dispatched`, `qty_damaged`, `shipment_weight_mt`, `truck_in_time`, `truck_out_time` |
| `invoices.csv` | `invoice_id`, `vendor`, `po_number`, `amount_inr`, `due_date`, `payment_status` |

Dates must use `YYYY-MM-DD`, timestamps `YYYY-MM-DDTHH:MM`, and blank `actual_delivery_date` means no confirmed delivery by the analysis date. Critical flags accept `Yes`, `true`, and `1`. Currency is assumed INR. Production use would require stronger validation, data stewardship, and integration controls.

## Calculation methodology

- **Days of stock cover** = `on_hand_units / avg_daily_demand`; zero demand is excluded from the stockout-risk rule.
- **Critical stock risk** = critical SKU with **< 5** days of cover, with P0 assigned below 2 days.
- **Aging stock** = `oldest_stock_days >= 90` (this does **not** prove every unit is old). The illustrative value `on_hand * unit_value` is an upper-bound proxy, not batch-accurate valuation.
- **Overdue dispatch** = planned date earlier than the analysis date and no confirmed delivery on/before the analysis date.
- **On-time delivery %** = on-time deliveries / confirmed deliveries × 100; pending shipments tracked separately.
- **Truck turnaround** = `truck_out_time - truck_in_time`, averaged across records with both times.
- **Unit damage rate %** = damaged units / dispatched units × 100. **Not** a substitute for volume-damaged per metric ton.
- **Unpaid invoice overdue** = payment status not paid or settled, due date before analysis date.
- **Action priorities** = illustrative P0/P1/P2 rules; action owners and recommendations are proposals, not system commands.

## Project structure

```text
logitrack-ai/
├── app.py                 # Streamlit dashboard: dynamic CSV upload and data explorer
├── engine.py              # Auditable KPI calculations, exception rules, priorities
├── agent.py               # Offline analytical question routing + optional LLM narrative
├── make_data.py           # Reproducible simulated CSV records
├── make_preview.py        # Build standalone GitHub Pages preview
├── docs/index.html        # No-server, read-only demo for recruiters
├── data/
│   ├── inventory.csv
│   ├── dispatches.csv
│   ├── invoices.csv
│   └── sample_analysis.json
├── tests/test_engine.py
├── OPERATIONS_BRIEF.md
├── requirements.txt
├── requirements-dev.txt
├── LICENSE
└── README.md
```

## Tests

```bash
pip install pytest
pytest -q
python -m py_compile engine.py agent.py app.py
```

The core analysis engine has automated tests for stockout detection, past-due shipments, vendor invoices, route selection, and invalid data. `app.py` syntax is checked, but its live Streamlit interface requires Streamlit installed to run.

## Publish to GitHub

1. Download and **unzip** the project archive.
2. Create a new repository at <https://github.com/new> called **`logitrack-ai`**, preferably **Public** for your portfolio. Do not initialize it with a separate README because one is included.
3. Easiest: use **GitHub Desktop → Add existing local repository → Publish repository**. Alternatively, with Git installed in the extracted project folder:

   ```bash
   git init
   git add .
   git commit -m "Build outbound logistics analytics agent portfolio"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/logitrack-ai.git
   git push -u origin main
   ```

   Create the empty repository first and replace `YOUR_USERNAME` with your GitHub username. GitHub authentication is required for pushing.
4. For a **live, zero-cost static demo**, in the repo go to **Settings → Pages → Build and deployment → Deploy from a branch → main → /docs → Save**. Your GitHub Pages URL will typically be `https://YOUR_USERNAME.github.io/logitrack-ai/`. Allow GitHub to finish publishing before opening it.
5. For the dynamic Python dashboard, run it locally or deploy `app.py` separately on a compatible Streamlit hosting provider. GitHub Pages itself **cannot execute Python or Streamlit**.

**Security:** Never upload API keys, internal employer reports, customer details, bank information, or confidential inventory records to a public repo. The sample CSVs here are entirely generated data.

## What this project does *not* claim

No experience with SAP, warehouse automation, actual 3PL integrations, company logistics systems, insurance workflows, or live decision execution is implied by this prototype. The project demonstrates analytical problem-solving and prototype development, not a production deployment.

### Portfolio description for a resume (after you test your published version)

**LogiTrack AI | Outbound Logistics Operations Agent (Python, Streamlit)** — Developed an independent analytics prototype using simulated inventory, delivery, and vendor invoice data; built auditable KPI calculations, exception detection, prioritized action recommendations, CSV uploads, and a shareable GitHub Pages demonstration.

---
*Created as an independent educational project by Garema Dogra, 2026.*
