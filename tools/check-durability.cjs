const assert = require('node:assert/strict');
const { calculate } = require('../src/solverline/assets/durability.js');
const base = { totalUsd:100, accounts:[{account:'a',usd:30},{account:'b',usd:20}],
  economic:{gross_fees_annualized_usd:'1000',captured_revenue_annualized_usd:'100'} };
const close = (a,b) => assert.ok(Math.abs(a-b)<1e-10, `${a} != ${b}`);
let r=calculate({coverage:.5,leaving:1,volumeChange:0},base);
close(r.exposure[0],.3);close(r.exposure[1],.8);
close(r.volumeAtRisk[0],30);close(r.volumeAtRisk[1],80);
close(r.feesAtRisk[0],300);close(r.feesAtRisk[1],800);
close(r.remainingRevenue[0],20);close(r.remainingRevenue[1],70);
r=calculate({coverage:1,leaving:1,volumeChange:0},base);
close(r.exposure[0],r.exposure[1]);
r=calculate({coverage:0,leaving:1,volumeChange:0},base);
assert.deepEqual(r.exposure,[0,1]);
r=calculate({coverage:.5,leaving:0,volumeChange:2},base);
assert.deepEqual(r.exposure,[0,0]);assert.deepEqual(r.remainingRevenue,[300,300]);
r=calculate({coverage:.5,leaving:2,volumeChange:-1},base);
assert.deepEqual(r.volumeAtRisk,[0,0]);assert.deepEqual(r.remainingRevenue,[0,0]);
for (const input of [{coverage:NaN,leaving:1,volumeChange:0},{coverage:1.1,leaving:1,volumeChange:0},
  {coverage:.5,leaving:1.5,volumeChange:0},{coverage:.5,leaving:3,volumeChange:0},
  {coverage:.5,leaving:1,volumeChange:-1.1}]) assert.throws(()=>calculate(input,base));
for(let i=0;i<=10;i++)for(let k=0;k<=2;k++){
  r=calculate({coverage:i/10,leaving:k,volumeChange:.25},base);
  assert.ok(r.exposure[0]<=r.exposure[1] && r.exposure[0]>=0 && r.exposure[1]<=1);
  assert.ok(r.remainingRevenue[0]>=0 && r.remainingRevenue[1]<=125);
}
const fs=require('node:fs'), path=require('node:path');
const real=JSON.parse(fs.readFileSync(path.join(__dirname,'../docs/data/durability-inputs.json')));
const summary=JSON.parse(fs.readFileSync(path.join(__dirname,'../docs/data/summary.json')));
r=calculate({coverage:real.observedCoverage,leaving:3,volumeChange:0},real);
close(r.exposure[0],Number(summary.top3_lower));close(r.exposure[1],Number(summary.top3_upper));
console.log('PASS: durability exposure bounds, fee/revenue units, zero exits, complete unknowns, volume collapse and invalid inputs.');
