/* Lloyd k-means in standardized coordinates, seeded k-means++ restarts. */
(function(root){
'use strict';
const distance=(a,b)=>(a[0]-b[0])**2+(a[1]-b[1])**2;
function random(seed){return()=>{seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t^=t+Math.imul(t^t>>>7,61|t);return((t^t>>>14)>>>0)/4294967296}}
function prepare(points){const mean=[0,1].map(j=>points.reduce((s,p)=>s+p[j],0)/points.length),sd=[0,1].map(j=>Math.sqrt(points.reduce((s,p)=>s+(p[j]-mean[j])**2,0)/points.length));return{mean,sd,Z:points.map(p=>p.map((v,j)=>(v-mean[j])/sd[j]))}}
function run(Z,initial){let centers=initial.map(p=>p.slice()),labels,iterations=0;
 for(;iterations<300;iterations++){
  labels=Z.map(p=>centers.reduce((best,c,j)=>distance(p,c)<distance(p,centers[best])?j:best,0));
  const sums=centers.map(()=>[0,0,0]);Z.forEach((p,i)=>{sums[labels[i]][0]+=p[0];sums[labels[i]][1]+=p[1];sums[labels[i]][2]++});
  const next=sums.map((s,j)=>s[2]?[s[0]/s[2],s[1]/s[2]]:Z.reduce((p,q)=>Math.min(...centers.map(c=>distance(q,c)))>Math.min(...centers.map(c=>distance(p,c)))?q:p,Z[0]).slice());
  const shift=Math.max(...centers.map((c,j)=>distance(c,next[j])));centers=next;if(shift<1e-18){iterations++;break;}
 }
 labels=Z.map(p=>centers.reduce((best,c,j)=>distance(p,c)<distance(p,centers[best])?j:best,0));
 return{centers,labels,inertia:Z.reduce((s,p,i)=>s+distance(p,centers[labels[i]]),0),iterations};
}
function silhouette(Z,labels,k,dist){if(k===1)return null;const counts=Array(k).fill(0);labels.forEach(j=>counts[j]++);return Z.reduce((total,p,i)=>{if(counts[labels[i]]===1)return total;const sums=Array(k).fill(0);Z.forEach((q,j)=>{sums[labels[j]]+=dist[i][j]});const a=sums[labels[i]]/(counts[labels[i]]-1),b=Math.min(...sums.map((s,j)=>j===labels[i]||!counts[j]?Infinity:s/counts[j]));return total+(b-a)/Math.max(a,b)},0)/Z.length;}
function calculate(points,maxK=8){const prep=prepare(points),Z=prep.Z,dist=Z.map(p=>Z.map(q=>Math.sqrt(distance(p,q)))),results=[];
 for(let k=1;k<=maxK;k++){let best=null;
  for(let trial=0;trial<21;trial++){const rand=random(4319+k*100+trial);let initial;
   if(trial===20&&k>1){initial=results[k-2].centers.map(p=>p.slice());initial.push(Z.reduce((p,q)=>Math.min(...initial.map(c=>distance(q,c)))>Math.min(...initial.map(c=>distance(p,c)))?q:p,Z[0]).slice())}
   else{initial=[Z[Math.floor(rand()*Z.length)].slice()];while(initial.length<k){const weights=Z.map(p=>Math.min(...initial.map(c=>distance(p,c))));let t=rand()*weights.reduce((a,b)=>a+b,0),idx=0;while(idx<weights.length-1&&(t-=weights[idx])>0)idx++;initial.push(Z[idx].slice())}}
   const r=run(Z,initial);if(!best||r.inertia<best.inertia)best=r;
  }
  const order=best.centers.map((p,j)=>j).sort((a,b)=>best.centers[a][0]-best.centers[b][0]);best.labels=best.labels.map(j=>order.indexOf(j));best.centers=order.map(j=>best.centers[j]);best.k=k;best.silhouette=silhouette(Z,best.labels,k,dist);best.originalCenters=best.centers.map(p=>p.map((v,j)=>v*prep.sd[j]+prep.mean[j]));best.counts=Array(k).fill(0);best.labels.forEach(j=>best.counts[j]++);results.push(best);
 }
 return{...prep,results};
}
const api={calculate,prepare,distance};if(typeof module!=='undefined')module.exports=api;root.Clusters=api;
})(globalThis);
