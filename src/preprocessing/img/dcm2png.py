import os
import pydicom
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

input_folder = os.path.join(REPO_ROOT, "data", "processed")  # de aquí LEEMOS

view_dict = {
    "CC": "cranio-caudal",
    "MLO": "medio-lateral oblique"
}

for folder_name in os.listdir(input_folder):
    folder_path = os.path.join(input_folder, folder_name)
    if os.path.isdir(folder_path):
        img_dir = os.path.join(folder_path, "png")
        os.makedirs(img_dir, exist_ok=True)
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".dcm"):
                dicom_path = os.path.join(folder_path, file_name)
                ds = pydicom.dcmread(dicom_path)
                # Obtener lateralidad y vista
                lateralidad = ds.ImageLaterality
                code_meaning = ds.ViewCodeSequence[0].CodeMeaning
                vista = None
                for key, value in view_dict.items():
                    if value == code_meaning:
                        vista = key
                        break
                # Convertir a imagen y guardar como PNG
                img = Image.fromarray(ds.pixel_array)
                png_name = f"{folder_name}_{lateralidad}_{vista}.png"
                png_path = os.path.join(img_dir, png_name)
                img.save(png_path)
                print(f"Guardado: {png_path}")
print("Conversión completada.")