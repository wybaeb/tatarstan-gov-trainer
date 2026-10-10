'use strict';
let datasets,D,parts,selected=new Set(),last=null,cut=2465;
const el=id=>document.getElementById(id),palette=['#00868c','#7863a6','#c29337','#3478a6','#a95873','#567b54','#dc7750','#6257b5','#348888','#ba697c','#716144','#5373a4'];
const number=x=>x.toLocaleString('ru-RU',{maximumFractionDigits:2});
function selectedIds(){return parts.filter(p=>selected.has(p.id)).map(p=>p.id)}
function activate(){D=datasets[el('dataset').value];parts=Harmonics.components(el('dataset').value);selected=new Set([...selected].filter(id=>parts.some(p=>p.id===id)));last=null;
 el('cut').min=D.dates[729];el('cut').max=D.dates[D.y.length-91];el('cut').value=D.dates[cut-1];
 el('source').textContent=D.source+' · '+D.unit+'. Обучение: '+D.dates[0]+' — '+D.dates[cut-1]+'.';
 el('components').replaceChildren();for(const group of [...new Set(parts.map(p=>p.group))]){const fs=document.createElement('fieldset'),lg=document.createElement('legend');lg.textContent=group;fs.append(lg);for(const p of parts.filter(p=>p.group===group)){let label=document.createElement('label'),cb=document.createElement('input');cb.type='checkbox';cb.id=p.id;cb.checked=selected.has(p.id);cb.addEventListener('change',()=>{cb.checked?selected.add(p.id):selected.delete(p.id);draw()});label.append(cb,document.createTextNode(p.label));fs.append(label)}el('components').append(fs)}draw();}
function chart(node,series,start,end,height,{boundary=true,zero=false}={}){
 const left=72,right=930,top=42,bottom=height-48,values=series.flatMap(s=>s.data.slice(start,end));let lo=Math.min(...values),hi=Math.max(...values);if(zero){lo=Math.min(lo,0);hi=Math.max(hi,0)}let pad=(hi-lo||1)*.09;lo-=pad;hi+=pad;const X=i=>left+(i-start)/Math.max(1,end-start-1)*(right-left),Y=v=>bottom-(v-lo)/(hi-lo)*(bottom-top);
 let svg=`<rect width="960" height="${height}" fill="white"/><text x="${left}" y="20" font-size="12" fill="#646c76">${D.unit}</text>`;
 if(boundary)svg+=`<rect x="${X(cut)}" y="${top}" width="${right-X(cut)}" height="${bottom-top}" fill="#fff2eb"/>`;
 for(let i=0;i<=4;i++){let v=lo+(hi-lo)*i/4;svg+=`<line x1="${left}" x2="${right}" y1="${Y(v)}" y2="${Y(v)}" stroke="#e6e5e1"/><text x="${left-9}" y="${Y(v)+4}" text-anchor="end" font-size="12" fill="#646c76">${number(v)}</text>`}
 if(zero)svg+=`<line x1="${left}" x2="${right}" y1="${Y(0)}" y2="${Y(0)}" stroke="#9198a0"/>`;
 for(let j=0;j<5;j++){let i=Math.round(start+(end-start-1)*j/4);svg+=`<text x="${X(i)}" y="${height-18}" text-anchor="${j===0?'start':j===4?'end':'middle'}" font-size="12" fill="#646c76">${D.dates[i]}</text>`}
 for(const s of series){const path=(a,z,dash)=>{if(z-a<1)return '';const points=s.data.slice(a,z).map((v,i)=>`${X(a+i).toFixed(2)},${Y(v).toFixed(2)}`).join(' ');return `<polyline points="${points}" fill="none" stroke="${s.color}" stroke-width="${s.width||2}" opacity="${s.opacity||1}" ${dash?'stroke-dasharray="7 5"':''}/>`};svg+=s.split?path(start,cut,false)+path(cut-1,end,true):path(start,end,false)}
 if(boundary)svg+=`<line x1="${X(cut)}" x2="${X(cut)}" y1="${top}" y2="${bottom}" stroke="#20232b" stroke-dasharray="4 4"/><text x="${X(cut)+8}" y="${top+17}" font-size="12">Прогноз</text>`;
 node.innerHTML=svg;
}
function draw(){const start=Math.max(0,cut-(el('window').value==='all'?cut:+el('window').value)),end=cut+90,result=Harmonics.fit(D,cut,parts,selectedIds()),baseline=Harmonics.fit(D,cut,parts,[]);
 chart(el('plot'),[{data:D.y,color:'#919aa3',width:1.6,opacity:.85},{data:result.prediction,color:'#ff5533',width:2.8,split:true}],start,end,460);
 el('train').textContent=number(result.trainRMSE);el('test').textContent=number(result.testRMSE);el('gain').textContent='Снижение к модели одного уровня: '+number(Math.max(0,(1-result.trainRMSE/baseline.trainRMSE)*100))+'%';
 el('count').textContent=parts.filter(p=>selected.has(p.id)&&/^(year|month)/.test(p.id)).length+' / '+result.rank;
 el('testNote').textContent=last?'К прошлому составу: '+(result.testRMSE>last.testRMSE?'+':'')+number(result.testRMSE-last.testRMSE)+' '+D.unit:'RMSE · '+D.unit;
 el('status').textContent=result.discarded.length?'До выбранной даты часть признаков не менялась: их вес нельзя оценить. Они временно исключены.':selected.size?'Сумма пересчитана по выбранным компонентам. Справа — 90 дней вне обучения.':'Пока включён только базовый уровень — среднее по обучающей истории. Добавьте тренд или первую годовую гармонику.';
 el('partLegend').replaceChildren();let series=[];for(const p of parts.filter(p=>selected.has(p.id))){const color=palette[parts.indexOf(p)%palette.length],span=document.createElement('span');span.textContent=p.group+': '+p.label;span.style.setProperty('--color',color);el('partLegend').append(span);series.push({data:result.contributions[p.id],color,split:true})}
 if(series.length)chart(el('partsPlot'),series,start,end,320,{zero:true});else el('partsPlot').innerHTML='<text x="40" y="70" font-size="18" fill="#646c76">Включите компонент, чтобы увидеть его вклад.</text>';
 window.harmonicsState={dataset:el('dataset').value,cut,selected:selectedIds(),...result};last=result;
}
function openMethod(){if(location.hash==='#method')el('method').open=true}
fetch('data.json').then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()}).then(d=>{datasets=d.datasets;activate();el('dataset').addEventListener('change',activate);el('window').addEventListener('change',()=>{last=null;draw()});el('cut').addEventListener('change',()=>{let next=D.dates.indexOf(el('cut').value)+1;if(next<730||next>D.y.length-90){el('cut').value=D.dates[cut-1];return}cut=next;activate()});document.querySelectorAll('[data-preset]').forEach(btn=>btn.addEventListener('click',()=>{const mode=btn.dataset.preset;selected=new Set(parts.filter(p=>mode==='all'||mode==='base'&&p.group==='Основа'||mode==='year'&&(p.group==='Основа'||p.group==='Годовые гармоники')).map(p=>p.id));document.querySelectorAll('#components input').forEach(cb=>cb.checked=selected.has(cb.id));draw()}));openMethod();window.addEventListener('hashchange',openMethod)}).catch(e=>{el('status').textContent='Не удалось загрузить тренажёр: '+e.message});
