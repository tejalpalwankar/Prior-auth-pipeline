import random
import csv
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Payers ──────────────────────────────────────────────────────────────────
PAYERS = [
    {"payer_id": "PAY001", "payer_name": "UnitedHealthcare",    "avg_response_hrs": 48,  "base_denial_rate": 0.18},
    {"payer_id": "PAY002", "payer_name": "Aetna",               "avg_response_hrs": 56,  "base_denial_rate": 0.22},
    {"payer_id": "PAY003", "payer_name": "Blue Cross Blue Shield","avg_response_hrs": 40, "base_denial_rate": 0.15},
    {"payer_id": "PAY004", "payer_name": "Cigna",               "avg_response_hrs": 88,  "base_denial_rate": 0.30},
    {"payer_id": "PAY005", "payer_name": "Humana",              "avg_response_hrs": 96,  "base_denial_rate": 0.35},
    {"payer_id": "PAY006", "payer_name": "Centene",             "avg_response_hrs": 110, "base_denial_rate": 0.40},
    {"payer_id": "PAY007", "payer_name": "Molina Healthcare",   "avg_response_hrs": 36,  "base_denial_rate": 0.12},
    {"payer_id": "PAY008", "payer_name": "Kaiser Permanente",   "avg_response_hrs": 28,  "base_denial_rate": 0.08},
]

# ── Procedures (CPT codes from ClinicalPriorAuthAgent reference) ─────────────
PROCEDURES = [
    {"procedure_code": "27447", "description": "Total Knee Replacement",      "specialty": "Orthopedics",    "high_denial": True},
    {"procedure_code": "70553", "description": "MRI Brain with Contrast",     "specialty": "Radiology",      "high_denial": True},
    {"procedure_code": "72148", "description": "MRI Lumbar Spine",            "specialty": "Radiology",      "high_denial": True},
    {"procedure_code": "J0135", "description": "Adalimumab (Humira) Inject",  "specialty": "Rheumatology",   "high_denial": True},
    {"procedure_code": "27130", "description": "Total Hip Replacement",       "specialty": "Orthopedics",    "high_denial": True},
    {"procedure_code": "93306", "description": "Echocardiogram",              "specialty": "Cardiology",     "high_denial": False},
    {"procedure_code": "45378", "description": "Colonoscopy Diagnostic",      "specialty": "Gastroenterology","high_denial": False},
    {"procedure_code": "70450", "description": "CT Head without Contrast",    "specialty": "Radiology",      "high_denial": False},
    {"procedure_code": "99213", "description": "Office Visit Level 3",        "specialty": "Primary Care",   "high_denial": False},
    {"procedure_code": "90837", "description": "Psychotherapy 60 min",        "specialty": "Behavioral",     "high_denial": False},
    {"procedure_code": "43239", "description": "Upper GI Endoscopy w/ Biopsy","specialty": "Gastroenterology","high_denial": False},
    {"procedure_code": "27245", "description": "Femur Fracture Treatment",    "specialty": "Orthopedics",    "high_denial": False},
    {"procedure_code": "93000", "description": "Electrocardiogram",           "specialty": "Cardiology",     "high_denial": False},
    {"procedure_code": "71250", "description": "CT Thorax Diagnostic",        "specialty": "Radiology",      "high_denial": False},
    {"procedure_code": "J2550", "description": "Promethazine HCl Injection",  "specialty": "Emergency",      "high_denial": False},
    {"procedure_code": "96413", "description": "Chemotherapy IV Infusion",    "specialty": "Oncology",       "high_denial": True},
    {"procedure_code": "77067", "description": "Screening Mammography",       "specialty": "Radiology",      "high_denial": False},
    {"procedure_code": "29827", "description": "Shoulder Arthroscopy",        "specialty": "Orthopedics",    "high_denial": False},
    {"procedure_code": "64483", "description": "Lumbar Epidural Injection",   "specialty": "Pain Mgmt",      "high_denial": True},
    {"procedure_code": "J1745", "description": "Infliximab (Remicade) Inject","specialty": "Rheumatology",   "high_denial": True},
    {"procedure_code": "43246", "description": "Upper GI Endoscopy w/ PEG",  "specialty": "Gastroenterology","high_denial": False},
    {"procedure_code": "27570", "description": "Closed Treatment Knee Disloc","specialty": "Orthopedics",    "high_denial": False},
    {"procedure_code": "90791", "description": "Psychiatric Diagnostic Eval", "specialty": "Behavioral",     "high_denial": False},
    {"procedure_code": "99223", "description": "Initial Hospital Care",       "specialty": "Primary Care",   "high_denial": False},
    {"procedure_code": "36415", "description": "Routine Venipuncture",        "specialty": "Lab",            "high_denial": False},
    {"procedure_code": "80053", "description": "Comprehensive Metabolic Panel","specialty": "Lab",           "high_denial": False},
    {"procedure_code": "93454", "description": "Coronary Angiography",        "specialty": "Cardiology",     "high_denial": True},
    {"procedure_code": "58150", "description": "Total Abdominal Hysterectomy","specialty": "GYN",            "high_denial": False},
    {"procedure_code": "47562", "description": "Laparoscopic Cholecystectomy","specialty": "Surgery",        "high_denial": False},
    {"procedure_code": "J3490", "description": "Unclassified Biologics",      "specialty": "Rheumatology",   "high_denial": True},
]

