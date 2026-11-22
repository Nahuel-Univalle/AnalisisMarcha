// Full HTTP acceptance in a dedicated PostgreSQL container, no production data.
// Start DB separately: docker run -d --name gait-v5cr-integration-20261119
//   -e POSTGRES_PASSWORD=v5cr-local-test-only -e POSTGRES_DB=gait_v5cr_test
//   -p 127.0.0.1:55432:5432 postgres:16-alpine
import { spawn, spawnSync } from 'node:child_process';
import { mkdir, readFile, writeFile, open, readdir } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { randomBytes, createHash } from 'node:crypto';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');
const root = process.cwd();
const reportDir = resolve(process.env.V5CR_TEST_REPORT_DIR ?? 'docs/integracion_v5cr_2026-11-19');
await mkdir(reportDir, {recursive:true});
const scratch = resolve('tmp/v5cr-e2e');
const base = 'http://127.0.0.1:3047';
const VERSION = 'gait_deep_v5exp_V5CR_7e9ed60965fe';
const env = { ...process.env, DATABASE_URL: 'postgresql://postgres:v5cr-local-test-only@127.0.0.1:55432/gait_v5cr_test?schema=public',
  AUTH_SESSION_SECRET: randomBytes(48).toString('hex'),
  CLOUDINARY_CLOUD_NAME: '', CLOUDINARY_API_KEY: '', CLOUDINARY_API_SECRET: '', CLOUDINARY_FOLDER: '',
  ENABLE_LEGACY_SPRINT4_DATASET: 'false',
  ANALYSIS_RECORD_STORAGE_DIR: join(scratch, 'records'), REPORT_PDF_STORAGE_DIR: join(scratch, 'pdfs') };
