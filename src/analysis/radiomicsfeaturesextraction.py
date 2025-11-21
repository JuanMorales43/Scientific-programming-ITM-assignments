import os
import pandas as pd
from radiomics import featureextractor
from pathlib import Path

"""
Module for extracting radiomic features with PyRadiomics.

This script:
- Defines the input path `data/processed`, which contains the images
  (mammograms) organized by patient and view, and the associated
  segmentation masks.
- Configures a PyRadiomics extractor (binWidth, interpolator, normalization,
  feature families, etc.).
- Recursively traverses the patient folders to locate pairs
  (image, mask) that match the defined naming pattern.
- Runs the extractor on each image-mask pair, filtering the
  diagnostic features (`diagnostics_*`) to retain only
  the radiomic ones.
- Adds the patient identifier (`PatientID`) to each record.
- Builds a DataFrame with all the extracted features and saves it
  as `radiomics_features.csv` in the `results/csv` folder.

It is used as a feature extraction stage in the project's radiomic analysis pipeline.
"""

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
input_folder = os.path.join (REPO_ROOT, "data", "processed")
output_folder = os.path.join (REPO_ROOT, "results", "csv")
out_csv_path = os.path.join (output_folder, "radiomics_features.csv")

params = {
    'binWidth': 10,
    'resampledPixelSpacing': None,
    'interpolator': 'sitkBSpline',
    'normalize': False,
    'enableCExtensions': True,
}

extractor = featureextractor.RadiomicsFeatureExtractor(**params)

extractor.enableFeatureClassByName('shape2D')
extractor.enableFeatureClassByName('firstorder')
extractor.enableFeatureClassByName('glcm')
extractor.enableFeatureClassByName('glrlm')
extractor.enableFeatureClassByName('glszm')
extractor.enableFeatureClassByName('gldm')
extractor.enableFeatureClassByName('ngtdm')

patient_ids = []

for patient_id in os.listdir(input_folder):
    patient_ids.append(patient_id)

imgs_path = []
segs_path = []

for patient_id in patient_ids:
    seg_path = os.path.join(input_folder, patient_id, "seg", "mask")
    img_path = os.path.join(input_folder, patient_id, "img")
    if not (os.path.isdir(seg_path) and os.path.isdir(img_path)):
        continue

    seg_files = [f for f in os.listdir(seg_path) if f.endswith('.tiff')]
    img_files = set(os.listdir(img_path))

    for seg_file in seg_files:
        base_name = seg_file.replace('_mask.tiff', '')
        img_file = f"{base_name}.tiff"
        if img_file in img_files:
            imgs_path.append(os.path.join(img_path, img_file))
            segs_path.append(os.path.join(seg_path, seg_file))

all_features = []
for img, seg in zip(imgs_path, segs_path):
    print(f"Processing image: {img} with mask: {seg}")
    ID = Path(img).parts[-3]
    result = extractor.execute(img, seg, label=255)
    features = {k: v for k, v in result.items() if 'diagnostics' not in k}
    features['PatientID'] = ID
    all_features.append(features)

df = pd.DataFrame(all_features)
df.to_csv(out_csv_path, index=False)
print("Features extracted and saved to radiomics_features.csv")