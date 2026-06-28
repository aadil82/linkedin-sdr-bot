"""
LinkedIn SDR Agent — Live Dashboard

A Streamlit dashboard to view qualified leads, scoring breakdowns,
upload CSV files, and download reports.

Usage:
    streamlit run dashboard.py
"""

import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

# Add project root to sys.path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import TECHNOLOGY_KEYWORDS
from src.lead_engine import (
    LeadHistory,
    generate_excel_report,
    generate_pdf_report,
    process_input_csv,
    score_lead,
)

DATA_DIR = "data"
INPUT_DIR = f"{DATA_DIR}/input"
OUTPUT_DIR = f"{DATA_DIR}/output"
HISTORY_DIR = f"{DATA_DIR}/history"

st.set_page_config(
    page_title="LinkedIn SDR Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════

st.sidebar.title("🎯 LinkedIn SDR Agent")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Live Dashboard", "📁 Upload & Process", "📈 Reports", "📋 History"],
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Today: {date.today().isoformat()}")

if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════


@st.cache_data(ttl=60)
def _load_history() -> Dict[str, Any]:
    h = LeadHistory()
    return {"contacts": h._data["contacts"], "companies": h._data["companies"]}


@st.cache_data(ttl=60)
def _get_todays_report_paths() -> Dict[str, str]:
    today = date.today().isoformat()
    return {
        "xlsx": os.path.join(OUTPUT_DIR, f"leads_{today}.xlsx"),
        "pdf": os.path.join(OUTPUT_DIR, f"leads_{today}.pdf"),
        "txt": os.path.join(OUTPUT_DIR, f"daily_summary_{today}.txt"),
    }


def _list_reports() -> List[str]:
    """List all available report files sorted by date descending."""
    files = []
    if os.path.isdir(OUTPUT_DIR):
        for f in sorted(os.listdir(OUTPUT_DIR), reverse=True):
            if f.endswith((".xlsx", ".pdf", ".txt", ".eml")) and f != ".gitkeep":
                files.append(f)
    return files


def _list_eml_files() -> Dict[str, List[str]]:
    """List .eml files grouped by date."""
    today = date.today().isoformat()
    eml_dir = os.path.join(OUTPUT_DIR, f"emails_{today}")
    files = []
    if os.path.isdir(eml_dir):
        for f in sorted(os.listdir(eml_dir)):
            if f.endswith(".eml"):
                files.append(os.path.join(eml_dir, f))

    digest = os.path.join(OUTPUT_DIR, f"approval_digest_{today}.eml")
    digest_exists = os.path.exists(digest)

    return {
        "digest": digest if digest_exists else None,
        "leads": files,
    }


def _score_color(score: float) -> str:
    if score >= 85:
        return "🟢"
    if score >= 75:
        return "🟡"
    return "🟠"


# ═══════════════════════════════════════════════════════════════
#  TAB 1: LIVE DASHBOARD
# ═══════════════════════════════════════════════════════════════

if page == "📊 Live Dashboard":
    st.title("📊 Live Lead Dashboard")

    reports = _get_todays_report_paths()
    xlsx_path = reports["xlsx"]

    if os.path.exists(xlsx_path):
        df = pd.read_excel(xlsx_path)
        # Rename columns for display
        df_display = df.rename(columns={
            "Lead Score": "Score",
            "Priority": "Priority",
            "Company Name": "Company",
            "Contact Name": "Contact",
            "Job Title": "Role",
            "Industry": "Industry",
            "Country": "Country",
            "Technology Stack": "Tech",
            "Customer Status": "Status",
            "Approval Status": "Approval",
        })

        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Qualified Leads", len(df_display))
        with col2:
            hot = len(df_display[df_display["Score"] >= 85])
            st.metric("🔥 HOT Leads", hot)
        with col3:
            warm = len(df_display[(df_display["Score"] >= 75) & (df_display["Score"] < 85)])
            st.metric("⭐ WARM Leads", warm)
        with col4:
            avg = round(df_display["Score"].mean(), 1)
            st.metric("📈 Avg Score", avg)

        st.markdown("---")

        # Score distribution chart
        st.subheader("Score Distribution")
        score_colors = ["#ff4b4b" if s >= 85 else "#ffa726" if s >= 75 else "#66bb6a" for s in df_display["Score"]]
        chart_data = df_display[["Score", "Company"]].sort_values("Score", ascending=False)
        st.bar_chart(chart_data.set_index("Company")["Score"])

        st.markdown("---")

        # Lead table with filters
        st.subheader("Qualified Leads")

        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            min_score_filter = st.slider("Minimum Score", 0, 100, 70)
        with filter_col2:
            industries = ["All"] + sorted(df_display["Industry"].dropna().unique().tolist())
            industry_filter = st.selectbox("Industry", industries)

        filtered = df_display[df_display["Score"] >= min_score_filter]
        if industry_filter != "All":
            filtered = filtered[filtered["Industry"] == industry_filter]

        # Display as styled table
        display_cols = ["Score", "Company", "Contact", "Role", "Tech", "Industry", "Country", "Status", "Approval"]
        available_cols = [c for c in display_cols if c in filtered.columns]
        st.dataframe(
            filtered[available_cols].style.map(
                lambda v: "color: red; font-weight: bold" if isinstance(v, (int, float)) and v >= 85 else "",
                subset=["Score"],
            ),
            use_container_width=True,
            height=400,
        )

        # Email drafts expander
        st.markdown("---")
        with st.expander("📧 View Email Drafts", expanded=False):
            for _, row in df.iterrows():
                email = row.get("Email Draft", "")
                if email and str(email).strip():
                    st.markdown(f"**{row.get('Company Name', '?')}** → {row.get('Contact Name', '?')}")
                    st.text(email[:500] + ("..." if len(str(email)) > 500 else ""))
                    st.markdown("---")

        # Download buttons — reports
        st.markdown("---")
        st.subheader("Download Reports")
        dcol1, dcol2, dcol3 = st.columns(3)
        with dcol1:
            with open(xlsx_path, "rb") as f:
                st.download_button("📥 Download Excel", f, file_name=os.path.basename(xlsx_path), use_container_width=True)
        with dcol2:
            pdf_path = reports["pdf"]
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    st.download_button("📥 Download PDF", f, file_name=os.path.basename(pdf_path), use_container_width=True)
        with dcol3:
            txt_path = reports["txt"]
            if os.path.exists(txt_path):
                with open(txt_path, "rb") as f:
                    st.download_button("📥 Download Summary", f, file_name=os.path.basename(txt_path), use_container_width=True)

        # EML download buttons
        eml_files = _list_eml_files()
        if eml_files["digest"] or eml_files["leads"]:
            st.markdown("---")
            st.subheader("📧 Email Files (Outlook)")
            ecol1, ecol2 = st.columns(2)
            with ecol1:
                if eml_files["digest"]:
                    digest_path = eml_files["digest"]
                    with open(digest_path, "rb") as f:
                        st.download_button(
                            "📥 Approval Digest (.eml)", f,
                            file_name=os.path.basename(digest_path),
                            use_container_width=True,
                            help="Open in Outlook to review and approve leads",
                        )
            with ecol2:
                if eml_files["leads"]:
                    st.caption(f"{len(eml_files['leads'])} lead .eml files available in Reports tab")
            with st.expander("View individual lead .eml files", expanded=False):
                for eml_path in eml_files["leads"]:
                    with open(eml_path, "rb") as f:
                        st.download_button(
                            f"📧 {os.path.basename(eml_path)}", f,
                            file_name=os.path.basename(eml_path),
                            use_container_width=True,
                        )

    else:
        st.info("No leads processed today yet. Go to **Upload & Process** to start.")

        # Show sample data if available
        st.markdown("### Quick Start")
        st.markdown(
            "1. Collect LinkedIn data and save as CSV\n"
            "2. Upload it via **Upload & Process** tab\n"
            "3. Review qualified leads here\n"
            "4. Download reports"
        )

# ═══════════════════════════════════════════════════════════════
#  TAB 2: UPLOAD & PROCESS
# ═══════════════════════════════════════════════════════════════

elif page == "📁 Upload & Process":
    st.title("📁 Upload Leads & Run Engine")

    st.markdown(
        "Upload a CSV file with LinkedIn lead data. "
        "The engine will score, qualify, and generate email drafts automatically."
    )

    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="Use the template at templates/leads_input_template.csv as a reference",
    )

    if uploaded_file is not None:
        # Save uploaded file
        os.makedirs(INPUT_DIR, exist_ok=True)
        today = date.today().isoformat()
        input_path = os.path.join(INPUT_DIR, f"leads_{today}.csv")

        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"Saved: {input_path}")

        min_score = st.slider("Minimum Score Threshold", 0, 100, 70, 5)
        run_col1, run_col2 = st.columns([1, 3])
        with run_col1:
            if st.button("🚀 Run Lead Engine", type="primary", use_container_width=True):
                with st.spinner("Scoring leads, generating emails, and building reports..."):
                    try:
                        qualified, rejected, history = process_input_csv(
                            input_path, min_score=float(min_score)
                        )
                        st.success(f"Done! {len(qualified)} leads qualified, {len(rejected)} rejected.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error: {e}")
        with run_col2:
            st.caption("This will score each lead, generate email drafts, and create Excel/PDF/text reports.")

    st.markdown("---")
    st.markdown("### CSV Format Requirements")
    st.code(
        "Required columns:\n"
        "  Company Name, Contact Name, Job Title, LinkedIn Profile,\n"
        "  Industry, Company Size, Country, City\n\n"
        "Optional columns:\n"
        "  Company LinkedIn, Company Website, Technology Stack,\n"
        "  Job Posting URL, Job Posted Date, notes",
        language="text",
    )

