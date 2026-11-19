import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
export function canonicalAnalysisPath(id: string) {
 if (!/^[A-Za-z0-9_-]{1,128}$/.test(id)) throw new Error("Identificador inválido");
 return path.join(process.env.ANALYSIS_RECORD_STORAGE_DIR || path.join(/* turbopackIgnore: true */ process.cwd(), "..", "analysis-records"), `${id}.json`);
}
export async function persistCanonicalAnalysis(analysis: { id: string }) {
 const file = canonicalAnalysisPath(analysis.id); await mkdir(path.dirname(file), { recursive: true });
 await writeFile(file, JSON.stringify({ analysis }), { flag: "wx" });
}
