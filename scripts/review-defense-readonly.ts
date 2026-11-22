// Habitual environment inspection: GET requests only, no record writes.
import { PrismaClient } from "@prisma/client";
import { loadEnvConfig } from "@next/env";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { spawn } from "node:child_process";
import path from "node:path";
import { signSession } from "../src/lib/auth/sessionToken";
import { activeGaitModel, hasActiveGaitModel } from "../src/lib/ml/activeModel";
import { canonicalAnalysisPath } from "../src/lib/analysis/canonicalAnalysis";

loadEnvConfig(process.cwd());
const out = path.resolve("docs/revision_defensa_2026-11-19");
const prisma = new PrismaClient();
const tables = ["User", "VideoMarcha", "PosePoint", "GaitAnalysis", "GaitParameter", "DetectedSignal", "AssociatedCondition", "MedicalReport", "SystemLog"];
const sha = (b: Buffer) => createHash("sha256").update(b).digest("hex");
async function snapshot() {
  return prisma.$transaction(async tx => {
    await tx.$executeRawUnsafe("SET TRANSACTION READ ONLY");
    const rows: Record<string, unknown> = {};
    for (const table of tables) {
      rows[table] = await tx.$queryRawUnsafe(`SELECT count(*)::int AS count, md5(COALESCE(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text)::text, '[]')) AS fingerprint FROM "${table}" t`);
    }
    return rows;
  });
}

async function main() {
  await mkdir(out, {recursive:true});
  const envUrl = new URL(process.env.DATABASE_URL!);
  const result: Record<string, unknown> = {environment:{host:envUrl.hostname,port:envUrl.port||"5432",database:envUrl.pathname},selectedModel:activeGaitModel(),artifactsPresent:hasActiveGaitModel(),visualTools:"unavailable; no desktop/mobile visual approval",http:[]};
  const before = await snapshot();
  await writeFile(path.join(out,"BD_ANTES.json"),JSON.stringify(before,null,2));
  let child: ReturnType<typeof spawn> | undefined;
  try {
    const users = await prisma.user.findMany({select:{id:true,email:true,name:true,role:true,_count:{select:{analyses:true,reports:true}}}});
    result.accounts={total:users.length,administrators:users.filter(u=>u.role==="ADMIN").length,ordinaryUsers:users.filter(u=>u.role==="USER").length};
    const reports = await prisma.medicalReport.findMany({select:{id:true,userId:true,analysisId:true,pdfUrl:true},orderBy:{createdAt:"desc"}});
    result.reports={total:reports.length,canonicalRecordsPresent:reports.filter(r=>existsSync(canonicalAnalysisPath(r.analysisId))).length,withStoredPdfUrl:reports.filter(r=>r.pdfUrl).length};
    const versions = await prisma.gaitParameter.groupBy({by:["value"],where:{name:"Versión del modelo"},_count:true});
    result.storedModelVersions=versions.map(v=>({version:v.value,count:v._count}));
    const stdout=await import("node:fs").then(fs=>fs.openSync(path.join(out,"SERVIDOR_HABITUAL.log"),"w"));
    child=spawn(process.execPath,["node_modules/next/dist/bin/next","dev","--hostname","127.0.0.1","--port","3000"],{env:process.env,windowsHide:true,stdio:["ignore",stdout,stdout]});
    const base="http://127.0.0.1:3000";
    let ready=false;
    for(let i=0;i<60;i++){try{const r=await fetch(base+"/api/auth/me");if(r.status===401){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,1000));}
    result.serverReady=ready;
    if(!ready)throw Error("El servidor habitual no estuvo disponible en el puerto 3000");
    const checks: Array<{path:string;status:number;expected?:number;passed?:boolean;note?:string}> = [];
    async function get(url:string,cookie?:string,expected?:number) {
      const r=await fetch(base+url,{headers:cookie?{cookie}:{},redirect:"manual"});
      const buffer=Buffer.from(await r.arrayBuffer());
      checks.push({path:url.replace(/\/[^/]+\/pdf$/, "/[id]/pdf"),status:r.status,expected,passed:expected===undefined?undefined:r.status===expected});
      return {response:r,buffer};
    }
    await get("/",undefined,200);await get("/login",undefined,200);await get("/api/admin/summary",undefined,401);
    const user=users.filter(u=>u.role==="USER").sort((a,b)=>b._count.analyses-a._count.analyses)[0];
    if(user){
      const cookie=`gait-session=${await signSession(user)}`;
      // Temporary in-memory sessions inspect existing records; no login POST,
      // upload, report creation or PDF regeneration touches the habitual DB.
      await get("/api/me/summary",cookie,200);await get("/api/me/analyses",cookie,200);await get("/api/me/reports",cookie,200);
      await get("/dashboard",cookie,200);await get("/analisis/subir-video",cookie,200);await get("/analisis/resultado",cookie,200);await get("/analisis/evaluacion",cookie,200);await get("/analisis/informe",cookie,200);await get("/seguimiento",cookie,200);
      const report=reports.find(r=>r.userId===user.id);
      if(report){const pdf=await get(`/api/me/reports/${report.id}/pdf`,cookie);result.existingPdfDownload={status:pdf.response.status,validPdf:pdf.buffer.subarray(0,5).toString()==="%PDF-",regenerationAttempted:false};}
    }
    const admin=users.find(u=>u.role==="ADMIN");
    if(admin){
      const cookie=`gait-session=${await signSession(admin)}`;
      const r=await get("/api/admin/summary",cookie,200);
      if(r.response.ok){const summary=JSON.parse(r.buffer.toString());result.adminModelStatus=summary.modelStatus;}
      await get("/admin",cookie,200);await get("/api/admin/analyses",cookie,200);await get("/api/admin/reports",cookie,200);
    }
    result.http=checks;
    result.notExecuted=["Browser login and desktop/mobile rendering/interactions","Real upload in habitual database (would create records)","PDF regeneration on existing habitual reports (would update their records)"];
  } finally {
    child?.kill();
    const after=await snapshot();result.databaseUnchanged=JSON.stringify(before)===JSON.stringify(after);
    await writeFile(path.join(out,"BD_DESPUES.json"),JSON.stringify(after,null,2));
    await writeFile(path.join(out,"REVISION_ENTORNO_HABITUAL.json"),JSON.stringify(result,null,2));
    const artifact=path.resolve("models/gait_deep_v5cr/gait_deep_v5exp_V5CR_7e9ed60965fe.pt");
    console.log(JSON.stringify({selected:activeGaitModel().version,weightsSha256:sha(await readFile(artifact)),databaseUnchanged:result.databaseUnchanged,accounts:result.accounts,reports:result.reports,existingPdf:result.existingPdfDownload,http:result.http},null,2));
  }
}
main().catch(e=>{console.error(e.message);process.exitCode=1;}).finally(()=>prisma.$disconnect());
