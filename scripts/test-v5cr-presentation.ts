// Presentation/selection regressions using an existing real-video test output.
import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { activeGaitModel, hasActiveGaitModel } from "../src/lib/ml/modelMetrics";
import { mapEvaluationToAnalysisResult } from "../src/lib/analysis/mapApiAnalysis";
import { keyGaitMetricGroups, quantitativeGroups, classDistribution } from "../src/lib/analysis/resultPresentation";
import { storedPatternOf } from "../src/lib/analysis/conditionLabels";

async function main() {
  const checks: Array<{name:string;passed:boolean}> = [];
  function check(name:string, fn:()=>void) { fn(); checks.push({name,passed:true}); console.log(`PASS ${name}`); }
  const dir="docs/integracion_v5cr_2026-11-19";
  const originalEnv=process.env.GAIT_MODEL_VERSION;
  try {
    delete process.env.GAIT_MODEL_VERSION;
    check("unit: default is accepted V5-CR",()=>assert.equal(activeGaitModel().key,"v5cr"));
    check("integrated: selected artifact files exist",()=>assert.ok(hasActiveGaitModel()));
    process.env.GAIT_MODEL_VERSION="v4";
    check("regression: explicit V4 rollback retains original predictor",()=>{assert.equal(activeGaitModel().predictor,"14_predict_deep_video_v4exp.py");assert.ok(hasActiveGaitModel());});
    process.env.GAIT_MODEL_VERSION="invalid";
    check("unit: invalid selection fails closed",()=>assert.throws(activeGaitModel));
    const payload=JSON.parse(await readFile(`${dir}/E2E_ANALYSIS.json`,"utf8"));
    const result=mapEvaluationToAnalysisResult(payload.analysis);
    const groups=keyGaitMetricGroups(result);
    check("integrated: V5-CR symmetry presented from actual relative feature",()=>{
      const p=groups.find(x=>x.title==="Simetría")?.params[0];assert.ok(p);assert.equal(p.unit,"%");
      assert.equal(p.value,String(Math.round(payload.analysis.gaitFeatures.leg_rel_motion_asymmetry*100)));
    });
    check("integrated: rhythm describes 2.6-second peak estimate",()=>{assert.match(groups[0].params[0].explanation,/2,6 s/);assert.equal(groups[0].params[0].unit,"picos/min");});
    const detail=quantitativeGroups(result);
    check("integrated: relative legs and angular arms included",()=>{assert.ok(detail.find(g=>g.title==="Movimiento de piernas")?.params.length);assert.ok(detail.find(g=>g.title==="Movimiento de brazos")?.params.some(p=>p.unit==="rad"));});
    check("regression: no global translation feature presented",()=>assert.ok(!detail.some(g=>g.params.some(p=>/avance horizontal/i.test(p.explanation)))));
    check("integrated: presentation preserves all four probabilities",()=>{assert.equal(classDistribution(result).length,4);assert.ok(Math.abs(classDistribution(result).reduce((s,p)=>s+p.fraction,0)-1)<1e-6);});
    const insufficient=JSON.parse(await readFile(`${dir}/E2E_POSE_INSUFICIENTE.json`,"utf8"));
    check("integrated: insufficient pose has no metrics/probabilities in presentation",()=>{const r=mapEvaluationToAnalysisResult(insufficient.analysis);assert.deepEqual(keyGaitMetricGroups(r),[]);assert.deepEqual(classDistribution(r),[]);});
    const history=JSON.parse(await readFile(`${dir}/E2E_HISTORY.json`,"utf8"));
    check("regression: historical parameters retain V4 version",()=>assert.ok(history.analyses.some((a:{parameters:Array<{value:string}>})=>a.parameters.some(p=>p.value==="gait_deep_v4exp_M1_BN_recalibrated_candidate_v1"))));
    check("regression: stored pattern uses record content",()=>assert.equal(storedPatternOf(history.analyses.find((a:{id:string})=>a.id===payload.analysis.id)).pattern,"normal"));
    await writeFile(`${dir}/PRUEBAS_TYPESCRIPT.json`,JSON.stringify({checks,passed:checks.length,failed:0},null,2));
  } finally {
    if(originalEnv===undefined)delete process.env.GAIT_MODEL_VERSION;else process.env.GAIT_MODEL_VERSION=originalEnv;
  }
}
main().catch(e=>{console.error(e);process.exitCode=1;});
