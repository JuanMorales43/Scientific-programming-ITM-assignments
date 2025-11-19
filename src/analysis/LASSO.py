import os
import sys
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegressionCV
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

# ==========================
# Configuración
# ==========================
INPUT_CSV   = "/media/imagenesmedicas/DATA1/01-ImagenesMedicas-US1/08-MasterCamilo/05-CMMD_Depurado/CSV/radiomics_merged.csv"
OUTPUT_CSV  = "radiomics_lasso_subset.csv"
TOP_K_FALLBACK = 20  # si LASSO no deja ninguna, conservar top-k por |coef|

# ==========================
# 1) Cargar CSV
# ==========================
df_full = pd.read_csv(INPUT_CSV)
# Conservamos el orden original de columnas para la salida
original_cols_order = df_full.columns.tolist()

# ==========================
# 2) Construir/Inferir 'label' SOLO para el ajuste (no se agrega si no existía)
# ==========================
if "label" in df_full.columns:
    label = df_full["label"].copy()
else:
    # Inferencia: Benign -> 0; TNBC/triple negative -> 1
    subtype_norm = (df_full["subtype"].astype("string").str.strip().str.lower()
                    if "subtype" in df_full.columns else pd.Series(pd.NA, index=df_full.index))
    class_cmmd_norm = (df_full["classification_cmmd"].astype("string").str.strip().str.lower()
                       if "classification_cmmd" in df_full.columns else pd.Series(pd.NA, index=df_full.index))
    label = pd.Series(pd.NA, index=df_full.index)
    label[subtype_norm.isin(["triple negative", "tnbc"])] = 1
    label[class_cmmd_norm.eq("benign")] = 0

# Filtramos filas con label válido 0/1 para entrenar LASSO
mask_valid = label.isin([0, 1])
df = df_full.loc[mask_valid].copy()
y  = label.loc[mask_valid].astype(int).values

# ==========================
# 3) Definir matriz de características: solo columnas 'original_*'
# ==========================
feature_cols = [c for c in df.columns if c.startswith("original_")]
if len(feature_cols) == 0:
    raise ValueError("No se encontraron columnas que inicien con 'original_'. Verifica tu CSV.")

X = df[feature_cols].copy()

# ==========================
# 4) Imputación + Estandarización (fit solo en las filas válidas)
# ==========================
imp = SimpleImputer(strategy="median")
X_imp = imp.fit_transform(X)

scaler = StandardScaler()
X_z = scaler.fit_transform(X_imp)

# ==========================
# 5) LASSO (Regresión Logística con L1) para selección
# ==========================
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

# Fallback: si nada queda seleccionado, conservar top-k por |coef|
if support.sum() == 0:
    k = min(TOP_K_FALLBACK, len(feature_cols))
    top_idx = np.argsort(-abs_coefs)[:k]
    support = np.zeros_like(abs_coefs, dtype=bool)
    support[top_idx] = True

selected_features = set(np.array(feature_cols)[support])

# ==========================
# 6) Construir el DataFrame de salida
#    - Mantener el ORDEN de columnas original
#    - Eliminar SOLO las 'original_*' que NO fueron seleccionadas
#    - Conservar todas las demás columnas (ID, subtype, etc.) tal cual
# ==========================
cols_out = []
for col in original_cols_order:
    if col.startswith("original_"):
        if col in selected_features:
            cols_out.append(col)
        # si no fue seleccionada, se descarta
    else:
        # columnas no características se conservan
        cols_out.append(col)

df_reduced = df_full[cols_out].copy()

# ==========================
# 7) Imprimir el dataset por stdout en formato CSV
# ==========================
csv_text = df_reduced.to_csv(index=False)
sys.stdout.write(csv_text)

# ==========================
# 8) (Opcional) Guardar a archivo
# ==========================
if OUTPUT_CSV:
    df_reduced.to_csv(OUTPUT_CSV, index=False)
    # Mensaje a stderr para no mezclar con la impresión del CSV en stdout
    print(f"\nGuardado en: {OUTPUT_CSV}", file=sys.stderr)