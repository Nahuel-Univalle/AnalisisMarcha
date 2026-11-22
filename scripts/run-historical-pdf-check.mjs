import {spawn} from 'node:child_process';
import {createWriteStream} from 'node:fs';
import {writeFile} from 'node:fs/promises';
const dir='docs/recuperacion_pdf_historicos_2026-11-19';
const jobs={habitual:['node_modules/tsx/dist/cli.mjs','scripts/check-all-historical-pdf-endpoints.ts'],download:['node_modules/tsx/dist/cli.mjs','scripts/test-historical-pdf-download.ts'],typescript:['node_modules/typescript/bin/tsc','--noEmit'],lint:['node_modules/eslint/bin/eslint.js'],build:['node_modules/next/dist/bin/next','build']};
const name=process.argv[2];if(!(name in jobs))throw Error('Use habitual|download|typescript|lint|build');
const out=createWriteStream(`${dir}/${name.toUpperCase()}.log`);const child=spawn(process.execPath,jobs[name],{windowsHide:true});child.stdout.pipe(out,{end:false});child.stderr.pipe(out,{end:false});
child.on('close',async(code,signal)=>{out.end();await writeFile(`${dir}/EXIT_${name.toUpperCase()}.json`,JSON.stringify({exitCode:code,signal},null,2));console.log(`${name}: exit=${code}`);process.exitCode=code??1;});
