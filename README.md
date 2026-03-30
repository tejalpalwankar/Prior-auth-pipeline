# Prior Authorization Analytics Pipeline

> An end-to-end data engineering project modelling the CMS 2024 Prior Authorization compliance problem — from synthetic data generation through dbt transformation, ML prediction, and interactive dashboards.

---

## The Problem

Prior authorization (PA) is one of the biggest administrative bottlenecks in US healthcare. Providers submit auth requests to insurers and wait days for approval with no visibility into delays or reasons. In 2024, CMS issued new rules requiring payers to respond within **72 hours** for standard requests and **24 hours** for expedited ones. Most health systems still track PAs in spreadsheets.

This project builds the analytics infrastructure that would let a health system actually measure and act on that problem.

---

## What This Project Builds

```
Faker (Python)
    │
    ▼
50,000 synthetic PA requests
    │
    ▼
DuckDB warehouse (raw schema)
    │
    ▼
dbt transformation layer
  ├── staging/        (clean + type-cast)
  ├── intermediate/   (SLA flags, enrichment)
  └── marts/          (fct, dims, SLA watch)
    │
    ├── Tableau Public dashboard  (8 charts, interactive)
    ├── Streamlit SLA monitor     (live breach alerts)
    └── Streamlit submission portal (ML approval prediction)
```

---

## Stack

| Layer | Tool | Purpose |
|---|---|---|
| Data generation | Python + Faker | 50k synthetic PA requests |
| Warehouse | DuckDB | Local analytical warehouse |
| Transformation | dbt (dbt-duckdb) | Staging → intermediate → marts |
| ML | scikit-learn (Random Forest) | Approval prediction + denial risk |
| Alert dashboard | Streamlit | Live SLA breach monitor |
| Submission portal | Streamlit | Provider-facing case submission form |
| BI dashboard | Tableau Public | 8-chart interactive compliance dashboard |

---

## Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/tejal-palwankar/Prior-auth-pipeline.git
cd Prior-auth-pipeline

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate synthetic data
python3 generator/generate_pa_data.py

# 5. Load to DuckDB
python3 generator/load_to_duckdb.py

# 6. Run dbt transformations
cd dbt_project
dbt build
cd ..

# 7. Train the ML model
python3 train_model.py

# 8. Launch SLA monitor
.venv/bin/streamlit run streamlit_app/app.py

# 9. Launch submission portal (separate terminal)
.venv/bin/streamlit run streamlit_app/portal.py
```

Or using make:

```bash
make run      # generate + load + dbt build
make app      # launch Streamlit SLA monitor
make docs     # serve dbt docs at localhost:8080
```

---

## Project Structure

```
Prior-auth-pipeline/
├── data/
│   ├── pa_requests.csv          # 50k synthetic PA requests
│   ├── payers.csv               # 8 payers with response benchmarks
│   ├── procedures.csv           # 30 CPT codes
│   ├── providers.csv            # 50 fictional providers
│   ├── pa_warehouse.duckdb      # DuckDB warehouse (gitignored)
│   └── tableau_exports/         # CSVs exported for Tableau
├── generator/
│   ├── generate_pa_data.py      # Faker data generation script
│   └── load_to_duckdb.py        # CSV → DuckDB raw schema loader
├── dbt_project/
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/             # stg_pa_requests, stg_payers, etc.
│       ├── intermediate/        # int_pa_requests_enriched
│       └── marts/               # fct, dims, SLA watch, weekly compliance
├── streamlit_app/
│   ├── app.py                   # SLA monitor (4 tabs)
│   └── portal.py                # PA submission form with ML prediction
├── models/
│   └── pa_model.pkl             # Trained Random Forest model
├── train_model.py               # Model training script
├── export_for_tableau.py        # Export marts to CSV for Tableau
├── Makefile
└── requirements.txt
```

---

## Data Model

### `fct_pa_requests` — core fact table (50k rows)

| Field | Type | Description |
|---|---|---|
| request_id | VARCHAR PK | Unique request identifier |
| patient_id | VARCHAR | Patient reference |
| provider_npi | VARCHAR FK | Provider reference |
| payer_id | VARCHAR FK | Payer reference |
| procedure_code | VARCHAR FK | CPT code reference |
| submitted_at | TIMESTAMP | When request was submitted |
| decided_at | TIMESTAMP | When payer responded |
| status | VARCHAR | approved / denied / pending |
| is_urgent | BOOLEAN | Expedited flag |
| denial_reason_code | VARCHAR | Reason if denied |
| elapsed_hours | FLOAT | Hours from submission to decision |
| sla_limit_hours | INTEGER | 72 standard / 24 expedited |
| sla_breach_flag | BOOLEAN | Exceeded SLA limit |
| approaching_breach | BOOLEAN | Within 12hrs of breaching |
| auto_approve_score | FLOAT | ML approval probability |

### dbt model lineage

```
raw.pa_requests ──┐
raw.payers ────────┤
raw.procedures ────┼──► stg_* ──► int_pa_requests_enriched ──► fct_pa_requests
raw.providers ─────┘                                        ──► dim_payer_summary
                                                            ──► dim_procedure_summary
                                                            ──► mart_sla_watch
                                                            ──► mart_weekly_compliance
