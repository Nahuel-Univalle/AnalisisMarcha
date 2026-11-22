"""Find original record IDs in bounded project/QA JSON and logs, without interpreting predictions."""
import json, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/recuperacion_pdf_historicos_2026-11-19'
audit=json.loads((OUT/'AUDITORIA_REGISTROS.json').read_text(encoding='utf-8'))
ids={r['reportId'] for r in audit['records']}|{r['analysisId'] for r in audit['records']}
roots=[ROOT/'tmp',ROOT/'data',ROOT/'outputs',Path('C:/Users/fnahu/Documents/Codex/2026-11-05/files-pasted-by-the-user-proyecto'),Path('C:/Users/fnahu/Desktop/QA_JMETER_2026_20261105_155207')]
skip={'node_modules','.next','.git','.venv311','.venv','bower_components','videos','private-videos','modelos_cv_V5CR','modelos_cv_V5C','modelos_cv_V5P','modelos_cv_V5S'}
matches=[];errors=[];count=0;size=0;canonical_dirs=[]
for root in roots:
    if not root.exists():continue
    for current,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[d for d in dirs if d not in skip]
        if Path(current).name=='analysis-records':canonical_dirs.append(current)
        for name in files:
            p=Path(current)/name
            if p.suffix.lower() not in ('.json','.txt','.log'):continue
            try:
                n=p.stat().st_size
                if n>5_000_000:continue
                data=p.read_bytes();count+=1;size+=len(data)
                found=[i for i in ids if i.encode() in data]
                if found:matches.append({'path':str(p),'matchingIds':found,'canonicalIdFilename':p.stem in ids})
            except OSError as exc:errors.append(str(exc))
(OUT/'REFERENCIAS_JSON_Y_LOGS.json').write_text(json.dumps({'filesInspected':count,'bytesInspected':size,'roots':list(map(str,roots)),'canonicalDirectories':canonical_dirs,'matches':matches,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'filesInspected':count,'bytesInspected':size,'canonicalDirs':len(canonical_dirs),'matches':matches,'errors':len(errors)},ensure_ascii=False))
