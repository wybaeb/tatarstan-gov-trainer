#!/usr/bin/env python3
"""Проверяет, что все шесть учебных запросов дают JSON требуемой формы.

Ключ передаётся только через GIGACHAT_AUTH_KEY. Скрипт не сохраняет и не
выводит ключ, полный ответ модели или учебные запросы.
"""
from __future__ import annotations

import json
import os
import sys
import uuid
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OAUTH = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat-2-Max")

TASKS = [
    ("показатель", ["metric", "period", "calculation_rule", "checks"], "Верни только JSON с ключами metric, period, calculation_rule, checks. Учебная задача: сравнить полные месяцы срока обработки обезличенных обращений."),
    ("качество", ["defects", "clarifications"], "Верни только JSON с ключами defects и clarifications. defects — массив объектов field, issue, rule, priority. Учебный массив содержит повторы и пустые даты."),
    ("классификация", ["items", "escalation"], "Верни только JSON с ключами items и escalation. Учебные обращения уже обезличены; при низкой уверенности направляй на уточнение."),
    ("формула", ["formula", "explanation", "checks"], "Верни только JSON с ключами formula, explanation, checks. Нужна формула Excel для доли завершённых записей в срок."),
    ("безопасность", ["confirmed_facts", "assumptions", "risks", "human_control"], "Верни только JSON с ключами confirmed_facts, assumptions, risks, human_control. Не придумывай факты."),
    ("пилот", ["problem", "confirmed_fact", "scope", "ai_role", "human_control", "test_set", "metric", "acceptance", "stop_conditions", "contractor_questions", "slides"], "Верни только JSON с ключами problem, confirmed_fact, scope, ai_role, human_control, test_set, metric, acceptance, stop_conditions, contractor_questions, slides. Учебный пилот классифицирует обезличенные обращения; сотрудник проверяет результат."),
]

def main() -> int:
    key = os.getenv("GIGACHAT_AUTH_KEY", "").strip()
    if not key:
        print("Нет переменной GIGACHAT_AUTH_KEY.")
        return 2
    oauth = requests.post(OAUTH, headers={"Authorization": "Basic " + key, "RqUID": str(uuid.uuid4())}, data={"scope": "GIGACHAT_API_PERS"}, verify=False, timeout=60)
    oauth.raise_for_status()
    token = oauth.json()["access_token"]
    failed = []
    for name, required, task in TASKS:
        body = {"model": MODEL, "temperature": 0.1, "messages": [{"role": "system", "content": "Ты помощник преподавателя. Используй только учебный контекст. Не упоминай реальных людей, организации и населённые пункты."}, {"role": "user", "content": task}]}
        res = requests.post(CHAT, headers={"Authorization": "Bearer " + token}, json=body, verify=False, timeout=120)
        if res.status_code != 200:
            failed.append(name)
            print(f"{name}: ошибка ответа ({res.status_code})")
            continue
        text = res.json()["choices"][0]["message"]["content"].strip().removeprefix("```json").removesuffix("```").strip()
        try:
            answer = json.loads(text)
            missing = [x for x in required if x not in answer]
            if missing:
                raise ValueError("нет обязательных ключей")
            print(f"{name}: структура принята")
        except (ValueError, KeyError, json.JSONDecodeError):
            failed.append(name)
            print(f"{name}: структура не принята")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
