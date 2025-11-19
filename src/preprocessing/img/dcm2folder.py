import os
import pydicom
import shutil

input_folder = "/mnt/Datos/05-CMMD_Depurado/CMMD_MSC"

view_dict = {
    "CC": "cranio-caudal",
    "MLO": "medio-lateral oblique"
}

for folder_name in os.listdir(input_folder):
    folder_path = os.path.join(input_folder, folder_name)
    if os.path.isdir(folder_path):
        dcm_dir = os.path.join(folder_path, "dcm")
        os.makedirs(dcm_dir, exist_ok=True)
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".dcm"):
                dicom_path = os.path.join(folder_path, file_name)
                ds = pydicom.dcmread(dicom_path)
                lateralidad = ds.ImageLaterality
                code_meaning = ds.ViewCodeSequence[0].CodeMeaning
                vista = None
                for key, value in view_dict.items():
                    if value == code_meaning:
                        vista = key
                        break
                new_name = f"{folder_name}_{lateralidad}_{vista}.dcm"
                new_path = os.path.join(dcm_dir, new_name)
                shutil.move(dicom_path, new_path)
                print(f"Movido: {new_path}")
print("Movimiento completado.")