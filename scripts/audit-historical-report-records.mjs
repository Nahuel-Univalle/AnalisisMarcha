// Read-only, per-record inventory. No inference, updates or migrations.
import { createRequire } from 'node:module';
import { mkdir, writeFile, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
const require=createRequire(import.meta.url);
require('@next/env').loadEnvConfig(process.cwd());
const {PrismaClient}=require('@prisma/client');
const p=new PrismaClient();
const out=path.resolve('docs/recuperacion_pdf_historicos_2026-11-19');
await mkdir(out,{recursive:true});
const tables=['User','VideoMarcha','PosePoint','GaitAnalysis','GaitParameter','DetectedSignal','AssociatedCondition','MedicalReport','SystemLog'];
const snapshot=tx=>Promise.all(tables.map(async t=>[t,await tx.$queryRawUnsafe(`SELECT count(*)::int AS count, md5(COALESCE(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text)::text,'[]')) AS fingerprint FROM "${t}" t`)]));
try {
  const result=await p.$transaction(async tx=>{
    await tx.$executeRawUnsafe('SET TRANSACTION READ ONLY');
    const before=Object.fromEntries(await snapshot(tx));
    const reports=await tx.medicalReport.findMany({orderBy:[{createdAt:'asc'},{id:'asc'}],include:{user:{select:{id:true,name:true}},analysis:{include:{parameters:true,signals:true,conditions:true,video:true}}}});
    const logs=await tx.systemLog.findMany({select:{action:true,detail:true}});
    const roots=[process.env.ANALYSIS_RECORD_STORAGE_DIR||path.resolve('..','analysis-records'),path.resolve('analysis-records'),path.resolve('data','analysis-records'),path.resolve('tmp','analysis-records')];
    const pdfRoots=[process.env.REPORT_PDF_STORAGE_DIR||path.resolve('tmp','reports'),path.resolve('public','reports'),path.resolve('uploads','reports'),path.resolve('private-reports')];
    const pdfDirs=[];for(const root of pdfRoots)for(const renderer of ['canonical-v4','canonical-v5-presentation']){const dir=path.join(root,renderer);for(const entry of await readdir(dir,{withFileTypes:true}).catch(()=>[]))if(entry.isDirectory())pdfDirs.push(path.join(dir,entry.name));}
    const paramNames={};const items=[];
    for(const r of reports){
      const a=r.analysis;for(const v of a.parameters)paramNames[v.name]=(paramNames[v.name]||0)+1;
      const canonical=[];for(const root of roots){const file=path.join(root,`${a.id}.json`);if(existsSync(file))canonical.push(file);}
      const caches=pdfDirs.filter(f=>path.basename(f).startsWith(`${r.id}-`));
      const linkedLogs=logs.filter(l=>{try{const v=JSON.parse(l.detail||'null');return v?.analysisId===a.id;}catch{return false;}}).map(l=>{let keys=[];try{keys=Object.keys(JSON.parse(l.detail));}catch{}return{action:l.action,keys};});
      const classP=a.parameters.find(v=>v.name==='Clase predicha por el modelo experimental');
      const confidenceP=a.parameters.find(v=>v.name==='Confianza del modelo');
      const versionP=a.parameters.find(v=>v.name==='Versión del modelo');
      const rawProbabilityFields=a.parameters.filter(v=>/probabil|confidence|logit/i.test(v.name)).map(v=>v.name);
      items.push({reportId:r.id,analysisId:a.id,userId:r.userId,ownershipConsistent:r.userId===a.userId,createdAt:r.createdAt.toISOString(),analysisCreatedAt:a.createdAt.toISOString(),pdfUrl:r.pdfUrl,canonicalFiles:canonical,cacheDirectories:caches,stored:{summaryPresent:!!a.summary,parameters:a.parameters.length,parameterNames:a.parameters.map(v=>v.name),signals:a.signals.length,conditions:a.conditions.length,classPresent:!!classP,roundedConfidencePresent:!!confidenceP,modelVersion:versionP?.value??null,rawProbabilityFields,linkedLogs},classification:canonical.length?'canonical_candidate':caches.length?'cache_candidate':r.pdfUrl?'file_reference_unverified':'no_original_or_canonical_located',faithfulFullReconstructionSupported:false,partialRecordExportPossible:!!a.summary&&a.parameters.length>0});
    }
    return{databaseSnapshot:before,canonicalRoots:roots,pdfRoots,records:items,parameterNames:paramNames,counts:{reports:items.length,pdfUrlPresent:items.filter(i=>i.pdfUrl).length,canonicalCandidates:items.filter(i=>i.canonicalFiles.length).length,cacheCandidates:items.filter(i=>i.cacheDirectories.length).length,classPresent:items.filter(i=>i.stored.classPresent).length,roundedConfidencePresent:items.filter(i=>i.stored.roundedConfidencePresent).length,partialRecordExportPossible:items.filter(i=>i.partialRecordExportPossible).length},dateRange:items.length?[items[0].createdAt,items.at(-1).createdAt]:[]};
  },{timeout:30000});
  await writeFile(path.join(out,'AUDITORIA_REGISTROS.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify({counts:result.counts,dateRange:result.dateRange,parameterNames:result.parameterNames,canonicalRoots:result.canonicalRoots,pdfRoots:result.pdfRoots},null,2));
}finally{await p.$disconnect();}
