// Diagnostico: servidor Next aislado (BD tecnica 55432, esquema propio, Cloudinary vacio) + POST de los videos dados.
import { spawn, spawnSync } from 'node:child_process';
import { readFile, writeFile, open, mkdir } from 'node:fs/promises';
import { resolve, join, basename } from 'node:path';
import { randomBytes } from 'node:crypto';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');
const scratch = resolve('tmp/timing/run'); await mkdir(scratch, { recursive: true });
const schema = 'diag_' + Date.now();
const url = `postgresql://postgres:v5cr-local-test-only@127.0.0.1:55432/gait_v5cr_test?schema=${schema}`;
const env = { ...process.env, DATABASE_URL: url, AUTH_SESSION_SECRET: randomBytes(48).toString('hex'),
  CLOUDINARY_CLOUD_NAME: '', CLOUDINARY_API_KEY: '', CLOUDINARY_API_SECRET: '', CLOUDINARY_FOLDER: '',
  ANALYSIS_RECORD_STORAGE_DIR: join(scratch, 'records'), REPORT_PDF_STORAGE_DIR: join(scratch, 'pdfs') };
const port = process.env.DIAG_PORT ?? '3053'; const base = `http://127.0.0.1:${port}`;
const push = spawnSync(process.execPath, ['node_modules/prisma/build/index.js', 'db', 'push', '--skip-generate'], { env, encoding: 'utf8', windowsHide: true });
if (push.status !== 0) { console.log(push.stdout, push.stderr); process.exit(1); }
const p = new PrismaClient({ datasources: { db: { url } } });
const hash = await bcrypt.hash('Diag2026!x', 10);
const user = await p.user.create({ data: { name: 'Diag', email: 'diag@example.invalid', passwordHash: hash, role: 'USER', age: 30 } });
const log = await open(join(scratch, 'server.log'), 'w');
const server = spawn(process.execPath, ['node_modules/next/dist/bin/next', 'start', '--hostname', '127.0.0.1', '--port', port], { env, windowsHide: true, stdio: ['ignore', log.fd, log.fd] });
try {
  for (let i = 0; i < 120; i++) { try { const r = await fetch(base + '/api/auth/me'); if (r.status === 401 || r.ok) break; } catch {} await new Promise(r => setTimeout(r, 1000)); }
  let r = await fetch(base + '/api/auth/login', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ email: user.email, password: 'Diag2026!x' }) });
  const cookie = r.headers.get('set-cookie').split(';')[0];
  for (const f of process.argv.slice(2)) {
    const form = new FormData(); form.set('video', new Blob([await readFile(f)], { type: f.toLowerCase().endsWith('.mov') ? 'video/quicktime' : 'video/mp4' }), basename(f));
    const t = Date.now(); r = await fetch(base + '/api/analysis/video', { method: 'POST', headers: { cookie }, body: form });
    const j = await r.json();
    console.log(JSON.stringify({ video: basename(f), status: r.status, seconds: Math.round((Date.now() - t) / 1000), success: j.success, errorCode: j.errorCode, message: j.message?.slice(0, 90), modelVersion: j.analysis?.modelVersion, detectedClass: j.analysis?.detectedClass, reliable: j.analysis?.analysisReliable }));
  }
} finally { server.kill(); await p.$disconnect(); }
