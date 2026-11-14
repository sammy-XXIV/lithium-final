/* Hypothetical, disjoint operator shares of the full sampled USD denominator. */
(() => {
  'use strict';
  function calculate(source) {
    const parts = source.trim() ? source.split(',').map(value => value.trim()) : [];
    if (parts.length > 200) throw new Error('Use at most 200 operator shares.');
    const units = parts.map(value => {
      if (value.length > 12 || !/^\d+(\.\d{1,6})?$/.test(value))
        throw new Error('Enter comma-separated percentages with up to six decimal places, such as 20, 15, 10.');
      const [whole, fraction = ''] = value.split('.');
      const amount = Number(whole) * 1000000 + Number(fraction.padEnd(6, '0'));
      if (!Number.isSafeInteger(amount) || amount > 100000000)
        throw new Error('Each share must be between 0 and 100.');
      return amount;
    });
    const total = units.reduce((sum, value) => sum + value, 0);
    if (total > 100000000) throw new Error('Operator shares must add up to 100% or less.');
    const shares = units.filter(value => value > 0).map(value => value / 100000000).sort((a, b) => b - a);
    const unknown = (100000000 - total) / 100000000;
    const top = n => {
      const lower = shares.slice(0, n).reduce((sum, value) => sum + value, 0);
      return [Math.min(1, lower), Math.min(1, lower + unknown)];
    };
    const squares = shares.reduce((sum, value) => sum + value * value, 0);
    const upper = ((shares[0] || 0) + unknown) ** 2 + shares.slice(1).reduce((sum, value) => sum + value * value, 0);
    return {coverage: total / 100000000, unknown, operators: shares.length,
      top1: top(1), top3: top(3), hhi: [Math.min(1, squares), Math.min(1, upper)]};
  }
  globalThis.LithiumDisclosure = Object.freeze({calculate});
  if (typeof document === 'undefined') return;
  const input = document.getElementById('disclosure-shares');
  if (!input) return;
  const error = document.getElementById('disclosure-error');
  const results = document.getElementById('disclosure-results');
  const output = document.getElementById('disclosure-status');
  const percent = value => (value * 100).toFixed(1) + '%';
  function render() {
    try {
      const value = calculate(input.value);
      error.hidden = true; results.hidden = false; input.removeAttribute('aria-invalid');
      output.textContent = `Hypothetical: ${percent(value.coverage)} disclosed across ${value.operators} assumed independent operators; ${percent(value.unknown)} remains unknown.`;
      for (const key of ['top1', 'top3', 'hhi']) {
        const [lower, upper] = value[key];
        const format = key === 'hhi' ? number => number.toFixed(4) : percent;
        document.getElementById(`scenario-${key}-lower`).textContent = format(lower);
        document.getElementById(`scenario-${key}-upper`).textContent = format(upper);
        const band = document.getElementById(`scenario-${key}-band`);
        band.style.left = `${lower * 100}%`; band.style.width = `${(upper - lower) * 100}%`;
        band.classList.toggle('resolved', Math.abs(upper - lower) < 1e-12);
      }
    } catch (failure) {
      results.hidden = true; error.hidden = false; error.textContent = failure.message;
      input.setAttribute('aria-invalid', 'true'); output.textContent = 'Scenario unavailable. Correct the percentages to continue.';
    }
  }
  input.addEventListener('input', render);
  for (const button of document.querySelectorAll('[data-disclosure-preset]')) {
    button.addEventListener('click', () => {
      input.value = button.dataset.disclosurePreset; render();
    });
  }
  render();
})();
