#!/usr/bin/env python3
"""Проверяет все запросы на младшей модели GigaChat.

Ключ передаётся только через GIGACHAT_AUTH_KEY. Скрипт не сохраняет и не
выводит ключ, полный ответ модели или учебные запросы.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import uuid
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OAUTH = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat")

TASKS = [
    (
        "показатель",
        ["name", "purpose", "numerator", "denominator", "period", "exclusions", "checks"],
        "Работай только с обезличенным учебным набором данных. Управленческий вопрос: какая доля завершённых обращений уложилась в установленный срок? Поля: идентификатор; дата регистрации; дата завершения; категория; канал; статус; целевой срок. Сформируй карточку расчёта показателя. Отдели подтверждённые правила от предположений. Верни только JSON: {\"name\":\"...\",\"purpose\":\"...\",\"numerator\":\"...\",\"denominator\":\"...\",\"period\":\"...\",\"exclusions\":[\"...\"],\"checks\":[\"...\"]}",
    ),
    (
        "классификация",
        ["items", "escalation"],
        "Классифицируй три обезличенных учебных обращения EDU-001, EDU-002 и EDU-003. Категории: благоустройство; транспортная доступность; социальная поддержка; иное. При уверенности ниже 0.70 укажи маршрут «проверка сотрудником». Верни только один корректный JSON-объект. В items должно быть ровно три объекта — по одному на каждый ID. В КАЖДОМ объекте обязательны четыре поля id, category, confidence и reason; reason — краткое основание, его нельзя пропускать. Структура: {\"items\":[{\"id\":\"EDU-001\",\"category\":\"...\",\"confidence\":0.0,\"reason\":\"краткое основание\"}],\"escalation\":[{\"condition\":\"...\",\"route\":\"...\"}]}",
    ),
    (
        "пилот",
        ["passport", "contractor_questions", "slides"],
        "Подготовь паспорт ограниченного пилота, вопросы к подрядчику и содержание презентации защиты из шести слайдов. Пилот проверяет предварительную классификацию на 100 обезличенных учебных обращениях; ИИ предлагает категорию, сотрудник утверждает маршрут. Не добавляй неподтверждённые сведения. Верни только JSON: {\"passport\":{\"problem\":\"...\",\"confirmed_fact\":\"...\",\"data\":\"...\",\"scope\":\"...\",\"ai_role\":\"...\",\"human_control\":\"...\",\"test_set\":\"...\",\"metric\":\"...\",\"acceptance\":\"...\",\"stop_conditions\":[\"...\"]},\"contractor_questions\":[\"...\"],\"slides\":[{\"title\":\"...\",\"key_message\":\"...\"}]}",
    ),
]

CODE_TASKS = [
    ("Формулы Excel", [("проверка пустых дат", r"(?:\b(?:OR|AND|ISBLANK|COUNTBLANK)\s*\(|[BC]2\s*(?:=|<>)\s*\"\")"), ("защита от отрицательного срока", r"(?:\bMAX\s*\(|(?:C2\s*-\s*B2|H2)\s*<\s*0)"), ("сравнение H2 с G2", r"(?:\$?H2\s*<=\s*\$?G2|\$?G2\s*>=\s*\$?H2)"), ("подсчёт доли через COUNTIF", r"COUNTIF\s*\(")], "Для листа Excel «Формулы» предложи три формулы: 1) в H2 длительность между датой завершения C2 и датой регистрации B2; пустые даты должны давать пустой результат, отрицательная длительность — 0; 2) в I2 «Да», если длительность H2 не превышает целевой срок G2, иначе «Нет»; 3) доля непустых результатов I2:I121 со значением «Да». Используй английские имена функций и запятые как разделители. Верни только формулы с краткими названиями."),
    ("VBA", [("строка Option Explicit", r"Option\s+Explicit"), ("точная строка Public Sub ProcessTrainingAppeals()", r"Public\s+Sub\s+ProcessTrainingAppeals\s*\(\s*\)"), ("чтение CurrentRegion.Value или CurrentRegion.Value2", r"CurrentRegion\.Value2?"), ("словарь Scripting.Dictionary", r"Scripting\.Dictionary"), ("разбор дат через DateSerial", r"DateSerial\s*\("), ("диаграмма через ChartObjects.Add", r"ChartObjects\.Add")], "Напиши полный модуль VBA для листа «Выгрузка» с 12 324 учебными строками. Поля: ID обращения, дата регистрации, дата завершения, канал, категория, статус, целевой срок, территориальная группа, краткое содержание. Удали полные повторы по исходным значениям; явно разбери даты ДД.ММ.ГГГГ и ГГГГ-ММ-ДД через DateSerial; нормализуй четыре канала; добавь длительность и соблюдение срока; сформируй лист «Сводка» по каналам и категориям и диаграмму. Код должен начинаться с Option Explicit и содержать точную строку Public Sub ProcessTrainingAppeals(). Всё прочитай одним CurrentRegion.Value2 в массив; используй Scripting.Dictionary; не обращайся к отдельным ячейкам в основном цикле; запиши очищенный массив одним присваиванием; создай ChartObjects.Add с xlColumnClustered. Верни только код VBA."),
    ("Apps Script", [("функция processTrainingAppeals", r"function\s+processTrainingAppeals"), ("единый диапазон getDataRange", r"getDataRange\s*\("), ("одно пакетное чтение getValues", r"getValues\s*\("), ("пакетная запись setValues", r"setValues\s*\("), ("множество Set для повторов", r"new\s+Set\s*\("), ("явное создание даты", r"new\s+Date\s*\("), ("диаграмма через newChart", r"newChart\s*\(")], "Напиши полный Google Apps Script для листа «Выгрузка» с 12 324 учебными строками и теми же девятью полями. Удали полные повторы до преобразований; явно разбери даты ДД.ММ.ГГГГ и ГГГГ-ММ-ДД; нормализуй четыре канала; добавь длительность и соблюдение срока; сформируй лист «Сводка» и столбчатую диаграмму. Требования: одна функция processTrainingAppeals; определить единый диапазон через getDataRange(), затем один раз вызвать getValues(); обработка массива в памяти с new Set(); одна запись setValues; без построчных getValue/setValue; диаграмма через newChart. Верни только код JavaScript."),
]


def first_json_object(text: str) -> dict:
    """Читает первый полный JSON-объект и игнорирует пояснение после него."""
    decoder = json.JSONDecoder()
    start = text.find("{")
    if start < 0:
        raise json.JSONDecodeError("нет объекта JSON", text, 0)
    value, _ = decoder.raw_decode(text[start:])
    if not isinstance(value, dict):
        raise ValueError("верхний уровень ответа должен быть объектом")
    return value


def validate_nested(name: str, answer: dict) -> None:
    schemas = {
        "классификация": (("items", ("id", "category", "confidence", "reason")), ("escalation", ("condition", "route"))),
        "пилот": (("slides", ("title", "key_message")),),
    }
    for list_name, row_keys in schemas.get(name, ()):
        rows = answer.get(list_name)
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{list_name} должен быть непустым списком")
        for index, row in enumerate(rows):
            missing = [key for key in row_keys if key not in row]
            if missing:
                raise ValueError(f"нет {list_name}[{index}].{','.join(missing)}")
    if name == "классификация" and len(answer.get("items", [])) != 3:
        raise ValueError("items должен содержать ровно три объекта")
    if name == "пилот":
        passport = answer.get("passport", {})
        missing = [key for key in ("problem", "confirmed_fact", "data", "scope", "ai_role", "human_control", "test_set", "metric", "acceptance", "stop_conditions") if key not in passport]
        if missing or not answer.get("contractor_questions") or len(answer.get("slides", [])) != 6:
            raise ValueError("паспорт неполон или слайдов не шесть")


SECURITY_TASK = """Вы — помощник по предварительной оценке информационной безопасности в российском государственном секторе. Это учебная самопроверка, а не окончательное юридическое заключение. Используйте актуальные на 9 октября 2026 года требования: 149-ФЗ, 152-ФЗ, постановление Правительства РФ № 1119, приказ ФСТЭК России № 117 в действующей редакции и специальные режимы, если они применимы. Не считайте сервис допустимым только по названию поставщика. При неопределённости выбирайте более строгий маршрут и формулируйте вопросы уполномоченному специалисту.

