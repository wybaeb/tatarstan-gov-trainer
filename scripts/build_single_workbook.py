"""One reproducible macro-enabled workbook; independent reference calculations."""
from pathlib import Path
from datetime import date,timedelta,datetime
from collections import Counter
import calendar,csv,json,zipfile,math
import xlsxwriter
R=Path(__file__).resolve().parents[1];O=R/'downloads';O.mkdir(exist_ok=True)
# Same January–March totals as the source donor charts. Other months are educational.
targets=[1500,1710,1575,1510,1630,1580,1490,1620,1570,1650,1510,1590]
counts={};start=date(2024,12,1)
for mo in range(13):
 year,month=(2024,12) if mo==0 else (2025,mo)
 nd=calendar.monthrange(year,month)[1];total=1519 if mo==0 else targets[mo-1]
 weights=[1+.12*math.sin(d*2*math.pi/7)+.05*math.cos(d*2*math.pi/nd) for d in range(nd)]
 raw=[total*w/sum(weights) for w in weights];c=[int(x) for x in raw]
 for i in sorted(range(nd),key=lambda i:raw[i]-c[i],reverse=True)[:total-sum(c)]:c[i]+=1
 for d,n in enumerate(c,1):counts[date(year,month,d)]=n
rows=[]
for dt,n in counts.items():
 for j in range(n):rows.append([f'EDU-{len(rows)+1:06}',datetime.combine(dt,datetime.min.time()),['Портал','Контакт-центр','Личный приём'][j%3],1])
# Retain a valid inert VBA container from the previously tested XLSM template.
z=zipfile.ZipFile(O/'obrashcheniya_12000_excel.xlsm');vba=R/'scripts'/'training-vba.bin';vba.write_bytes(z.read('xl/vbaProject.bin'))
w=xlsxwriter.Workbook(O/'praktikum_obrashcheniya.xlsm');w.add_vba_project(str(vba));w.set_properties({'title':'Обращения: три сопоставимых расчёта','comments':'Обезличенный обучающий пример'})
h=w.add_format({'bold':True,'bg_color':'#E9D8AB','border':1,'text_wrap':True});df=w.add_format({'num_format':'dd.mm.yyyy'});nf=w.add_format({'num_format':'0.00'});wrap=w.add_format({'text_wrap':True,'valign':'top'})
s=w.add_worksheet('Обращения');s.write_row(0,0,['ID обращения','Дата регистрации','Канал','Количество'],h)
for i,row in enumerate(rows,1):s.write_row(i,0,row);s.write_datetime(i,1,row[1],df)
s.freeze_panes(1,0);s.autofilter(0,0,len(rows),3);s.set_column('A:A',20);s.set_column('B:B',20,df);s.set_column('C:C',24);s.set_column('D:D',15)
for name,headers in [('По месяцам',['Начало месяца','Количество обращений']),('На день',['Начало месяца','Дней в месяце','Обращений за день']),('Окно 30 дней',['Дата','Обращений за день','Сумма за 30 дней','Среднее за день','Индекс 30 дней']),('Итог окна',['Начало месяца','Средний индекс 30 дней','Среднее за день'])]:
 s=w.add_worksheet(name);s.write_row(0,0,headers,h);s.set_column(0,len(headers)-1,25);s.set_column(0,0,20,df);s.freeze_panes(1,0)
 if name in ['По месяцам','На день']:
  for m in range(1,13):s.write_datetime(m,0,datetime(2025,m,1),df)
ref=w.add_worksheet('Контроль');ref.write_row(0,0,['Месяц','Количество','Дней','На день','Средний индекс 30 дней','Среднее окна за день'],h);ref.set_column('A:A',20,df);ref.set_column('B:F',25,nf)
reference=[]
for m in range(1,13):
 ds=[d for d in counts if d.year==2025 and d.month==m];window=[sum(counts[d-timedelta(days=k)] for k in range(30)) for d in ds];total=sum(counts[d] for d in ds);avg=sum(window)/len(window)
 row=[datetime(2025,m,1),total,len(ds),total/len(ds),avg,avg/30];ref.write_row(m,0,row);ref.write_datetime(m,0,row[0],df);reference.append({'month':f'2025-{m:02}', 'count':total,'days':len(ds),'per_day':total/len(ds),'rolling30_month_mean':avg,'rolling_day_mean':avg/30})
s=w.add_worksheet('Инструкция');notes=['Обезличенный обучающий пример; это не статистика Республики Татарстан.','Одна строка — одно обращение. Даты — настоящие даты Excel, без времени.','Данные: 01.12.2024–31.12.2025. Декабрь нужен для полных январских окон.','Лист «Обращения»: A ID, B дата, C канал, D количество = 1.','Листы «По месяцам» и «На день»: A2:A13 уже содержат начала месяцев 2025 года.','Запрос 1 заполняет B2:B13 листа «По месяцам». Запрос 2 заполняет B2:C13 листа «На день».','Запрос 3 заполняет листы «Окно 30 дней» и «Итог окна», создаёт диаграмму.','Окно [d−29; d] содержит ровно 30 календарных дней, включая нулевые дни.','Для дня: сумма / 30; индекс 30 дней = дневное среднее × 30. Для месяца: среднее дневных индексов.','Не заменяйте реальное скользящее окно формулой «итог месяца / дни × 30».','Учебная книга XLSM уже поддерживает макросы. Вставьте полученный проверенный модуль в эту книгу.','Лист «Контроль» содержит значения независимого расчёта для проверки.','В рабочей среде соблюдайте правила организации по запуску макросов; не отключайте защиту глобально.']
for i,t in enumerate(notes):s.write(i,0,t,wrap);s.set_row(i,34)
s.set_column('A:A',110);w.close();vba.unlink()
(R/'data'/'excel-reference.json').write_text(json.dumps({'rows':len(rows),'source_last_row':len(rows)+1,'monthly':reference},ensure_ascii=False,indent=2))
print('XLSM:',len(rows),'rows; monthly counts:',[x['count'] for x in reference[:3]])
