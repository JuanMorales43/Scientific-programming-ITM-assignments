import os
import pandas as pd
import shutil

"""
Cleaning molecular subtypes and copying valid patient folders.

This script:
- Reads the `CMMD_clinicaldata_revision.xlsx` file located in `data/raw csv`.
- Filters the DataFrame to discard records where the `subtype` is
  null and the `classification` column is ‘Malignant’, avoiding malignant cases
  without a defined subtype.
- For each value of `ID1` in the filtered DataFrame, copies the corresponding folder
  from `data/raw` to `data/raw csv`, preserving the
  directory structure.
- Uses `shutil.copytree` with `dirs_exist_ok=True` to update or create
  the output folders.

This is part of the preprocessing to obtain a subset of patients
with consistent molecular subtype information.
"""

# File paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

route_input_folder  = os.path.join (REPO_ROOT, "data", "raw")
route_output_folder = os.path.join (REPO_ROOT, "data", "raw csv")
csv_file            = os.path.join (route_output_folder, "CMMD_clinicaldata_revision.xlsx")

# Read the Excel file
df = pd.read_excel(csv_file)

# Filter out records with null subtype and classification 'Malignant'
filtered_df = df[~(df['subtype'].isnull() & (df['classification'] == 'Malignant'))]

# Copy corresponding folders for each valid ID1
for folder_name in filtered_df['ID1']:
    src = os.path.join(route_input_folder, str(folder_name))
    dst = os.path.join(route_output_folder, str(folder_name))
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
