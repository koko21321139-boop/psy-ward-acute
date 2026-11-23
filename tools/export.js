/* data.js の内容を JSON に書き出す（Excel版の生成用） */
const fs = require('fs'), path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'data.js'), 'utf8').replace('"use strict";', '').replace(/\bconst (\w+)\s*=/g, 'var $1 =');
const ctx = {}; new Function('ctx', src + ';ctx.out={MEDS,STATES,SYMS,NEEDS,NIGHT,TEST_KINDS,kinds:SYMS.map(s=>s.tests.map(testKind))};')(ctx);
fs.writeFileSync(path.join(__dirname, 'data.json'), JSON.stringify(ctx.out));
console.log('ok', ctx.out.SYMS.length);
