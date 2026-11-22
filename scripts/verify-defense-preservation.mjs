import { createRequire } from 'node:module';
import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
const require=createRequire(import.meta.url);
require('@next/env').loadEnvConfig(process.cwd());
const {PrismaClient}=require('@prisma/client');
const p=new PrismaClient();
const dir=resolve('docs/revision_defensa_2026-11-19');
const hash=async file=>createHash('sha256').update(await readFile(file)).digest('hex');
try {
  const before=JSON.parse(await readFile(`${dir}/BD_ANTES.json`,'utf8'));
  const after=await p.$transaction(async tx=>{
    await tx.$executeRawUnsafe('SET TRANSACTION READ ONLY');const result={};
    for(const table of Object.keys(before))result[table]=await tx.$queryRawUnsafe(`SELECT count(*)::int AS count, md5(COALESCE(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text)::text, '[]')) AS fingerprint FROM "${table}" t`);
    return result;
  });
  const old=JSON.parse(await readFile('docs/integracion_v5cr_2026-11-19/MANIFIESTO_SHA256_POSTERIOR.json','utf8'));
  const artifacts=[];
  for(const file of old.files.filter(f=>f.path.startsWith('models/')||f.path.includes('/checkpoints/')))artifacts.push({path:file.path,expected:file.after,actual:await hash(file.path)});
  const oldPdfSource=await readFile(`${dir}/respaldo_previo/canonicalPdf.ts.txt`,'utf8');
  const currentPdfSource=await readFile('src/lib/analysis/canonicalPdf.ts','utf8');
  const documentFunction=s=>s.slice(s.indexOf('export async function canonicalDocument'),s.indexOf('export function renderCanonicalPdf'));
  const result={habitualDatabaseUnchanged:JSON.stringify(before)===JSON.stringify(after),tables:after,modelArtifacts:artifacts,allModelArtifactsUnchanged:artifacts.every(a=>a.actual===a.expected),canonicalScientificValidationUnchanged:documentFunction(oldPdfSource)===documentFunction(currentPdfSource),modifiedFiles:[]};
  for(const file of ['src/lib/analysis/canonicalPdf.ts','src/app/api/me/reports/[id]/pdf/route.ts','src/lib/analysis/pdfPresentation.ts'])result.modifiedFiles.push({path:file,sha256:await hash(file)});
  await writeFile(`${dir}/CONSERVACION_FINAL.json`,JSON.stringify(result,null,2));
  console.log(JSON.stringify({habitualDatabaseUnchanged:result.habitualDatabaseUnchanged,modelArtifactsChecked:artifacts.length,allModelArtifactsUnchanged:result.allModelArtifactsUnchanged,canonicalScientificValidationUnchanged:result.canonicalScientificValidationUnchanged}));
  if(!result.habitualDatabaseUnchanged||!result.allModelArtifactsUnchanged||!result.canonicalScientificValidationUnchanged)process.exitCode=1;
}finally{await p.$disconnect();}
