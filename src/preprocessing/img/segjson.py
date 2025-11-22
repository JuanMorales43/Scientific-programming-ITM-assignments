import os, re, shutil

"""
Copy and rename JSON segmentation files to the processed structure.

This script:
- Traverses the `data/processed` folder to build a dictionary that maps
  the patient ID to their folder name.
- Reads the original segmentation files in JSON format from
  `data/raw/TOMPEI-CMMD-Segmentations`.
- From the JSON file name, extracts the patient ID, view, and
  laterality using regular expressions.
- Locate the corresponding folder in `data/processed` and create the
  `seg/json` subfolder within each patient if it does not exist.
- Copy each JSON file to that location, renaming it according to the pattern
  `<ID>_<Laterality>_<View>_AnnotationFile.json`.
- (Optionally) allows internal references in the JSON to be corrected to the
  original names, if the corresponding lines are uncommented.
- Prints success or error messages for each processed file and a final one
  when finished.

Prepares the TOMPEI-CMMD segmentation files so that they have a
structure and nomenclature consistent with the processed images.
"""

# File paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

input_folder = os.path.join(REPO_ROOT, "data", "processed")

input_folder_segmentations = os.path.join(REPO_ROOT, "data", "raw", "TOMPEI-CMMD-Segmentations")

# Build a dictionary mapping patient IDs to folder names
folder_dict = {
    fn.split("_")[0]: fn
    for fn in os.listdir(input_folder)
    if os.path.isdir(os.path.join(input_folder, fn))
}

# Regular expression to parse the original JSON file names
pat = re.compile(r"^(D\d-\d{4})_(MLO|CC)_(R|L)_AnnotationFile\.json$", re.IGNORECASE)

for file_name in os.listdir(input_folder_segmentations):
    if not file_name.lower().endswith(".json"):
        continue

    m = pat.match(file_name)
    if not m:
        print(f"[SKIP] nombre no reconocido: {file_name}")
        continue

    pid, view, lat = m.group(1), m.group(2).upper(), m.group(3).upper()

    if pid not in folder_dict:
        print(f"[WARN] paciente {pid} no existe en {input_folder}")
        continue

    folder_name = folder_dict[pid]
    folder_path = os.path.join(input_folder, folder_name)
    json_dir = os.path.join(folder_path, "seg", "json")
    os.makedirs(json_dir, exist_ok=True)

    # New file name
    new_name = f"{folder_name}_{lat}_{view}_AnnotationFile.json"
    src_file = os.path.join(input_folder_segmentations, file_name)
    dst_file = os.path.join(json_dir, new_name)

    # Copy and rename the file
    shutil.copy2(src_file, dst_file)
    print(f"[OK] Copy and rename: {src_file} -> {dst_file}")

print("All done!")
