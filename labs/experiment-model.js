/* Educational fixed-horizon experiment, equal independent Gaussian arms.
   sigma is known in the simulator. Never use an observed crossing as a stop rule. */
(function(root){
'use strict';
const Z=1.959963984540054, POWER_Z={80:.8416212335729143,90:1.2815515655446004};
function plan(p){
 const n=Math.ceil(2*(Z+POWER_Z[p.power])**2*p.sigma**2/p.mde**2);
 const eventRate=p.eventRate??p.traffic,effectiveRate=Math.min(p.traffic,eventRate);
 const enrollment=Math.ceil(2*n/p.traffic),processing=Math.ceil(2*n/effectiveRate),finish=processing+p.lag+p.horizon;
 return {n,enrollment,finish,effectiveRate,processing,queue:processing-enrollment};
}
function normalSource(seed){let s=seed>>>0;const u=()=>{s=(1664525*s+1013904223)>>>0;return (s+.5)/4294967296;};return ()=>Math.sqrt(-2*Math.log(u()))*Math.cos(2*Math.PI*u());}
function simulate(p){
 const q=plan(p),ga=normalSource(p.seed),gb=normalSource(p.seed+7919),a=[0],b=[0];
 for(let i=1;i<=q.n;i++){a.push(a[i-1]+1000+p.sigma*ga());b.push(b[i-1]+1000+p.effect+p.sigma*gb());}
 function at(day){
  const enrolled=Math.min(q.n,Math.floor(Math.max(0,day)*p.traffic/2));
  const active=Math.min(q.n,Math.floor(Math.max(0,day-p.lag)*q.effectiveRate/2));
  const n=Math.min(q.n,Math.floor(Math.max(0,day-p.lag-p.horizon)*q.effectiveRate/2));
  if(!n)return {day,enrolled,active,n,ready:false};
  const ma=a[n]/n,mb=b[n]/n,h=Z*p.sigma/Math.sqrt(n),delta=mb-ma,dh=h*Math.SQRT2;
  return {day,enrolled,active,n,ready:day>=q.finish,a:ma,b:mb,h,delta,low:delta-dh,high:delta+dh};
 }
 const days=Array.from(new Set([...Array.from({length:Math.min(q.finish,500)+1},(_,i)=>Math.round(i*q.finish/Math.min(q.finish,500))),p.lag+p.horizon+1,q.enrollment,q.finish])).filter(d=>d<=q.finish).sort((a,b)=>a-b);
 return {plan:q,rows:days.map(at),at};
}
const api={plan,simulate,Z};if(typeof module!=='undefined')module.exports=api;root.ExperimentModel=api;
})(typeof window==='undefined'?globalThis:window);
