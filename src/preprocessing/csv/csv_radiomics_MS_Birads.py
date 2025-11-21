import pandas as pd
import os

"""
Combination of radiomics, molecular subtype, and BI-RADS in a single CSV.

This script:
- Loads three CSV files from `results/csv`:
  - `radiomics_features.csv`: radiomic features extracted with PyRadiomics.
  - `CMMD_clinicaldata_revision_clean.csv`: clinical and subtype information.
  - `TOMPEI-CMMD_imaging_diagnosis_details.csv`: BI-RADS and diagnosis information.
- Merges these DataFrames using patient identifiers
  to obtain a single combined DataFrame.
- Creates an `ID` column as the primary identifier (derived from the CMMD/TOMPEI IDs
).
- Remove redundant identification columns (`PatientID`, `ID_cmmd`,
  `ID_tompei`) and reorder the columns so that they appear at the beginning:
  `ID`, `classification_cmmd`, `classification_tompei`, `subtype`, `BI-RADS`.
- Save the result in `results/csv/radiomics_merged.csv`.

This combined file is used as the main input for
feature selection and supervised classification analyses.
"""


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

csv_subtype  = os.path.join (REPO_ROOT, "results", "csv", "CMMD_clinicaldata_revision_clean.csv")
csv_radiomics= os.path.join (REPO_ROOT, "results", "csv", "radiomics_features.csv")
csv_birads   = os.path.join (REPO_ROOT, "results", "csv", "TOMPEI-CMMD_imaging_diagnosis_details.csv")
csv_output   = os.path.join (REPO_ROOT, "results", "csv", "radiomics_merged.csv")

# Leer archivos
df_radiomics = pd.read_csv(csv_radiomics, dtype=str)
df_subtype   = pd.read_csv(csv_subtype, dtype=str)
df_birads    = pd.read_csv(csv_birads, dtype=str)

# (Opcional pero recomendado) normalizar IDs para evitar no-coincidencias
df_radiomics["PatientID"] = df_radiomics["PatientID"].astype(str).str.strip().str.upper()
df_subtype["ID"]          = df_subtype["ID1"].astype(str).str.strip().str.upper()
df_birads["ID"]           = df_birads["ID"].astype(str).str.strip().str.upper()

# Unir radiomics con subtype
df_merged = df_radiomics.merge(
    df_subtype[['ID', 'classification', 'subtype']].drop_duplicates('ID'),
    left_on='PatientID', right_on='ID', how='left'
)

# Unir con birads (los sufijos crean classification_cmmd y classification_tompei)
df_merged = df_merged.merge(
    df_birads[['ID', 'classification', 'BI-RADS']].drop_duplicates('ID'),
    left_on='PatientID', right_on='ID', how='left', suffixes=('_cmmd', '_tompei')
)

# Usar el ID de subtype como identificador principal
df_merged['ID'] = df_merged['ID_cmmd']

# Eliminar columnas de PatientID y IDs extra
df_merged.drop(columns=['PatientID', 'ID_cmmd', 'ID_tompei'], inplace=True)

# Reordenar columnas al inicio
cols_inicio = ['ID', 'classification_cmmd', 'classification_tompei',  'subtype', 'BI-RADS']
cols_inicio = [c for c in cols_inicio if c in df_merged.columns]  # por si acaso
cols_restantes = [c for c in df_merged.columns if c not in cols_inicio]
df_merged = df_merged[cols_inicio + cols_restantes]

# Guardar CSV
df_merged.to_csv(csv_output, index=False)
print(f"CSV generado en: {csv_output}")