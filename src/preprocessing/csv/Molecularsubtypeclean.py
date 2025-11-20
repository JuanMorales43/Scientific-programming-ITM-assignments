import os
import pandas as pd
import shutil

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

route_input_folder  = os.path.join (REPO_ROOT, "data", "raw")
route_output_folder = os.path.join (REPO_ROOT, "data", "raw csv")
csv_file            = os.path.join (route_output_folder, "CMMD_clinicaldata_revision.xlsx")

# Leer el archivo CSV/Excel
df = pd.read_excel(csv_file)

# Filtrar: ignorar donde subtype es nulo y classification es 'Malignant'
filtered_df = df[~(df['subtype'].isnull() & (df['classification'] == 'Malignant'))]

# Copiar carpetas que coincidan con el valor de la columna ID1
for folder_name in filtered_df['ID1']:
    src = os.path.join(route_input_folder, str(folder_name))
    dst = os.path.join(route_output_folder, str(folder_name))
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