await mkdir(scratch, {recursive:true});
const checks = [];
function check(name, condition, detail = {}) { checks.push({name, passed:!!condition, ...detail}); console.log(`${condition ? 'PASS' : 'FAIL'} ${name}`); if (!condition) throw new Error(name); }
const p = new PrismaClient({datasources:{db:{url:env.DATABASE_URL}}});
let server;
try {
  const push = spawnSync(process.execPath, ['node_modules/prisma/build/index.js','db','push','--skip-generate'], {env,encoding:'utf8',timeout:90000,windowsHide:true});
  await writeFile(join(reportDir,'E2E_SCHEMA.log'), (push.stdout ?? '') + (push.stderr ?? ''));
  check('setup: schema in isolated database on port 55432', push.status === 0);
  const password = 'V5crPrueba2026!';
  const hash = await bcrypt.hash(password, 10);
  const user = await p.user.upsert({where:{email:'v5cr-test@example.invalid'},update:{role:'USER'},create:{name:'Prueba técnica V5-CR',email:'v5cr-test@example.invalid',passwordHash:hash,role:'USER',age:30}});
  const adminUser = await p.user.upsert({where:{email:'v5cr-admin@example.invalid'},update:{},create:{name:'Administrador de prueba V5-CR',email:'v5cr-admin@example.invalid',passwordHash:hash,role:'ADMIN'}});
  // An explicitly labeled technical fixture checks historical model identity;
  // it is not a synthetic patient or a new inference sample.
  const historical = await p.gaitAnalysis.create({data:{user:{connect:{id:user.id}},alert:'BAJO',summary:'REGISTRO TÉCNICO: compatibilidad de versión histórica V4; sin paciente ni inferencia',
    video:{create:{userId:user.id,originalName:'fixture-version-v4',mimeType:'application/x-test-fixture',sizeBytes:0}},
    parameters:{create:[{name:'Versión del modelo',value:'gait_deep_v4exp_M1_BN_recalibrated_candidate_v1',state:'Referencia'}]}}});
  const stdout = await open(join(reportDir,'E2E_SERVER.log'),'w');
  server = spawn(process.execPath,['node_modules/next/dist/bin/next',process.env.V5CR_E2E_MODE??'dev','--hostname','127.0.0.1','--port','3047'],{env,cwd:root,windowsHide:true,stdio:['ignore',stdout.fd,stdout.fd]});
  let ready = false;
  for(let i=0;i<120;i++){try{const r=await fetch(base+'/api/auth/me');if(r.status===401||r.ok){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,1000));}
  check('setup: isolated Next.js server',ready);
  let cookie='';
  async function request(path, options={}) { return fetch(base+path,{...options,headers:{...(cookie?{cookie}:{}),...options.headers}}); }
  let r=await request('/api/admin/summary'); check('regression: unauthenticated admin denied',r.status===401);
  r=await request('/api/auth/login',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({email:user.email,password})});
  check('e2e: login with test account',r.ok,{status:r.status});cookie=r.headers.get('set-cookie').split(';')[0];
  // Existing technical PDFs exercise legacy cache compatibility, read-only.
  const legacyRoot=join(scratch,'pdfs','canonical-v4');
  let legacyChecked=false;
  for(const entry of (await readdir(legacyRoot).catch(()=>[])).sort().reverse()) {
    const id=entry.slice(0,-65);
    if(!/^[a-z0-9]+$/.test(id))continue;
    const previous=await p.medicalReport.findFirst({where:{id,userId:user.id}});
    if(!previous)continue;
    const file=join(legacyRoot,entry,'document.pdf');
    const before=await readFile(file);
    const response=await request(`/api/me/reports/${id}/pdf`);
    const downloaded=Buffer.from(await response.arrayBuffer());
    check('regression: legacy PDF remains downloadable and unchanged',response.ok&&downloaded.equals(before)&&createHash('sha256').update(await readFile(file)).digest('hex')===createHash('sha256').update(before).digest('hex'));
    legacyChecked=true;break;
  }
  if(!legacyChecked)console.log('NOT EXECUTED legacy PDF cache compatibility: no previous technical PDF available');
  r=await request('/api/analysis/video',{method:'POST',body:new FormData()});check('e2e: missing video rejected',r.status===400);
  // Get only a path from existing research metadata; do not alter the manifest.
  const py=spawnSync(resolve('.venv311/Scripts/python.exe'),['-c',"import csv,json; from pathlib import Path; r=next(r for r in csv.DictReader(open('outputs/dataset_v4_4class/manifest_v4_preview.csv',encoding='utf-8')) if r['class']=='normal' and r['include_in_preview']=='true'); print(json.dumps(r['video_path']))"],{encoding:'utf8',windowsHide:true});
  const video=resolve(JSON.parse(py.stdout.trim()));
  const form=new FormData();form.set('video',new Blob([await readFile(video)],{type:'video/quicktime'}),'real-existing-research-video.MOV');
  r=await request('/api/analysis/video',{method:'POST',body:form});
  const result=await r.json();await writeFile(join(reportDir,'E2E_ANALYSIS.json'),JSON.stringify(result,null,2));
  check('e2e: real upload, pose extraction, V5-CR inference',r.ok&&result.success&&result.analysis?.modelUsed,{status:r.status});
  const analysis=result.analysis;
  check('e2e: actual version and valid probabilities',analysis.modelVersion===VERSION&&analysis.classProbabilitiesList.length===4&&Math.abs(analysis.classProbabilitiesList.reduce((s,x)=>s+x.probability,0)-1)<1e-6);
  check('e2e: PostgreSQL persistence',analysis.savedToDatabase===true);
  const saved=await p.gaitAnalysis.findUnique({where:{id:analysis.id},include:{parameters:true}});
  check('integrated: version stored per analysis',saved.parameters.some(x=>x.value===VERSION));
  r=await request('/api/me/analyses');const history=await r.json();
  await writeFile(join(reportDir,'E2E_HISTORY.json'),JSON.stringify(history,null,2));
  check('e2e: history includes real analysis',r.ok&&history.analyses.some(x=>x.id===analysis.id));
  check('regression: historical V4 identity preserved',history.analyses.find(x=>x.id===historical.id)?.parameters.some(x=>x.value==='gait_deep_v4exp_M1_BN_recalibrated_candidate_v1'));
  r=await request('/api/me/reports',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({analysisId:analysis.id,title:'PRUEBA TÉCNICA V5-CR — video existente de investigación'})});const report=(await r.json()).report;
  check('e2e: save report',r.status===201&&!!report?.id);
  r=await request(`/api/me/reports/${report.id}/pdf`,{method:'POST',headers:{'content-type':'application/json'},body:'{}'});
  const generation=await r.text();check('e2e: canonical PDF generation',r.ok,{status:r.status,response:generation});
  r=await request(`/api/me/reports/${report.id}/pdf`);const pdf=Buffer.from(await r.arrayBuffer());
  await writeFile(join(reportDir,'E2E_INFORME.pdf'),pdf);
  check('e2e: PDF download',r.ok&&r.headers.get('content-type')==='application/pdf'&&pdf.subarray(0,5).toString()==='%PDF-',{bytes:pdf.length});
  r=await request('/api/admin/summary');check('regression: ordinary user cannot read admin summary',r.status===403);
  r=await request('/api/auth/login',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({email:adminUser.email,password})});
  check('e2e: test administrator login',r.ok);cookie=r.headers.get('set-cookie').split(';')[0];
  r=await request('/api/admin/summary');const admin=await r.json();await writeFile(join(reportDir,'E2E_ADMIN.json'),JSON.stringify(admin,null,2));
  check('e2e: admin active version/internal metrics',r.ok&&admin.modelStatus.modelVersion===VERSION&&admin.modelStatus.accuracy===0.8598&&admin.modelStatus.macroF1===0.7852&&admin.modelStatus.available);
  r=await request('/api/auth/login',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({email:user.email,password})});cookie=r.headers.get('set-cookie').split(';')[0];
  const bad=new FormData();bad.set('video',new Blob(['not a video'],{type:'video/mp4'}),'corrupt.mp4');r=await request('/api/analysis/video',{method:'POST',body:bad});
  check('e2e: corrupt upload rejected',r.status===400,{status:r.status});
  const negativePath=join(scratch,'no-person.mp4');
  const negative=spawnSync(resolve('.venv311/Scripts/python.exe'),['-c',"import cv2,numpy as np,sys; w=cv2.VideoWriter(sys.argv[1],cv2.VideoWriter_fourcc(*'mp4v'),15,(320,240)); [w.write(np.zeros((240,320,3),np.uint8)) for _ in range(60)]; w.release()",negativePath],{windowsHide:true});
  check('setup: empty video is a negative code fixture',negative.status===0);
  const emptyForm=new FormData();emptyForm.set('video',new Blob([await readFile(negativePath)],{type:'video/mp4'}),'no-person.mp4');
  r=await request('/api/analysis/video',{method:'POST',body:emptyForm});const insufficient=await r.json();
  await writeFile(join(reportDir,'E2E_POSE_INSUFICIENTE.json'),JSON.stringify(insufficient,null,2));
  check('e2e: no-person video has no fabricated prediction',r.ok&&insufficient.analysis?.analysisReliable===false&&insufficient.analysis?.modelUsed===false&&insufficient.analysis?.detectedClass===null&&insufficient.analysis?.confidence===null&&insufficient.analysis?.predictionConfidence===null&&insufficient.analysis?.classProbabilities===null&&insufficient.analysis?.classProbabilitiesList.length===0,{status:r.status});
  // Save test login metadata only, no signed token or actual user data.
  await writeFile(join(scratch,'browser-test.json'),JSON.stringify({base,email:user.email,password,analysisId:analysis.id,reportId:report.id}));
  console.log('HTTP acceptance complete. Server remains for visual checks.');
  await writeFile(join(scratch,'server-pid.txt'),String(server.pid));
  if(process.env.V5CR_E2E_KEEP_SERVER!=='1') server.unref();
} catch(error) { console.error(error.message); if(server)server.kill();process.exitCode=1; }
finally {
  await writeFile(join(reportDir,'PRUEBAS_E2E.json'),JSON.stringify({environment:'Dedicated PostgreSQL container, database gait_v5cr_test, port 55432; only technical test accounts and existing research videos',checks,passed:checks.filter(x=>x.passed).length,failed:checks.filter(x=>!x.passed).length},null,2));
  await p.$disconnect();
}
