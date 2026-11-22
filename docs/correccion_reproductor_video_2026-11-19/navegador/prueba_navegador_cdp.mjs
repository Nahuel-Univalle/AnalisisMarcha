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
const out = resolve('tmp/player/out'); await mkdir(out, { recursive: true });
const schema = 'player_' + Date.now();
const url = `postgresql://postgres:v5cr-local-test-only@127.0.0.1:55432/gait_v5cr_test?schema=${schema}`;
const port = process.env.PLAYER_PORT ?? '3054'; const base = `http://127.0.0.1:${port}`;
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
const cport = 9333 + Math.floor(Math.random() * 50);
const profile = resolve('tmp/player/profile_' + Date.now());
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
  const t0 = Date.now();
  // instrumentacion del elemento <video> de la pagina de procesamiento
  await ev(`(()=>{const v=document.querySelector('video');window.__v=v;window.__ev=[];window.__origEl=v;for(const n of ['loadedmetadata','canplay','play','pause','ended','error','seeking','seeked','emptied','abort','stalled']){v.addEventListener(n,()=>window.__ev.push({n,t:Math.round(performance.now()),err:v.error&&v.error.code,msg:v.error&&v.error.message,rs:v.readyState,ct:+v.currentTime.toFixed(2)}))}return !!v})()`);
  const state = () => ev(`(()=>{const v=document.querySelector('video');return {sameEl:v===window.__origEl,hasVideo:!!v,src:v&&v.currentSrc.slice(0,40),err:v&&v.error?{code:v.error.code,msg:v.error.message}:null,rs:v&&v.readyState,paused:v&&v.paused,ended:v&&v.ended,ct:v&&+v.currentTime.toFixed(2),dur:v&&+v.duration.toFixed(2),msgShown:document.body.innerText.includes('no pudo reproducirse'),noticeShown:!!document.querySelector('[role=status]'),notice:(document.querySelector('[role=status]')||{}).innerText||null,processing:document.body.innerText.includes('Analizando tu video')}})()`);
  let s = await state(); check('player present at processing start', s.hasVideo && !s.err, s);
  const analysisRunning = async () => (await state()).processing;
  check('analysis running while we test', await analysisRunning());
  const play = () => ev(`document.querySelector('video').play().then(()=>'ok').catch(e=>'ERR '+e.name+': '+e.message)`);
  await ev(`document.querySelector('video').playbackRate=4`);
  check('first play()', (await play()) === 'ok');
  for (let i = 0; i < 40; i++) { s = await state(); if (s.ended || s.noticeShown) break; await sleep(500); }
  check('first playback finished (ended, or recoverable end-of-file notice)', s.ended || s.noticeShown, s);
  if (s.noticeShown) await send('Page.captureScreenshot').then(async r => writeFile(join(out, `shot_notice_${scenario}.png`), Buffer.from(r.result.data, 'base64')));
  const stillRunning = await analysisRunning(); check('analysis still running at end of first playback', stillRunning, { sinceStartS: Math.round((Date.now() - t0) / 1000) });
  // 2) volver a reproducir tras terminar
  const again = await play(); await sleep(1500); s = await state();
  check('second play() after ended succeeds', again === 'ok', again);
  check('after replay: no <video> error and no "no pudo reproducirse" message', !s.err && !s.msgShown, s);
  check('after replay: same <video> element (not remounted)', s.sameEl, s);
  check('after replay: it is playing/advancing', s.ct !== null && (s.ct > 0 || !s.paused), s);
  if (scenario.startsWith('full') || scenario.startsWith('replay')) {
    // 3) pausar/reanudar varias veces y 4) buscar adelante/atras
    let ok = true; for (let i = 0; i < 4; i++) { await ev(`document.querySelector('video').pause()`); await sleep(200); ok = ok && (await play()) === 'ok'; await sleep(200); }
    check('pause/resume x4', ok && !(await state()).err);
    let seekOk = true; for (const f of [0.8, 0.2, 0.6, 0.0]) { await ev(`(()=>{const v=document.querySelector('video');v.currentTime=v.duration*${f}})()`); await sleep(500); const st = await state(); seekOk = seekOk && !st.err && !st.msgShown; }
    check('seek forward/back', seekOk);
  }
  if (scenario.startsWith('full')) {
    // fallo real de carga: la fuente deja de ser valida -> panel de error con "Reintentar"; reintentar remonta con la URL valida
    await ev(`document.querySelector('video').setAttribute('src','blob:'+location.origin+'/00000000-0000-0000-0000-000000000000')`); await sleep(2500);
    let st = await state(); const panel = await ev(`document.body.innerText.includes('no pudo reproducirse')&&[...document.querySelectorAll('button')].some(b=>b.textContent.includes('Reintentar'))`);
    check('unrecoverable load failure shows error + Reintentar button (not hidden)', panel, st);
    check('analysis still running during the player failure', await analysisRunning());
    const retried = await clickText('Reintentar'); await sleep(1500); st = await state();
    check('Reintentar restores the player with the original URL', retried && st.hasVideo && !st.msgShown && !st.err && st.src?.startsWith('blob:') && !st.src.includes('0000000'), st);
    await ev(`document.querySelector('video').playbackRate=4`); check('play after Reintentar', (await play()) === 'ok');
  }
  // 5) esperar fin del analisis y comprobar reproductor
  let done = false; for (let i = 0; i < 240; i++) { const t = await ev(`document.body.innerText`); if (t.includes('Análisis completado') || t.includes('No se pudo completar')) { done = true; break; } await sleep(1000); }
  check('analysis finished', done); await sleep(1500); s = await state();
  check('after analysis: player present, no error', s.hasVideo && !s.err && !s.msgShown, s);
  await ev(`document.querySelector('video').pause()`);
  const replay2 = await play(); await sleep(1000); s = await state(); check('after analysis: play works', replay2 === 'ok' && !s.err, s);
  const processedTab = await ev(`[...document.querySelectorAll('[role=tab]')].map(b=>b.textContent.trim())`); results.notes.push({ tabsAfterAnalysis: processedTab });
  // 6) resultado y PDF
  check('go to result', await clickText('Ver resultado')); await sleep(3000);
  results.notes.push({ resultText: (await ev(`document.body.innerText`)).slice(0, 400) });
  results.events = await ev(`window.__ev||[]`).catch(() => []); results.console = consoleLines.slice(-20); results.netErrors = netErrors.slice(-10);
  await send('Page.captureScreenshot').then(async r => writeFile(join(out, `shot_${scenario}.png`), Buffer.from(r.result.data, 'base64')));
} catch (e) { console.log('ERROR', e.message.slice(0,200)); results.error = e.message; results.dump = await globalThis.__dump?.().catch(()=>null); }
finally {
  await writeFile(join(out, `result_${scenario}.json`), JSON.stringify(results, null, 1));
  chrome.kill(); spawnSync('taskkill', ['/pid', String(chrome.pid), '/T', '/F'], { windowsHide: true }); server.kill(); spawnSync('taskkill', ['/pid', String(server.pid), '/T', '/F'], { windowsHide: true });
  await db.$disconnect(); await sleep(500); await rm(profile, { recursive: true, force: true }).catch(() => {});
  console.log('passed', results.checks.filter(c => c.passed).length, 'failed', results.checks.filter(c => !c.passed).length);
}
