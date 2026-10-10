/* Ordinary least squares using re-orthogonalized QR; no test observations in fitting. */
(function(root){
'use strict';
function components(key){
 const base=key==='case'?3:2;
 return [{id:'trend',label:'Линейный тренд',cols:[1],group:'Основа'},...(key==='case'?[{id:'bend',label:'Изменение тренда с 2025 года',cols:[2],group:'Основа'}]:[]),
 ...Array.from({length:6},(_,i)=>({id:'year'+(i+1),label:`${i+1} ${i===0?'волна':i<4?'волны':'волн'} за год`,cols:[base+2*i,base+2*i+1],group:'Годовые гармоники'})),
 ...Array.from({length:3},(_,i)=>({id:'month'+(i+1),label:`${i+1} ${i===0?'волна':'волны'} за месяц`,cols:[base+12+2*i,base+13+2*i],group:'Месячные гармоники'})),
 {id:'week',label:'Дни недели',cols:Array.from({length:6},(_,i)=>base+18+i),group:'Недельный ритм'}];
}
function fit(D,cut,parts,selected){
 const cols=[0,...parts.filter(p=>selected.includes(p.id)).flatMap(p=>p.cols)];
 const Q=[],R=[],accepted=[],discarded=[];const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
 for(const col of cols){
  let v=D.features.slice(0,cut).map(row=>row[col]),length=Math.sqrt(dot(v,v)),rs=Array(Q.length).fill(0);
  for(let pass=0;pass<2;pass++)for(let j=0;j<Q.length;j++){let a=dot(Q[j],v);rs[j]+=a;v=v.map((x,i)=>x-a*Q[j][i]);}
  const norm=Math.sqrt(dot(v,v));
  if(norm<1e-10*Math.max(1,length)){discarded.push(col);continue;}
  rs.push(norm);R.push(rs);Q.push(v.map(x=>x/norm));accepted.push(col);
 }
 const z=Q.map(q=>dot(q,D.y.slice(0,cut))),beta=Array(Q.length).fill(0);
 for(let i=Q.length-1;i>=0;i--){let value=z[i];for(let j=i+1;j<Q.length;j++)value-=R[j][i]*beta[j];beta[i]=value/R[i][i];}
 const weights=Object.fromEntries(accepted.map((c,i)=>[c,beta[i]])),prediction=D.features.map(row=>accepted.reduce((s,c)=>s+row[c]*weights[c],0));
 const contributions=Object.fromEntries(parts.filter(p=>selected.includes(p.id)).map(p=>[p.id,D.features.map(row=>p.cols.reduce((s,c)=>s+row[c]*(weights[c]||0),0))]));
 const rmse=(a,z)=>Math.sqrt(a.reduce((s,y,i)=>s+(y-z[i])**2,0)/a.length);
 return {prediction,contributions,weights,rank:accepted.length,discarded,trainRMSE:rmse(D.y.slice(0,cut),prediction.slice(0,cut)),testRMSE:rmse(D.y.slice(cut,cut+90),prediction.slice(cut,cut+90))};
}
const api={components,fit};if(typeof module!=='undefined')module.exports=api;root.Harmonics=api;
})(typeof globalThis!=='undefined'?globalThis:this);
