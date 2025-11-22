import os
import pydicom
from PIL import Image

"""
Converting DICOM files to TIFF images by patient and view.

This script:
- Scans the `data/processed` folder to locate patient folders
  with DICOM files.
- Reads each DICOM with `pydicom`, obtains the laterality and view, and uses
  `view_dict` to map the description to codes such as CC or MLO.
- Generates, if it does not exist, an `img` folder within each patient's folder
.
- Convert the pixel data from the DICOM into a `PIL.Image` image.
- Save the image as a TIFF with the name
  `<ID>_<Laterality>_<View>.tiff` in the `img` folder.
- Write the path of each file created and a final message saying
  “Conversion complete” to the console.

Allows TIFF images (suitable for certain workflows and
scientific tools) to be obtained from DICOM mammograms.
"""

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

input_folder = os.path.join(REPO_ROOT, "data", "processed")

view_dict = {
    "CC": "cranio-caudal",
    "MLO": "medio-lateral oblique"
}

# Process each patient folder
for folder_name in os.listdir(input_folder):
    folder_path = os.path.join(input_folder, folder_name)
    if os.path.isdir(folder_path):
        img_dir = os.path.join(folder_path, "img")
        os.makedirs(img_dir, exist_ok=True)
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".dcm"):
                dicom_path = os.path.join(folder_path, file_name)
                ds = pydicom.dcmread(dicom_path)
                #  Extract laterality and view
                lateralidad = ds.ImageLaterality
                code_meaning = ds.ViewCodeSequence[0].CodeMeaning
                vista = None
                for key, value in view_dict.items():
                    if value == code_meaning:
                        vista = key
                        break
                # Convert to TIFF
                img = Image.fromarray(ds.pixel_array)
                tiff_name = f"{folder_name}_{lateralidad}_{vista}.tiff"
                tiff_path = os.path.join(img_dir, tiff_name)
                img.save(tiff_path)
                print(f"Saved: {tiff_path}")
print("Conversion complete.")