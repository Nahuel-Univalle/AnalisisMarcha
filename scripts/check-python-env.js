/* eslint-disable @typescript-eslint/no-require-imports */
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const projectRoot = path.resolve(__dirname, "..");

function loadEnvFile(fileName) {
  const filePath = path.join(projectRoot, fileName);
  if (!fs.existsSync(filePath)) return;

  const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;

    const index = trimmed.indexOf("=");
    const key = trimmed.slice(0, index).trim();
    const value = trimmed
      .slice(index + 1)
      .trim()
      .replace(/^["']|["']$/g, "");

    if (!process.env[key]) {
      process.env[key] = value;
    }
  }
}

function normalizeExecutable(value) {
  return String(value || "")
    .trim()
    .replace(/^["']|["']$/g, "");
}

function run(command, args) {
  return spawnSync(command, args, {
    cwd: projectRoot,
    encoding: "utf8",
    timeout: 10000,
    windowsHide: true,
  });
}

function printResult(label, ok, detail, statusLabel) {
  const status = statusLabel || (ok ? "OK" : "ERROR");
  console.log(`[${status}] ${label}${detail ? `: ${detail}` : ""}`);
}

function candidateExecutables() {
  const candidates = [];
  const configured = normalizeExecutable(process.env.PYTHON_ANALYSIS_EXECUTABLE);

  if (configured) candidates.push(configured);
  candidates.push(path.join(projectRoot, ".venv311", "Scripts", "python.exe"));
  candidates.push(path.join(projectRoot, ".venv", "Scripts", "python.exe"));
  candidates.push("python");

  return [...new Set(candidates)];
}

function findWorkingPython() {
  for (const candidate of candidateExecutables()) {
    const result = run(candidate, ["--version"]);
    if (!result.error && result.status === 0) {
      return {
        command: candidate,
        version: `${result.stdout}${result.stderr}`.trim(),
      };
    }
  }

  return null;
}

function checkImport(pythonCommand, moduleName) {
  const result = run(pythonCommand, [
    "-c",
    `import ${moduleName}; print(getattr(${moduleName}, "__version__", "sin version"))`,
  ]);
  return {
    ok: !result.error && result.status === 0,
    detail: result.error
      ? result.error.message
      : `${result.stdout}${result.stderr}`.trim(),
  };
}

loadEnvFile(".env.local");
loadEnvFile(".env");

console.log(`Proyecto: ${projectRoot}`);

const configured = normalizeExecutable(process.env.PYTHON_ANALYSIS_EXECUTABLE);
printResult(
  "PYTHON_ANALYSIS_EXECUTABLE",
  Boolean(configured),
  configured || "no configurado"
);

let configuredMissing = false;
if (configured) {
  const configuredExists = fs.existsSync(configured);
  configuredMissing = !configuredExists;
  printResult(
    "Existe PYTHON_ANALYSIS_EXECUTABLE",
    configuredExists,
    configured,
    configuredExists ? "OK" : "WARN"
  );
}

const workingPython = findWorkingPython();
if (!workingPython) {
  printResult(
    "Python válido",
    false,
    "No se encontró Python ejecutable. Instale Python 3.11 y recree .venv311."
  );
  process.exit(1);
}

printResult("Python válido", true, workingPython.command);
printResult("Versión de Python", true, workingPython.version);

let hasImportError = false;
for (const moduleName of ["cv2", "mediapipe", "numpy", "pandas"]) {
  const result = checkImport(workingPython.command, moduleName);
  printResult(`Importación ${moduleName}`, result.ok, result.detail);
  if (!result.ok) hasImportError = true;
}

if (hasImportError) {
  console.log(
    "Instale dependencias con: .\\.venv311\\Scripts\\python.exe -m pip install -r requirements.txt"
  );
  process.exit(1);
}

if (configuredMissing && workingPython.command !== configured) {
  console.log(
    "Aviso: el ejecutable configurado no existe. La API usará el fallback válido mostrado arriba hasta recrear .venv311 con Python 3.11."
  );
}
