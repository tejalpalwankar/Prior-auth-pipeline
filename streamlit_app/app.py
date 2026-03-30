import streamlit as st
import duckdb
import pandas as pd
from datetime import datetime
import os

st.set_page_config(
    page_title="PA SLA Monitor",
    page_icon="🏥",
    layout="wide"
)

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/pa_warehouse.duckdb")

@st.cache_data(ttl=300)
def load_data():
    con = duckdb.connect(DB_PATH, read_only=True)

    sla_watch = con.execute("""
        SELECT * FROM analytics_marts.mart_sla_watch
    """).fetchdf()

    payer_summary = con.execute("""
        SELECT * FROM analytics_marts.dim_payer_summary
        ORDER BY avg_approval_hrs DESC
    """).fetchdf()

    procedure_summary = con.execute("""
        SELECT * FROM analytics_marts.dim_procedure_summary
        ORDER BY denial_rate_pct DESC
        LIMIT 15
    """).fetchdf()

    weekly = con.execute("""
        SELECT * FROM analytics_marts.mart_weekly_compliance
        ORDER BY submission_week
    """).fetchdf()

    kpis = con.execute("""
        SELECT
            COUNT(*)                                            AS total_requests,
            ROUND(AVG(elapsed_hours), 1)                       AS avg_approval_hrs,
            ROUND(COUNT(CASE WHEN status = 'denied'
                THEN 1 END) * 100.0 / COUNT(*), 1)             AS denial_rate_pct,
            COUNT(CASE WHEN sla_breach_flag = true THEN 1 END) AS total_breaches
        FROM analytics_marts.fct_pa_requests
    """).fetchdf()

    con.close()
    return sla_watch, payer_summary, procedure_summary, weekly, kpis

def color_sla(val):
    if val == "Breached":
        return "background-color: #FCEBEB; color: #A32D2D; font-weight: 500"
    elif val == "At Risk":
        return "background-color: #FAEEDA; color: #854F0B; font-weight: 500"
    elif val == "On Track":
        return "background-color: #EAF3DE; color: #3B6D11; font-weight: 500"
    return ""

def color_row(row):
    styles = [""] * len(row)
    idx = row.index.tolist()
    if "sla_status" in idx:
        val = row["sla_status"]
        if val == "Breached":
            styles = ["background-color: #FCEBEB"] * len(row)
        elif val == "At Risk":
            styles = ["background-color: #FAEEDA"] * len(row)
    return styles

# ── Load data ────────────────────────────────────────────────────────────────
sla_watch, payer_summary, procedure_summary, weekly, kpis = load_data()

breached    = sla_watch[sla_watch["sla_status"] == "Breached"]
at_risk     = sla_watch[sla_watch["sla_status"] == "At Risk"]

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🏥 Prior Authorization SLA Monitor")
st.caption(f"CMS 72-hour compliance dashboard · Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ── KPI row ──────────────────────────────────────────────────────────────────
k = kpis.iloc[0]
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Requests",     f"{int(k['total_requests']):,}")
c2.metric("Avg Approval Time",  f"{k['avg_approval_hrs']} hrs")
c3.metric("Overall Denial Rate",f"{k['denial_rate_pct']}%")
c4.metric("Total SLA Breaches", f"{int(k['total_breaches']):,}")
c5.metric("Pending At Risk",    f"{len(at_risk):,}",    delta_color="inverse")
c6.metric("Pending Breached",   f"{len(breached):,}",   delta_color="inverse")

st.divider()

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🚨 SLA Watch",
    "📊 Payer Performance",
    "💊 Procedure Analysis",
    "📈 Compliance Trend"
])

# ── Tab 1: SLA Watch ─────────────────────────────────────────────────────────
with tab1:
    st.subheader("Open requests approaching or past the CMS deadline")

    col1, col2 = st.columns(2)
    with col1:
        payer_filter = st.multiselect(
            "Filter by payer",
            options=sorted(sla_watch["payer_name"].unique()),
            default=[]
        )
    with col2:
        urgency_filter = st.multiselect(
            "Filter by urgency",
            options=["Standard", "Expedited"],
            default=[]
        )

    filtered = sla_watch.copy()
    if payer_filter:
        filtered = filtered[filtered["payer_name"].isin(payer_filter)]
    if urgency_filter:
        filtered = filtered[filtered["urgency_type"].isin(urgency_filter)]

    b_count = len(filtered[filtered["sla_status"] == "Breached"])
    r_count = len(filtered[filtered["sla_status"] == "At Risk"])

    if b_count > 0:
        st.error(f"🔴 {b_count} requests have already breached the CMS SLA deadline")
    if r_count > 0:
        st.warning(f"🟡 {r_count} requests will breach within 12 hours")
    if b_count == 0 and r_count == 0:
        st.success("✅ No requests currently at risk of breaching SLA")

    display_cols = [
        "request_id", "payer_name", "procedure_description",
        "urgency_type", "sla_limit_hours", "days_pending",
        "hours_until_breach", "sla_status", "auto_approve_score"
    ]
    available = [c for c in display_cols if c in filtered.columns]

    if not filtered.empty:
        styled = (
            filtered[available]
            .rename(columns={
                "request_id":           "Request ID",
                "payer_name":           "Payer",
                "procedure_description":"Procedure",
                "urgency_type":         "Urgency",
                "sla_limit_hours":      "SLA Limit (hrs)",
                "days_pending":         "Hours Pending",
                "hours_until_breach":   "Hours Until Breach",
                "sla_status":           "SLA Status",
                "auto_approve_score":   "Approval Score",
            })
            .style.applymap(color_sla, subset=["SLA Status"])
        )
        st.dataframe(styled, use_container_width=True, height=420)
    else:
        st.info("No requests match the current filters.")

