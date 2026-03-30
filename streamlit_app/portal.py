import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime

st.set_page_config(
    page_title="PA Submission Portal",
    page_icon="🏥",
    layout="wide"
)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../models/pa_model.pkl")

@st.cache_resource
def load_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

artifacts = load_model()

approval_model  = artifacts["approval_model"]
reason_model    = artifacts["reason_model"]
le_payer        = artifacts["le_payer"]
le_procedure    = artifacts["le_procedure"]
le_specialty    = artifacts["le_specialty"]
le_reason       = artifacts["le_reason"]
FEATURES        = artifacts["features"]
payer_meta      = artifacts["payer_meta"]
procedure_meta  = artifacts["procedure_meta"]

PAYER_NAMES = {
    "PAY001": "UnitedHealthcare",
    "PAY002": "Aetna",
    "PAY003": "Blue Cross Blue Shield",
    "PAY004": "Cigna",
    "PAY005": "Humana",
    "PAY006": "Centene",
    "PAY007": "Molina Healthcare",
    "PAY008": "Kaiser Permanente",
}

PROCEDURE_NAMES = {
    "27447": "Total Knee Replacement",
    "70553": "MRI Brain with Contrast",
    "72148": "MRI Lumbar Spine",
    "J0135": "Adalimumab (Humira) Injection",
    "27130": "Total Hip Replacement",
    "93306": "Echocardiogram",
    "45378": "Colonoscopy Diagnostic",
    "70450": "CT Head without Contrast",
    "99213": "Office Visit Level 3",
    "90837": "Psychotherapy 60 min",
    "43239": "Upper GI Endoscopy w/ Biopsy",
    "27245": "Femur Fracture Treatment",
    "93000": "Electrocardiogram",
    "71250": "CT Thorax Diagnostic",
    "96413": "Chemotherapy IV Infusion",
    "77067": "Screening Mammography",
    "29827": "Shoulder Arthroscopy",
    "64483": "Lumbar Epidural Injection",
    "J1745": "Infliximab (Remicade) Injection",
    "93454": "Coronary Angiography",
    "47562": "Laparoscopic Cholecystectomy",
    "58150": "Total Abdominal Hysterectomy",
    "90791": "Psychiatric Diagnostic Evaluation",
    "99223": "Initial Hospital Care",
    "J3490": "Unclassified Biologics",
}

SPECIALTY_MAP = {
    "27447": "Orthopedics",  "27130": "Orthopedics",  "27245": "Orthopedics",
    "29827": "Orthopedics",  "70553": "Radiology",    "72148": "Radiology",
    "70450": "Radiology",    "71250": "Radiology",    "77067": "Radiology",
    "J0135": "Rheumatology", "J1745": "Rheumatology", "J3490": "Rheumatology",
    "93306": "Cardiology",   "93000": "Cardiology",   "93454": "Cardiology",
    "45378": "Gastroenterology","43239": "Gastroenterology","99213": "Primary Care",
    "99223": "Primary Care", "90837": "Behavioral",   "90791": "Behavioral",
    "96413": "Oncology",     "64483": "Pain Mgmt",    "47562": "Surgery",
    "58150": "GYN",
}

DENIAL_REASON_LABELS = {
    "MEDICAL_NECESSITY":  "Service not deemed medically necessary",
    "MISSING_DOCS":       "Required documentation not provided",
    "NOT_COVERED":        "Service not covered under plan",
    "STEP_THERAPY":       "Step therapy requirements not met",
    "DUPLICATE":          "Duplicate request already on file",
    "EXPERIMENTAL":       "Classified as experimental/investigational",
    "PRIOR_TREATMENT":    "Prior treatment requirements not satisfied",
    "OUT_OF_NETWORK":     "Provider not in network",
}

def predict(payer_id, procedure_code, is_urgent, hour, dow):
    meta_p  = payer_meta.get(payer_id, {})
    meta_pr = procedure_meta.get(procedure_code, {})

    try:
        payer_enc = le_payer.transform([payer_id])[0]
    except ValueError:
        payer_enc = 0
    try:
        proc_enc = le_procedure.transform([procedure_code])[0]
    except ValueError:
        proc_enc = 0

    specialty = SPECIALTY_MAP.get(procedure_code, "Primary Care")
    try:
        spec_enc = le_specialty.transform([specialty])[0]
    except ValueError:
        spec_enc = 0

    row = pd.DataFrame([{
        "payer_encoded":     payer_enc,
        "procedure_encoded": proc_enc,
        "specialty_encoded": spec_enc,
        "is_urgent":         int(is_urgent),
        "high_denial":       int(meta_pr.get("high_denial", False)),
        "avg_response_hrs":  float(meta_p.get("avg_response_hrs", 72)),
        "base_denial_rate":  float(meta_p.get("base_denial_rate", 0.20)),
        "hour_of_day":       hour,
        "day_of_week":       dow,
        "is_weekend":        int(dow >= 5),
    }])

    approval_proba = approval_model.predict_proba(row)[0][1]

    reason_proba  = reason_model.predict_proba(row)[0]
    top_reason_idx = np.argsort(reason_proba)[::-1][:3]
    top_reasons = [
        (le_reason.inverse_transform([i])[0], float(reason_proba[i]))
        for i in top_reason_idx
    ]

    return approval_proba, top_reasons

