/* Independent browser arithmetic from the shipped swap CSV; no remote library. */
(() => {
  'use strict';
  const status = document.getElementById('browser-check');
  const payload = JSON.parse(document.getElementById('verification-input').textContent);
  function parseCSV(source) {
    const rows = []; let row = [], field = '', quoted = false;
    for (let i = 0; i < source.length; i++) {
      const c = source[i];
      if (c === '"') {
        if (quoted && source[i + 1] === '"') { field += '"'; i++; }
        else quoted = !quoted;
      } else if (!quoted && (c === ',' || c === '\n')) {
        row.push(field); field = '';
        if (c === '\n') { rows.push(row); row = []; }
      } else if (c !== '\r' || quoted) field += c;
    }
    if (quoted) throw new Error('Unclosed CSV field');
    if (field || row.length) { row.push(field); rows.push(row); }
    const header = rows.shift();
    return rows.map(values => {
      if (values.length !== header.length) throw new Error('CSV columns differ');
      return Object.fromEntries(header.map((key, i) => [key, values[i]]));
    });
  }
  async function verify() {
    let source = payload.csv;
    if (location.protocol === 'http:' || location.protocol === 'https:') {
      const response = await fetch('data/swaps.csv', {cache: 'no-store'});
      if (!response.ok) throw new Error('Cannot load the shipped CSV');
      source = await response.text();
    }
    const rows = parseCSV(source), accounts = new Map();
    let total = 0, known = 0, invalid = 0, complete = 0, completeCount = 0;
    const classes = {public: 0, confidential_treasury: 0, unresolved: 0};
    for (const row of rows) {
      const value = row.input_usd === '' ? NaN : Number(row.input_usd);
      if (!Number.isFinite(value) || value < 0) { invalid++; continue; }
      if (!(row.settlement_class in classes)) throw new Error('Unknown classification');
      total += value; classes[row.settlement_class] += value;
      if (row.rpc_complete === 'true') { complete += value; completeCount++; }
      if (row.attribution_status === 'attributed' && row.filler_account && row.settlement_class === 'public') {
        known += value;
        accounts.set(row.filler_account, (accounts.get(row.filler_account) || 0) + value);
      }
    }
    const div = (a, b) => b === 0 ? null : a / b;
    const computed = {count: rows.length, valid_usd_count: rows.length - invalid, invalid_usd_count: invalid,
      total_usd: total, attributable_usd: known, unknown_usd: total - known,
      attributable_share: div(known, total), rpc_complete_usd_share: div(complete, total),
      rpc_complete_count: completeCount, attributed_account_count: accounts.size};
    for (const [name, value] of Object.entries(classes)) {
      computed[name + '_usd'] = value; computed[name + '_share'] = div(value, total);
    }
    const volumes = [...accounts.values()].sort((a,b) => b-a), largest = volumes[0] || 0;
    const squares = volumes.reduce((sum, value) => sum + value * value, 0), unknown = total - known;
    for (const n of [1,3,10]) {
      const top = volumes.slice(0,n).reduce((sum,v) => sum+v,0);
      computed['subset_top' + n] = div(top, known);
      computed['top' + n + '_lower'] = div(top, total);
      computed['top' + n + '_upper'] = div(Math.min(total,top+unknown),total);
    }
    computed.subset_hhi = div(squares, known * known);
    computed.hhi_lower = div(squares, total * total);
    computed.hhi_upper = div((largest+unknown)**2 + squares - largest**2,total*total);
    for (const [key, actual] of Object.entries(computed)) {
      const expected = payload.summary[key];
      if (expected === null ? actual !== null : actual === null || !Number.isFinite(actual) ||
          Math.abs(Number(expected)-actual) > 1e-10*Math.max(1,Math.abs(Number(expected)))) {
        throw new Error('Mismatch: ' + key);
      }
    }
    status.dataset.status = 'pass';
    status.textContent = 'PASS · ' + Object.keys(computed).length + ' figures recomputed from ' + rows.length +
      ' CSV rows. Floating-point tolerance: 1e-10 relative (1e-10 absolute near zero).';
  }
  verify().catch(error => { status.dataset.status = 'fail'; status.textContent = 'FAIL · ' + error.message; });
  const search = document.getElementById('evidence-search');
  search.addEventListener('input', () => {
    const query = search.value.toLowerCase();
    for (const row of document.querySelectorAll('#evidence-table tbody tr'))
      row.hidden = !row.textContent.toLowerCase().includes(query);
  });
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches && 'IntersectionObserver' in window) {
    const chart = document.querySelector('.coverage-chart');
    if (chart) {
      chart.classList.add('motion-ready');
      const reveal = new IntersectionObserver(entries => {
        if (entries.some(entry => entry.isIntersecting)) {
          chart.classList.add('is-visible');
          reveal.disconnect();
        }
      }, {threshold: 0.15});
      reveal.observe(chart);
    }
  }
})();
