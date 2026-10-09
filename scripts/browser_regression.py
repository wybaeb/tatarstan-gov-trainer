#!/usr/bin/env python3
"""Проверяет все маршруты тренажёра в браузере."""
from __future__ import annotations

import json
import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

ROOT = Path(__file__).resolve().parents[1]
BASE = os.getenv("TRAINER_URL", "http://127.0.0.1:4173")

ANSWERS = {
    "metric": {"metric": "Доля завершённых в срок", "period": "полный месяц", "calculation_rule": "завершённые в срок / завершённые", "checks": ["медиана", "сопоставимость"]},
    "quality": {"defects": [{"field": "дата", "issue": "пустое значение", "rule": "допустимо для открытых", "priority": "средний"}], "clarifications": ["правило статуса"]},
    "classification": {"items": [{"id": "EDU-1", "category": "иное", "confidence": 0.7, "reason": "недостаточно признаков", "metric": "доля иных"}], "escalation": [{"condition": "уверенность ниже 0.7", "route": "проверка сотрудником"}]},
    "formula": {"formula": "=СЧЁТЕСЛИМН(B:B;\"Завершено\")", "explanation": "учитываются завершённые", "checks": ["нулевой знаменатель", "пустые даты"]},
    "security": {"confirmed_facts": ["массив обезличен"], "assumptions": ["полнота очистки требует проверки"], "risks": [{"risk": "остаточные сведения", "control": "проверка выборки"}], "human_control": "утверждение сотрудником"},
    "pilot": {"problem": "предварительная классификация", "confirmed_fact": "учебный массив обезличен", "scope": "100 записей", "ai_role": "предложить категорию", "human_control": "утвердить результат", "test_set": "100 записей", "metric": "доля верных предложений", "acceptance": "заданный порог", "stop_conditions": ["обнаружение закрытых сведений"], "contractor_questions": ["как ведётся журнал"], "slides": [{"title": "Задача", "key_message": "ограниченный пилот"}]},
}


def main() -> None:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1440,1200")
    driver = webdriver.Chrome(options=options)
    try:
        for case_id, answer in ANSWERS.items():
            driver.get(f"{BASE}/?case={case_id}")
            driver.find_element(By.ID, "fill").click()
            driver.find_element(By.ID, "make").click()
            assert len(driver.find_element(By.ID, "prompt").text) > 100
            driver.find_element(By.ID, "response").send_keys(json.dumps(answer, ensure_ascii=False))
            driver.find_element(By.ID, "check").click()
            assert "соответствует" in driver.find_element(By.ID, "status").text

        for case_id, filename in [("excel", "reference_process_appeals.bas"), ("sheets", "reference_process_appeals.gs")]:
            driver.get(f"{BASE}/?case={case_id}")
            driver.find_element(By.ID, "fill").click()
            driver.find_element(By.ID, "make").click()
            assert "Большая выгрузка" in driver.find_element(By.CSS_SELECTOR, ".case-head").text
            code = (ROOT / "downloads" / filename).read_text(encoding="utf-8")
            driver.find_element(By.ID, "response").send_keys(code)
            driver.find_element(By.ID, "check").click()
            assert "Все обязательные признаки" in driver.find_element(By.ID, "status").text
            assert not driver.find_elements(By.CSS_SELECTOR, ".code-check.fail")

        driver.get(f"{BASE}/labs/seasonality/")
        before = driver.find_element(By.ID, "verdict").text
        driver.find_element(By.CSS_SELECTOR, '[data-stage="year"]').click()
        assert driver.find_element(By.ID, "verdict").text != before
        assert len(driver.find_element(By.ID, "plot").get_attribute("innerHTML")) > 500

        driver.get(f"{BASE}/labs/experiment/")
        before = driver.find_element(By.ID, "decision").text
        driver.find_element(By.CSS_SELECTOR, '[data-i="2"]').click()
        assert driver.find_element(By.ID, "decision").text != before
        assert int(driver.find_element(By.ID, "days").text) > 0
        print("all browser routes: passed")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