# ═══════════════════════════════════════════════════════════════
#  TAB 3: REPORTS
# ═══════════════════════════════════════════════════════════════

elif page == "📈 Reports":
    st.title("📈 Historical Reports")

    reports = _list_reports()
    if reports:
        st.markdown(f"Found **{len(reports)}** report files.")

        for report in reports:
            fp = os.path.join(OUTPUT_DIR, report)
            size_kb = round(os.path.getsize(fp) / 1024, 1)
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(report)
            with col2:
                st.caption(f"{size_kb} KB")
            with col3:
                with open(fp, "rb") as f:
                    st.download_button("Download", f, file_name=report, key=report, use_container_width=True)
            st.divider()
    else:
        st.info("No reports found. Process some leads first.")

# ═══════════════════════════════════════════════════════════════
#  TAB 4: HISTORY
# ═══════════════════════════════════════════════════════════════

elif page == "📋 History":
    st.title("📋 Lead History (CRM)")

    # Summary stats
    history_path = os.path.join(HISTORY_DIR, "leads_history.json")
    if os.path.exists(history_path):
        with open(history_path) as f:
            data = json.load(f)

        contacts = data.get("contacts", {})
        companies = data.get("companies", {})

        col1, col2 = st.columns(2)
        with col1:
            st.metric("👤 Unique Contacts", len(contacts))
        with col2:
            st.metric("🏢 Unique Companies", len(companies))

        if contacts:
            st.subheader("Contact History")
            contact_rows = []
            for key, val in contacts.items():
                name, comp = key.split("|", 1)
                contact_rows.append({
                    "Name": val.get("name", name),
                    "Company": val.get("company", comp),
                    "Last Contacted": val.get("last_contacted", "")[:19],
                })
            contact_df = pd.DataFrame(contact_rows)
            st.dataframe(contact_df, use_container_width=True)

        if companies:
            st.subheader("Company History")
            company_rows = []
            for key, val in companies.items():
                company_rows.append({
                    "Company": val.get("company", key),
                    "Last Contacted": val.get("last_contacted", "")[:19],
                })
            company_df = pd.DataFrame(company_rows)
            st.dataframe(company_df, use_container_width=True)

        if st.button("🗑️ Clear History", type="secondary"):
            os.remove(history_path)
            st.cache_data.clear()
            st.success("History cleared!")
            st.rerun()
    else:
        st.info("No lead history yet. Process some leads first.")
        st.markdown(
            "The history file (`data/history/leads_history.json`) is auto-created "
            "when you run the lead engine."
        )
