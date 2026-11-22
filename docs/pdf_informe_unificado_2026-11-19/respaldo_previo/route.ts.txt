import { mkdir, writeFile, rename } from "node:fs/promises";
import path from "node:path";
import { createHash, randomUUID } from "node:crypto";
import { requireUser } from "@/lib/auth/guards";
import { prisma } from "@/lib/prisma";
import { canonicalDocument, renderCanonicalPdf } from "@/lib/analysis/canonicalPdf";
import { PDF_PRESENTATION_RENDERER } from "@/lib/analysis/pdfPresentation";
import { reportPdfFiles as files, readValidatedReportPdf as validated, reportPdfAvailability } from "@/lib/analysis/reportPdfStorage";
type Context = { params: Promise<{ id: string }> };
export const runtime = "nodejs";
const pending = new Map<string, Promise<void>>();
async function authorized(context: Context) {const auth=await requireUser();if("error" in auth)return {error:auth.error};const {id}=await context.params;if(!/^[A-Za-z0-9_-]{1,128}$/.test(id))return {error:new Response(null,{status:404})};const r=await prisma.medicalReport.findFirst({where:{id,userId:auth.user.id}});if(!r)return {error:new Response(null,{status:404})};return {id,userId:auth.user.id,analysisId:r.analysisId};}
export async function GET(_r:Request,c:Context){const a=await authorized(c);if("error" in a)return a.error;try{return new Response(new Uint8Array(await validated(a.id,a.userId)),{headers:{"Content-Type":"application/pdf","Content-Disposition":'attachment; filename="informe_analisis_marcha.pdf"',"Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff"}});}catch{const availability=await reportPdfAvailability(a.id,a.userId,a.analysisId);return Response.json({code:availability.status==="not_generated"?"PDF_NOT_GENERATED":"HISTORICAL_PDF_UNAVAILABLE",message:availability.message},{status:404,headers:{"Cache-Control":"private, no-store"}});}}
export async function POST(r:Request,c:Context){const a=await authorized(c);if("error" in a)return a.error;
 if(r.headers.get("content-type")?.split(";")[0].trim()!=="application/json")return new Response("Se admite sólo el comando de generación JSON",{status:415});
 if(Number(r.headers.get("content-length")??0)>1024)return new Response(null,{status:413});
 try{const t=await r.text();if(t.length>1024)return new Response(null,{status:413});const body=JSON.parse(t);if(!body||Array.isArray(body)||typeof body!=="object"||Object.keys(body).length)return new Response("El cliente no puede aportar contenido",{status:400});}catch{return new Response(null,{status:400});}
 try {const availability=await reportPdfAvailability(a.id,a.userId,a.analysisId);if(availability.status==="unavailable")return Response.json({code:"HISTORICAL_PDF_UNAVAILABLE",message:availability.message},{status:404});try{await validated(a.id,a.userId,false);return Response.json({success:true,reused:true});}catch{}
 if(!pending.has(a.id))pending.set(a.id,(async()=>{const d=await canonicalDocument(a.id,a.userId);if(!d)throw new Error("No encontrado");const f=files(a.id,d.hash);await mkdir(f.root,{recursive:true});const data=renderCanonicalPdf(d);const staging=path.join(f.root,`.pending-${a.id}-${randomUUID()}`);await mkdir(staging);await writeFile(path.join(staging,"document.pdf"),data,{flag:"wx"});await writeFile(path.join(staging,"manifest.json"),JSON.stringify({sourceHash:d.hash,pdfHash:createHash("sha256").update(data).digest("hex"),renderer:PDF_PRESENTATION_RENDERER}),{flag:"wx"});try{await rename(staging,f.dir);}catch(error){if(!["EEXIST","ENOTEMPTY"].includes((error as NodeJS.ErrnoException).code ?? ""))throw error;await validated(a.id,a.userId,false);}await prisma.medicalReport.update({where:{id:a.id},data:{pdfUrl:`/api/me/reports/${a.id}/pdf`}});})().finally(()=>pending.delete(a.id)));
 await pending.get(a.id);await validated(a.id,a.userId);return Response.json({success:true,reused:false});
 }catch{return new Response("Registro canónico incompleto o generación no disponible",{status:422});}}
