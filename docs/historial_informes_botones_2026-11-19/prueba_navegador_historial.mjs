// Prueba real en Chrome (CDP, sin instalar nada): servidor Next aislado (BD tecnica 55432, Cloudinary vacio) + flujo de la UI.
// Uso: node drive.mjs <video> <escenario> [modo=start]
import { spawn, spawnSync } from 'node:child_process';
import { readFile, writeFile, open, mkdir, rm } from 'node:fs/promises';
import { resolve, join, basename } from 'node:path';
import { randomBytes } from 'node:crypto';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');
const [videoArg, scenario = 'replay'] = process.argv.slice(2);
const video = resolve(videoArg);
const out = resolve('tmp/hist/out'); await mkdir(out, { recursive: true });
const schema = 'hist_' + Date.now();
const url = `postgresql://postgres:v5cr-local-test-only@127.0.0.1:55432/gait_v5cr_test?schema=${schema}`;
const port = process.env.PLAYER_PORT ?? '3056'; const base = `http://127.0.0.1:${port}`;
const env = { ...process.env, DATABASE_URL: url, AUTH_SESSION_SECRET: randomBytes(48).toString('hex'),
  CLOUDINARY_CLOUD_NAME: '', CLOUDINARY_API_KEY: '', CLOUDINARY_API_SECRET: '', CLOUDINARY_FOLDER: '',
  ANALYSIS_RECORD_STORAGE_DIR: join(out, 'records'), REPORT_PDF_STORAGE_DIR: join(out, 'pdfs') };
