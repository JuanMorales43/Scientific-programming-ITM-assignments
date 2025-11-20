import os
import json
import numpy as np
from PIL import Image, ImageDraw

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

input_folder = os.path.join(REPO_ROOT, "data", "processed")

def create_mask_from_json(json_path, size_wh):
    # size_wh: (width, height)
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Recolectar polígonos como lista de [(x,y), ...]
    polygons = []

    # Caso lista (tu JSON con cgPoints o points)
    if isinstance(data, list):
        for ann in data:
            if isinstance(ann, dict):
                pts = ann.get('cgPoints') or ann.get('points')
                if isinstance(pts, list) and len(pts) >= 3:
                    poly = []
                    for p in pts:
                        if isinstance(p, dict) and 'x' in p and 'y' in p:
                            poly.append((int(round(p['x'])), int(round(p['y']))))
                        elif isinstance(p, (list, tuple)) and len(p) == 2:
                            poly.append((int(round(p[0])), int(round(p[1]))))
                    if len(poly) >= 3:
                        polygons.append(poly)

    # Caso dict (LabelMe / genérico / VGG)
    if isinstance(data, dict):
        # LabelMe
        if isinstance(data.get('shapes'), list):
            for sh in data['shapes']:
                pts = sh.get('points', [])
                if isinstance(pts, list) and len(pts) >= 3:
                    poly = []
                    for p in pts:
                        if isinstance(p, (list, tuple)) and len(p) == 2:
                            poly.append((int(round(p[0])), int(round(p[1]))))
                        elif isinstance(p, dict) and 'x' in p and 'y' in p:
                            poly.append((int(round(p['x'])), int(round(p['y']))))
                    if len(poly) >= 3:
                        polygons.append(poly)
        # Genérico {"polygons":[...]}
        if not polygons and isinstance(data.get('polygons'), list):
            for pts in data['polygons']:
                if isinstance(pts, list) and len(pts) >= 3:
                    poly = []
                    for p in pts:
                        if isinstance(p, (list, tuple)) and len(p) == 2:
                            poly.append((int(round(p[0])), int(round(p[1]))))
                        elif isinstance(p, dict) and 'x' in p and 'y' in p:
                            poly.append((int(round(p['x'])), int(round(p['y']))))
                    if len(poly) >= 3:
                        polygons.append(poly)
        # VGG (top-level o anidado)
        if not polygons:
            regions = data.get('regions')
            if isinstance(regions, list):
                for r in regions:
                    sa = r.get('shape_attributes', {})
                    if sa.get('name') == 'polygon':
                        xs, ys = sa.get('all_points_x', []), sa.get('all_points_y', [])
                        if len(xs) == len(ys) and len(xs) >= 3:
                            polygons.append([(int(round(x)), int(round(y))) for x, y in zip(xs, ys)])
            else:
                for _, v in data.items():
                    if isinstance(v, dict) and isinstance(v.get('regions'), list):
                        for r in v['regions']:
                            sa = r.get('shape_attributes', {})
                            if sa.get('name') == 'polygon':
                                xs, ys = sa.get('all_points_x', []), sa.get('all_points_y', [])
                                if len(xs) == len(ys) and len(xs) >= 3:
                                    polygons.append([(int(round(x)), int(round(y))) for x, y in zip(xs, ys)])

    # Construir máscara binaria (0 fondo / 255 lesión)
    mask = Image.new('L', size_wh, 0)
    draw = ImageDraw.Draw(mask)
    for poly in polygons:
        draw.polygon(poly, outline=1, fill=1)
    return (np.array(mask, dtype=np.uint8) * 255)

for paciente in os.listdir(input_folder):
    paciente_path = os.path.join(input_folder, paciente)
    if not os.path.isdir(paciente_path):
        continue

    seg_json = os.path.join(paciente_path, 'seg', 'json')
    seg_mask = os.path.join(paciente_path, 'seg', 'mask')
    png_folder = os.path.join(paciente_path, 'png')
    tiff_folder = os.path.join(paciente_path, 'tiff')

    if not os.path.isdir(seg_json):
        continue
    os.makedirs(seg_mask, exist_ok=True)

    for fname in os.listdir(seg_json):
        if not fname.endswith('_AnnotationFile.json'):
            continue

        id_lv = fname.replace('_AnnotationFile.json', '')
        json_path = os.path.join(seg_json, fname)

        # Imagen de referencia: PNG, luego TIFF/TIF
        png_path  = os.path.join(png_folder,  f'{id_lv}.png')
        tiff_path = os.path.join(tiff_folder, f'{id_lv}.tiff')
        tif_path  = os.path.join(tiff_folder, f'{id_lv}.tif')

        ref_path = png_path if os.path.exists(png_path) else (tiff_path if os.path.exists(tiff_path) else (tif_path if os.path.exists(tif_path) else None))
        if ref_path is None:
            print(f'[Aviso] Imagen no encontrada para {id_lv}')
            continue

        with Image.open(ref_path) as ref_im:
            w, h = ref_im.size

        mask_arr = create_mask_from_json(json_path, (w, h))
        mask_img = Image.fromarray(mask_arr, mode='L')

        out_png  = os.path.join(seg_mask, f'{id_lv}_mask.png')
        out_tiff = os.path.join(seg_mask, f'{id_lv}_mask.tiff')

        mask_img.save(out_png)
        try:
            mask_img.save(out_tiff, compression='tiff_lzw')
        except Exception:
            mask_img.save(out_tiff)

        print(f'[OK] {paciente}: {id_lv} → máscara guardada (PNG y TIFF)')