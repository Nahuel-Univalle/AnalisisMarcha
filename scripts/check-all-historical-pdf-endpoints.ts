// Habitual DB: GET-only audit of every report, never PDF POST/regeneration.
import { loadEnvConfig } from "@next/env";
import { PrismaClient } from "@prisma/client";
import { readFile, writeFile, open } from "node:fs/promises";
import { spawn } from "node:child_process";
import { signSession } from "../src/lib/auth/sessionToken";
loadEnvConfig(process.cwd());
const p=new PrismaClient();
const dir="docs/recuperacion_pdf_historicos_2026-11-19";
const tables=["User","VideoMarcha","PosePoint","GaitAnalysis","GaitParameter","DetectedSignal","AssociatedCondition","MedicalReport","SystemLog"];
async function snapshot(){return p.$transaction(async tx=>{await tx.$executeRawUnsafe("SET TRANSACTION READ ONLY");const result:Record<string,unknown>={};for(const table of tables)result[table]=await tx.$queryRawUnsafe(`SELECT count(*)::int AS count, md5(COALESCE(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text)::text,'[]')) AS fingerprint FROM "${table}" t`);return result;});}
async function main(){
 const url=new URL(process.env.DATABASE_URL!);if(url.hostname!=="127.0.0.1"||url.port!=="5433"||url.pathname!=="/analisis_marcha_db")throw Error("Habitual environment guard");
 const before=await snapshot();const serverLog=await open(`${dir}/SERVIDOR_HABITUAL.log`,"w");
 const child=spawn(process.execPath,["node_modules/next/dist/bin/next","dev","--hostname","127.0.0.1","--port","3000"],{windowsHide:true,env:process.env,stdio:["ignore",serverLog.fd,serverLog.fd]});
 const responses:Array<{reportId:string;analysisId:string;status:number;code:string;pdfHeader:boolean;message:string}>=[];
 try{
  const base="http://127.0.0.1:3000";let ready=false;for(let i=0;i<60;i++){try{if((await fetch(base+"/api/auth/me")).status===401){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,1000));}if(!ready)throw Error("Server unavailable");
  const reports=await p.medicalReport.findMany({include:{user:{select:{id:true,email:true,name:true,role:true}}},orderBy:{id:"asc"}});
  const cookies=new Map<string,string>();
  for(const r of reports){if(!cookies.has(r.userId))cookies.set(r.userId,`gait-session=${await signSession(r.user)}`);
    const response=await fetch(`${base}/api/me/reports/${r.id}/pdf`,{headers:{cookie:cookies.get(r.userId)!}});const bytes=Buffer.from(await response.arrayBuffer());let message="",code="";try{const body=JSON.parse(bytes.toString());message=body.message;code=body.code;}catch{}
    responses.push({reportId:r.id,analysisId:r.analysisId,status:response.status,code,message,pdfHeader:bytes.subarray(0,5).toString()==="%PDF-"});
  }
  const listing=[];
  for(const [userId,cookie] of cookies){const response=await fetch(base+"/api/me/reports",{headers:{cookie}});const body=await response.json();listing.push({userId,http:response.status,count:body.reports?.length,unavailable:body.reports?.filter((r:{pdfAvailability?:{status:string}})=>r.pdfAvailability?.status==="unavailable").length});}
  await writeFile(`${dir}/HTTP_79_INFORMES.json`,JSON.stringify({environment:"habitual:5433, GET only",total:responses.length,originalDownloadsAvailable:responses.filter(r=>r.status===200&&r.pdfHeader).length,explicitUnavailable:responses.filter(r=>r.status===404&&r.code==="HISTORICAL_PDF_UNAVAILABLE").length,responses,listings:listing,postRequestsExecuted:0},null,2));
  console.log(JSON.stringify({reportsChecked:responses.length,explicitUnavailable:responses.filter(r=>r.status===404&&r.code==="HISTORICAL_PDF_UNAVAILABLE").length}));
 }finally{
  child.kill();const after=await snapshot();
  const initial=JSON.parse(await readFile(`${dir}/AUDITORIA_REGISTROS.json`,"utf8")).databaseSnapshot;
  const unchanged=JSON.stringify(before)===JSON.stringify(after)&&JSON.stringify(initial)===JSON.stringify(after);
  await writeFile(`${dir}/CONSERVACION_BD_HABITUAL.json`,JSON.stringify({unchanged,before,after,initialAuditAlsoMatches:JSON.stringify(initial)===JSON.stringify(after)},null,2));
  if(!unchanged)throw Error("Database fingerprint changed");
 }
}
main().catch(e=>{console.error(e.message);process.exitCode=1;}).finally(()=>p.$disconnect());