# ─────────────────────────────────────────────────────────────────────────────
# Layout
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
.big-score { font-size: 52px; font-weight: 700; line-height: 1.1; }
.score-label { font-size: 13px; color: #888; margin-bottom: 4px; }
.verdict-approved {
    background: #EAF3DE; color: #27500A;
    border-radius: 10px; padding: 16px 20px;
    font-size: 15px; font-weight: 500; margin: 12px 0;
    border-left: 4px solid #3B6D11;
}
.verdict-likely {
    background: #FAEEDA; color: #633806;
    border-radius: 10px; padding: 16px 20px;
    font-size: 15px; font-weight: 500; margin: 12px 0;
    border-left: 4px solid #854F0B;
}
.verdict-denied {
    background: #FCEBEB; color: #501313;
    border-radius: 10px; padding: 16px 20px;
    font-size: 15px; font-weight: 500; margin: 12px 0;
    border-left: 4px solid #A32D2D;
}
.reason-bar-wrap {
    background: #1e1e1e; border-radius: 6px;
    padding: 10px 14px; margin: 6px 0;
}
.sla-chip {
    display: inline-block; padding: 3px 10px;
    border-radius: 12px; font-size: 12px; font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 11])
with col_title:
    st.title("🏥 Prior Authorization Submission Portal")
    st.caption("Enter patient and procedure details to get an instant approval prediction before submitting to the payer.")

st.divider()

# ── Two-column layout ─────────────────────────────────────────────────────────
left, right = st.columns([1.1, 1], gap="large")

with left:
    st.subheader("Patient & Request Details")

    with st.form("pa_form", border=False):

        st.markdown("**Patient information**")
        c1, c2 = st.columns(2)
        with c1:
            patient_id   = st.text_input("Patient ID", placeholder="e.g. PAT001234")
            patient_age  = st.number_input("Age", min_value=1, max_value=110, value=52)
        with c2:
            patient_name = st.text_input("Patient Name", placeholder="e.g. John Smith")
            patient_sex  = st.selectbox("Sex", ["Male", "Female", "Other"])

        st.divider()
        st.markdown("**Provider & payer**")
        c3, c4 = st.columns(2)
        with c3:
            provider_npi  = st.text_input("Provider NPI", placeholder="e.g. NPI1234567890")
        with c4:
            payer_id = st.selectbox(
                "Insurance Payer",
                options=list(PAYER_NAMES.keys()),
                format_func=lambda x: PAYER_NAMES[x],
            )

        st.divider()
        st.markdown("**Procedure**")
        procedure_code = st.selectbox(
            "Procedure (CPT Code)",
            options=list(PROCEDURE_NAMES.keys()),
            format_func=lambda x: f"{x} — {PROCEDURE_NAMES[x]}",
        )

        clinical_notes = st.text_area(
            "Clinical justification notes",
            placeholder="Describe medical necessity, prior treatments attempted, supporting diagnoses...",
            height=120,
        )

        st.divider()
        st.markdown("**Request type**")
        c5, c6 = st.columns(2)
        with c5:
            is_urgent = st.toggle("Expedited / Urgent request", value=False)
        with c6:
            submit_date = st.date_input("Submission date", value=datetime.today())

        submitted = st.form_submit_button(
            "Get Approval Prediction",
            use_container_width=True,
            type="primary",
        )

