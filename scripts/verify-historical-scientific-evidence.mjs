import {createRequire} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const require=createRequire(import.meta.url);require('@next/env').loadEnvConfig(process.cwd());
const {PrismaClient}=require('@prisma/client');const p=new PrismaClient();
const out='docs/recuperacion_pdf_historicos_2026-11-19';
const sources=['outputs/dataset_v4_4class/final_cleanup/e2e_api_results.json','outputs/dataset_v4_4class/step16_final_integration/api_e2e_4clases.json','outputs/dataset_v4_4class/step20_integration/e2e_api_results.json','outputs/dataset_v4_4class/step22_final_qa/e2e_api_results.json'];
const labels=['normal','parkinson','esclerosis_multiple','riesgo_caida'];
const evidence=[];
for(const file of sources){const bytes=await readFile(file);const parsed=JSON.parse(bytes);const key=parsed.filas?'filas':'analisis';for(const [index,row] of parsed[key].entries())evidence.push({file,sourceSha256:createHash('sha256').update(bytes).digest('hex'),jsonPointer:`/${key}/${index}`,ownerEmail:parsed.usuario_prueba,row});}
try{
 const result=await p.$transaction(async tx=>{
  await tx.$executeRawUnsafe('SET TRANSACTION READ ONLY');
  const reports=await tx.medicalReport.findMany({include:{user:{select:{email:true}},analysis:{include:{parameters:true}}}});
  return reports.map(r=>{
   const found=evidence.filter(e=>e.row.analysisId===r.analysisId).map(e=>{
    const row=e.row;const probs=row.cand_probs??row.classProbabilitiesByName;const pred=row.cand_pred??row.detectedClass;const confidence=row.cand_conf??row.confidence;
    const value=name=>r.analysis.parameters.find(p=>p.name===name);
    const validProbs=probs&&Object.keys(probs).length===4&&labels.every(k=>Number.isFinite(probs[k])&&probs[k]>=0&&probs[k]<=1)&&Math.abs(labels.reduce((s,k)=>s+probs[k],0)-1)<1e-6;
    const checks={identity:row.analysisId===r.analysisId,owner:e.ownerEmail===r.user.email,modelVersion:row.modelVersion===value('Versión del modelo')?.value,predictedClass:pred===value('Clase predicha por el modelo experimental')?.state,roundedConfidence:Math.round(confidence*100)===Number.parseFloat(value('Confianza del modelo')?.value??''),probabilitiesValid:!!validProbs,confidenceMatchesProbability:!!validProbs&&Math.abs(probs[pred]-confidence)<1e-7,topClassMatches:!!validProbs&&labels.reduce((a,b)=>probs[a]>=probs[b]?a:b)===pred};
    return{file:e.file,sourceSha256:e.sourceSha256,jsonPointer:e.jsonPointer,checks,verified:Object.values(checks).every(Boolean),fieldsRecoverable:['analysisId','modelVersion','predictedClass','originalConfidence','fourOriginalProbabilities','warningCodes'],fieldsNotProven:['originalPdfBytes','originalIssueDate','completeModelGaitFeatures','completeOriginalUiState','originalPdfLayout']};
   });
   return{reportId:r.id,analysisId:r.analysisId,scientificEvidence:found,classification:found.some(e=>e.verified)?'verified_original_probabilities_reconstruction_requires_authorization':'database_subset_only',originalPdfRestorationConfirmed:false,fullFaithfulPdfReconstructionConfirmed:false};
  });
 },{timeout:30000});
 const summary={total:result.length,originalPdfRestorable:0,verifiedOriginalProbabilities:result.filter(r=>r.scientificEvidence.some(e=>e.verified)).length,databaseSubsetOnly:result.filter(r=>!r.scientificEvidence.some(e=>e.verified)).length,evidenceConflicts:result.flatMap(r=>r.scientificEvidence.filter(e=>!e.verified).map(e=>({reportId:r.reportId,...e}))),records:result};
 await writeFile(`${out}/CLASIFICACION_INDIVIDUAL_FINAL.json`,JSON.stringify(summary,null,2));
 await writeFile(`${out}/CLASIFICACION_INDIVIDUAL.csv`,['reportId,analysisId,classification,originalPdfRestorable,fullFaithfulPdfReconstructionConfirmed',...result.map(r=>`${r.reportId},${r.analysisId},${r.classification},false,false`)].join('\n'));
 console.log(JSON.stringify({total:summary.total,originalPdfRestorable:0,verifiedOriginalProbabilities:summary.verifiedOriginalProbabilities,databaseSubsetOnly:summary.databaseSubsetOnly,conflicts:summary.evidenceConflicts.length},null,2));
}finally{await p.$disconnect();}
