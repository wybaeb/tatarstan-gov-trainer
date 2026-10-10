"""Evaluate exact UI prompts on the small GigaChat model. No credentials in reports."""
import os,json,uuid,time
from pathlib import Path
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
R=Path(__file__).resolve().parents[1];O=R/'reviews';ca=os.getenv('GIGACHAT_CA','/tmp/tat-russian-root.crt');key=os.getenv('GIGACHAT_AUTH_KEY')
if not key:raise SystemExit('missing credential')
try:
 r=requests.post('https://ngw.devices.sberbank.ru:9443/api/v2/oauth',headers={'Authorization':'Basic '+key,'RqUID':str(uuid.uuid4())},data={'scope':'GIGACHAT_API_PERS'},verify=ca,timeout=25)
 if r.status_code!=200:raise SystemExit('OAuth status '+str(r.status_code))
 token=r.json()['access_token']
except requests.exceptions.SSLError:raise SystemExit('TLS failed: trusted chain incomplete')
o=Options()
for a in ['--headless=new','--no-sandbox','--disable-gpu','--window-size=1440,1100']:o.add_argument(a)
d=webdriver.Chrome(options=o);w=WebDriverWait(d,20);d.get('http://127.0.0.1:4174/');d.execute_script("sessionStorage.setItem('tat-course-entered','yes')")
results=[]
try:
 for slug in ['excel-month','excel-day','excel-window','assistant','routing','memo','mermaid','process','security','defense']:
  
  if os.getenv('PROMPT_FILTER') and slug not in os.environ['PROMPT_FILTER'].split(','):continue
  d.get('http://127.0.0.1:4174/?section='+slug);w.until(lambda d:d.execute_script('return document.querySelector("[data-section].active")?.dataset.section===arguments[0]',slug));w.until(lambda d:d.find_elements('css selector','.prompt-preview'))
  if slug=='defense':d.execute_script("document.querySelector('#defense-seed').click()")
  prompt=d.find_element('css selector','.prompt-preview').get_attribute('textContent');entry={'section':slug,'model':'GigaChat','prompt':prompt}
  try:
   r=requests.post('https://gigachat.devices.sberbank.ru/api/v1/chat/completions',headers={'Authorization':'Bearer '+token},json={'model':'GigaChat','temperature':0.1,'max_tokens':5000,'messages':[{'role':'user','content':prompt}]},verify=ca,timeout=110)
   if r.status_code!=200:raise ValueError('HTTP '+str(r.status_code))
   text=r.json()['choices'][0]['message']['content'];entry['response']=text
   if slug in ['routing','assistant','memo','mermaid','process']:
    d.execute_script("document.querySelector('#course-response').value=arguments[0];document.querySelector('#course-build').click()",text);entry['accepted']='ok' in d.find_element('id','course-status').get_attribute('class');entry['validation']=d.find_element('id','course-status').text
   elif slug=='security':
    d.execute_script("document.querySelector('#safe-response').value=arguments[0];document.querySelector('#safe-build').click()",text);entry['accepted']='ok' in d.find_element('id','safe-status').get_attribute('class');entry['validation']=d.find_element('id','safe-status').text
   elif slug=='defense':
    d.execute_script("document.querySelector('#defense-response').value=arguments[0];document.querySelector('#defense-build').click()",text);entry['accepted']='ok' in d.find_element('id','defense-status').get_attribute('class');entry['validation']=d.find_element('id','defense-status').text
   else:
    step={'excel-month':1,'excel-day':2,'excel-window':3}[slug];issues=d.execute_script('return validateExcelAnswer(arguments[0],arguments[1])',text,step);entry['accepted']=not issues;entry['validation']=issues or ['Контрольные признаки найдены; Excel/VBA в Microsoft Excel не исполнялся.']
   print(slug,'received','accepted='+str(entry['accepted']),flush=True)
  except Exception as e:entry['error']=type(e).__name__+': '+str(e)[:200];print(slug,entry['error'],flush=True)
  results.append(entry);(O/os.getenv('MODEL_REPORT','gigachat-course.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2))
finally:d.quit()
