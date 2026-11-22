"""Manifiesto de trazabilidad anonimizado de los 117 videos (SIN rutas, SIN texto libre de evidencia, SIN copiar videos) y resumen por clase.
Entrada (solo lectura): outputs/dataset_v4_4class/manifest_v4_preview.csv (include_in_preview == true), dataset_v4_preview.npz."""
import csv, collections, json, numpy as np
from pathlib import Path
PKG = Path(__file__).resolve().parents[2]; REPO = PKG.parents[1]
V4 = REPO / "outputs/dataset_v4_4class"
rows = [r for r in csv.DictReader(open(V4 / "manifest_v4_preview.csv", encoding="utf-8")) if r["include_in_preview"] == "true"]
d = np.load(V4 / "dataset_v4_preview.npz")
vids = [str(v) for v in d["video"]]; assert [r["video"] for r in rows] == vids or sorted(r["video"] for r in rows) == sorted(vids)
ix = {v: i for i, v in enumerate(vids)}
SRC = {"lab_A": "laboratorio (trípode, 1920x1080)", "social_vertical": "redes sociales (vertical)", "clinic_848x478_60fps": "clínica / repositorio clínico (848x478, 60 fps)"}
out = []
for r in rows:
    ev = r["subject_evidence"].lower()
    ev_cls = "ID de sujeto en el nombre del archivo del dataset" if "nombre de archivo" in ev else ("sin evidencia de repetición entre videos (1 video = 1 grupo técnico)" if "sin evidencia" in ev else "otra evidencia documentada en el manifiesto")
    out.append({"indice_en_OOF": ix[r["video"]], "id_video": r["video"], "clase_registrada": r["class"], "grupo_tecnico_de_sujeto": r["split_group"],
                "estado_del_grupo": r["subject_status"], "evidencia_de_identidad": ev_cls, "fuente_de_grabacion": SRC.get(r["source"].split(" ")[0], r["source"].split(" ")[0]),
                "orientacion": r["orientation"], "vista": r["view"], "estilo_de_camara": r["camera_style"], "duracion_s": r["video_duration_s"], "fps": r["fps"],
                "resolucion": f'{r["width"]}x{r["height"]}', "segmento": r["segment_type"], "validacion_clinica_individual": "no acreditada"})
with open(PKG / "03_DATASET_Y_METODOLOGIA/MANIFIESTO_TRAZABILIDAD_117_VIDEOS.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(sorted(out, key=lambda o: o["indice_en_OOF"]))
CL = ["normal", "parkinson", "esclerosis_multiple", "riesgo_caida"]
res = []
for c in CL:
    rs = [o for o in out if o["clase_registrada"] == c]; g = {o["grupo_tecnico_de_sujeto"] for o in rs}; gp = {o["grupo_tecnico_de_sujeto"] for o in rs if o["estado_del_grupo"] == "provisional"}
    fu = collections.Counter(o["fuente_de_grabacion"] for o in rs); ori = collections.Counter(o["orientacion"] for o in rs)
    dur = [float(o["duracion_s"]) for o in rs]
    res.append({"clase": c, "videos": len(rs), "grupos": len(g), "grupos_provisionales": len(gp), "grupos_con_identidad_registrada": len(g) - len(gp), "fuentes": json.dumps(dict(fu), ensure_ascii=False), "orientacion": json.dumps(dict(ori)), "duracion_media_s": round(sum(dur) / len(dur), 2), "duracion_min_s": min(dur), "duracion_max_s": max(dur)})
res.append({"clase": "TOTAL", "videos": len(out), "grupos": len({o["grupo_tecnico_de_sujeto"] for o in out}), "grupos_provisionales": sum(r["grupos_provisionales"] for r in res), "grupos_con_identidad_registrada": sum(r["grupos_con_identidad_registrada"] for r in res)})
with open(PKG / "03_DATASET_Y_METODOLOGIA/RESUMEN_DATASET_POR_CLASE.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=sorted({k for r in res for k in r}, key=lambda k: list(res[0]).index(k) if k in res[0] else 99)); w.writeheader(); w.writerows(res)
assert len(out) == 117 and res[-1]["grupos"] == 67 and res[-1]["grupos_provisionales"] == 27
print("OK", [(r["clase"], r["videos"], r["grupos"], r["grupos_provisionales"]) for r in res])
