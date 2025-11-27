import os
import pandas as pd

"""
Generation of filtered clinical CSVs from the TOMPEI-CMMD sheet.

This script:
- Locates the `data/raw` folder, where each subfolder corresponds to a patient ID
  with its images.
- Reads the Excel file `TOMPEI-CMMD_clinical_data_v01_20250121.xlsx`
  located in `data/raw csv`.
- Filters the “Imaging Diagnosis Details Sheet” to keep only those
  records whose patient ID has a corresponding folder in `data/raw`.
- Filters the “Lesion Details Sheet” in the same way.
- Saves two filtered CSV files in `results/csv`:
  - `TOMPEI-CMMD_imaging_diagnosis_details.csv`
  - `TOMPEI-CMMD_lesion_details.csv`

This serves as a cleanup step to ensure that the clinical data is consistent with
the image folders actually available in the repository.
"""

# --- Paths ---
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

input_folder = os.path.join(REPO_ROOT, "data", "raw")
excel_file = os.path.join(
    REPO_ROOT, "data", "raw csv", "TOMPEI-CMMD_clinical_data_v01_20250121.xlsx"
)
output_csv_1 = os.path.join(
    REPO_ROOT, "results", "csv", "TOMPEI-CMMD_imaging_diagnosis_details.csv"
)
output_csv_2 = os.path.join(
    REPO_ROOT, "results", "csv", "TOMPEI-CMMD_lesion_details.csv"
)

# --- Existing IDs according to image folders ---
folder_names = set(os.listdir(input_folder))

# The actual header row is the second row in the sheet -> header=1
df1 = pd.read_excel(
    excel_file,
    sheet_name="Imaging Diagnosis Details Sheet",
    header=1
)

# Rename the first columns to more meaningful names
df1 = df1.rename(columns={
    "Unnamed: 0": "ID",
    "Unnamed: 1": "LeftRight",
    "Unnamed: 2": "Age",
    "Unnamed: 3": "classification",
})

# Filter rows by IDs that exist in data/raw
df1_filtered = df1[df1["ID"].astype(str).isin(folder_names)]

# Save filtered CSV
df1_filtered.to_csv(output_csv_1, index=False)

# In this sheet the real header row is the third row -> header=2
df2 = pd.read_excel(
    excel_file,
    sheet_name="Lesion Details Sheet",
    header=2
)

# In this sheet the patient ID column is named 'ID1'
df2_filtered = df2[df2["ID1"].astype(str).isin(folder_names)]

# Save filtered CSV
df2_filtered.to_csv(output_csv_2, index=False)

print("Filtered CSV files generated:")
print(" -", output_csv_1)
print(" -", output_csv_2)
