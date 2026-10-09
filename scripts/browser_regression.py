#!/usr/bin/env python3
"""Сквозная браузерная проверка девяти шагов практикума."""
from __future__ import annotations

import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

BASE = os.getenv("TRAINER_URL", "http://127.0.0.1:4173")


def main() -> None:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1440,1200")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 12)

    def open_step(number: int, title: str) -> None:
        driver.get(f"{BASE}/?step={number}")
        wait.until(lambda d: title in d.find_element(By.CSS_SELECTOR, ".stage-head h2").text)
        assert len(driver.find_elements(By.CSS_SELECTOR, "#journey button")) == 9

    def click(by: str, value: str) -> None:
        driver.execute_script("arguments[0].click()", driver.find_element(by, value))

    try:
        open_step(1, "Показатель")
        assert "массив" not in driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "учебная форма" in driver.find_element(By.CSS_SELECTOR, ".method").get_attribute("textContent")
        assert not driver.find_elements(By.XPATH, "//button[contains(normalize-space(.), 'Сформировать')]")
        composer = driver.find_element(By.ID, "metric-prompt-composer")
        assert composer.find_element(By.CSS_SELECTOR, ".prompt-open").get_attribute("href") == "https://gosprompt.ru/"
        before = composer.find_element(By.CSS_SELECTOR, ".prompt-preview").text
        driver.execute_script("arguments[0].value = 'код; период; значение'; arguments[0].dispatchEvent(new Event('input', {bubbles:true}))", driver.find_element(By.ID, "metric-fields"))
        assert composer.find_element(By.CSS_SELECTOR, ".prompt-preview").text != before
        assert composer.find_elements(By.CSS_SELECTOR, ".prompt-value")
        click(By.CSS_SELECTOR, "#metric-prompt-composer [data-prompt-mode='template']")
        assert composer.find_elements(By.CSS_SELECTOR, ".prompt-variable")
        click(By.CSS_SELECTOR, "#metric-prompt-composer [data-prompt-mode='filled']")
        click(By.ID, "metric-example")
        click(By.ID, "metric-check")
        assert "Структура принята" in driver.find_element(By.ID, "metric-status").text
        assert "числитель" in driver.find_element(By.ID, "metric-artifact").text.lower()

        open_step(2, "Календарный месяц")
        click(By.CSS_SELECTOR, '[data-period="day"]')
        assert "рабочий день" in driver.find_element(By.ID, "period-thesis").text
        assert driver.find_elements(By.CSS_SELECTOR, "#period-chart polyline")
        assert "Месяц" in driver.find_element(By.CSS_SELECTOR, "#period-chart svg").text
        assert "Как выполняется пересчёт" in driver.find_element(By.CSS_SELECTOR, ".method").get_attribute("textContent")

        open_step(3, "Повторяющиеся циклы")
        for stage in range(5):
            click(By.CSS_SELECTOR, f'[data-season="{stage}"]')
            assert driver.find_elements(By.CSS_SELECTOR, ".chart polyline")
        assert "снизился на 16%" in driver.find_element(By.CSS_SELECTOR, ".thesis").text
        assert "Дата наблюдения" in driver.find_element(By.CSS_SELECTOR, ".chart").text
        assert "Как разделены" in driver.find_element(By.CSS_SELECTOR, ".method").get_attribute("textContent")

        open_step(4, "Прогноз проверяется")
        frame = driver.find_element(By.CSS_SELECTOR, "iframe.forecast-frame")
        assert frame.get_attribute("src") == "https://wybaeb.github.io/data-literacy-forecast-lab/"

        open_step(5, "случайного разброса")
        click(By.CSS_SELECTOR, '[data-experiment="2"]')
        first = driver.find_element(By.CSS_SELECTOR, ".ci-point").get_attribute("style")
        click(By.CSS_SELECTOR, '[data-exp-days="15"]')
        assert driver.find_element(By.CSS_SELECTOR, ".ci-point").get_attribute("style") != first
        assert "1.8 п.п." in driver.find_element(By.CSS_SELECTOR, ".metric-row").text
        assert "-1.4…+5.1" in driver.find_element(By.CSS_SELECTOR, ".panel").text
        assert "День эксперимента" in driver.find_element(By.CSS_SELECTOR, ".chart").text
        assert "Как читать доверительный интервал" in driver.find_element(By.CSS_SELECTOR, ".method").get_attribute("textContent")

        open_step(6, "Большой набор")
        for mode in ("excel", "sheets"):
            click(By.CSS_SELECTOR, f'[data-auto="{mode}"]')
            click(By.ID, "auto-reference")
            wait.until(lambda d: "Все обязательные признаки" in d.find_element(By.ID, "auto-status").text)
            assert not driver.find_elements(By.CSS_SELECTOR, ".check.fail")
        assert len(driver.find_elements(By.CSS_SELECTOR, 'a[download]')) == 2

        open_step(7, "утверждает маршрут")
        driver.execute_script(
            "arguments[0].value = arguments[1]",
            driver.find_element(By.ID, "class-response"),
            '{"items":[{"id":"EDU-1","category":"иное","confidence":0.5}],"escalation":[{"condition":"x","route":"y"}]}',
        )
        click(By.ID, "class-build")
        assert "items[0].reason" in driver.find_element(By.ID, "class-status").text
        click(By.ID, "class-example")
        driver.execute_script("arguments[0].value += '\\nПояснение после JSON {}'", driver.find_element(By.ID, "class-response"))
        click(By.ID, "class-build")
        assert "Матрица построена" in driver.find_element(By.ID, "class-status").text
        assert "проверка сотрудником" in driver.find_element(By.ID, "class-artifact").text

        open_step(8, "Безопасность")
        click(By.ID, "safe-example")
        click(By.ID, "safe-build")
        assert "Матрица сформирована" in driver.find_element(By.ID, "safe-status").text
        assert "Стоп" in driver.find_element(By.ID, "safe-artifact").text

        open_step(9, "презентацию защиты")
        click(By.ID, "pilot-example")
        click(By.ID, "pilot-build")
        assert "Презентация сформирована" in driver.find_element(By.ID, "pilot-status").text
        assert len(driver.find_elements(By.CSS_SELECTOR, ".slide-card")) == 6

        severe = [entry for entry in driver.get_log("browser") if entry["level"] == "SEVERE"]
        assert not severe, severe
        print("9 sequential steps: passed")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
