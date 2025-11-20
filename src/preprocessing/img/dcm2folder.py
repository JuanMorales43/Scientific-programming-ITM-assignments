import os
import pydicom
import shutil

# ==========================
# 0. Rutas base
# ==========================
# src/preprocessing/img/dcm2folder.py  → subimos 3 niveles → raíz del repo
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

input_folder = os.path.join(REPO_ROOT, "data", "raw")       # de aquí LEEMOS
output_folder = os.path.join(REPO_ROOT, "data", "processed")  # aquí ESCRIBIMOS

view_dict = {
    "CC": "cranio-caudal",
    "MLO": "medio-lateral oblique"
}

# ==========================
# 1. Recorrer pacientes en data/raw
# ==========================
for folder_name in os.listdir(input_folder):
    patient_raw_dir = os.path.join(input_folder, folder_name)
    if not os.path.isdir(patient_raw_dir):
        continue  # por si hay archivos sueltos

    # Carpeta destino: data/processed/<paciente>/dcm
    patient_out_dir = os.path.join(output_folder, folder_name)
    dcm_dir = os.path.join(patient_out_dir, "dcm")
    os.makedirs(dcm_dir, exist_ok=True)

    # ==========================
    # 2. Buscar .dcm de forma recursiva
    # ==========================
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
                vista = "UNK"  # por si aparece otra vista rara

            new_name = f"{folder_name}_{lateralidad}_{vista}.dcm"
            new_path = os.path.join(dcm_dir, new_name)

            shutil.move(dicom_path, new_path)
            print(f"Movido: {dicom_path} -> {new_path}")

print("Movimiento completado.")