# ── Providers ────────────────────────────────────────────────────────────────
SPECIALTIES = ["Orthopedics", "Cardiology", "Radiology", "Primary Care",
               "Rheumatology", "Oncology", "Behavioral", "Gastroenterology",
               "Pain Mgmt", "Surgery"]

PROVIDERS = []
for i in range(50):
    npi = f"NPI{str(random.randint(1000000000, 9999999999))}"
    PROVIDERS.append({
        "provider_npi": npi,
        "provider_name": fake.name(),
        "specialty": random.choice(SPECIALTIES),
        "state": fake.state_abbr(),
        "organization": fake.company(),
    })

# ── Denial reason codes ──────────────────────────────────────────────────────
DENIAL_REASONS = [
    ("MEDICAL_NECESSITY", "Service not deemed medically necessary"),
    ("MISSING_DOCS",      "Required documentation not provided"),
    ("NOT_COVERED",       "Service not covered under plan"),
    ("STEP_THERAPY",      "Step therapy requirements not met"),
    ("DUPLICATE",         "Duplicate request already on file"),
    ("EXPERIMENTAL",      "Service classified as experimental"),
    ("PRIOR_TREATMENT",   "Prior treatment requirements not satisfied"),
    ("OUT_OF_NETWORK",    "Provider not in network"),
]

# ── Helper functions ─────────────────────────────────────────────────────────
def pick_denial_reason(procedure_code):
    high_denial_codes = {"27447", "70553", "72148", "J0135", "27130",
                         "96413", "64483", "J1745", "93454", "J3490"}
    if procedure_code in high_denial_codes:
        weights = [0.35, 0.20, 0.10, 0.15, 0.05, 0.08, 0.05, 0.02]
    else:
        weights = [0.20, 0.25, 0.20, 0.08, 0.10, 0.05, 0.07, 0.05]
    code, text = random.choices(DENIAL_REASONS, weights=weights, k=1)[0]
    return code, text

def make_timestamps(payer, is_urgent, status):
    submitted_at = fake.date_time_between(
        start_date="-180d", end_date="-1d"
    )
    if status == "pending":
        decided_at = None
        elapsed_hours = None
    else:
        avg = payer["avg_response_hrs"]
        stddev = avg * 0.4
        raw_hrs = max(1, random.gauss(avg, stddev))
        # Urgent requests are supposed to be faster
        if is_urgent:
            raw_hrs = raw_hrs * 0.4
        elapsed_hours = round(raw_hrs, 2)
        decided_at = submitted_at + timedelta(hours=elapsed_hours)
    return submitted_at, decided_at, elapsed_hours

def compute_sla(is_urgent, elapsed_hours, submitted_at, decided_at, status):
    sla_limit = 24 if is_urgent else 72
    if status == "pending":
        days_pending = (datetime.now() - submitted_at).total_seconds() / 3600
        days_pending = round(days_pending, 2)
        sla_breach_flag = False
        approaching_breach = days_pending >= (sla_limit - 12)
    else:
        days_pending = None
        sla_breach_flag = elapsed_hours > sla_limit
        approaching_breach = False
    return sla_limit, sla_breach_flag, approaching_breach, days_pending