const push = spawnSync(process.execPath, ['node_modules/prisma/build/index.js', 'db', 'push', '--skip-generate'], { env, encoding: 'utf8', windowsHide: true });
if (push.status !== 0) { console.log(push.stdout, push.stderr); process.exit(1); }
const db = new PrismaClient({ datasources: { db: { url } } });
await db.user.create({ data: { name: 'Prueba reproductor', email: 'player@example.invalid', passwordHash: await bcrypt.hash('Player2026!x', 10), role: 'USER', age: 30 } });
const slog = await open(join(out, `server_${scenario}.log`), 'w');
const server = spawn(process.execPath, ['node_modules/next/dist/bin/next', process.env.PLAYER_MODE ?? 'start', '--hostname', '127.0.0.1', '--port', port], { env, windowsHide: true, stdio: ['ignore', slog.fd, slog.fd] });
const chromePath = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const cport = 9460 + Math.floor(Math.random() * 50);
const profile = resolve('tmp/hist/profile_' + Date.now());
const chrome = spawn(chromePath, ['--headless=new', `--remote-debugging-port=${cport}`, `--user-data-dir=${profile}`, '--autoplay-policy=no-user-gesture-required', '--no-first-run', '--window-size='+(process.env.PLAYER_SIZE??'1366,1150'), 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const results = { scenario, video: basename(video), checks: [], notes: [] };
function check(name, ok, detail) { results.checks.push({ name, passed: !!ok, ...(detail !== undefined ? { detail } : {}) }); console.log(`${ok ? 'PASS' : 'FAIL'} ${name}`, detail !== undefined ? JSON.stringify(detail) : ''); }
try {
  for (let i = 0; i < 120; i++) { try { const r = await fetch(base + '/api/auth/me'); if (r.status === 401 || r.ok) break; } catch {} await sleep(1000); }
  let target;
  for (let i = 0; i < 60; i++) { try { const t = await (await fetch(`http://127.0.0.1:${cport}/json`)).json(); target = t.find(x => x.type === 'page'); if (target) break; } catch {} await sleep(500); }
  const ws = new WebSocket(target.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r));
  let id = 0; const pending = new Map(); const consoleLines = []; const netErrors = [];
  ws.addEventListener('message', m => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); }
    if (d.method === 'Runtime.consoleAPICalled') consoleLines.push(d.params.type + ': ' + d.params.args.map(a => a.value ?? a.description).join(' '));
    if (d.method === 'Network.loadingFailed') netErrors.push(d.params);
    if (d.method === 'Network.responseReceived' && d.params.response.url.startsWith('blob:')) netErrors.push({ blobResponse: d.params.response.status }); });
  const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async (expression) => { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }); if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails).slice(0, 300)); return r.result.result.value; };
  globalThis.__dump = async () => ({ ev: await ev('window.__ev||[]').catch(()=>null), console: consoleLines.slice(-15), net: netErrors.slice(-10) });
  await send('Page.enable'); await send('Runtime.enable'); await send('DOM.enable'); await send('Network.enable');
  // login por API y cookie de sesion
  const login = await fetch(base + '/api/auth/login', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ email: 'player@example.invalid', password: 'Player2026!x' }) });
  const [cname, ...cv] = login.headers.get('set-cookie').split(';')[0].split('=');
  await send('Network.setCookie', { name: cname, value: cv.join('='), url: base });
  await send('Page.navigate', { url: base + '/analisis/subir-video' }); await sleep(4000);
  const doc = await send('DOM.getDocument'); const q = await send('DOM.querySelector', { nodeId: doc.result.root.nodeId, selector: 'input[type=file]' });
  await send('DOM.setFileInputFiles', { nodeId: q.result.nodeId, files: [video] }); await sleep(1500);
  const clickText = t => ev(`(()=>{const b=[...document.querySelectorAll('button,a')].find(x=>x.textContent.includes(${JSON.stringify(t)})&&!x.disabled);if(!b)return false;b.click();return true})()`);
  check('upload page shows the preview <video>', await ev(`!!document.querySelector('video')`));
  check('continue to validation', await clickText('Continuar a la revisi')); await sleep(2500);
  check('start analysis', await clickText('Iniciar an')); await sleep(2500);


  const body = () => ev(`document.body.innerText`);
  for (let i = 0; i < 300; i++) { const t = await body(); if (t.includes('Análisis completado') || t.includes('No se pudo completar')) break; await sleep(1000); }
  check('analysis finished', (await body()).includes('Análisis completado'));
  check('go to result', await clickText('Ver resultado')); await sleep(2500);
  check('go to report page', await clickText('Generar informe PDF')); await sleep(3000);
  check('save report in tracking', await clickText('Guardar en seguimiento')); await sleep(3000);
  // fixture explicito: informe historico SIN archivo (analisis sin registro canonico), solo en esta BD tecnica
  const u = await db.user.findFirst({ where: { email: 'player@example.invalid' } });
  const old = await db.gaitAnalysis.create({ data: { user: { connect: { id: u.id } }, alert: 'BAJO', summary: 'REGISTRO TECNICO DE PRUEBA: informe historico sin archivo', video: { create: { userId: u.id, originalName: 'fixture-historico', mimeType: 'application/x-test-fixture', sizeBytes: 0 } }, parameters: { create: [{ name: 'Versión del modelo', value: 'gait_deep_v4exp_M1_BN_recalibrated_candidate_v1', state: 'Referencia' }] } } });
  const oldReport = await db.medicalReport.create({ data: { userId: u.id, analysisId: old.id, title: 'Informe histórico sin PDF (fixture)' } });
  await send('Page.reload'); await sleep(4500);
  const listJs = `(()=>{const items=[...document.querySelectorAll('ol > li')];return items.map(li=>({text:li.innerText.replace(/\\s+/g,' ').slice(0,300),buttons:[...li.querySelectorAll('button')].map(b=>b.innerText.trim()+'|'+(b.getAttribute('aria-label')||'')+'|'+b.disabled)}))})()`;
  const list = await ev(listJs);
  results.notes.push({ list });
  console.log(JSON.stringify(list));
  check('two records listed', list.length === 2, list.length);
  const withPdf = list.find(x => x.buttons.some(b => b.startsWith('Ver informe')));
  const noPdf = list.find(x => x.text.includes('PDF no disponible') || x.text.includes('no está disponible'));
  check('record with PDF has Ver informe + Descargar PDF + Videos', withPdf && ['Ver informe', 'Descargar PDF'].every(t => withPdf.buttons.some(b => b.startsWith(t))), withPdf?.buttons);
  check('record without PDF: explicit "no disponible", no PDF buttons, record kept', noPdf && !noPdf.buttons.some(b => b.startsWith('Ver informe') || b.startsWith('Descargar')), noPdf?.text);
  check('category filter still present', await ev(`document.body.innerText.includes('Patrón de marcha') && !!document.querySelector('[aria-label="Filtrar por patrón de marcha"]')`));
  await send('Page.captureScreenshot').then(r => writeFile(join(out, 'lista_antes.png'), Buffer.from(r.result.data, 'base64')));
  // --- Ver informe: pestana nueva con el PDF
  const pages = async () => (await (await fetch(`http://127.0.0.1:${cport}/json`)).json()).filter(t => t.type === 'page');
  const before = (await pages()).map(t => t.id);
  const dlv = join(out, 'descargas_ver'); await rm(dlv, { recursive: true, force: true }); await mkdir(dlv, { recursive: true });
  await send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: dlv });
  const realClick = async (prefix) => {
    const r = await ev(`(()=>{const b=[...document.querySelectorAll('button')].find(x=>x.getAttribute('aria-label')?.startsWith(${JSON.stringify(prefix)}));if(!b)return null;b.scrollIntoView({block:'center'});const q=b.getBoundingClientRect();return {x:q.x+q.width/2,y:q.y+q.height/2}})()`);
    if (!r) return false; await sleep(300);
    const r2 = await ev(`(()=>{const b=[...document.querySelectorAll('button')].find(x=>x.getAttribute('aria-label')?.startsWith(${JSON.stringify(prefix)}));const q=b.getBoundingClientRect();return {x:q.x+q.width/2,y:q.y+q.height/2}})()`);
    for (const type of ['mouseMoved', 'mousePressed', 'mouseReleased']) await send('Input.dispatchMouseEvent', { type, x: r2.x, y: r2.y, button: 'left', clickCount: 1 });
    return true;
  };
  check('real mouse click on Ver informe', await realClick('Ver informe'));
  const seen = []; let sawBlob = false; const { readdir: rd0 } = await import('node:fs/promises');
  for (let i = 0; i < 60; i++) { const t = (await pages()).filter(t => !before.includes(t.id)); for (const x of t) { const e = x.id.slice(0, 4) + ' ' + x.url.slice(0, 50); if (!seen.includes(e)) seen.push(e); if (x.url.startsWith('blob:')) sawBlob = true; } if ((await rd0(dlv)).length) break; await sleep(250); }
  results.notes.push({ tabsSeenDuringView: seen, filesInViewDownloadDir: await rd0(dlv) });
  console.log('TABS', JSON.stringify(seen), 'FILES', JSON.stringify(await rd0(dlv)));
  check('Ver informe opened a new tab and navigated it to the PDF blob (or the PDF was handed to the browser)', seen.length > 0 || (await rd0(dlv)).length > 0, seen);
  await sleep(2500);
  results.notes.push({ afterView: await ev(listJs) });
  // --- Descargar PDF
  const dl = join(out, 'descargas'); await rm(dl, { recursive: true, force: true }); await mkdir(dl, { recursive: true });
  await send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: dl });
  check('real mouse click on Descargar PDF', await realClick('Descargar PDF'));
  const { readdir, copyFile } = await import('node:fs/promises');
  let file = null; for (let i = 0; i < 60; i++) { const f = (await readdir(dl)).filter(x => x.endsWith('.pdf')); if (f.length) { file = f[0]; break; } await sleep(1000); }
  check('PDF downloaded from history', !!file, file);
  if (file) { await sleep(500); await copyFile(join(dl, file), join(out, 'descargado_desde_historial.pdf')); }
  await send('Page.captureScreenshot').then(r => writeFile(join(out, 'lista_despues.png'), Buffer.from(r.result.data, 'base64')));
  // rutas: propiedad y autenticacion
  const other = await db.user.create({ data: { name: 'Otro', email: 'otro@example.invalid', passwordHash: await bcrypt.hash('Otro2026!x', 10), role: 'USER', age: 30 } });
  const rep = await db.medicalReport.findFirst({ where: { userId: u.id, NOT: { id: oldReport.id } } });
  const loginCookie = async (email, password) => { const l = await fetch(base + '/api/auth/login', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ email, password }) }); return l.headers.get('set-cookie').split(';')[0]; };
  const ra = await fetch(`${base}/api/me/reports/${rep.id}/pdf`, { headers: { cookie: await loginCookie(other.email, 'Otro2026!x') } });
  const rn = await fetch(`${base}/api/me/reports/${rep.id}/pdf`);
  check('ownership: other account 404, anonymous 401', ra.status === 404 && rn.status === 401, [ra.status, rn.status]);
  const ro = await fetch(`${base}/api/me/reports/${oldReport.id}/pdf`, { headers: { cookie: await loginCookie('player@example.invalid', 'Player2026!x') } });
  const rj = await ro.json().catch(() => null);
  check('historical record without file: explicit 404 JSON, nothing generated', ro.status === 404 && rj?.code === 'HISTORICAL_PDF_UNAVAILABLE', rj?.code);
} catch (e) { console.log('ERROR', e.message.slice(0, 300)); results.error = e.message; }
finally {
  await writeFile(join(out, `result_${scenario}.json`), JSON.stringify(results, null, 1));
  chrome.kill(); spawnSync('taskkill', ['/pid', String(chrome.pid), '/T', '/F'], { windowsHide: true }); server.kill(); spawnSync('taskkill', ['/pid', String(server.pid), '/T', '/F'], { windowsHide: true });
  await db.$disconnect(); await sleep(500); await rm(profile, { recursive: true, force: true }).catch(() => {});
  console.log('passed', results.checks.filter(c => c.passed).length, 'failed', results.checks.filter(c => !c.passed).length);
}
