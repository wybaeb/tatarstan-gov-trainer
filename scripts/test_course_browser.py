import os,json,base64,time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from pypdf import PdfReader
import io
R=Path(__file__).resolve().parents[1];BASE=os.environ.get('TRAINER_URL','http://127.0.0.1:4174');O=R/'reviews';O.mkdir(exist_ok=True)
o=Options()
for a in ['--headless=new','--no-sandbox','--disable-gpu','--window-size=1440,1100']:o.add_argument(a)
d=webdriver.Chrome(options=o);w=WebDriverWait(d,25);report=[]
def click(id):d.execute_script('arguments[0].click()',d.find_element('id',id))
def goto(slug):
 d.get(BASE+'/?section='+slug);w.until(lambda d:d.find_elements('css selector','#journey [data-section]'));w.until(lambda d:d.find_elements('css selector','.stage-head h2'))
 print('CHECK',slug,flush=True);report.append({'section':slug,'title':d.find_element('css selector','.stage-head h2').text,'overflow':d.execute_script('return document.documentElement.scrollWidth>innerWidth+2')})
try:
 d.get(BASE);w.until(lambda d:d.find_elements('id','entry-password'));d.find_element('id','entry-password').send_keys('wrong');click('entry-password') if False else None;d.execute_script("document.querySelector('#entry').requestSubmit()");assert 'Проверьте' in d.find_element('id','entry-error').text
 d.find_element('id','entry-password').clear();d.find_element('id','entry-password').send_keys('TATARSTAN13');d.execute_script("document.querySelector('#entry').requestSubmit()");w.until(lambda d:d.find_elements('id','journey'))
 for slug in ['welcome','metric','excel-month','excel-day','excel-window','season','waves','forecast','distribution','experiment','assistant','routing','memo','rag-demo','mermaid','agent-demo','process','security','defense','present']:
  goto(slug)
  if slug.startswith('excel'):
   text=d.find_element('css selector','.prompt-preview').text;assert '20455' in text and 'аргументов ;' in text
   d.execute_script("document.querySelector('#excel-region').value='en';document.querySelector('#excel-region').dispatchEvent(new Event('input',{bubbles:true}))")
   assert 'separator comma' in d.find_element('css selector','.prompt-preview').text
   d.execute_script("document.querySelector('#excel-region').value='ru';document.querySelector('#excel-region').dispatchEvent(new Event('input',{bubbles:true}))")
  if slug in ['assistant','routing','memo','mermaid','process']:
   click('course-example');click('course-build');assert 'Структура принята' in d.find_element('id','course-status').text
   if slug=='routing':assert len(d.find_elements('css selector','.route-card'))==6
   d.save_screenshot(str(O/(slug+'.png')))
  if slug=='security':click('safe-example');click('safe-build');assert 'извлечено' in d.find_element('id','safe-status').text;click('security-save')
  if slug in ['waves','forecast','distribution','experiment']:
   d.switch_to.frame(d.find_element('css selector','iframe'));w.until(lambda d:d.find_elements('css selector','svg,canvas'))
   if slug=='experiment':w.until(lambda d:d.execute_script('return Boolean(window.experimentState?.current?.n)'));a=d.execute_script('return experimentState.current');assert a['high']>a['low'];d.save_screenshot(str(O/'experiment.png'))
   if slug=='waves':w.until(lambda d:d.execute_script('return Boolean(window.harmonicsState)'))
   d.switch_to.default_content()
  if slug=='defense':
   assert d.find_element('id','defense-process').get_attribute('value');assert d.find_element('id','defense-security').get_attribute('value')
   click('defense-example');click('defense-build');assert 'Шесть слайдов готовы' in d.find_element('id','defense-status').text
   srcdoc=d.find_element('id','defense-frame').get_attribute('srcdoc');(O/'sample-defense.html').write_text(srcdoc)
   d.switch_to.frame(d.find_element('id','defense-frame'));assert len(d.find_elements('css selector','.slide'))==6;click('next');assert '2 / 6' in d.find_element('id','counter').text;d.switch_to.default_content()
   d.save_screenshot(str(O/'defense.png'))
 # Actual offline document and page count.
 d.get('file://'+str(O/'sample-defense.html'));click('next');assert '2 / 6' in d.find_element('id','counter').text
 pdf=base64.b64decode(d.execute_cdp_cmd('Page.printToPDF',{'printBackground':False,'preferCSSPageSize':True})['data']);(O/'sample-defense.pdf').write_bytes(pdf);r=PdfReader(io.BytesIO(pdf));assert len(r.pages)==6,len(r.pages);assert all(p.mediabox.width>p.mediabox.height for p in r.pages)
 for step in range(1,10):
  d.get(BASE+'/?step='+str(step));w.until(lambda d:d.find_elements('css selector','#journey [data-step]'));assert len(d.find_elements('css selector','#journey [data-step]'))==9
 report.append({'legacy_routes':'1..9 PASS','offline_html':'PASS','print':'6 landscape pages PASS'})
 errors=[e for e in d.get_log('browser') if e['level']=='SEVERE' and 'favicon' not in e['message']];report.append({'browser_errors':errors});assert not errors,errors
 assert not any(x.get('overflow') for x in report)
 (O/'browser-course.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('PASS:',len(report),'checks')
finally:d.quit()