def pick_status(payer, procedure):
    denial_rate = payer["base_denial_rate"]
    if procedure["high_denial"]:
        denial_rate = min(0.55, denial_rate * 1.8)
    r = random.random()
    if r < 0.08:
        return "pending"
    elif r < 0.08 + denial_rate:
        return "denied"
    else:
        return "approved"

# ── Generate PA requests ─────────────────────────────────────────────────────
def generate_pa_requests(n=50000):
    rows = []
    payer_lookup = {p["payer_id"]: p for p in PAYERS}
    proc_lookup  = {p["procedure_code"]: p for p in PROCEDURES}

    for i in range(n):
        payer     = random.choice(PAYERS)
        procedure = random.choice(PROCEDURES)
        provider  = random.choice(PROVIDERS)
        is_urgent = random.random() < 0.15

        status = pick_status(payer, procedure)
        submitted_at, decided_at, elapsed_hours = make_timestamps(payer, is_urgent, status)
        sla_limit, sla_breach, approaching, days_pending = compute_sla(
            is_urgent, elapsed_hours, submitted_at, decided_at, status
        )

        denial_reason_code = None
        denial_reason_text = None
        if status == "denied":
            denial_reason_code, denial_reason_text = pick_denial_reason(procedure["procedure_code"])

        # Mirror elenafmoseyko RF model approval distribution (73.87% approval)
        auto_approve_score = None
        if status == "approved":
            auto_approve_score = round(random.uniform(0.47, 0.99), 4)
        elif status == "denied":
            auto_approve_score = round(random.uniform(0.01, 0.46), 4)
        else:
            auto_approve_score = round(random.uniform(0.20, 0.80), 4)

        rows.append({
            "request_id":          f"REQ{str(i+1).zfill(6)}",
            "patient_id":          f"PAT{fake.numerify('######')}",
            "provider_npi":        provider["provider_npi"],
            "payer_id":            payer["payer_id"],
            "procedure_code":      procedure["procedure_code"],
            "submitted_at":        submitted_at.strftime("%Y-%m-%d %H:%M:%S"),
            "decided_at":          decided_at.strftime("%Y-%m-%d %H:%M:%S") if decided_at else None,
            "status":              status,
            "is_urgent":           is_urgent,
            "denial_reason_code":  denial_reason_code,
            "denial_reason_text":  denial_reason_text,
            "elapsed_hours":       elapsed_hours,
            "sla_limit_hours":     sla_limit,
            "sla_breach_flag":     sla_breach,
            "approaching_breach":  approaching,
            "days_pending":        days_pending,
            "auto_approve_score":  auto_approve_score,
            "created_at":          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    return rows

# ── Write CSVs ───────────────────────────────────────────────────────────────
def write_csv(filename, rows, fieldnames):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Written: {path}  ({len(rows)} rows)")

if __name__ == "__main__":
    print("Generating synthetic PA data...")

    print("\n[1/4] pa_requests.csv")
    requests = generate_pa_requests(50000)
    write_csv("pa_requests.csv", requests, requests[0].keys())

    print("\n[2/4] payers.csv")
    write_csv("payers.csv", PAYERS, PAYERS[0].keys())

    print("\n[3/4] procedures.csv")
    write_csv("procedures.csv", PROCEDURES, PROCEDURES[0].keys())

    print("\n[4/4] providers.csv")
    write_csv("providers.csv", PROVIDERS, PROVIDERS[0].keys())

    # Quick sanity check
    approved = sum(1 for r in requests if r["status"] == "approved")
    denied   = sum(1 for r in requests if r["status"] == "denied")
    pending  = sum(1 for r in requests if r["status"] == "pending")
    breached = sum(1 for r in requests if r["sla_breach_flag"])

    print("\nDistribution check:")
    print(f"  Approved : {approved:,}  ({approved/500:.1f}%)")
    print(f"  Denied   : {denied:,}  ({denied/500:.1f}%)")
    print(f"  Pending  : {pending:,}  ({pending/500:.1f}%)")
    print(f"  SLA breach: {breached:,}  ({breached/500:.1f}%)")
    print("\nDone. All CSV files written to data/")