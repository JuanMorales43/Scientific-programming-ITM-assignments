import os
import pandas as pd
from radiomics import featureextractor
from pathlib import Path


class RadiomicsFeatureExtractor:
    def __init__(self, input_folder, output_file="radiomics_features.csv"):
        self.input_folder = input_folder
        self.output_file = output_file
        self.params = {
            'binWidth': 10,
            'resampledPixelSpacing': None,
            'interpolator': 'sitkBSpline',
            'normalize': False,
            'enableCExtensions': True,
        }
        self.extractor = None
        self.imgs_path = []
        self.segs_path = []
        self.all_features = []
    
    def setup_extractor(self):
        self.extractor = featureextractor.RadiomicsFeatureExtractor(**self.params)
        self.extractor.enableFeatureClassByName('shape2D')
        self.extractor.enableFeatureClassByName('firstorder')
        self.extractor.enableFeatureClassByName('glcm')
        self.extractor.enableFeatureClassByName('glrlm')
        self.extractor.enableFeatureClassByName('glszm')
        self.extractor.enableFeatureClassByName('gldm')
        self.extractor.enableFeatureClassByName('ngtdm')
    
    def find_image_mask_pairs(self):
        patient_ids = [patient_id for patient_id in os.listdir(self.input_folder)]
        
        for patient_id in patient_ids:
            seg_path = os.path.join(self.input_folder, patient_id, "seg", "mask")
            img_path = os.path.join(self.input_folder, patient_id, "img")
            
            if not (os.path.isdir(seg_path) and os.path.isdir(img_path)):
                continue
            
            seg_files = [f for f in os.listdir(seg_path) if f.endswith('.tiff')]
            img_files = set(os.listdir(img_path))
            
            for seg_file in seg_files:
                base_name = seg_file.replace('_mask.tiff', '')
                img_file = f"{base_name}.tiff"
                if img_file in img_files:
                    self.imgs_path.append(os.path.join(img_path, img_file))
                    self.segs_path.append(os.path.join(seg_path, seg_file))
    
    def extract_features(self):
        for img, seg in zip(self.imgs_path, self.segs_path):
            print(f"Processing image: {img} with mask: {seg}")
            ID = Path(img).parts[-3]
            result = self.extractor.execute(img, seg, label=255)
            features = {k: v for k, v in result.items() if 'diagnostics' not in k}
            features['PatientID'] = ID
            self.all_features.append(features)
    
    def save_features(self):
        df = pd.DataFrame(self.all_features)
        df.to_csv(self.output_file, index=False)
        print(f"Features extracted and saved to {self.output_file}")
    
    def run(self):
        self.setup_extractor()
        self.find_image_mask_pairs()
        self.extract_features()
        self.save_features()


if __name__ == "__main__":
    input_folder = "/mnt/Datos/05-CMMD_Depurado/CMMD_MSC" # Para cambiar esto debo subir toda la base de datos
    extractor = RadiomicsFeatureExtractor(input_folder)
    extractor.run()
