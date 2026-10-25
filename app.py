"""Streamlit dashboard for LogiTrack AI | educational portfolio project.

Run with: streamlit run app.py
All default data is simulated and resettable. No operational systems are changed.
"""
from __future__ import annotations

import csv
from datetime import date
import io
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from engine import assess, load_csv, offline_answer
from agent import llm_answer, markdown_report

ROOT = Path(__file__).resolve().parent
DEFAULT_DATE = date(2026, 10, 24)
DATA_CONFIG = {
    "inventory": {"file": "inventory.csv", "columns": ["sku", "depot", "on_hand_units", "avg_daily_demand", "oldest_stock_days", "damaged_units", "unit_value_inr", "critical_sku"]},
    "dispatches": {"file": "dispatches.csv", "columns": ["shipment_id", "depot", "transporter", "planned_delivery_date", "actual_delivery_date", "qty_dispatched", "qty_damaged", "shipment_weight_mt", "truck_in_time", "truck_out_time"]},
    "invoices": {"file": "invoices.csv", "columns": ["invoice_id", "vendor", "po_number", "amount_inr", "due_date", "payment_status"]},
}

st.set_page_config(page_title="LogiTrack AI | Outbound Logistics Agent", page_icon="📦", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
.block-container {padding-top:1.6rem; max-width: 1340px;}
.small-note {font-size:.87rem;color:#64748b;}
.hero {padding:.65rem 0 1.3rem 0;}
.hero h1 {font-weight:750;letter-spacing:-.03em;margin-bottom:.2rem;}
.hero p {color:#64748b;margin-top:.25rem;}
</style>""", unsafe_allow_html=True)


def parse_uploaded(upload, category):
    if upload is None:
        return load_csv(ROOT / "data" / DATA_CONFIG[category]["file"])
    content = upload.getvalue().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    missing = sorted(set(DATA_CONFIG[category]["columns"]) - set(reader.fieldnames or []))
    if missing:
        raise ValueError(f"{category} upload is missing required columns: {', '.join(missing)}")
    return list(reader)


def as_frame(records):
    return pd.DataFrame.from_records(records)


def csv_bytes(records):
    if not records:
        return b""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=records[0].keys(), extrasaction="ignore")
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue().encode("utf-8")


def money(value):
    return f"₹{value:,.0f}"


with st.sidebar:
    st.title("LogiTrack AI")
    st.caption("Decision support • portfolio demonstration")
    selected_date = st.date_input("Analysis as of", value=DEFAULT_DATE, help="Synthetic sample records are dated around 24 October 2026. Keep this date for the demo, or choose your own when uploading CSVs.")
    st.subheader("Data sources")
    st.caption("Optional: upload CSVs with the same columns as those in the sample files. Uploaded data stays in this session; no data is sent to a model unless you enable LLM mode.")
    uploaded = {}
    for category, config in DATA_CONFIG.items():
        uploaded[category] = st.file_uploader(f"{category.title()} CSV", type="csv", key=f"up_{category}")
    st.divider()
    enable_llm = st.toggle("Use an LLM for answers (optional)", value=False, help="Without an API key the app works in free, explainable offline mode.")
    model_name = "gpt-4.1-mini"
    if enable_llm:
        model_name = st.text_input("OpenAI model", value="gpt-4.1-mini")
        if not os.getenv("OPENAI_API_KEY"):
            st.warning("Set OPENAI_API_KEY in your environment to enable model-generated explanations. Do not upload API keys to GitHub.")
    st.caption("No purchase orders, payments, or transporter messages are executed.")

st.markdown("""<div class='hero'>
<h1>📦 LogiTrack AI</h1>
<p>Outbound logistics control tower · Inventory health, dispatch performance, payment exceptions, and recommended next actions</p>
</div>""", unsafe_allow_html=True)
st.info("**Simulated portfolio data — not Asian Paints data.** The dashboard is an educational prototype; thresholds and recommendations are illustrative and need human verification.", icon="ℹ️")

try:
    inputs = {k: parse_uploaded(v, k) for k, v in uploaded.items()}
    report = assess(inputs["inventory"], inputs["dispatches"], inputs["invoices"], selected_date)
except (ValueError, UnicodeError, KeyError) as error:
    st.error(f"Data validation failed: {error}")
    st.stop()

inv, dis, pay = report["inventory"], report["dispatch"], report["invoices"]
kpi_cols = st.columns(5)
kpi_cols[0].metric("Critical SKUs at risk", len(inv["critical_stockout_risk"]), help="Critical SKUs with less than 5 days of stock cover")
kpi_cols[1].metric("Open overdue shipments", len(dis["overdue_shipments"]))
kpi_cols[2].metric("On-time deliveries", "N/A" if dis["on_time_delivery_pct"] is None else f'{dis["on_time_delivery_pct"]}%')
kpi_cols[3].metric("Avg truck turnaround", "N/A" if dis["avg_truck_turnaround_minutes"] is None else f'{dis["avg_truck_turnaround_minutes"]} min')
kpi_cols[4].metric("Overdue supplier invoices", len(pay["overdue_invoices"]), help=money(pay["overdue_amount_inr"]))

overview, inventory_tab, dispatch_tab, payments_tab, chat_tab, about_tab = st.tabs(["Command center", "Inventory", "Dispatches", "Vendor payments", "Ask the agent", "Methodology"])

with overview:
    st.subheader("Priority action queue")
    st.caption("Proposed actions are sorted P0 → P1 → P2. Nothing is automatically dispatched, purchased, or paid.")
    priorities = ["P0", "P1", "P2"]
    selected_priorities = st.multiselect("Show priorities", priorities, default=priorities)
    selected_actions = [a for a in report["actions"] if a["priority"] in selected_priorities]
    if selected_actions:
        st.dataframe(as_frame(selected_actions), use_container_width=True, hide_index=True)
        st.download_button("Download action queue (CSV)", csv_bytes(selected_actions), file_name="logitrack_action_queue.csv", mime="text/csv")
    else:
        st.success("No action items in this filter.")
    st.subheader("Daily operations brief")
    brief = markdown_report(report)
    st.download_button("Download operations brief (.md)", brief.encode("utf-8"), file_name="logitrack_operations_brief.md", mime="text/markdown")
    st.download_button("Download analysis JSON", json.dumps(report, indent=2).encode("utf-8"), file_name="logitrack_evidence.json", mime="application/json")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Exception breakdown**")
        st.bar_chart(pd.Series({"Critical stock": len(inv["critical_stockout_risk"]), "Aging stock": len(inv["old_stock"]), "Overdue dispatch": len(dis["overdue_shipments"]), "Overdue invoices": len(pay["overdue_invoices"])}))
    with c2:
        st.markdown("**Operations snapshot**")
        st.write(f"On-hand inventory: **{inv['total_units']:,} units**")
        st.write(f"Old-stock indicative valuation: **{money(inv['old_stock_value_inr'])}**")
        st.write(f"Damage rate: **{dis['damage_rate_pct'] if dis['damage_rate_pct'] is not None else 'N/A'}% of dispatched units**")
        st.write(f"Unpaid supplier invoices: **{money(pay['unpaid_amount_inr'])}**")
        st.write(f"Overdue invoice amount: **{money(pay['overdue_amount_inr'])}**")

with inventory_tab:
    st.subheader("Critical SKU stockout risk")
    st.caption("Days of cover = units on hand ÷ average daily demand. Critical SKUs below 5 days of cover are flagged.")
    if inv["critical_stockout_risk"]:
        st.dataframe(as_frame(inv["critical_stockout_risk"]), use_container_width=True, hide_index=True)
    else:
        st.success("No critical SKU below the sample threshold.")
    st.subheader("Old stock / aging inventory")
    st.caption("Records with oldest unit age ≥ 90 days are shown. Indicative value assumes all on-hand units are old; this is not batch-level accounting.")
    if inv["old_stock"]:
        st.dataframe(as_frame(inv["old_stock"]), use_container_width=True, hide_index=True)
    st.download_button("Download critical stockout risks CSV", csv_bytes(inv["critical_stockout_risk"]), file_name="critical_stockout_risks.csv", mime="text/csv")
    st.download_button("Download aging stock CSV", csv_bytes(inv["old_stock"]), file_name="aging_stock.csv", mime="text/csv")
    with st.expander("Show input inventory records"):
        st.dataframe(as_frame(inputs["inventory"]), use_container_width=True, hide_index=True)

with dispatch_tab:
    st.subheader("Overdue in-transit shipments")
    if dis["overdue_shipments"]:
        st.dataframe(as_frame(dis["overdue_shipments"]), use_container_width=True, hide_index=True)
        st.download_button("Download overdue shipments CSV", csv_bytes(dis["overdue_shipments"]), file_name="overdue_shipments.csv", mime="text/csv")
    else:
        st.success("No open shipments past their planned delivery date.")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Truck turnaround (average)", "N/A" if dis["avg_truck_turnaround_minutes"] is None else f'{dis["avg_truck_turnaround_minutes"]} minutes')
        st.caption(f'Illustrative target: {dis["truck_tat_target_minutes"]} minutes')
    with c2:
        st.metric("Shipment damage, unit basis", "N/A" if dis["damage_rate_pct"] is None else f'{dis["damage_rate_pct"]}%')
        st.caption("Not the same as weight-based damage per metric ton")
    if dis["overdue_shipments"]:
        vendor_counts = as_frame(dis["overdue_shipments"]).groupby("transporter").size().sort_values(ascending=False)
        st.markdown("**Overdue shipments by transporter**")
        st.bar_chart(vendor_counts)
    with st.expander("Show input dispatch records"):
        st.dataframe(as_frame(inputs["dispatches"]), use_container_width=True, hide_index=True)

with payments_tab:
    st.subheader("Overdue unpaid vendor invoices")
    if pay["overdue_invoices"]:
        st.dataframe(as_frame(pay["overdue_invoices"]), use_container_width=True, hide_index=True)
        st.download_button("Download overdue invoices CSV", csv_bytes(pay["overdue_invoices"]), file_name="overdue_invoices.csv", mime="text/csv")
        pay_by_vendor = as_frame(pay["overdue_invoices"]).groupby("vendor")["amount_inr"].sum().sort_values(ascending=False)
        st.markdown("**Overdue amount by vendor (INR)**")
        st.bar_chart(pay_by_vendor)
    else:
        st.success("No unpaid invoice past the due date.")
    with st.expander("Show input invoice records"):
        st.dataframe(as_frame(inputs["invoices"]), use_container_width=True, hide_index=True)

with chat_tab:
    st.subheader("Ask LogiTrack")
    st.caption("Offline mode chooses relevant analysis tools by question and explains the result. Optional LLM mode uses verified analysis evidence; it never directly modifies business records.")
    examples = ["What are today's highest priority issues?", "Which SKUs have stockout risk?", "How many shipments are overdue and which transporters?", "What's our truck turnaround time?", "How much is overdue to vendors?", "What old stock requires attention?"]
    example = st.selectbox("Example question", examples)
    question = st.text_input("Your operations question", value=example)
    if st.button("Analyze question", type="primary"):
        with st.spinner("Inspecting available analytical tools..."):
            try:
                if enable_llm:
                    if not os.getenv("OPENAI_API_KEY"):
                        st.warning("LLM mode needs OPENAI_API_KEY. Using offline reasoning instead.")
                        answer = offline_answer(question, report)
                    else:
                        answer = llm_answer(question, report, model_name)
                else:
                    answer = offline_answer(question, report)
                st.session_state["latest_answer"] = (question, answer)
            except Exception as err:
                st.error(f"LLM request failed: {err}. You can turn off LLM mode for a free offline answer.")
    if "latest_answer" in st.session_state:
        previous_q, answer = st.session_state["latest_answer"]
        st.markdown(f"**Question:** {previous_q}")
        st.markdown(answer)

with about_tab:
    st.subheader("What the portfolio project demonstrates")
    st.markdown("""This is a **decision-support prototype** inspired by outbound warehouse and transport operations. It demonstrates clean KPI logic, exception identification, transparent prioritization, report generation, and a tool-routing assistant.

**Features:** Stock cover and critical SKUs, old/aging stock, delivery timeliness, pending overdue shipments, truck turnaround, damaged units, vendor invoice aging, P0/P1/P2 action ranking.

**Limits:** No SAP/ERP, 3PL, insurer, email, or transporter integration; no inventory transfers, payment approvals, orders, or other transactions; no verified forecasting model. All example data is synthetic.

**Human review required:** Operational decisions, financial transactions, quality approvals, risk escalations, and vendor communications.

**Method:** Use the README and `tests/` for formulas, data dictionary, reproducibility, and tests. This is an independent educational project and is not affiliated with Asian Paints.""")
