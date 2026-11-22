import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
import { validatedPdfBlob } from "../src/lib/analysis/pdfDownload";
import { HISTORICAL_PDF_UNAVAILABLE_MESSAGE } from "../src/lib/analysis/reportPdfStatus";

async function main() {
  const checks: Array<{name:string;passed:boolean}> = [];
  async function rejects(name:string,response:Response,message?:string) {
    if (message) await assert.rejects(validatedPdfBlob(response), new RegExp(message));
    else await assert.rejects(validatedPdfBlob(response));
    checks.push({name,passed:true});
  }
  const bytes="%PDF-1.3\nTechnical byte fixture for download validation only";
  const blob=await validatedPdfBlob(new Response(bytes,{headers:{"content-type":"application/pdf"}}));
  assert.equal(await blob.text(),bytes);checks.push({name:"valid PDF bytes preserved",passed:true});
  await rejects("historical 404 is a visible error, never a download",Response.json({code:"HISTORICAL_PDF_UNAVAILABLE",message:HISTORICAL_PDF_UNAVAILABLE_MESSAGE},{status:404}),"archivo histórico");
  await rejects("HTTP 200 JSON cannot be saved as PDF",Response.json({success:true}));
  await rejects("HTML error page cannot be saved as PDF",new Response("<html>Error</html>",{headers:{"content-type":"text/html"}}));
  await rejects("false PDF MIME type is rejected",new Response("not PDF",{headers:{"content-type":"application/pdf"}}));
  await rejects("empty PDF response is rejected",new Response("",{headers:{"content-type":"application/pdf"}}));
  await writeFile("docs/recuperacion_pdf_historicos_2026-11-19/PRUEBAS_DESCARGA_CLIENTE.json",JSON.stringify({checks,passed:checks.length,failed:0},null,2));
  console.log(`${checks.length} checks passed`);
}
main().catch(e=>{console.error(e);process.exitCode=1;});