```

---

## Key Findings (Synthetic Data)

### Payer performance

| Payer | Avg Response | SLA Breach Rate | Denial Rate |
|---|---|---|---|
| Centene | 100 hrs | 80.88% | 45.33% |
| Humana | 88 hrs | 75.26% | 41.6% |
| Cigna | 80 hrs | 69.7% | 37.9% |
| Aetna | 51 hrs | 27.44% | 28.26% |
| UnitedHealthcare | 44 hrs | 13.27% | 22.76% |
| Blue Cross Blue Shield | 37 hrs | 3.53% | 18.41% |
| Molina Healthcare | 33 hrs | 1.15% | 15.5% |
| Kaiser Permanente | 25 hrs | 0.03% | 10.27% |

### Top denied procedures

| Procedure | CPT | Denial Rate |
|---|---|---|
| Total Hip Replacement | 27130 | 38.8% |
| MRI Lumbar Spine | 72148 | 38.6% |
| Lumbar Epidural Injection | 64483 | 38.4% |
| MRI Brain with Contrast | 70553 | 37.6% |
| Total Knee Replacement | 27447 | 37.6% |

### Top denial reasons (across all payers)
1. Medical Necessity — 35% of denials
2. Missing Documentation — 25%
3. Step Therapy not met — 15%
4. Not Covered — 12%

---

## ML Model

A Random Forest classifier trained on 45,940 decided requests predicts approval probability before submission.

**Features used:**
- Payer (encoded)
- Procedure code (encoded)
- Specialty (encoded)
- Urgency flag
- High denial procedure flag
- Payer avg response hours
- Payer base denial rate
- Hour of day / day of week / weekend flag

**Performance:**
- ROC-AUC: ~0.78
- Mirrors elenafmoseyko/Auto-Approval-Prior-Authorization-ML distribution: 73.87% approval at threshold 0.47

**Submission portal features:**
- Instant approval probability score (0–100%)
- Colour-coded verdict (green / amber / red)
- Top 3 denial risk factors with probability bars
- Suggested actions before submitting
- Payer avg response time vs CMS SLA deadline

---

## Streamlit Apps

### SLA Monitor (`app.py`)
- 6 KPI metrics: total requests, avg approval time, denial rate, breach count, at-risk count
- Tab 1 — SLA Watch: colour-coded table of pending requests (red = breached, amber = at risk)
- Tab 2 — Payer Performance: bar chart with 72hr reference line
- Tab 3 — Procedure Analysis: denial rate by CPT code
- Tab 4 — Compliance Trend: weekly SLA compliance line chart
- Auto-refreshes every 5 minutes

#### Screenshots

1. <img width="1920" height="905" alt="image" src="https://github.com/user-attachments/assets/da790e2e-3db3-45b3-a706-624907355a6c" />

2. <img width="1851" height="719" alt="image" src="https://github.com/user-attachments/assets/af82f9fc-ebb9-4821-ab0f-116654ec2b67" />

3. <img width="1829" height="420" alt="image" src="https://github.com/user-attachments/assets/395f62e6-c0cc-432a-a5bd-1642c13af94f" />

4. <img width="1828" height="903" alt="image" src="https://github.com/user-attachments/assets/d82ee0e8-bf03-44fc-bfa4-43afec912c52" />

5. <img width="1809" height="470" alt="image" src="https://github.com/user-attachments/assets/c5b55d19-fd93-4fc7-abd2-03287a97658f" />

6. <img width="1842" height="503" alt="image" src="https://github.com/user-attachments/assets/6326333e-4f03-47ed-b051-3a17a9dd20f3" />

7. <img width="1860" height="464" alt="image" src="https://github.com/user-attachments/assets/a8606f2c-54ba-4dc0-9eac-0a235a4524b6" />

### Submission Portal (`portal.py`)
- Provider form: patient details, payer, procedure, clinical notes, urgency flag
- Instant ML prediction on submit
- Approval probability score with visual gauge
- Denial risk factor breakdown
- Suggested documentation actions

1. <img width="1920" height="1484" alt="image" src="https://github.com/user-attachments/assets/d974d3c9-ded5-4bfb-b920-86dec14802ed" />

2. <img width="1920" height="1833" alt="image" src="https://github.com/user-attachments/assets/bec0645c-b87d-46b4-bfbd-94e8b8f54567" />
---

## Tableau Dashboard

8-chart interactive compliance dashboard published to Tableau Public:

- Approval time by payer (bar, red/green vs 72hr line)
- SLA breach rate by payer (%)
- Denial reason breakdown (stacked bar by payer)
- Denial rate by procedure (CPT codes, high-denial flagged)
- Denial rate by specialty
- Pending requests by urgency type
- Approval rate trend over time by payer
- SLA compliance trend (weekly)

**[View live dashboard → Tableau Public](https://public.tableau.com/views/PriorAuthorizationAnalyticsCMS2024ComplianceDashboard/PriorAuthorizationAnalyticsCMSComplianceDashboard?:language=en-GB&publish=yes&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)**

<img width="1913" height="1001" alt="image" src="https://github.com/user-attachments/assets/5f54e83e-e9f8-49b8-9910-8650c80f9e07" />

Dynamic KPIs: Total Requests · Overall Denial Rate · Avg Approval Time · SLA Breaches

Fully interactive — selecting a payer filters all 8 charts simultaneously.

---

## dbt Tests

```bash
dbt test
```

Tests include:
- `unique` + `not_null` on all primary keys
- `accepted_values` on status (approved / denied / pending)
- `relationships` between fact and dimension tables
- Custom test: `sla_breach_flag` never TRUE on pending rows

---

## Attribution

- Schema design informed by [elenafmoseyko/Auto-Approval-Prior-Authorization-ML](https://github.com/elenafmoseyko/Auto-Approval-Prior-Authorization-ML)
- CPT codes and payer policy reference from [SenayYakut/ClinicalPriorAuthAgent](https://github.com/SenayYakut/ClinicalPriorAuthAgent)
- CMS 2024 Prior Authorization rule: [CMS-0057-F](https://www.cms.gov/newsroom/fact-sheets/cms-interoperability-and-prior-authorization-final-rule-cms-0057-f)

---

## Requirements

```
faker
pandas
duckdb
dbt-duckdb
streamlit
scikit-learn
pytest
```

---

## License

MIT
