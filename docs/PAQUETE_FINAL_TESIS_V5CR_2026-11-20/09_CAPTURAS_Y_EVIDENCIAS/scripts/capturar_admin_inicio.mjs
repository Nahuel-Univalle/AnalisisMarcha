// Capturas REALES de la aplicación (build de producción, `next start`) en un entorno AISLADO: base técnica del puerto 55432 con esquema propio,
// cuentas técnicas @example.invalid, Cloudinary vacío. No toca la base habitual ni datos de usuarios.
// Privacidad: los elementos <video> se ocultan (visibility:hidden) para no publicar fotogramas de personas; el resto de la pantalla es real.
// Uso: node capturar_pantallas.mjs <video.mp4> <carpeta_salida>
import { spawn, spawnSync } from 'node:child_process';
import { writeFile, open, mkdir, rm } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { randomBytes } from 'node:crypto';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');
const video = resolve(process.argv[2]);
const out = resolve(process.argv[3]); await mkdir(out, { recursive: true });
const scratch = resolve('tmp/capturas'); await mkdir(scratch, { recursive: true });
const schema = 'capt_' + Date.now();
const dbPassword = process.env.V5CR_TEST_DB_PASSWORD; // contraseña del contenedor PostgreSQL técnico local (no se incluye en el paquete)
if (!dbPassword) throw new Error('Defina V5CR_TEST_DB_PASSWORD con la contraseña del contenedor técnico (puerto 55432)');
const url = `postgresql://postgres:${encodeURIComponent(dbPassword)}@127.0.0.1:55432/gait_v5cr_test?schema=${schema}`;
const port = '3057'; const base = `http://127.0.0.1:${port}`;
const env = { ...process.env, DATABASE_URL: url, AUTH_SESSION_SECRET: randomBytes(48).toString('hex'), CLOUDINARY_CLOUD_NAME: '', CLOUDINARY_API_KEY: '', CLOUDINARY_API_SECRET: '', CLOUDINARY_FOLDER: '',
  ANALYSIS_RECORD_STORAGE_DIR: join(scratch, 'records'), REPORT_PDF_STORAGE_DIR: join(scratch, 'pdfs') };
const push = spawnSync(process.execPath, ['node_modules/prisma/build/index.js', 'db', 'push', '--skip-generate'], { env, encoding: 'utf8', windowsHide: true });
if (push.status !== 0) { console.log(push.stdout, push.stderr); process.exit(1); }
const db = new PrismaClient({ datasources: { db: { url } } });
const pw = 'Captura2026!x'; const hash = await bcrypt.hash(pw, 10);
await db.user.create({ data: { name: 'Usuario de prueba', email: 'usuario@example.invalid', passwordHash: hash, role: 'USER', age: 40 } });
await db.user.create({ data: { name: 'Administrador de prueba', email: 'admin@example.invalid', passwordHash: hash, role: 'ADMIN' } });
const slog = await open(join(scratch, 'server.log'), 'w');
const server = spawn(process.execPath, ['node_modules/next/dist/bin/next', 'start', '--hostname', '127.0.0.1', '--port', port], { env, windowsHide: true, stdio: ['ignore', slog.fd, slog.fd] });
const cport = 9500 + Math.floor(Math.random() * 40); const profile = resolve('tmp/capturas/profile_' + Date.now());
const chrome = spawn('C:/Program Files/Google/Chrome/Application/chrome.exe', ['--headless=new', `--remote-debugging-port=${cport}`, `--user-data-dir=${profile}`, '--autoplay-policy=no-user-gesture-required', '--no-first-run', 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const log = []; const note = (f, what) => { log.push({ archivo: f, contenido: what }); console.log('captura', f); };
try {
  for (let i = 0; i < 120; i++) { try { const r = await fetch(base + '/api/auth/me'); if (r.status === 401 || r.ok) break; } catch {} await sleep(1000); }
  let target; for (let i = 0; i < 60; i++) { try { target = (await (await fetch(`http://127.0.0.1:${cport}/json`)).json()).find(x => x.type === 'page'); if (target) break; } catch {} await sleep(500); }
  const ws = new WebSocket(target.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r));
  let id = 0; const pend = new Map();
  ws.addEventListener('message', m => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); } });
  const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async (expression) => { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }); if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails).slice(0, 200)); return r.result.result.value; };
  await send('Page.enable'); await send('Runtime.enable'); await send('DOM.enable'); await send('Network.enable');
  await send('Page.addScriptToEvaluateOnNewDocument', { source: `new MutationObserver(()=>{if(!document.getElementById('__hidevid')&&document.head){const s=document.createElement('style');s.id='__hidevid';s.textContent='video{visibility:hidden!important}';document.head.appendChild(s)}}).observe(document,{childList:true,subtree:true})` });
  const size = async (w, h, mobile = false) => send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: mobile ? 2 : 1, mobile });
  const shot = async (name, what, full = true) => {
    await sleep(900);
    const h = full ? await ev(`Math.max(document.documentElement.scrollHeight, innerHeight)`) : null; const w = await ev(`innerWidth`);
    const r = await send('Page.captureScreenshot', full ? { captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: Math.min(h, 4000), scale: 1 } } : {});
    await writeFile(join(out, name), Buffer.from(r.result.data, 'base64')); note(name, what);
  };
  const clickText = t => ev(`(()=>{const b=[...document.querySelectorAll('button,a')].find(x=>x.textContent.includes(${JSON.stringify(t)})&&!x.disabled);if(!b)return false;b.click();return true})()`);
  const nav = async p => { await send('Page.navigate', { url: base + p }); await sleep(3500); };
  const cookie = async (email) => { const l = await fetch(base + '/api/auth/login', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ email, password: pw }) }); const [n, ...v] = l.headers.get('set-cookie').split(';')[0].split('='); await send('Network.setCookie', { name: n, value: v.join('='), url: base }); };

  await size(1366, 800, false);
  await cookie('admin@example.invalid');
  await nav('/dashboard'); await shot('20_administracion_inicio_estado_del_modelo.png', 'Inicio del administrador: estado del sistema y del modelo');
  await writeFile(join(out, 'INDICE_CAPTURAS_ADMIN_EXTRA.json'), JSON.stringify(log, null, 1));
} catch (e) { console.log('ERROR', e.message.slice(0, 300)); await writeFile(join(out, 'ERROR_CAPTURAS.txt'), e.message); }
finally {
  chrome.kill(); spawnSync('taskkill', ['/pid', String(chrome.pid), '/T', '/F'], { windowsHide: true }); server.kill(); spawnSync('taskkill', ['/pid', String(server.pid), '/T', '/F'], { windowsHide: true });
  await db.$disconnect(); await sleep(500); await rm(profile, { recursive: true, force: true }).catch(() => {});
  console.log('fin');
}
