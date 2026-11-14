(function (root) {
  'use strict';
  function calculate(input, data) {
    const {coverage, leaving, volumeChange} = input;
    const accounts = data.accounts.map(r => ({account:r.account, usd:Number(r.usd)}))
      .sort((a,b) => b.usd-a.usd || a.account.localeCompare(b.account));
    const total = Number(data.totalUsd), known = accounts.reduce((s,r)=>s+r.usd,0);
    const fee = Number(data.economic.gross_fees_annualized_usd);
    const revenue = Number(data.economic.captured_revenue_annualized_usd);
    if (![coverage,leaving,volumeChange,total,fee,revenue,...accounts.map(r=>r.usd)].every(Number.isFinite)
        || coverage<0 || coverage>1 || !Number.isInteger(leaving) || leaving<0 || leaving>accounts.length
        || volumeChange < -1 || total<0 || fee<0 || revenue<0 || accounts.some(r=>r.usd<0)
        || (leaving>0 && known<=0)) throw new Error('Invalid durability inputs');
    const selected=accounts.slice(0,leaving), weight=known ? selected.reduce((s,r)=>s+r.usd,0)/known : 0;
    const lower = leaving ? Math.min(1,coverage*weight) : 0;
    const upper = leaving ? Math.min(1,lower+1-coverage) : 0;
    const factor=1+volumeChange, scaled=value=>[value*factor*lower,value*factor*upper];
    return {exposure:[lower,upper],volumeAtRisk:scaled(total),feesAtRisk:scaled(fee),
      revenueAtRisk:scaled(revenue),remainingRevenue:[revenue*factor*(1-upper),revenue*factor*(1-lower)],
      selectedAccounts:selected.map(r=>r.account)};
  }
  if (typeof module!=='undefined' && module.exports) {module.exports={calculate};return;}
  root.LithiumDurability={calculate};
  const payload=document.getElementById('durability-input');
  if (!payload) return;
  const data=JSON.parse(payload.textContent);
  const coverage=document.getElementById('durability-coverage');
  const leaving=document.getElementById('durability-leaving');
  const volume=document.getElementById('durability-volume');
  const pct=v=>(v*100).toFixed(2)+'%';
  const money=v=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(v);
  const range=(values,format)=>format(values[0])+' – '+format(values[1]);
  function update() {
    const result=calculate({coverage:Number(coverage.value)/100,leaving:Number(leaving.value),volumeChange:Number(volume.value)/100},data);
    document.getElementById('coverage-assumption').textContent=pct(Number(coverage.value)/100);
    document.getElementById('leaving-assumption').textContent=leaving.value;
    document.getElementById('volume-assumption').textContent=(Number(volume.value)>0?'+':'')+volume.value+'%';
    document.getElementById('risk-share').textContent=range(result.exposure,pct);
    const band=document.getElementById('risk-interval');
    band.style.left=(result.exposure[0]*100)+'%';band.style.width=((result.exposure[1]-result.exposure[0])*100)+'%';
    band.parentElement.setAttribute('aria-label','Conditional exposure: '+range(result.exposure,pct)+', on a zero to one hundred percent scale.');
    document.getElementById('risk-volume').textContent=range(result.volumeAtRisk,money);
    document.getElementById('risk-fees').textContent=range(result.feesAtRisk,money);
    document.getElementById('risk-revenue').textContent=range(result.revenueAtRisk,money);
    document.getElementById('durable-revenue').textContent=range(result.remainingRevenue,money);
    document.getElementById('departing-accounts').textContent=result.selectedAccounts.join(', ') || 'None';
    document.getElementById('durability-status').textContent='Scenarios, not predictions. Observed measurements are unchanged.';
  }
  for (const control of [coverage,leaving,volume]) control.addEventListener('input',update);
  coverage.addEventListener('keydown',event=>{
    const direction=({ArrowRight:1,ArrowUp:1,ArrowLeft:-1,ArrowDown:-1})[event.key];
    if (!direction) return;
    event.preventDefault();
    coverage.value=String(Math.max(0,Math.min(100,Number(coverage.value)+direction*(event.shiftKey ? 0.01 : 1))));update();
  });
  document.getElementById('durability-reset').addEventListener('click',()=>{
    coverage.value=String(data.observedCoverage*100);leaving.value='1';volume.value='0';update();
  });
  update();
})(globalThis);
