import os
import sys
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegressionCV
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

"""
Module for selecting radiomic features using LASSO.

This script:
- Loads the `radiomics_merged.csv` file from the `results/csv` folder.
- Constructs a binary label vector (0 = benign, 1 = triple negative/TNBC)
  from the `classification_cmmd` and `subtype` columns.
- Extracts only the radiomic feature columns whose names
  begin with `original_`.
- Applies missing value imputation and standardization (z-score).
- Fits a logistic regression with L1 penalty (LASSO) using cross-validation
  to select the best regularization parameter.
- Determine which features have a non-zero coefficient and, if none
  are selected, keep the `TOP_K_FALLBACK` with the highest |coefficient|.
- Generate a new DataFrame that keeps all non-radiomic columns
  (ID, classification, etc.) and only the selected radiomic features.
- Prints the resulting CSV to `stdout` and additionally saves it to
  `radiomics_lasso_subset.csv` inside `results/csv`.

The script is designed to be run from the console as part of the feature selection analysis flow in the scientific programming lab.
"""

# File paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
csv_dir = os.path.join (REPO_ROOT, "results", "csv")
INPUT_CSV   = os.path.join (csv_dir, "radiomics_merged.csv")
OUTPUT_CSV  = os.path.join (csv_dir, "radiomics_lasso_subset.csv")
TOP_K_FALLBACK = 20 

df_full = pd.read_csv(INPUT_CSV)
original_cols_order = df_full.columns.tolist()
# Binary label construction
if "label" in df_full.columns:
    label = df_full["label"].copy()
else:
    subtype_norm = (df_full["subtype"].astype("string").str.strip().str.lower()
                    if "subtype" in df_full.columns else pd.Series(pd.NA, index=df_full.index))
    class_cmmd_norm = (df_full["classification_cmmd"].astype("string").str.strip().str.lower()
                       if "classification_cmmd" in df_full.columns else pd.Series(pd.NA, index=df_full.index))
    label = pd.Series(pd.NA, index=df_full.index)
    label[subtype_norm.isin(["triple negative", "tnbc"])] = 1
    label[class_cmmd_norm.eq("benign")] = 0

# Filter valid labels
mask_valid = label.isin([0, 1])
df = df_full.loc[mask_valid].copy()
y  = label.loc[mask_valid].astype(int).values

feature_cols = [c for c in df.columns if c.startswith("original_")]
if len(feature_cols) == 0:
    raise ValueError("No se encontraron columnas que inicien con 'original_'. Verifica tu CSV.")

X = df[feature_cols].copy()

imp = SimpleImputer(strategy="median")
X_imp = imp.fit_transform(X)

scaler = StandardScaler()
X_z = scaler.fit_transform(X_imp)

# LASSO 
lasso = LogisticRegressionCV(
    Cs=np.logspace(-3, 3, 20),
    cv=5,
    penalty="l1",
    solver="saga",
    scoring="roc_auc",
    class_weight="balanced",
    max_iter=5000,
    n_jobs=-1,
    refit=True,
    random_state=42
)
lasso.fit(X_z, y)

coefs = lasso.coef_.ravel()
abs_coefs = np.abs(coefs)
support = abs_coefs > 0

# Fallback if no features selected
if support.sum() == 0:
    k = min(TOP_K_FALLBACK, len(feature_cols))
    top_idx = np.argsort(-abs_coefs)[:k]
    support = np.zeros_like(abs_coefs, dtype=bool)
    support[top_idx] = True

selected_features = set(np.array(feature_cols)[support])

# Build reduced DataFrame
cols_out = []
for col in original_cols_order:
    if col.startswith("original_"):
        if col in selected_features:
            cols_out.append(col)
    else:
        cols_out.append(col)

df_reduced = df_full[cols_out].copy()
# Print to stdout
csv_text = df_reduced.to_csv(index=False)
sys.stdout.write(csv_text)

# Save to file
if OUTPUT_CSV:
    df_reduced.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved: {OUTPUT_CSV}", file=sys.stderr)