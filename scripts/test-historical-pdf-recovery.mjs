// PDF-only HTTP tests. Copies existing technical records into a fresh isolated
// schema; never reruns inference or writes to the habitual database.
import {createRequire} from 'node:module';
import {readFile,writeFile,mkdir,readdir,copyFile,open} from 'node:fs/promises';
import path from 'node:path';
import {spawn,spawnSync} from 'node:child_process';
import {createHash,randomBytes,createHmac} from 'node:crypto';
const require=createRequire(import.meta.url);const {PrismaClient}=require('@prisma/client');
const out=path.resolve('docs/recuperacion_pdf_historicos_2026-11-19');await mkdir(out,{recursive:true});
const sourceUrl='postgresql://postgres:v5cr-local-test-only@127.0.0.1:55432/gait_v5cr_test?schema=public';
const schema=`pdf_recovery_${Date.now()}_${randomBytes(3).toString('hex')}`;
const targetUrl=new URL(sourceUrl);targetUrl.searchParams.set('schema',schema);
if(targetUrl.port!=='55432'||targetUrl.pathname!=='/gait_v5cr_test'||schema==='public')throw Error('Test isolation guard');
const source=new PrismaClient({datasources:{db:{url:sourceUrl}}});
const target=new PrismaClient({datasources:{db:{url:String(targetUrl)}}});
const scratch=path.resolve('tmp/historical-pdf-tests',schema);const recordsDir=path.join(scratch,'records');const pdfDir=path.join(scratch,'pdfs');
await mkdir(recordsDir,{recursive:true});await mkdir(pdfDir,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex');const checks=[];
function check(name,condition,details={}){checks.push({name,passed:!!condition,...details});console.log(`${condition?'PASS':'FAIL'} ${name}`);if(!condition)throw Error(name);}
let server;
try{
 const collisions=await source.$queryRawUnsafe('SELECT nspname FROM pg_namespace WHERE nspname=$1',schema);
 check('setup: fresh test schema, never public or habitual',collisions.length===0);
 const secret=randomBytes(48).toString('hex');
 const env={...process.env,DATABASE_URL:String(targetUrl),AUTH_SESSION_SECRET:secret,ANALYSIS_RECORD_STORAGE_DIR:recordsDir,REPORT_PDF_STORAGE_DIR:pdfDir};
 const push=spawnSync(process.execPath,['node_modules/prisma/build/index.js','db','push','--skip-generate'],{env,windowsHide:true,encoding:'utf8',timeout:90000});
 await writeFile(path.join(out,'ESQUEMA_PRUEBAS.log'),(push.stdout??'')+(push.stderr??''));check('setup: isolated schema created',push.status===0);
 const selected=JSON.parse(await readFile('tmp/v5cr-e2e/browser-test.json','utf8'));
 const all=await source.$transaction(async tx=>{await tx.$executeRawUnsafe('SET TRANSACTION READ ONLY');return tx.medicalReport.findMany({include:{user:true,analysis:{include:{parameters:true,signals:true,conditions:true,video:true}}}});});
 const full=all.find(r=>r.id===selected.reportId);check('setup: original real-video technical result exists',!!full);
 const legacyRoot=path.resolve('tmp/v5cr-e2e/pdfs/canonical-v4');let legacy,legacyFolder;
 for(const name of (await readdir(legacyRoot)).sort().reverse()){const id=name.slice(0,-65);const row=all.find(r=>r.id===id&&r.userId===full.userId);if(row){legacy=row;legacyFolder=path.join(legacyRoot,name);break;}}
 check('setup: actual previous technical PDF exists',!!legacy);
 const missing=all.find(r=>r.userId===full.userId&&r.id!==full.id&&r.id!==legacy.id);
 check('setup: third existing technical record for missing-artifact fixture',!!missing);
 const chosen=[full,legacy,missing];
 const sourceSnapshot=sha(Buffer.from(JSON.stringify(chosen)));
 const users=new Map(chosen.map(r=>[r.user.id,r.user]));
 const other=await source.user.findFirst({where:{email:'v5cr-admin@example.invalid'}});users.set(other.id,other);
 for(const user of users.values())await target.user.create({data:user});
 for(const row of chosen){
  const {user,analysis,...report}=row;const{video,parameters,signals,conditions,...a}=analysis;
  await target.videoMarcha.create({data:video});await target.gaitAnalysis.create({data:a});
  if(parameters.length)await target.gaitParameter.createMany({data:parameters});
  if(signals.length)await target.detectedSignal.createMany({data:signals});
  if(conditions.length)await target.associatedCondition.createMany({data:conditions});
  await target.medicalReport.create({data:report});
 }
 // Absence of missing.analysisId is the negative artifact fixture; no scientific
 // values are removed or changed in any source or target row.
 for(const row of [full,legacy])await copyFile(path.resolve('tmp/v5cr-e2e/records',`${row.analysisId}.json`),path.join(recordsDir,`${row.analysisId}.json`));
 const legacyBytes=await readFile(path.join(legacyFolder,'document.pdf'));const legacyMeta=await readFile(path.join(legacyFolder,'manifest.json'));
 check('setup: previous PDF checksum matches its original manifest',sha(legacyBytes)===JSON.parse(legacyMeta).pdfHash);
 const legacyCopy=path.join(pdfDir,'canonical-v4',path.basename(legacyFolder));await mkdir(legacyCopy,{recursive:true});await writeFile(path.join(legacyCopy,'document.pdf'),legacyBytes);await writeFile(path.join(legacyCopy,'manifest.json'),legacyMeta);
 const std=await open(path.join(out,'SERVIDOR_PRUEBAS.log'),'w');
 server=spawn(process.execPath,['node_modules/next/dist/bin/next',process.env.V5CR_E2E_MODE??'dev','--hostname','127.0.0.1','--port','3049'],{env,windowsHide:true,stdio:['ignore',std.fd,std.fd]});
 const base='http://127.0.0.1:3049';let ready=false;for(let i=0;i<60;i++){try{const r=await fetch(base+'/api/auth/me');if(r.status===401){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,1000));}check('setup: test server ready',ready);
 const cookie=user=>{const body=Buffer.from(JSON.stringify({email:user.email,name:user.name,role:user.role,exp:Math.floor(Date.now()/1000)+3600})).toString('base64url');return `gait-session=${body}.${createHmac('sha256',secret).update(body).digest('base64url')}`;};
 const request=(url,user=full.user,options={})=>fetch(base+url,{...options,headers:{...(user?{cookie:cookie(user)}:{}),...options.headers}});
 let r=await request(`/api/me/reports/${full.id}/pdf`,null);check('auth: unauthenticated request rejected',r.status===401);
 r=await request(`/api/me/reports/${full.id}/pdf`,other);check('auth: another account cannot read the report',r.status===404);
 const beforeMissing=await target.medicalReport.findUnique({where:{id:missing.id}});
 r=await request(`/api/me/reports/${missing.id}/pdf`);let body=await r.json();check('http: missing historical artifact has explicit 404 JSON',r.status===404&&body.code==='HISTORICAL_PDF_UNAVAILABLE'&&body.message.includes('registro se conserva')&&!r.headers.has('content-disposition'));
 r=await request(`/api/me/reports/${missing.id}/pdf`,full.user,{method:'POST',headers:{'content-type':'application/json'},body:'{}'});body=await r.json();check('http: cannot silently reconstruct a missing historical record',r.status===404&&body.code==='HISTORICAL_PDF_UNAVAILABLE');
 check('integrity: unavailable report row was not changed',JSON.stringify(beforeMissing)===JSON.stringify(await target.medicalReport.findUnique({where:{id:missing.id}})));
 r=await request('/api/me/reports');const list=await r.json();check('http: history distinguishes unavailable and ungenerated PDF',list.reports.find(v=>v.id===missing.id)?.pdfAvailability.status==='unavailable'&&list.reports.find(v=>v.id===full.id)?.pdfAvailability.status==='not_generated');
 r=await request(`/api/me/reports/${full.id}/pdf`);body=await r.json();check('http: complete source is distinguished from missing history',r.status===404&&body.code==='PDF_NOT_GENERATED');
 r=await request(`/api/me/reports/${full.id}/pdf`,full.user,{method:'POST',headers:{'content-type':'application/json'},body:'{}'});check('http: new PDF generated from unchanged original technical data',r.ok);
 r=await request(`/api/me/reports/${full.id}/pdf`);const pdf=Buffer.from(await r.arrayBuffer());check('http: new PDF downloaded with valid MIME and header',r.ok&&r.headers.get('content-type')==='application/pdf'&&pdf.subarray(0,5).toString()==='%PDF-');await writeFile(path.join(out,'PDF_NUEVO_PRUEBA.pdf'),pdf);
 r=await request(`/api/me/reports/${full.id}/pdf`);check('http: repeated download is byte-identical',Buffer.from(await r.arrayBuffer()).equals(pdf));
 r=await request(`/api/me/reports/${legacy.id}/pdf`);check('http: compatible legacy cache downloaded byte-for-byte',r.ok&&Buffer.from(await r.arrayBuffer()).equals(legacyBytes));
 r=await request('/api/me/reports');const afterList=await r.json();check('http: history only marks validated PDFs as available',afterList.reports.find(v=>v.id===full.id)?.pdfAvailability.status==='available'&&afterList.reports.find(v=>v.id===legacy.id)?.pdfAvailability.status==='available'&&afterList.reports.find(v=>v.id===missing.id)?.pdfAvailability.status==='unavailable');
 r=await request('/api/admin/reports',other);const admin=await r.json();check('http: admin list includes true PDF availability',r.ok&&admin.reports.find(v=>v.id===missing.id)?.pdfAvailability.status==='unavailable');
 check('integrity: previous original PDF file untouched',sha(await readFile(path.join(legacyFolder,'document.pdf')))===sha(legacyBytes));
 const sourceAfter=await source.medicalReport.findMany({where:{id:{in:chosen.map(r=>r.id)}},include:{user:true,analysis:{include:{parameters:true,signals:true,conditions:true,video:true}}}});
 const ordered=chosen.map(c=>sourceAfter.find(r=>r.id===c.id));
 check('integrity: source technical records unchanged',sha(Buffer.from(JSON.stringify(ordered)))===sourceSnapshot);
}catch(e){console.error(e.message);process.exitCode=1;}finally{
 server?.kill();await source.$disconnect();await target.$disconnect();
 await writeFile(path.join(out,'PRUEBAS_HTTP_AISLADAS.json'),JSON.stringify({schema,habitualDatabaseUsed:false,inferenceExecuted:false,source:'Copies of existing real-video technical records; no new patient or scientific prediction',checks,passed:checks.filter(c=>c.passed).length,failed:checks.filter(c=>!c.passed).length},null,2));
}