# ── Tab 2: Payer Performance ─────────────────────────────────────────────────
with tab2:
    st.subheader("Average approval time and SLA breach rate by payer")

    ref_line = 72
    for _, row in payer_summary.iterrows():
        hrs = row["avg_approval_hrs"] or 0
        pct = min(hrs / 150, 1.0)
        color = "#E24B4A" if hrs > ref_line else "#1D9E75"
        st.markdown(
            f"**{row['payer_name']}** — `{hrs:.0f} hrs avg` &nbsp; "
            f"denial rate: `{row['denial_rate_pct']}%` &nbsp; "
            f"breach rate: `{row['sla_breach_rate_pct']}%`"
        )
        st.markdown(
            f"""<div style="background:#e8e8e8;border-radius:4px;height:12px;margin-bottom:12px">
            <div style="width:{pct*100:.1f}%;background:{color};height:12px;border-radius:4px"></div>
            </div>""",
            unsafe_allow_html=True
        )

    st.caption("Red bar = average response time exceeds CMS 72-hour threshold")
    st.divider()
    st.dataframe(
        payer_summary[[
            "payer_name", "total_requests", "avg_approval_hrs",
            "denial_rate_pct", "sla_breach_rate_pct",
            "total_sla_breaches", "requests_approaching_breach"
        ]].rename(columns={
            "payer_name":                  "Payer",
            "total_requests":              "Total Requests",
            "avg_approval_hrs":            "Avg Approval (hrs)",
            "denial_rate_pct":             "Denial Rate %",
            "sla_breach_rate_pct":         "Breach Rate %",
            "total_sla_breaches":          "Total Breaches",
            "requests_approaching_breach": "Approaching Breach",
        }),
        use_container_width=True
    )

# ── Tab 3: Procedure Analysis ─────────────────────────────────────────────────
with tab3:
    st.subheader("Denial rate by CPT procedure code (top 15)")

    for _, row in procedure_summary.iterrows():
        pct = row["denial_rate_pct"] or 0
        color = "#E24B4A" if row["high_denial_flag"] else "#378ADD"
        flag  = "⚠️ High-denial" if row["high_denial_flag"] else ""
        st.markdown(
            f"**{row['procedure_description']}** `{row['procedure_code']}` "
            f"— `{pct:.1f}%` denial &nbsp; {flag}"
        )
        st.markdown(
            f"""<div style="background:#e8e8e8;border-radius:4px;height:10px;margin-bottom:10px">
            <div style="width:{min(pct,100):.1f}%;background:{color};height:10px;border-radius:4px"></div>
            </div>""",
            unsafe_allow_html=True
        )

    st.divider()
    st.dataframe(
        procedure_summary[[
            "procedure_code", "procedure_description", "procedure_specialty",
            "total_requests", "denial_rate_pct", "top_denial_reason", "avg_approval_hrs"
        ]].rename(columns={
            "procedure_code":        "CPT Code",
            "procedure_description": "Procedure",
            "procedure_specialty":   "Specialty",
            "total_requests":        "Total Requests",
            "denial_rate_pct":       "Denial Rate %",
            "top_denial_reason":     "Top Denial Reason",
            "avg_approval_hrs":      "Avg Approval (hrs)",
        }),
        use_container_width=True
    )

# ── Tab 4: Compliance Trend ───────────────────────────────────────────────────
with tab4:
    st.subheader("Weekly SLA compliance rate over time")

    if not weekly.empty:
        weekly["submission_week"] = pd.to_datetime(weekly["submission_week"])
        weekly_display = weekly[[
            "submission_week", "total_decided",
            "sla_compliance_pct", "denial_rate_pct", "avg_elapsed_hrs"
        ]].rename(columns={
            "submission_week":    "Week",
            "total_decided":      "Requests Decided",
            "sla_compliance_pct": "SLA Compliance %",
            "denial_rate_pct":    "Denial Rate %",
            "avg_elapsed_hrs":    "Avg Elapsed (hrs)",
        })

        st.line_chart(
            weekly_display.set_index("Week")[["SLA Compliance %", "Denial Rate %"]],
            use_container_width=True
        )

        st.dataframe(weekly_display, use_container_width=True)
    else:
        st.info("No weekly data available yet.")

# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Data source: DuckDB · dbt transformation layer · "
    "CMS 2024 Prior Authorization Rule — 72hr standard / 24hr expedited SLA"
)