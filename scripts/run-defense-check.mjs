import { spawn } from 'node:child_process';
import { createWriteStream } from 'node:fs';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
const dir=resolve('docs/revision_defensa_2026-11-19');
await mkdir(dir,{recursive:true});
const commands={
  readonly:['node_modules/tsx/dist/cli.mjs','scripts/review-defense-readonly.ts'],
  pdf:['node_modules/tsx/dist/cli.mjs','scripts/test-defense-pdf.ts'],
  e2e:['scripts/test-v5cr-e2e.mjs'],
  typescript:['node_modules/typescript/bin/tsc','--noEmit'],
  lint:['node_modules/eslint/bin/eslint.js'],
  build:['node_modules/next/dist/bin/next','build'],
};
const name=process.argv[2];if(!(name in commands))throw Error('Use readonly|pdf|e2e|typescript|lint|build');
const log=createWriteStream(`${dir}/${name.toUpperCase()}.log`);
const child=spawn(process.execPath,commands[name],{windowsHide:true,env:{...process.env,V5CR_TEST_REPORT_DIR:resolve(dir,'e2e')}});
child.stdout.pipe(log,{end:false});child.stderr.pipe(log,{end:false});
child.on('close',async(code,signal)=>{log.end();await writeFile(`${dir}/EXIT_${name.toUpperCase()}.json`,JSON.stringify({exitCode:code,signal},null,2));console.log(`${name}: exit=${code}`);process.exitCode=code??1;});
