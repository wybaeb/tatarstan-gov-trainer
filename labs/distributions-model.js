(function(root){'use strict';
const BINS=40,MAX=100,WIDTH=MAX/BINS;
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
function quantile(sorted,p){if(!sorted.length)return null;const h=(sorted.length-1)*p,i=Math.floor(h),f=h-i;return sorted[i]+f*((sorted[i+1]??sorted[i])-sorted[i]);}
function statistics(values){if(!values.length)return {n:0,mean:null,median:null,p90:null};const s=[...values].sort((a,b)=>a-b);return {n:s.length,mean:s.reduce((a,b)=>a+b,0)/s.length,median:quantile(s,.5),p90:quantile(s,.9)};}
function histogram(values){const c=Array(BINS).fill(0);for(const v of values)c[Math.min(BINS-1,Math.floor(clamp(v,0,MAX)/WIDTH))]++;return c;}
function random(seed){let a=seed>>>0;return ()=>{a=(1664525*a+1013904223)>>>0;return (a+.5)/4294967296;};}
function fromHistogram(counts){const values=[];counts.forEach((n,i)=>{for(let j=0;j<Math.max(0,Math.round(n));j++)values.push((i+.5)*WIDTH);});const r=random(51423);for(let i=values.length-1;i>0;i--){const j=Math.floor(r()*(i+1));[values[i],values[j]]=[values[j],values[i]];}return values;}
function preset(name){const r=random(name==='spikes'?101:name==='bimodal'?102:103);const normal=()=>Math.sqrt(-2*Math.log(r()))*Math.cos(2*Math.PI*r());let a=Array.from({length:160},()=>clamp(name==='bimodal'?(r()<.65?27+5*normal():73+7*normal()):name==='spikes'?25+2*normal():48+10*normal(),0,100));if(name==='spikes')for(const [i,v] of [[8,88],[41,98],[77,91],[113,95],[146,86]])a[i]=v;return a.map(v=>Math.round(v*10)/10);}
function stroke(values,start,end,lo=0,hi=MAX){const a=clamp(Math.round(start.i),0,values.length-1),b=clamp(Math.round(end.i),0,values.length-1);if(!values.length)return values;for(let i=Math.min(a,b);i<=Math.max(a,b);i++){const f=a===b?1:(i-a)/(b-a);values[i]=clamp(start.v+(end.v-start.v)*f,lo,hi);}return values;}
const api={BINS,MAX,WIDTH,quantile,statistics,histogram,fromHistogram,preset,stroke,clamp};if(typeof module!=='undefined'&&module.exports)module.exports=api;root.DistributionModel=api;
})(typeof window==='undefined'?globalThis:window);
