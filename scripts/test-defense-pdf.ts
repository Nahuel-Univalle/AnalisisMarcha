// Pure presentation regression, using the previously recorded real-video test.
import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { createHash } from "node:crypto";
import { formatPdfValue, pdfParameterLine } from "../src/lib/analysis/pdfPresentation";
import { MODEL_CLASS_PARAMETER } from "../src/lib/analysis/conditionLabels";
import { renderCanonicalPdf, canonicalDocument } from "../src/lib/analysis/canonicalPdf";
import { mapEvaluationToAnalysisResult } from "../src/lib/analysis/mapApiAnalysis";
import { keyGaitMetricGroups, modelQualityWarnings, experimentalClassification, analysisQuality } from "../src/lib/analysis/resultPresentation";

async function main() {
  const out="docs/revision_defensa_2026-11-19";
  const input="docs/integracion_v5cr_2026-11-19";
  await mkdir(out,{recursive:true});
  const checks: Array<{name:string;passed:boolean}>=[];
  function check(name:string, run:()=>void){run();checks.push({name,passed:true});}
  check("decimal display trimmed",()=>assert.equal(formatPdfValue("0.091629"),"0,092"));
  check("integer has no artificial decimals",()=>assert.equal(formatPdfValue("270.00000"),"270"));
  check("tiny nonzero value is not rounded to zero",()=>assert.equal(formatPdfValue("0.000012345"),"0,0000123"));
  check("version identifier remains exact",()=>assert.equal(formatPdfValue("gait_deep_v5exp_V5CR_7e9ed60965fe"),"gait_deep_v5exp_V5CR_7e9ed60965fe"));
  check("no redundant machine class",()=>assert.equal(pdfParameterLine({name:MODEL_CLASS_PARAMETER,value:"Marcha normal",state:"normal"}),`${MODEL_CLASS_PARAMETER}: Marcha normal`));
  check("legacy rhythm uses presentation precision",()=>assert.equal(pdfParameterLine({name:"Ritmo de la marcha",value:"61.016949",state:""}),"Ritmo de la marcha: 61"));
  const payload=JSON.parse(await readFile(`${input}/E2E_ANALYSIS.json`,"utf8"));
  const history=JSON.parse(await readFile(`${input}/E2E_HISTORY.json`,"utf8"));
  const analysis=payload.analysis;
  const stored=history.analyses.find((a:{id:string})=>a.id===analysis.id);
  assert.ok(stored);
  const ui=mapEvaluationToAnalysisResult(analysis);
  const warnings=modelQualityWarnings(ui);
  const data={version:"canonical-v4",ui:{metrics:keyGaitMetricGroups(ui),warnings:[...warnings.alerts,...warnings.notes],confidence:experimentalClassification(ui).confidenceText,caveat:experimentalClassification(ui).caveat,quality:analysisQuality(ui).explanation},
    reportId:"revision-tecnica-sin-paciente-nuevo",analysisId:analysis.id,name:"Prueba técnica V5-CR",date:`${stored.date}T12:00:00.000Z`,summary:stored.summary,parameters:stored.parameters,signals:stored.signals,conditions:stored.conditions,analysis};
  const hash=createHash("sha256").update(JSON.stringify(data)).digest("hex");
  const before=JSON.stringify(data);
  const pdf=renderCanonicalPdf({data,hash} as NonNullable<Awaited<ReturnType<typeof canonicalDocument>>>);
  check("rendering does not mutate raw scientific data",()=>assert.equal(JSON.stringify(data),before));
  check("valid PDF output",()=>assert.equal(pdf.subarray(0,5).toString(),"%PDF-"));
  await writeFile(`${out}/PDF_PRESENTACION_REVISADA.pdf`,pdf);
  await writeFile(`${out}/PRUEBAS_PRESENTACION_PDF.json`,JSON.stringify({checks,passed:checks.length,failed:0,source:"Existing real-video technical test output; no database writes or new patient",originalScientificDataSha256:hash},null,2));
  console.log(`${checks.length} presentation checks passed`);
}
main().catch(e=>{console.error(e);process.exitCode=1;});
