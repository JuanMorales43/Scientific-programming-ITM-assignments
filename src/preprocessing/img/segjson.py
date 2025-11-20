import os, re, shutil

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

input_folder = os.path.join(REPO_ROOT, "data", "processed")

input_folder_segmentations = os.path.join(REPO_ROOT, "data", "raw", "TOMPEI-CMMD-Segmentations")

# Mapa: ID de paciente -> nombre de carpeta en input_folder
folder_dict = {
    fn.split("_")[0]: fn
    for fn in os.listdir(input_folder)
    if os.path.isdir(os.path.join(input_folder, fn))
}

# Nombres tipo: D1-0001_MLO_R_AnnotationFile.json
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

    # Nuevo nombre normalizado: ID_LAT_VIEW_AnnotationFile.json
    new_name = f"{folder_name}_{lat}_{view}_AnnotationFile.json"
    src_file = os.path.join(input_folder_segmentations, file_name)
    dst_file = os.path.join(json_dir, new_name)

    # Copiar tal cual (sin tocar el contenido)
    shutil.copy2(src_file, dst_file)

    # --- OPCIONAL: si dentro del JSON aparece el nombre viejo y quieres corregirlo:
    # with open(dst_file, "r", encoding="utf-8") as f:
    #     s = f.read()
    # s = s.replace(f"{pid}_{view}_{lat}_", f"{folder_name}_{lat}_{view}_")
    # with open(dst_file, "w", encoding="utf-8") as f:
    #     f.write(s)

    print(f"[OK] Copiado y renombrado: {src_file} -> {dst_file}")

print("All done!")
