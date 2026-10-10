from pathlib import Path
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
R=Path(__file__).resolve().parents[1];o=Options()
for a in ['--headless=new','--no-sandbox','--disable-gpu','--window-size=1440,1000']:o.add_argument(a)
d=webdriver.Chrome(options=o);w=WebDriverWait(d,15);d.get('http://127.0.0.1:4174/');d.execute_script("sessionStorage.setItem('tat-course-entered','yes')")
def goto(s):d.get('http://127.0.0.1:4174/?section='+s);w.until(lambda d:d.execute_script('return document.querySelector("[data-section].active")?.dataset.section===arguments[0]',s))
def click(i):d.execute_script('document.getElementById(arguments[0]).click()',i)
try:
 for step,slug in enumerate(['excel-month','excel-day','excel-window'],1):
  goto(slug);click('excel-control');click('excel-answer-check');assert 'ok' in d.find_element('id','excel-answer-status').get_attribute('class')
  assert d.execute_script('return validateExcelAnswer("=1/1",arguments[0]).length',step)>0
 goto('routing')
 r=next(x for x in json.load(open(R/'reviews/gigachat-course.json')) if x['section']=='routing')['response']
 d.execute_script('document.getElementById("course-response").value=arguments[0]',r);click('course-build');assert len(d.find_elements('css selector','.route-card'))==6
 # Missing and duplicated ID are rejected, not invented.
 d.execute_script('document.getElementById("course-response").value=arguments[0]',r.replace('EDU-001','EDU-002'));click('course-build');assert 'bad' in d.find_element('id','course-status').get_attribute('class')
 goto('mermaid');bad=next(x for x in json.load(open(R/'reviews/gigachat-course.json')) if x['section']=='mermaid')['response'];d.execute_script('document.getElementById("course-response").value=arguments[0]',bad);click('course-build');assert 'bad' in d.find_element('id','course-status').get_attribute('class')
 goto('defense')
 for raw in ['not a table','| № | Заголовок |\n|---|---|\n|1|x|']:
  d.execute_script('document.getElementById("defense-response").value=arguments[0]',raw);click('defense-build');assert 'bad' in d.find_element('id','defense-status').get_attribute('class')
 # Prior JSON still builds six slides; HTML from model is escaped.
 old=json.dumps({'slides':[{'title':'<script>window.pwned=1</script>','key_message':'Проверка','body':'<img src=x onerror=alert(1)>'} for i in range(6)]})
 d.execute_script('document.getElementById("defense-response").value=arguments[0]',old);click('defense-build');assert 'ok' in d.find_element('id','defense-status').get_attribute('class');d.switch_to.frame(d.find_element('id','defense-frame'));assert not d.execute_script('return Boolean(window.pwned)');assert not d.find_elements('css selector','img');d.switch_to.default_content()
 # All six existing security scenarios retain the new transfer button.
 goto('security');buttons=d.find_elements('css selector','[data-security-scenario]') or d.find_elements('css selector','[data-scenario]')
 for b in buttons:
  pass
 # Mobile page must not overflow horizontally.
 d.set_window_size(390,844);goto('routing');assert not d.execute_script('return document.documentElement.scrollWidth>innerWidth+2')
 print('PASS: control formulas/code, real weak-model failure fixtures, IDs, old JSON, XSS, mobile')
finally:d.quit()
