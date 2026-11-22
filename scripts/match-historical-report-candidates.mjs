import {createRequire} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const require=createRequire(import.meta.url);require('@next/env').loadEnvConfig(process.cwd());
const {PrismaClient}=require('@prisma/client');const p=new PrismaClient();
const out='docs/recuperacion_pdf_historicos_2026-11-19';
const normalize=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim().toLowerCase();
// Transcribed from visual inspection of the original raster PDFs, not inferred.
const candidates=[{file:'C:/Users/fnahu/Downloads/informe_analisis_marcha.pdf',name:'Nahuel Ferrufino',emissionDay:'2026-10-30',class:'parkinson',confidence:'89%',cadenceVisible:167,symmetryPercentVisible:4,creationDate:"D:20261030002846-04'00'"},{file:'C:/Users/fnahu/Downloads/informe_analisis_marchaprueba.pdf',name:'Usuario QA',emissionDay:'2026-11-05',class:'riesgo_caida',confidence:'70%',cadenceVisible:72,symmetryPercentVisible:5,creationDate:"D:20261105181716-04'00'"}];
try{
  const r=await p.$transaction(async tx=>{
    await tx.$executeRawUnsafe('SET TRANSACTION READ ONLY');
    const users=await tx.user.findMany({select:{id:true,name:true}});
    const reports=await tx.medicalReport.findMany({include:{analysis:{include:{parameters:true,signals:true,conditions:true}}}});
    return Promise.all(candidates.map(async c=>{
      const owners=users.filter(u=>normalize(u.name)===normalize(c.name));
      const owned=reports.filter(r=>owners.some(u=>u.id===r.userId));
      const matching=owned.filter(r=>r.analysis.parameters.some(p=>p.name==='Clase predicha por el modelo experimental'&&p.state===c.class)&&r.analysis.parameters.some(p=>p.name==='Confianza del modelo'&&Number.parseFloat(p.value)===Number.parseFloat(c.confidence)));
      return{file:c.file,sha256:createHash('sha256').update(await readFile(c.file)).digest('hex'),pdfType:'raster_html2canvas_no_embedded_analysis_id',producer:'jsPDF 4.2.1',creationDate:c.creationDate,emissionDay:c.emissionDay,observedClass:c.class,observedRoundedConfidence:c.confidence,cadenceVisible:c.cadenceVisible,symmetryPercentVisible:c.symmetryPercentVisible,matchingOwnerIds:owners.map(u=>u.id),reportsOwned:owned.length,ownedReportSummaries:owned.map(r=>({reportId:r.id,createdAt:r.createdAt,class:r.analysis.parameters.find(p=>p.name==='Clase predicha por el modelo experimental')?.state??null,confidence:r.analysis.parameters.find(p=>p.name==='Confianza del modelo')?.value??null})),candidateReportIds:matching.map(r=>r.id),candidateDetails:matching.map(r=>({reportId:r.id,analysisId:r.analysisId,createdAt:r.createdAt,analysisCreatedAt:r.analysis.createdAt,parameters:r.analysis.parameters.map(p=>({name:p.name,value:p.value,state:p.state})),signalNames:r.analysis.signals.map(s=>s.name)})),mappingConfirmed:false,reason:matching.length>1?'Ambiguous: owner/class/rounded-confidence match multiple reports; PDF has no analysis/report identifier':matching.length===0?'No corresponding MedicalReport with matching current owner/class/confidence':'Candidate requires corroborating original analysis evidence; visual rounded values alone are not a durable identifier'};
    }));
  });
  await writeFile(`${out}/CANDIDATOS_ORIGINALES.json`,JSON.stringify(r,null,2));
  console.log(JSON.stringify(r.map(({file,matchingOwnerIds,reportsOwned,candidateReportIds,reason})=>({file,matchingOwnerIds,reportsOwned,candidateReportIds,reason})),null,2));
}finally{await p.$disconnect();}
