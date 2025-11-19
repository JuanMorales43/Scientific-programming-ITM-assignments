import os
import pandas as pd

input_folder = "/mnt/Datos/05-CMMD_Depurado/CMMD_MSC"
excel_file = "/mnt/Datos/04 - TOMPEI-CMMD/TOMPEI-CMMD_clinical_data_v01_20250121.xlsx"
output_csv_1 = "/mnt/Datos/05-CMMD_Depurado/TOMPEI-CMMD_imaging_diagnosis_details.csv"
output_csv_2 = "/mnt/Datos/05-CMMD_Depurado/TOMPEI-CMMD_lesion_details.csv"

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