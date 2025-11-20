import os
import pandas as pd
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

input_folder = os.path.join (REPO_ROOT, "data", "raw")
route_output_folder = os.path.join (REPO_ROOT, "data", "raw csv")
excel_file = os.path.join (REPO_ROOT, "data", "raw csv", "TOMPEI-CMMD_clinical_data_v01_20250121.xlsx")
output_csv_1 = os.path.join (REPO_ROOT, "results", "csv","TOMPEI-CMMD_imaging_diagnosis_details.csv")
output_csv_2 = os.path.join (REPO_ROOT, "results", "csv","TOMPEI-CMMD_lesion_details.csv")

# Obtener nombres de carpetas existentes
folder_names = set(os.listdir(input_folder))

# Leer hoja "Imaging Diagnosis Details Sheet"
df1 = pd.read_excel(excel_file, sheet_name="Imaging Diagnosis Details Sheet")
df1_filtered = df1[df1['ID'].astype(str).isin(folder_names)]
df1_filtered.to_csv(output_csv_1, index=False)

# Leer hoja "Lesion Details Sheet"
df2 = pd.read_excel(excel_file, sheet_name="Lesion Details Sheet")
df2_filtered = df2[df2['ID1'].astype(str).isin(folder_names)]
df2_filtered.to_csv(output_csv_2, index=False)