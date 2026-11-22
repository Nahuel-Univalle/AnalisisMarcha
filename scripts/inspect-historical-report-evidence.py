"""Inspect PDF metadata/text and archive indexes. No original is changed/extracted."""
import hashlib, json, subprocess, zipfile
from pathlib import Path
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/recuperacion_pdf_historicos_2026-11-19'
inventory=json.loads((OUT/'INVENTARIO_ARCHIVOS.json').read_text(encoding='utf-8'))
records=json.loads((OUT/'AUDITORIA_REGISTROS.json').read_text(encoding='utf-8'))['records']
ids={r['reportId'] for r in records}|{r['analysisId'] for r in records}
pdfs=[]; archives=[]; errors=[]
for entry in inventory['files']:
    path=Path(entry['path'])
    if entry['suffix']=='.pdf':
        try:
            with pymupdf.open(path) as doc:
                text=''.join(p.get_text() for p in doc) if len(doc)<=12 else doc[0].get_text()
                pdfs.append({'path':str(path),'sha256':entry['sha256'],'pages':len(doc),'producer':doc.metadata.get('producer'),'creationDate':doc.metadata.get('creationDate'),'textLength':len(text),'matchingIds':sorted(i for i in ids if i in text),'gaitReportText':('informe de análisis de marcha' in text.lower()),'rasterJsPdf':len(text)==0 and 'jspdf' in (doc.metadata.get('producer')or'').lower()})
        except Exception as exc: errors.append({'path':str(path),'error':str(exc)})
    elif entry['suffix'] in ('.zip','.rar','.7z') and any(x in path.name.lower() for x in ('marcha','jmeter','evidencias_para_actualizar','integracion_v5cr','revision_defensa','optimizacion_final_v5','mejora_modelo_v5')):
        result={'path':str(path),'pdfMembers':[],'canonicalMembers':[],'idEvidence':[]}
        try:
            if entry['suffix']=='.zip':
                with zipfile.ZipFile(path) as z:
                    total=0
                    for item in z.infolist():
                        n=item.filename
                        if n.lower().endswith('.pdf'):result['pdfMembers'].append(n)
                        if 'analysis-records' in n:result['canonicalMembers'].append(n)
                        if n.lower().endswith(('.json','.txt','.log','.sql')) and item.file_size<2_000_000 and total+item.file_size<20_000_000:
                            data=z.read(item);total+=len(data)
                            matches=[i for i in ids if i.encode() in data]
                            if matches:result['idEvidence'].append({'member':n,'matchingIds':matches})
                    result['members']=len(z.infolist());result['textBytesInspected']=total
            else:
                cp=subprocess.run(['C:/Program Files/7-Zip/7z.exe','l','-slt',str(path)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
                names=[l[7:] for l in cp.stdout.splitlines() if l.startswith('Path = ')][1:]
                result['members']=len(names);result['pdfMembers']=[n for n in names if n.lower().endswith('.pdf')];result['canonicalMembers']=[n for n in names if 'analysis-records' in n]
                result['matchingIdPaths']=[n for n in names if any(i in n for i in ids)]
                result['exitCode']=cp.returncode
            archives.append(result)
        except Exception as exc:errors.append({'path':str(path),'error':str(exc)})
result={'pdfs':pdfs,'archives':archives,'errors':errors}
(OUT/'INSPECCION_PDF_Y_RESPALDOS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pdfsInspected':len(pdfs),'rastersJsPdf':[p['path'] for p in pdfs if p['rasterJsPdf']],'matchingPdfIds':[p for p in pdfs if p['matchingIds']],'archiveCount':len(archives),'archiveMatchingIds':[a for a in archives if a['idEvidence'] or a.get('matchingIdPaths')],'errors':len(errors)},ensure_ascii=False))
