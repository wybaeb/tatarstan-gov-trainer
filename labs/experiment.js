'use strict';
const $=id=>document.getElementById(id),fmt=n=>n.toLocaleString('ru-RU',{maximumFractionDigits:1});
let seed=91524,model,params,timer=null;
const inputs=['traffic','eventRate','lag','horizon','sigma','mde','power'];
const text=(x,y,t,fill='#69717e',anchor='start',size=16)=>`<text x="${x}" y="${y}" fill="${fill}" text-anchor="${anchor}" font-family="Arial,sans-serif" font-size="${size}">${t}</text>`;
const line=(x1,y1,x2,y2,c,width=1,dash='')=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${width}" ${dash?`stroke-dasharray="${dash}"`:''}/>`;
function rebuild(){
 stop();params=Object.fromEntries(inputs.map(id=>[id,+$(id).value]));params.effect=+$('effect').value*params.mde;params.seed=seed;model=ExperimentModel.simulate(params);window.experimentState={params,model};
 inputs.forEach(id=>{if($(id+'Out'))$(id+'Out').textContent=fmt(params[id]);});
 const q=model.plan;$('target').textContent=fmt(q.n);$('enrollment').textContent=`день ${q.enrollment}`;$('finish').textContent=`день ${q.finish}`;
 $('formula').textContent=`${q.enrollment} дн. набора${q.queue?` + ${q.queue} дн. из-за более медленного потока действий`:''} + ${params.lag} дн. до действия + ${params.horizon} дн. наблюдения = ${q.finish} дней. Набор и действия идут параллельно.`;
 $('day').max=q.finish;$('day').value=q.finish;draw();
}
function draw(){
 const day=+$('day').value,q=model.plan,s=model.at(day);window.experimentState.current=s;$('dayOut').textContent=day;
 $('enrolled').textContent=fmt(s.enrolled*2);$('mature').textContent=`${fmt(s.n*2)} / ${fmt(2*q.n)}`;$('difference').textContent=s.n?`${fmt(s.delta)} усл. ед. [${fmt(s.low)}; ${fmt(s.high)}]`:'Ещё нет данных';
 $('phase').textContent=s.ready?'Все участники завершили одинаковое окно наблюдения. Можно провести запланированный анализ.':s.n?`Готов результат ${fmt(2*s.n)} участников из ${fmt(2*q.n)}. Интервалы пока промежуточные.`:s.enrolled<q.n?'Набираем участников; их действия и результаты будут появляться с задержкой.':'Участники набраны. Ждём действий и полного окна наблюдения.';
 $('verdict').textContent=!s.ready?'Расхождение интервалов до планового дня ещё не является разрешением закончить тест.':s.low>0?'Интервал разницы выше нуля: результат поддерживает преимущество B на выбранном горизонте.':s.high<0?'Интервал разницы ниже нуля: результат поддерживает преимущество A на выбранном горизонте.':'Интервал разницы включает ноль: пока нельзя утверждать, что группы различаются.';
 const xmax=Math.ceil(q.finish*1.15)+1,px=d=>75+d/xmax*860;
 let flow='';const fy=n=>98-n/(2*q.n)*60;
 flow+=line(75,fy(2*q.n),935,fy(2*q.n),'#cbd5d0',1,'3 4')+text(70,fy(2*q.n)+5,fmt(2*q.n),'#69717e','end',13);
 for(const [key,c] of [['enrolled','#2274b8'],['active','#bd7619'],['n','#00868c']]){
  let rows=model.rows.filter(r=>r.day<=day);if(!rows.some(r=>r.day===day))rows.push(s);
  flow+=`<polyline fill="none" stroke="${c}" stroke-width="3" points="${rows.map(r=>`${px(r.day)},${fy(r[key]*2)}`).join(' ')}"/>`;
 }
 flow+=line(px(q.enrollment),30,px(q.enrollment),103,'#b4c4d4',1,'3 4');
 flow+=line(px(q.finish),24,px(q.finish),103,'#20232b',2,'6 5')+text(px(q.finish)-8,20,`Анализ · день ${q.finish}`,'#20232b','end',15);
 flow+=line(px(day),36,px(day),103,'#20232b',1);
 for(const d of [0,Math.round(xmax/3),Math.round(xmax*2/3),xmax])flow+=text(px(d),121,d,'#69717e','middle',13);
 flow+=text(935,142,'День эксперимента','#69717e','end',13);$('flow').innerHTML=flow;
 const all=model.rows.filter(r=>r.n),rows=all.filter(r=>r.day<=day);if(s.n&&!rows.some(r=>r.day===day))rows.push(s);
 const final=model.at(q.finish),zoom=$('zoom').checked;let lo,hi;
 if(zoom){const pad=Math.max(final.h*2,Math.abs(params.effect)*.55,25);lo=Math.min(final.a,final.b)-pad;hi=Math.max(final.a,final.b)+pad;}
 else{lo=Math.min(...all.map(r=>Math.min(r.a,r.b)-r.h));hi=Math.max(...all.map(r=>Math.max(r.a,r.b)+r.h));const pad=(hi-lo)*.08;lo-=pad;hi+=pad;}
 const py=v=>310-(v-lo)/(hi-lo)*260;let svg='<defs><clipPath id="plotClip"><rect x="75" y="45" width="860" height="265"/></clipPath></defs>';
 for(let i=0;i<5;i++){const y=lo+(hi-lo)*i/4;svg+=line(75,py(y),935,py(y),'#e1e5e2')+text(68,py(y)+5,fmt(y),'#69717e','end',13);}
 for(let i=0;i<5;i++){const d=Math.round(xmax*i/4);svg+=text(px(d),337,d,'#69717e','middle',14);}
 svg+=text(75,22,'Показатель на пользователя, усл. ед.','#69717e','start',14)+text(935,369,'День эксперимента','#69717e','end',14);
 svg+='<g clip-path="url(#plotClip)">';
 for(const [key,c] of [['a','#ff5533'],['b','#00868c']]){
  if(!rows.length)continue;
  const upper=rows.map(r=>`${px(r.day)},${py(r[key]+r.h)}`),lower=[...rows].reverse().map(r=>`${px(r.day)},${py(r[key]-r.h)}`);
  svg+=`<polygon points="${[...upper,...lower].join(' ')}" fill="${c}" opacity=".24"/>`;
  for(const sign of [-1,1])svg+=`<polyline points="${rows.map(r=>`${px(r.day)},${py(r[key]+sign*r.h)}`).join(' ')}" fill="none" stroke="${c}" stroke-width="1" opacity=".6"/>`;
  svg+=`<polyline points="${rows.map(r=>`${px(r.day)},${py(r[key])}`).join(' ')}" fill="none" stroke="${c}" stroke-width="3"/>`;
  if(s.n){const x=px(day)+(key==='a'?-3:3),a=py(s[key]-s.h),b=py(s[key]+s.h);svg+=line(x,a,x,b,c,3)+line(x-7,a,x+7,a,c,2)+line(x-7,b,x+7,b,c,2);}
 }
 svg+='</g>'+line(px(q.finish),32,px(q.finish),310,'#20232b',2,'6 5')+text(px(q.finish)-8,38,`Плановый анализ · ${q.finish}-й день`,'#20232b','end',15);
 if(day!==q.finish)svg+=line(px(day),45,px(day),310,'#7b838b',1,'2 4');
 if(!rows.length)svg+=text(500,180,'Ждём завершения первых наблюдений','#69717e','middle',21);
 $('chart').innerHTML=svg;$('scaleNote').textContent=zoom?'Увеличенный масштаб; ось показательа начинается не с нуля. Ранние широкие интервалы могут выходить за рамку.':'Полный диапазон доверительных интервалов. Полосы показывают неопределённость оценки, а не разброс отдельных клиентов.';
}
function stop(){if(timer)clearInterval(timer);timer=null;$('play').textContent='▶ По дням';}
inputs.forEach(id=>$(id).addEventListener('input',rebuild));$('effect').addEventListener('change',rebuild);$('zoom').addEventListener('change',draw);$('rerun').onclick=()=>{seed+=17;rebuild();};$('day').addEventListener('input',()=>{stop();draw();});$('play').onclick=()=>{if(timer){stop();return;}$('day').value=0;draw();$('play').textContent='Ⅱ Пауза';timer=setInterval(()=>{$('day').value=Math.min(model.plan.finish,+$('day').value+Math.max(1,Math.ceil(model.plan.finish/120)));draw();if(+$('day').value>=model.plan.finish)stop();},140);};
if(location.hash==='#method')$('method').open=true;window.addEventListener('hashchange',()=>{if(location.hash==='#method')$('method').open=true;});rebuild();
