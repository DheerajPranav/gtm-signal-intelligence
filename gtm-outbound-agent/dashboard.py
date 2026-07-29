"""Streamlit dashboard for batch runs, cost tracking, and evals."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.gtm_outbound.batch import BatchRunner


st.set_page_config(
    page_title="GTM Outbound Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 GTM Outbound Agent Dashboard")

# Sidebar navigation
page = st.sidebar.radio(
    "Select View",
    ["Home", "Live Run", "Company Drill-Down", "Cost Dashboard", "Eval Dashboard"],
)

runner = BatchRunner()

# ============================================================================
# HOME: Run History Table + New Batch Button
# ============================================================================

if page == "Home":
    st.header("Run History")

    batches = runner.list_batches()

    if batches:
        # Convert to DataFrame for display
        batch_data = []
        for batch in batches[:20]:  # Show last 20
            batch_data.append({
                "Run ID": batch.run_id,
                "Created": batch.created_at[:10],  # Date only
                "Companies": batch.total_companies,
                "Completed": batch.completed,
                "Failed": batch.failed,
                "Status": batch.status,
                "Cost": f"${batch.total_cost:.2f}",
                "Time (s)": f"{batch.elapsed_seconds:.1f}",
            })

        df = pd.DataFrame(batch_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        total_runs = len(batches)
        completed_runs = sum(1 for b in batches if b.status == "completed")
        total_cost = sum(b.total_cost for b in batches)
        total_companies = sum(b.total_companies for b in batches)

        col1.metric("Total Runs", total_runs)
        col2.metric("Completed", completed_runs)
        col3.metric("Total Cost", f"${total_cost:.2f}")
        col4.metric("Total Companies", total_companies)

    else:
        st.info("No batch runs yet. Create one to get started!")

    st.divider()
    st.subheader("Run a New Batch")

    col1, col2 = st.columns(2)

    with col1:
        input_method = st.radio("Input Method", ["CSV File", "Manual Domains"])

    if input_method == "CSV File":
        csv_file = st.file_uploader("Upload CSV with 'domain' column", type=["csv"])
        if csv_file and st.button("📤 Run Batch from CSV"):
            # Read CSV
            df = pd.read_csv(csv_file)
            if "domain" not in df.columns:
                st.error("CSV must have a 'domain' column")
            else:
                domains = df["domain"].tolist()
                run_id = runner.create_batch(domains)
                st.success(f"✓ Batch {run_id} created with {len(domains)} companies")
                st.info(f"Run ID: `{run_id}` (save this to resume later)")

    else:
        domains_text = st.text_area("Enter domains (one per line)", height=150)
        if domains_text and st.button("▶️ Run Batch from Domains"):
            domains = [d.strip() for d in domains_text.split("\n") if d.strip()]
            run_id = runner.create_batch(domains)
            st.success(f"✓ Batch {run_id} created with {len(domains)} companies")
            st.info(f"Run ID: `{run_id}` (save this to resume later)")

# ============================================================================
# LIVE RUN: Progress Bars + Per-Agent Status
# ============================================================================

elif page == "Live Run":
    st.header("Live Run Monitor")

    col1, col2 = st.columns([2, 1])

    with col1:
        run_id = st.text_input("Enter Run ID to monitor", placeholder="e.g., abc123")

    if run_id:
        batch = runner.load_batch(run_id)

        if not batch:
            st.error(f"Run {run_id} not found")
        else:
            # Load company results
            companies_file = Path("runs") / f"batch_{run_id}_companies.jsonl"

            if companies_file.exists():
                companies = [
                    json.loads(line)
                    for line in companies_file.read_text().strip().split("\n")
                ]

                # Overall progress
                st.subheader("Batch Progress")

                completed = sum(1 for c in companies if c["status"] == "completed")
                failed = sum(1 for c in companies if c["status"] == "failed")
                pending = sum(1 for c in companies if c["status"] == "pending")
                running = sum(1 for c in companies if c["status"] == "running")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Completed", completed)
                col2.metric("Failed", failed)
                col3.metric("Running", running)
                col4.metric("Pending", pending)

                # Progress bar
                total = len(companies)
                progress_pct = (completed + failed) / total if total > 0 else 0
                st.progress(progress_pct, text=f"{completed + failed}/{total}")

                st.divider()
                st.subheader("Per-Company Status")

                # Status table
                status_data = []
                for c in companies:
                    status_icon = {
                        "completed": "✅",
                        "failed": "❌",
                        "running": "⏳",
                        "pending": "⏹️",
                    }.get(c["status"], "?")

                    status_data.append({
                        "Status": status_icon,
                        "Domain": c["domain"],
                        "Result": c.get("brief_path", "—"),
                        "Time (s)": f"{c.get('elapsed_seconds', 0):.1f}",
                        "Cost": f"${c.get('cost_usd', 0):.3f}",
                    })

                df = pd.DataFrame(status_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Error details
                errors = [c for c in companies if c["status"] == "failed"]
                if errors:
                    st.divider()
                    st.subheader("⚠️ Failed Companies")
                    for error_company in errors:
                        with st.expander(f"{error_company['domain']} — {error_company.get('error', 'Unknown error')}"):
                            st.code(error_company.get("error", "No error message"))

            else:
                st.warning(f"No results file found for {run_id}")
    else:
        st.info("Enter a Run ID above to monitor progress")

# ============================================================================
# COMPANY DRILL-DOWN: Profile, Scores, Personas, Emails, Critiques
# ============================================================================

elif page == "Company Drill-Down":
    st.header("Company Details")

    col1, col2 = st.columns([2, 1])

    with col1:
        run_id = st.text_input("Run ID", placeholder="e.g., abc123")

    if run_id:
        runs_dir = Path("runs") / run_id
        companies_file = Path("runs") / f"batch_{run_id}_companies.jsonl"

        if companies_file.exists():
            companies = [
                json.loads(line)
                for line in companies_file.read_text().strip().split("\n")
                if json.loads(line)["status"] == "completed"
            ]

            domain = st.selectbox("Select Company", [c["domain"] for c in companies])

            if domain:
                # Try to load the brief
                brief_path = runs_dir / f"{domain}.md"

                if brief_path.exists():
                    st.subheader(f"Account Brief: {domain}")

                    # Display the markdown
                    brief_content = brief_path.read_text()
                    st.markdown(brief_content)

                    # Download button
                    st.download_button(
                        label="📥 Download Brief",
                        data=brief_content,
                        file_name=f"{domain}_brief.md",
                        mime="text/markdown",
                    )

                else:
                    st.warning(f"Brief not found for {domain}")
        else:
            st.error(f"Run {run_id} not found")
    else:
        st.info("Enter a Run ID and select a company")

# ============================================================================
# COST DASHBOARD: Breakdown by Run, Company, Agent
# ============================================================================

elif page == "Cost Dashboard":
    st.header("Cost Analysis")

    batches = runner.list_batches()

    if batches:
        # Overall cost metrics
        col1, col2, col3 = st.columns(3)

        total_cost = sum(b.total_cost for b in batches)
        avg_cost = total_cost / sum(b.total_companies for b in batches) if sum(b.total_companies for b in batches) > 0 else 0
        max_run_cost = max(b.total_cost for b in batches) if batches else 0

        col1.metric("Total Sprint Cost", f"${total_cost:.2f}")
        col2.metric("Avg Cost/Company", f"${avg_cost:.3f}")
        col3.metric("Max Run Cost", f"${max_run_cost:.2f}")

        st.divider()

        # Cost by run (time series)
        st.subheader("Cost Trend")

        cost_data = [
            {
                "Date": batch.created_at[:10],
                "Run ID": batch.run_id,
                "Cost": batch.total_cost,
                "Companies": batch.total_companies,
            }
            for batch in reversed(batches)
        ]

        df_costs = pd.DataFrame(cost_data)

        if not df_costs.empty:
            fig = px.line(
                df_costs,
                x="Date",
                y="Cost",
                title="Cost Per Run Over Time",
                markers=True,
            )
            st.plotly_chart(fig, use_container_width=True)

        # Cost per company distribution
        st.subheader("Cost Per Company Distribution")

        company_costs = []
        for batch in batches:
            companies_file = Path("runs") / f"batch_{batch.run_id}_companies.jsonl"
            if companies_file.exists():
                for line in companies_file.read_text().strip().split("\n"):
                    company = json.loads(line)
                    if company.get("cost_usd", 0) > 0:
                        company_costs.append({
                            "Domain": company["domain"],
                            "Cost": company["cost_usd"],
                            "Status": company["status"],
                        })

        if company_costs:
            df_company = pd.DataFrame(company_costs)
            fig = px.histogram(
                df_company,
                x="Cost",
                nbins=20,
                title="Distribution of Per-Company Costs",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Statistics
            st.subheader("Cost Statistics")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Mean", f"${df_company['Cost'].mean():.3f}")
            col2.metric("Median", f"${df_company['Cost'].median():.3f}")
            col3.metric("Min", f"${df_company['Cost'].min():.3f}")
            col4.metric("Max", f"${df_company['Cost'].max():.3f}")
        else:
            st.info("No cost data available yet (live runs needed)")

    else:
        st.info("No batch runs yet")

# ============================================================================
# EVAL DASHBOARD: Scores Over Time
# ============================================================================

elif page == "Eval Dashboard":
    st.header("Evaluation Metrics")

    st.info(
        "This view will show eval metrics when the full eval harness (Day 17) is integrated. "
        "Metrics tracked: enrichment accuracy, ICP correlation, email quality, would-send pass rate."
    )

    # Placeholder for future eval integration
    st.subheader("Metrics (Placeholder)")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Enrichment Accuracy", "—", delta="Pending")
    col2.metric("ICP Correlation", "—", delta="Pending")
    col3.metric("Email Quality", "—", delta="Pending")
    col4.metric("Would-Send Rate", "—", delta="Pending")

    st.divider()
    st.subheader("Coming Soon")
    st.markdown("""
    - **Enrichment Accuracy**: % of companies where enriched profile matches gold
    - **ICP Correlation**: Spearman rank correlation vs labeled companies
    - **Email Quality**: Avg critique score across all generated emails
    - **Would-Send Rate**: % of emails passing the would-send bar
    - **Trend Charts**: Metrics over time as new eval runs complete
    """)

# Footer
st.divider()
st.caption(
    "GTM Outbound Agent Dashboard — Day 16 · "
    "[Repo](https://github.com/DheerajPranav/gtm-signal-intelligence) · "
    "[Docs](https://github.com/DheerajPranav/gtm-signal-intelligence/blob/main/gtm-outbound-agent/README.md)"
)
