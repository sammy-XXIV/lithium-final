// Mathematical boundary cases for the hypothetical disclosure calculator.
const assert = require('node:assert/strict');
require('../src/solverline/assets/disclosure.js');
const calculate = globalThis.LithiumDisclosure.calculate;
const near = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-12, `${actual} != ${expected}`);
let result = calculate('');
assert.deepEqual(result.top3, [0, 1]);
assert.deepEqual(result.hhi, [0, 1]);
result = calculate('20, 15, 10');
near(result.coverage, .45);
near(result.top1[0], .2); near(result.top1[1], .75);
near(result.top3[0], .45); near(result.top3[1], 1);
near(result.hhi[0], .0725); near(result.hhi[1], .595);
result = calculate('50, 30, 20');
near(result.top3[0], 1); near(result.top3[1], 1);
near(result.hhi[0], .38); near(result.hhi[1], .38);
result = calculate('0.1, 0.2, 99.7');
near(result.coverage, 1); near(result.top1[1], .997);
for (const input of ['60, 50', '-1', 'NaN', '10,,20', '1e2', '101', '10%']) {
  assert.throws(() => calculate(input), Error, input);
}
console.log('PASS: disclosure bounds, unknown and complete disclosure, decimal totals, invalid input rejection.');
