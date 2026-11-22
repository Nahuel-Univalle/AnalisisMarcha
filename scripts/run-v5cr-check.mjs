// UTF-8 logs and native exit codes, independent of PowerShell redirection.
import { spawn } from 'node:child_process';
import { createWriteStream } from 'node:fs';
import { writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
const commands = {
  build: [process.execPath, ['node_modules/next/dist/bin/next','build'], 'BUILD.log'],
  lint: [process.execPath, ['node_modules/eslint/bin/eslint.js'], 'ESLINT.log'],
  typescript: [process.execPath, ['node_modules/typescript/bin/tsc','--noEmit'], 'TYPESCRIPT.log'],
  python: [resolve('.venv311/Scripts/python.exe'), ['scripts/video_training/deep/test_v5cr_deployment.py','--real-videos'], 'PRUEBAS_PYTHON.log'],
  presentation: [process.execPath, ['node_modules/tsx/dist/cli.mjs','scripts/test-v5cr-presentation.ts'], 'PRUEBAS_TYPESCRIPT.log'],
  e2e: [process.execPath, ['scripts/test-v5cr-e2e.mjs'], 'PRUEBAS_E2E.log'],
};
const name=process.argv[2];
if (!(name in commands)) throw new Error('Use build|lint|typescript|python|presentation|e2e');
const [command,args,log]=commands[name];
const dir='docs/integracion_v5cr_2026-11-19';
const out=createWriteStream(`${dir}/${log}`);
const started=new Date().toISOString();
const child=spawn(command,args,{windowsHide:true,env:{...process.env,PYTHONIOENCODING:'utf-8'}});
child.stdout.pipe(out,{end:false});child.stderr.pipe(out,{end:false});
child.on('error',error=>{out.write(String(error));});
child.on('close',async(code,signal)=>{
  out.end();
  await writeFile(`${dir}/EXIT_${name.toUpperCase()}.json`,JSON.stringify({command:[command,...args],started,finished:new Date().toISOString(),exitCode:code,signal},null,2));
  console.log(`${name}: exit=${code}; log=${dir}/${log}`);process.exitCode=code??1;
});
