from pathlib import Path
from collections import Counter
from datetime import datetime,timedelta
import json,zipfile,hashlib,subprocess,math
import openpyxl
R=Path(__file__).resolve().parents[1]
w=openpyxl.load_workbook(R/'downloads/praktikum_obrashcheniya.xlsm',read_only=True,keep_vba=True,data_only=True)
c=Counter();ids=set()
for row in w['Обращения'].iter_rows(min_row=2,values_only=True):
 assert row[0] not in ids;ids.add(row[0]);assert isinstance(row[1],datetime);c[row[1].date()]+=1;assert row[3]==1
assert len(ids)==20454
ref=json.load(open(R/'data/excel-reference.json'))
for r in ref['monthly']:
 year,month=map(int,r['month'].split('-'));days=sorted(d for d in c if (d.year,d.month)==(year,month));assert len(days)==r['days'];assert sum(c[d] for d in days)==r['count']
 true=sum(sum(c[d-timedelta(days=k)] for k in range(30)) for d in days)/len(days)
 assert math.isclose(true,r['rolling30_month_mean'],abs_tol=1e-10)
assert not math.isclose(ref['monthly'][0]['rolling30_month_mean'],1500/31*30,abs_tol=.01)
with zipfile.ZipFile(R/'downloads/praktikum_obrashcheniya.xlsm') as z:
 assert 'xl/vbaProject.bin' in z.namelist();assert b'macroEnabled' in z.read('[Content_Types].xml')
for filename in ['experiment-model.js','harmonics-model.js','distributions-model.js']:
 assert (R/'labs'/filename).read_bytes()==(Path('/root/work/data-literacy-forecast-lab')/filename).read_bytes(),filename
js='''const m=require(process.argv[1]);const p={sigma:250,mde:30,power:80,traffic:200,eventRate:100,lag:4,horizon:30,effect:30,seed:91524};const a=m.simulate(p),q=a.plan;const first=a.at(40),last=a.at(q.finish);if(!last.ready||first.ready||!(first.h>last.h)||Math.abs((last.high-last.low)/2-1.959963984540054*250*Math.sqrt(2/last.n))>1e-8)throw Error('interval invariant');console.log(JSON.stringify({n:q.n,finish:q.finish,firstWidth:first.h*2,lastWidth:last.h*2}));'''
res=subprocess.run(['node','-e',js,str(R/'labs/experiment-model.js')],capture_output=True,text=True,check=True)
print('PASS: workbook, real rolling windows, original model identity, intervals',res.stdout.strip())
