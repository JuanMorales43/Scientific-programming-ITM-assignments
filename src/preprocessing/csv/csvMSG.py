import os
import pandas as pd

"""
Filtering the CMMD clinical file to retain only patients with available images.

This script:
- Obtains the list of patient folders in `data/raw`.
- Reads the `CMMD_clinicaldata_revision.xlsx` file from `data/raw csv`.
- Filters the rows whose `ID1` matches any of the patient folders.
- Saves the result in `results/csv/CMMD_clinicaldata_revision_filtered.csv`.

It is used to align CMMD clinical information with the images that
are actually on the disk.
"""

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

input_folder = os.path.join (REPO_ROOT, "data", "raw")
route_output_folder = os.path.join (REPO_ROOT, "data", "raw csv")
csv_file            = os.path.join (route_output_folder, "CMMD_clinicaldata_revision.xlsx")
output_csv   = os.path.join (REPO_ROOT, "results", "csv", "CMMD_clinicaldata_revision_filtered.csv")

# Obtener nombres de carpetas existentes
folder_names = set(os.listdir(input_folder))

# Leer el archivo Excel
df = pd.read_excel(csv_file)

# Filtrar solo los registros cuyo ID1 esté en las carpetas
filtered_df = df[df['ID1'].astype(str).isin(folder_names)]

# Guardar el nuevo CSV
filtered_df.to_csv(output_csv, index=False)