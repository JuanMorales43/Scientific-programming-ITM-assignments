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

# File paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
csv_subtype  = os.path.join (REPO_ROOT, "results", "csv", "CMMD_clinicaldata_revision_filtered.csv")
csv_radiomics= os.path.join (REPO_ROOT, "results", "csv", "radiomics_features.csv")
csv_birads   = os.path.join (REPO_ROOT, "results", "csv", "TOMPEI-CMMD_imaging_diagnosis_details.csv")
csv_output   = os.path.join (REPO_ROOT, "results", "csv", "radiomics_merged.csv")

# Read files
df_radiomics = pd.read_csv(csv_radiomics, dtype=str)
df_subtype   = pd.read_csv(csv_subtype, dtype=str)
df_birads    = pd.read_csv(csv_birads, dtype=str)

# Normalize IDs
df_radiomics["PatientID"] = df_radiomics["PatientID"].astype(str).str.strip().str.upper()
df_subtype["ID"]          = df_subtype["ID1"].astype(str).str.strip().str.upper()
df_birads["ID"]           = df_birads["ID"].astype(str).str.strip().str.upper()

# Combine radiomics with subtype
df_merged = df_radiomics.merge(
    df_subtype[['ID', 'classification', 'subtype']].drop_duplicates('ID'),
    left_on='PatientID', right_on='ID', how='left'
)

# Join with birads (the suffixes create classification_cmmd and classification_tompei)
df_merged = df_merged.merge(
    df_birads[['ID', 'classification', 'Unnamed: 21']].drop_duplicates('ID'),
    left_on='PatientID', right_on='ID', how='left', suffixes=('_cmmd', '_tompei')
)

# Use the subtype ID as the primary identifier
df_merged['ID'] = df_merged['ID_cmmd']

# Remove PatientID and extra ID columns
df_merged.drop(columns=['PatientID', 'ID_cmmd', 'ID_tompei'], inplace=True)

# Reorder new columns at the beginning
cols_inicio = ['ID', 'classification_cmmd', 'classification_tompei',  'subtype', 'BI-RADS']
cols_inicio = [c for c in cols_inicio if c in df_merged.columns]  # por si acaso
cols_restantes = [c for c in df_merged.columns if c not in cols_inicio]
df_merged = df_merged[cols_inicio + cols_restantes]

# Save CSV
df_merged.to_csv(csv_output, index=False)
print(f"CSV generado en: {csv_output}")