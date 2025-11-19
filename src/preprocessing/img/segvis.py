import os
import json
from PIL import Image, ImageDraw

input_folder = "/mnt/Datos/05-CMMD_Depurado/CMMD_MSC"

for patient in os.listdir(input_folder):
    patient_path = os.path.join(input_folder, patient)
    if not os.path.isdir(patient_path):
        continue

    json_folder = os.path.join(patient_path, "seg", "json")
    vis_folder  = os.path.join(patient_path, "seg", "vis")
    png_folder  = os.path.join(patient_path, "png")

    if not os.path.exists(json_folder):
        print(f"[Aviso] No existe la carpeta JSON para {patient}")
        continue

    os.makedirs(vis_folder, exist_ok=True)

    for fname in os.listdir(json_folder):
        if not fname.lower().endswith("_annotationfile.json"):
            continue

        json_path = os.path.join(json_folder, fname)
        id_lat_view = fname.replace("_AnnotationFile.json", "")
        png_path = os.path.join(png_folder, f"{id_lat_view}.png")
        vis_path = os.path.join(vis_folder, f"{id_lat_view}_segvis.png")

        if not os.path.exists(png_path):
            print(f"[Aviso] No existe la imagen PNG: {png_path}")
            continue

        # Cargar JSON (puede ser dict o lista)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ERROR] JSON inválido {json_path}: {e}")
            continue

        # ======== Extraer polígonos en formato [(x,y), ...] ========
        polygons = []

        # Caso: dict (LabelMe: shapes; Genérico: polygons; VGG: regions)
        if isinstance(data, dict):
            # LabelMe: {"shapes":[{"points":[[x,y],...]}, ...]}
            if "shapes" in data and isinstance(data["shapes"], list):
                for sh in data["shapes"]:
                    pts = sh.get("points", [])
                    if isinstance(pts, list) and len(pts) >= 3:
                        poly = []
                        for p in pts:
                            if isinstance(p, (list, tuple)) and len(p) == 2:
                                poly.append((float(p[0]), float(p[1])))
                            elif isinstance(p, dict) and "x" in p and "y" in p:
                                poly.append((float(p["x"]), float(p["y"])))
                        if len(poly) >= 3:
                            polygons.append(poly)

            # Genérico: {"polygons":[[(x,y),...], ...]}
            if not polygons and "polygons" in data and isinstance(data["polygons"], list):
                for pts in data["polygons"]:
                    if isinstance(pts, list) and len(pts) >= 3:
                        poly = []
                        for p in pts:
                            if isinstance(p, (list, tuple)) and len(p) == 2:
                                poly.append((float(p[0]), float(p[1])))
                            elif isinstance(p, dict) and "x" in p and "y" in p:
                                poly.append((float(p["x"]), float(p["y"])))
                        if len(poly) >= 3:
                            polygons.append(poly)

            # VGG VIA: {"regions":[{"shape_attributes":{"name":"polygon","all_points_x":[...],"all_points_y":[...]}}]}
            if not polygons:
                # top-level regions
                if "regions" in data and isinstance(data["regions"], list):
                    for r in data["regions"]:
                        sa = r.get("shape_attributes", {})
                        if sa.get("name") == "polygon":
                            xs = sa.get("all_points_x", [])
                            ys = sa.get("all_points_y", [])
                            if isinstance(xs, list) and isinstance(ys, list) and len(xs) == len(ys) and len(xs) >= 3:
                                poly = []
                                for x, y in zip(xs, ys):
                                    poly.append((float(x), float(y)))
                                polygons.append(poly)
                # nested dict-of-items con regions adentro
                if not polygons:
                    for _, v in data.items():
                        if isinstance(v, dict) and isinstance(v.get("regions"), list):
                            for r in v["regions"]:
                                sa = r.get("shape_attributes", {})
                                if sa.get("name") == "polygon":
                                    xs = sa.get("all_points_x", [])
                                    ys = sa.get("all_points_y", [])
                                    if isinstance(xs, list) and isinstance(ys, list) and len(xs) == len(ys) and len(xs) >= 3:
                                        poly = []
                                        for x, y in zip(xs, ys):
                                            poly.append((float(x), float(y)))
                                        polygons.append(poly)

        # Caso: lista (tu JSON con items que tienen cgPoints o points)
        if isinstance(data, list):
            for ann in data:
                if isinstance(ann, dict):
                    pts = None
                    if "cgPoints" in ann:
                        pts = ann["cgPoints"]
                    elif "points" in ann:
                        pts = ann["points"]

                    if isinstance(pts, list) and len(pts) >= 3:
                        poly = []
                        for p in pts:
                            if isinstance(p, dict) and "x" in p and "y" in p:
                                poly.append((float(p["x"]), float(p["y"])))
                            elif isinstance(p, (list, tuple)) and len(p) == 2:
                                poly.append((float(p[0]), float(p[1])))
                        if len(poly) >= 3:
                            polygons.append(poly)

        if not polygons:
            print(f"[Aviso] No hay polígonos en: {json_path}")
            continue
        # ===========================================================

        # Dibuja en rojo sobre la PNG original
        try:
            with Image.open(png_path).convert("RGB") as img:
                draw = ImageDraw.Draw(img)
                for poly in polygons:
                    # contorno rojo y línea reforzada (3 px)
                    draw.polygon(poly, outline=(255, 0, 0))
                    poly_closed = poly + [poly[0]]
                    for i in range(len(poly_closed) - 1):
                        draw.line([poly_closed[i], poly_closed[i+1]], fill=(255, 0, 0), width=3)
                img.save(vis_path)
            print(f"[OK] Guardado: {vis_path}")
        except Exception as e:
            print(f"[ERROR] Dibujando/guardando {vis_path}: {e}")
