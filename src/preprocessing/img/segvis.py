import os
import json
from PIL import Image, ImageDraw

"""
Display segmentation polygons on the original images.

This script:
- Scans the patient folders in `data/processed`.
- For each patient, it searches for the segmentation JSON files in `seg/json`
  and the corresponding radiographic images in `img`.
- Loads the geometry of the polygons from each JSON.
- Opens the associated PNG image and draws the contours of the polygons on
  it using `PIL.ImageDraw`, with reinforced red lines.
- Saves the result in the `seg/vis` folder with the same base identifier,
  allowing visual inspection of the segmentation quality.
- Handles and reports exceptions when a valid image cannot be opened or saved.

It is used as a quality control tool to review the masks
and annotations of TOMPEI-CMMD superimposed on the original images.
"""

# File paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

input_folder = os.path.join(REPO_ROOT, "data", "processed")

# Process each patient folder
for patient in os.listdir(input_folder):
    patient_path = os.path.join(input_folder, patient)
    if not os.path.isdir(patient_path):
        continue

    json_folder = os.path.join(patient_path, "seg", "json")
    vis_folder  = os.path.join(patient_path, "seg", "vis")
    png_folder  = os.path.join(patient_path, "png")

    if not os.path.exists(json_folder):
        print(f"[Warning] No Json {patient}")
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
            print(f"[Warning] Image PNG do not exist: {png_path}")
            continue

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ERROR] JSON Wrong {json_path}: {e}")
            continue

        # Extract polygons from JSON
        polygons = []

        if isinstance(data, dict):
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
                # nested dict-of-items with regions
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
            print(f"[Warning]: {json_path}")
            continue

        # Draw polygons on the image
        try:
            with Image.open(png_path).convert("RGB") as img:
                draw = ImageDraw.Draw(img)
                for poly in polygons:
                    # Draw polygon outline with reinforced lines
                    draw.polygon(poly, outline=(255, 0, 0))
                    poly_closed = poly + [poly[0]]
                    for i in range(len(poly_closed) - 1):
                        draw.line([poly_closed[i], poly_closed[i+1]], fill=(255, 0, 0), width=3)
                img.save(vis_path)
            print(f"[OK] Saved: {vis_path}")
        except Exception as e:
            print(f"[ERROR] Drawing/Saving {vis_path}: {e}")
