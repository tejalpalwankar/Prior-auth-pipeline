import pandas as pd
import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_CANDIDATES = [
    # Where the generator *writes* the DuckDB file (not the CSVs).
    os.path.join(SCRIPT_DIR, "data"),
    # Where the synthetic input CSVs live.
    os.path.join(SCRIPT_DIR, "generator", "data"),
]

def resolve_data_dir():
    # Expected CSVs for training.
    required = ["pa_requests.csv", "payers.csv", "procedures.csv"]
    for d in DATA_CANDIDATES:
        if all(os.path.exists(os.path.join(d, f)) for f in required):
            return d
    raise FileNotFoundError(
        "Could not find required training CSVs (pa_requests.csv, payers.csv, procedures.csv). "
        f"Tried: {DATA_CANDIDATES}"
    )

DATA_DIR = resolve_data_dir()
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# ── Load data ────────────────────────────────────────────────────────────────
print("Loading data...")
requests   = pd.read_csv(f"{DATA_DIR}/pa_requests.csv")
payers     = pd.read_csv(f"{DATA_DIR}/payers.csv")
procedures = pd.read_csv(f"{DATA_DIR}/procedures.csv")

df = requests.merge(payers, on="payer_id", how="left")
df = df.merge(procedures, on="procedure_code", how="left")

# ── Feature engineering ──────────────────────────────────────────────────────
print("Engineering features...")

# Only use decided requests (not pending — no label)
df = df[df["status"] != "pending"].copy()

df["submitted_at"] = pd.to_datetime(df["submitted_at"])
df["hour_of_day"]  = df["submitted_at"].dt.hour
df["day_of_week"]  = df["submitted_at"].dt.dayofweek
df["is_weekend"]   = (df["day_of_week"] >= 5).astype(int)
df["is_urgent"]    = df["is_urgent"].astype(int)
df["high_denial"]  = df["high_denial"].astype(int)

# Encode categoricals
le_payer   = LabelEncoder()
le_proc    = LabelEncoder()
le_spec    = LabelEncoder()

df["payer_encoded"]     = le_payer.fit_transform(df["payer_id"])
df["procedure_encoded"] = le_proc.fit_transform(df["procedure_code"])
df["specialty_encoded"] = le_spec.fit_transform(df["specialty"])

# Target: 1 = approved, 0 = denied
df["target"] = (df["status"] == "approved").astype(int)

FEATURES = [
    "payer_encoded",
    "procedure_encoded",
    "specialty_encoded",
    "is_urgent",
    "high_denial",
    "avg_response_hrs",
    "base_denial_rate",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
]

X = df[FEATURES]
y = df["target"]

print(f"Training set: {len(df):,} decided requests")
print(f"Approval rate: {y.mean()*100:.1f}%")

# ── Train / test split ───────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── Train Random Forest ──────────────────────────────────────────────────────
print("\nTraining Random Forest...")
rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=8,
    min_samples_leaf=20,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced",
)
rf.fit(X_train, y_train)

y_pred  = rf.predict(X_test)
y_proba = rf.predict_proba(X_test)[:, 1]

print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=["Denied", "Approved"]))
print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")

# ── Feature importance ───────────────────────────────────────────────────────
importance = pd.DataFrame({
    "feature":    FEATURES,
    "importance": rf.feature_importances_
}).sort_values("importance", ascending=False)
print("\nFeature Importance:")
print(importance.to_string(index=False))

# ── Denial reason model (multi-class) ────────────────────────────────────────
print("\nTraining denial reason classifier...")
denied_df = df[df["status"] == "denied"].copy()
le_reason = LabelEncoder()
denied_df["reason_encoded"] = le_reason.fit_transform(
    denied_df["denial_reason_code"].fillna("UNKNOWN")
)

X_denied = denied_df[FEATURES]
y_reason = denied_df["reason_encoded"]

X_tr2, X_te2, y_tr2, y_te2 = train_test_split(
    X_denied, y_reason, test_size=0.2, random_state=42
)

reason_model = GradientBoostingClassifier(
    n_estimators=100, max_depth=4, random_state=42
)
reason_model.fit(X_tr2, y_tr2)
print(f"Denial reason accuracy: {reason_model.score(X_te2, y_te2)*100:.1f}%")

# ── Save everything ──────────────────────────────────────────────────────────
print("\nSaving model artifacts...")
artifacts = {
    "approval_model":   rf,
    "reason_model":     reason_model,
    "le_payer":         le_payer,
    "le_procedure":     le_proc,
    "le_specialty":     le_spec,
    "le_reason":        le_reason,
    "features":         FEATURES,
    "payer_meta":       payers.set_index("payer_id").to_dict("index"),
    "procedure_meta":   procedures.set_index("procedure_code").to_dict("index"),
}

with open(f"{MODEL_DIR}/pa_model.pkl", "wb") as f:
    pickle.dump(artifacts, f)

print(f"Saved to {MODEL_DIR}/pa_model.pkl")
print("\nDone.")