with right:
    st.subheader("Prediction Results")

    if not submitted:
        st.markdown("""
        <div style='text-align:center; padding: 60px 20px; color: #666;'>
            <div style='font-size:48px; margin-bottom:16px'>📋</div>
            <div style='font-size:15px'>Fill in the form and click<br>
            <strong>Get Approval Prediction</strong> to see results.</div>
        </div>
        """, unsafe_allow_html=True)

    else:
        now = datetime.now()
        approval_score, top_reasons = predict(
            payer_id, procedure_code, is_urgent,
            hour=now.hour, dow=now.weekday()
        )

        denial_score = 1 - approval_score
        payer_name   = PAYER_NAMES[payer_id]
        proc_name    = PROCEDURE_NAMES[procedure_code]
        sla_hrs      = 24 if is_urgent else 72

        # ── Score gauge ─────────────────────────────────────────────────────
        score_pct = int(approval_score * 100)
        if approval_score >= 0.70:
            score_color  = "#1D9E75"
            verdict_cls  = "verdict-approved"
            verdict_icon = "✅"
            verdict_text = f"High likelihood of approval. This request meets typical {payer_name} criteria for {proc_name}."
            recommendation = "Submit now — documentation looks strong."
        elif approval_score >= 0.47:
            score_color  = "#EF9F27"
            verdict_cls  = "verdict-likely"
            verdict_icon = "⚠️"
            verdict_text = f"Borderline case. {payer_name} may request additional documentation before approving {proc_name}."
            recommendation = "Consider strengthening clinical notes before submitting."
        else:
            score_color  = "#E24B4A"
            verdict_cls  = "verdict-denied"
            verdict_icon = "🔴"
            verdict_text = f"High denial risk. {payer_name} frequently denies {proc_name} without step therapy or additional criteria."
            recommendation = "Review denial reasons below before submitting."

        # Score display
        bar_pct = score_pct
        st.markdown(f"""
        <div style='display:flex; align-items:flex-end; gap:24px; margin-bottom:8px'>
            <div>
                <div class='score-label'>Approval probability</div>
                <div class='big-score' style='color:{score_color}'>{score_pct}%</div>
            </div>
            <div style='flex:1; padding-bottom:14px'>
                <div style='background:#2a2a2a;border-radius:8px;height:18px;overflow:hidden'>
                    <div style='width:{bar_pct}%;background:{score_color};
                    height:18px;border-radius:8px;transition:width 0.4s'></div>
                </div>
                <div style='display:flex;justify-content:space-between;
                font-size:11px;color:#666;margin-top:4px'>
                    <span>0% (certain denial)</span><span>100% (certain approval)</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='{verdict_cls}'>{verdict_icon} {verdict_text}<br>
        <span style='font-weight:400;font-size:13px;opacity:0.85'>
        {recommendation}</span></div>
        """, unsafe_allow_html=True)

        # ── Key metrics ──────────────────────────────────────────────────────
        m1, m2, m3 = st.columns(3)
        payer_breach = payer_meta.get(payer_id, {}).get("avg_response_hrs", 72)
        m1.metric("Payer avg response", f"{payer_breach:.0f} hrs")
        m2.metric("SLA deadline", f"{sla_hrs} hrs")
        m3.metric("Denial risk", f"{int(denial_score*100)}%")

        st.divider()

        # ── Top denial risks ─────────────────────────────────────────────────
        st.markdown("**Top denial risk factors**")
        st.caption("If denied, these are the most likely reasons based on payer and procedure patterns:")

        for reason_code, prob in top_reasons:
            label = DENIAL_REASON_LABELS.get(reason_code, reason_code)
            pct   = int(prob * 100)
            color = "#E24B4A" if pct > 40 else "#EF9F27" if pct > 20 else "#378ADD"
            st.markdown(f"""
            <div class='reason-bar-wrap'>
                <div style='display:flex;justify-content:space-between;
                margin-bottom:5px;font-size:13px'>
                    <span>{label}</span>
                    <span style='color:{color};font-weight:500'>{pct}%</span>
                </div>
                <div style='background:#333;border-radius:4px;height:7px'>
                    <div style='width:{min(pct,100)}%;background:{color};
                    height:7px;border-radius:4px'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # ── Suggested actions ────────────────────────────────────────────────
        st.markdown("**Suggested actions before submitting**")

        proc_high_denial = procedure_meta.get(
            procedure_code, {}
        ).get("high_denial", False)

        actions = []
        if proc_high_denial:
            actions.append("📎 Attach all prior treatment records and conservative therapy documentation")
        if top_reasons[0][0] == "MEDICAL_NECESSITY":
            actions.append("📄 Include physician letter of medical necessity with ICD-10 diagnosis codes")
        if top_reasons[0][0] == "STEP_THERAPY":
            actions.append("💊 Document all prior medications or treatments attempted and their outcomes")
        if top_reasons[0][0] == "MISSING_DOCS":
            actions.append("🗂️ Ensure lab results, imaging reports, and referral notes are attached")
        if payer_id in ["PAY004", "PAY005", "PAY006"]:
            actions.append(f"⚡ Note: {payer_name} has a {payer_breach:.0f}hr avg response time — flag for SLA monitoring")
        if is_urgent:
            actions.append("🚨 Expedited flag set — ensure clinical urgency is explicitly stated in notes")
        if not actions:
            actions.append("✅ Documentation looks standard — proceed with submission")

        for a in actions:
            st.markdown(f"- {a}")

        st.divider()

        # ── Summary card ─────────────────────────────────────────────────────
        st.markdown("**Request summary**")
        summary_data = {
            "Field": ["Patient", "Payer", "Procedure", "Urgency",
                      "SLA Deadline", "Approval Score", "Denial Risk"],
            "Value": [
                patient_name or patient_id or "—",
                payer_name,
                f"{procedure_code} — {proc_name}",
                "Expedited" if is_urgent else "Standard",
                f"{sla_hrs} hours",
                f"{score_pct}%",
                f"{int(denial_score*100)}%",
            ]
        }
        st.dataframe(
            pd.DataFrame(summary_data),
            hide_index=True,
            use_container_width=True
        )
