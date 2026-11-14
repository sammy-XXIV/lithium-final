// Optional browser verification: PLAYWRIGHT_MODULE may point to an existing install.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const root = path.resolve(__dirname, '../docs');
const screenshots = path.resolve(__dirname, '../data/logs');

(async () => {
  fs.mkdirSync(screenshots, {recursive:true});
  const server = http.createServer((req, res) => {
    if (req.url === '/favicon.ico') { res.writeHead(204).end(); return; }
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const file = path.resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
    if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
      res.writeHead(404).end(); return;
    }
    const types = {'.html':'text/html', '.css':'text/css', '.js':'application/javascript', '.csv':'text/csv', '.json':'application/json'};
    res.writeHead(200, {'Content-Type':types[path.extname(file)] || 'text/plain'});
    fs.createReadStream(file).pipe(res);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({channel:'chrome',headless:true});
  const errors = [];
  try {
    const page = await browser.newPage({viewport:{width:1365,height:900}});
    page.on('pageerror', error => errors.push(error.message));
    const url = 'http://127.0.0.1:' + server.address().port;
    for (const mode of ['desktop','mobile','small-mobile']) {
      await page.setViewportSize(mode === 'desktop' ? {width:1365,height:900} : {width:mode==='mobile'?390:320,height:844});
      await page.goto(url);
      await page.waitForSelector('#browser-check[data-status="pass"]');
      assert.match(await page.locator('#durability-status').textContent(), /Scenarios, not predictions/);
      assert.equal(await page.locator('.observed-tile > details').count(),5);
      assert.equal(await page.locator('.scenario-tiles .metric-tile > details').count(),5);
      assert.match(await page.locator('#stress').textContent(), /Real stress event: not established/);
      await page.locator('#durability-leaving').evaluate(el=>{el.value='0';el.dispatchEvent(new Event('input',{bubbles:true}));});
      assert.equal(await page.locator('#risk-share').textContent(),'0.00% – 0.00%');
      assert.equal(await page.locator('#durable-revenue').textContent(),'$19,190,000 – $19,190,000');
      await page.locator('#durability-reset').click();
      assert.match(await page.locator('#risk-share').textContent(),/18.30% – 89.92%/);
      await page.locator('#durability-coverage').focus();
      await page.keyboard.press('ArrowRight');
      assert.equal(await page.locator('#coverage-assumption').textContent(),'29.37%');
      await page.locator('#durability-reset').click();
      await page.locator('#durability-volume').evaluate(el=>{el.value='-100';el.dispatchEvent(new Event('input',{bubbles:true}));});
      assert.equal(await page.locator('#risk-volume').textContent(),'$0 – $0');
      assert.equal(await page.locator('#durable-revenue').textContent(),'$0 – $0');
      await page.locator('#durability-reset').click();
      assert.equal(await page.locator('#bigquery tbody tr').count(), 24);
      assert.equal(await page.locator('#sensitivity > .table-wrap tbody tr').count(), 7);
      assert.match(await page.locator('#sensitivity').textContent(), /7 of 8 sampled dates/);
      await page.locator('#date-sensitivity summary').click();
      assert.equal(await page.locator('#date-sensitivity tbody tr').count(), 8);
      await page.locator('#date-sensitivity summary').click();
      assert.match(await page.locator('#bigquery').textContent(), /9,280/);
      assert.match(await page.locator('#bigquery').textContent(), /not swaps/);
      await page.locator('#disclosure-status').filter({hasText:'0.0% disclosed'}).waitFor();
      const observed = await page.locator('.decision-verdict').textContent();
      await page.locator('#disclosure-shares').fill('20, 15, 10');
      assert.equal(await page.locator('#scenario-top1-lower').textContent(), '20.0%');
      assert.equal(await page.locator('#scenario-top1-upper').textContent(), '75.0%');
      assert.equal(await page.locator('#scenario-hhi-upper').textContent(), '0.5950');
      await page.locator('#disclosure-shares').fill('60, 50');
      assert.equal(await page.locator('#disclosure-error').isVisible(), true);
      assert.equal(await page.locator('#disclosure-results').isVisible(), false);
      await page.getByRole('button', {name:'Example: 90% across 20 equal operators'}).click();
      assert.match(await page.locator('#disclosure-status').textContent(), /90.0% disclosed across 20/);
      assert.equal(await page.locator('.decision-verdict').textContent(), observed);
      await page.getByRole('button', {name:'Clear scenario'}).click();
      assert.equal(await page.locator('#scenario-top3-upper').textContent(), '100.0%');
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 1, mode + ' horizontal page overflow: ' + overflow);
      await page.screenshot({path:path.join(screenshots,'dashboard-'+mode+'.png')});
      if (mode === 'desktop') await page.locator('#coverage').screenshot({path:path.join(screenshots,'dashboard-coverage.png')});
      if (mode === 'desktop') await page.locator('#bigquery').screenshot({path:path.join(screenshots,'dashboard-bigquery.png')});
      if (mode === 'desktop') await page.locator('#decision').screenshot({path:path.join(screenshots,'dashboard-decision.png')});
      if (mode === 'desktop') await page.locator('#durability').screenshot({path:path.join(screenshots,'dashboard-durability.png')});
    }
    await page.locator('#evidence-search').fill('__no_swaps_match__');
    assert.equal(await page.locator('#evidence-table tbody tr:not([hidden])').count(),0);
    await page.locator('#evidence-search').fill('');
    const expected = JSON.parse(fs.readFileSync(path.join(root,'data/summary.json'))).count;
    assert.equal(await page.locator('#evidence-table tbody tr:not([hidden])').count(), expected);
    await page.goto(pathToFileURL(path.join(root,'index.html')).href);
    await page.waitForSelector('#browser-check[data-status="pass"]');
    await page.locator('#durability-leaving').focus();
    await page.keyboard.press('ArrowRight');
    assert.equal(await page.locator('#leaving-assumption').textContent(),'2');
    assert.match(await page.locator('#durability-status').textContent(),/Observed measurements are unchanged/);
    await page.locator('#disclosure-shares').fill('50, 30, 20');
    assert.equal(await page.locator('#scenario-hhi-lower').textContent(), '0.3800');
    assert.equal(await page.locator('#scenario-hhi-upper').textContent(), '0.3800');
    assert.deepEqual(errors, []);
    console.log('PASS: HTTP and file CSV checks, desktop/mobile layout, evidence search, zero browser exceptions.');
  } finally {
    await browser.close(); server.close();
  }
})().catch(error => { console.error(error); process.exitCode=1; });