Уровень: персональные данные. Тип сведений: ФИО, контактные сведения и содержание обращения, позволяющее определить заявителя. Обработка: подготовка проекта ответа. Хранение: только в утверждённой информационной системе. Использование: сотрудник проверяет и утверждает результат. Пограничный случай: поставщик известен, но договор, размещение, хранение и удаление не подтверждены.

Верните только Markdown: таблицу с колонками «Уровень | Категория сведений | Значимость | Допустимый контур | Передача | Хранение | Решение | Нормативное основание», затем маркированные разделы «НЕ ДЕЛАТЬ», «СДЕЛАТЬ», «ВОПРОСЫ СПЕЦИАЛИСТУ». Не придумывайте согласования и свойства сервиса."""


def validate_security_markdown(text: str) -> None:
    required_headers = ("Уровень", "Категория сведений", "Значимость", "Допустимый контур", "Передача", "Хранение", "Решение", "Нормативное основание")
    table_lines = [line for line in text.splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 3 or not all(header.lower() in table_lines[0].lower() for header in required_headers):
        raise ValueError("нет полной Markdown-таблицы")
    for section in ("НЕ ДЕЛАТЬ", "СДЕЛАТЬ", "ВОПРОСЫ СПЕЦИАЛИСТУ"):
        match = re.search(rf"^#+\s*{section}\s*$([\s\S]*?)(?=^#+|\Z)", text, re.I | re.M)
        if not match or not re.search(r"^\s*[-*]\s+", match.group(1), re.M):
            raise ValueError(f"нет маркированного раздела {section}")

def main() -> int:
    key = os.getenv("GIGACHAT_AUTH_KEY", "").strip()
    if not key:
        print("Нет переменной GIGACHAT_AUTH_KEY.")
        return 2
    oauth = requests.post(OAUTH, headers={"Authorization": "Basic " + key, "RqUID": str(uuid.uuid4())}, data={"scope": "GIGACHAT_API_PERS"}, verify=False, timeout=60)
    oauth.raise_for_status()
    token = oauth.json()["access_token"]
    def ask(task: str, max_tokens: int = 4096) -> str:
        body = {"model": MODEL, "temperature": 0.1, "max_tokens": max_tokens, "messages": [{"role": "system", "content": "Ты помощник преподавателя. Используй только учебный контекст. Не упоминай реальных людей, организации и населённые пункты."}, {"role": "user", "content": task}]}
        for attempt in range(3):
            res = requests.post(CHAT, headers={"Authorization": "Bearer " + token}, json=body, verify=False, timeout=180)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"].strip()
            if res.status_code not in (429, 500, 502, 503, 504) or attempt == 2:
                res.raise_for_status()
            time.sleep(attempt + 1)
        raise RuntimeError("ИИ-сервис не ответил")

    only = os.getenv("PROMPT_FILTER", "").strip().lower()
    failed = []
    for name, required, task in TASKS:
        if only and only not in name.lower():
            continue
        try:
            text = ask(task).strip()
            for attempt in range(3):
                try:
                    answer = first_json_object(text)
                    missing = [x for x in required if x not in answer]
                    if missing:
                        raise ValueError("нет обязательных ключей: " + ", ".join(missing))
                    validate_nested(name, answer)
                    break
                except (ValueError, KeyError, json.JSONDecodeError) as exc:
                    if attempt == 2:
                        raise
                    text = ask(f"Ответ не прошёл машинную проверку: {exc}. Исправьте синтаксис, обязательные поля и вложенные списки. Проверьте, что результат разбирается JSON.parse: без комментариев, многоточий и висячих запятых. Верните только один полный JSON-объект.\n\n{text}").strip()
            missing = [x for x in required if x not in answer]
            if missing:
                raise ValueError("нет обязательных ключей")
            print(f"{name}: структура принята")
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            failed.append(name)
            print(f"{name}: структура не принята ({type(exc).__name__}: {exc})")

    if not only or only in "безопасность":
        try:
            security_text = ask(SECURITY_TASK).strip()
            for attempt in range(3):
                try:
                    validate_security_markdown(security_text)
                    break
                except ValueError as exc:
                    if attempt == 2:
                        raise
                    security_text = ask(f"Ответ не прошёл машинную проверку: {exc}. Нужна полная Markdown-таблица со всеми восемью колонками и ровно три заголовка вида ### НЕ ДЕЛАТЬ, ### СДЕЛАТЬ, ### ВОПРОСЫ СПЕЦИАЛИСТУ; под каждым нужен маркированный список. Верните только исправленный Markdown.\n\n" + security_text).strip()
            print("безопасность: Markdown принят")
        except (ValueError, KeyError, requests.RequestException) as exc:
            failed.append("безопасность")
            print(f"безопасность: Markdown не принят ({type(exc).__name__}: {exc})")

    for name, rules, task in CODE_TASKS:
        if only and only not in name.lower():
            continue
        missing = [label for label, _ in rules]
        try:
            code = ask(task, 8192).removeprefix("```vba").removeprefix("```javascript").removesuffix("```").strip()
            missing = [label for label, pattern in rules if not re.search(pattern, code, re.I)]
            for _ in range(2):
                if not missing:
                    break
                repair = "Исправь полный код. Обязательно выполни следующие требования: " + "; ".join(missing) + ". Ничего не сокращай. Верни только полный исправленный код.\n\n" + code
                code = ask(repair, 8192)
                missing = [label for label, pattern in rules if not re.search(pattern, code, re.I)]
            if missing:
                raise ValueError("не выполнены требования")
            print(f"{name}: код принят")
        except (ValueError, KeyError, requests.RequestException):
            failed.append(name)
            print(f"{name}: код не принят; отсутствуют {', '.join(missing)}")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
