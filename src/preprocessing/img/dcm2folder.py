import os
import pydicom
import shutil

"""
Reorganization of DICOM files into folders by patient and view.

This script:
- Scans the `data/raw` folder for DICOM files.
- For each DICOM file, reads the relevant metadata with `pydicom`:
  - `PatientID` to identify the patient folder.
  - `ImageLaterality` (L/R) and `ViewCodeSequence` to identify the view
    (e.g., CC or MLO).
- Creates, if they do not exist, output subfolders in `data/processed` with the
  structure:
    data/processed/<ID>/dcm
- Renames and moves each DICOM file with the pattern
  `<ID>_<Laterality>_<View>.dcm`.
- Uses the `view_dict` dictionary to translate the view description
  from PyDICOM to the abbreviated code (CC, MLO); if not recognized, uses `UNK`.
- Print the movements made and a final message to the console when
  the process is complete.

This serves as the first step in organizing raw mammograms before
their subsequent conversion to images and segmentations.
"""

# File paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

input_folder = os.path.join(REPO_ROOT, "data", "raw")     
output_folder = os.path.join(REPO_ROOT, "data", "processed") 

view_dict = {
    "CC": "cranio-caudal",
    "MLO": "medio-lateral oblique"
}


# Process each patient folder
for folder_name in os.listdir(input_folder):
    patient_raw_dir = os.path.join(input_folder, folder_name)
    if not os.path.isdir(patient_raw_dir):
        continue 

    patient_out_dir = os.path.join(output_folder, folder_name)
    dcm_dir = os.path.join(patient_out_dir, "dcm")
    os.makedirs(dcm_dir, exist_ok=True)

    for root, dirs, files in os.walk(patient_raw_dir):
        for file_name in files:
            if not file_name.lower().endswith(".dcm"):
                continue

            dicom_path = os.path.join(root, file_name)
            ds = pydicom.dcmread(dicom_path)

            lateralidad = ds.ImageLaterality
            code_meaning = ds.ViewCodeSequence[0].CodeMeaning

            vista = None
            for key, value in view_dict.items():
                if value == code_meaning:
                    vista = key
                    break
            if vista is None:
                vista = "UNK"
            # Move and rename the DICOM file
            new_name = f"{folder_name}_{lateralidad}_{vista}.dcm"
            new_path = os.path.join(dcm_dir, new_name)
            shutil.move(dicom_path, new_path)
            print(f"Moved: {dicom_path} -> {new_path}")

print("DICOM files have been reorganized successfully.")
