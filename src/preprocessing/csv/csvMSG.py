import os
import pandas as pd

input_folder = "/mnt/Datos/05-CMMD_Depurado/CMMD_MSC"
csv_file     = "/mnt/Datos/03 - CMMD/CMMD_clinicaldata_revision.xlsx"
output_csv   = "/mnt/Datos/05-CMMD_Depurado/CMMD_clinicaldata_revision_filtered.csv"

# Obtener nombres de carpetas existentes
folder_names = set(os.listdir(input_folder))

# Leer el archivo Excel
df = pd.read_excel(csv_file)

# Filtrar solo los registros cuyo ID1 esté en las carpetas
filtered_df = df[df['ID1'].astype(str).isin(folder_names)]

# Guardar el nuevo CSV
filtered_df.to_csv(output_csv, index=False)