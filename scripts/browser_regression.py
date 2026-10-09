#!/usr/bin/env python3
"""Сквозная браузерная проверка девяти шагов практикума."""
from __future__ import annotations

import base64
import io
import json
import os
import tempfile
from pathlib import Path

from pypdf import PdfReader
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
        trend_directions = []
        for stage in range(4):
            click(By.CSS_SELECTOR, f'[data-season="{stage}"]')
            assert driver.find_elements(By.CSS_SELECTOR, ".chart polyline")
            trend_directions.append("up" if driver.find_elements(By.CSS_SELECTOR, ".trend-result.up") else "down")
        assert trend_directions == ["up", "down", "up", "down"]
        assert "итоговый слабый спад" in driver.find_element(By.CSS_SELECTOR, ".thesis").text
        assert "Дата наблюдения" in driver.find_element(By.CSS_SELECTOR, ".chart").text
        assert "Как устроен учебный расчёт" in driver.find_element(By.CSS_SELECTOR, ".method").get_attribute("textContent")

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

        open_step(8, "Расчёт начинается")
        assert driver.find_element(By.CSS_SELECTOR, '[data-excel-locale="ru"]').get_attribute("class") == "active"
        formula_download = driver.find_element(By.CSS_SELECTOR, 'a[download]').get_attribute("href")
        assert formula_download.endswith("uchebny_nabor_formuly_excel.xlsm")
        prompt = driver.find_element(By.CSS_SELECTOR, "#auto-prompt-composer .prompt-preview").get_attribute("textContent")
        assert "разделитель аргументов — «;»" in prompt
        assert "десятичный знак — «,»" in prompt
        click(By.ID, "auto-reference")
        wait.until(lambda d: "Все обязательные признаки" in d.find_element(By.ID, "auto-status").text)
        assert ";" in driver.find_element(By.ID, "auto-code").get_attribute("value")
        assert not driver.find_elements(By.CSS_SELECTOR, ".check.fail")

        click(By.CSS_SELECTOR, '[data-excel-locale="international"]')
        prompt = driver.find_element(By.CSS_SELECTOR, "#auto-prompt-composer .prompt-preview").get_attribute("textContent")
        assert "разделитель аргументов — «,»" in prompt
        assert "десятичный знак — «.»" in prompt
        click(By.ID, "auto-reference")
        wait.until(lambda d: "Все обязательные признаки" in d.find_element(By.ID, "auto-status").text)
        assert "," in driver.find_element(By.ID, "auto-code").get_attribute("value")
        assert not driver.find_elements(By.CSS_SELECTOR, ".check.fail")

        click(By.CSS_SELECTOR, '[data-excel-locale="ru"]')
        for mode in ("formula", "excel", "sheets"):
            click(By.CSS_SELECTOR, f'[data-auto="{mode}"]')
            click(By.ID, "auto-reference")
            wait.until(lambda d: "Все обязательные признаки" in d.find_element(By.ID, "auto-status").text)
            assert not driver.find_elements(By.CSS_SELECTOR, ".check.fail")
        assert len(driver.find_elements(By.CSS_SELECTOR, 'a[download]')) == 2
        click(By.CSS_SELECTOR, '[data-auto="excel"]')
        assert driver.find_element(By.CSS_SELECTOR, 'a[download]').get_attribute("href").endswith(".xlsm")
        assert not driver.find_elements(By.CSS_SELECTOR, 'a[href$=".xlsx"]')

        open_step(6, "утверждает маршрут")
        driver.execute_script(
            "arguments[0].value = arguments[1]",
            driver.find_element(By.ID, "class-response"),
            '{"items":[{"id":"EDU-1","category":"иное","confidence":0.5}],"escalation":[{"condition":"x","route":"y"}]}',
        )
        click(By.ID, "class-build")
        assert "items[0].reason" in driver.find_element(By.ID, "class-status").text
        driver.execute_script(
            "arguments[0].value = arguments[1]",
            driver.find_element(By.ID, "class-response"),
            '{"items":[{"id":"EDU-001","category":"иное","confidence":0.5,"reason":"недостаточно данных",},{"id":"EDU-002","category":"благоустройство","confidence":0.9,"reason":"состояние объекта",},{"id":"EDU-003","category":"транспортная доступность","confidence":0.8,"reason":"маршрут",}],"escalation":[{"condition":"x","route":"y",}],}',
        )
        click(By.ID, "class-build")
        assert "Матрица построена" in driver.find_element(By.ID, "class-status").text
        click(By.ID, "class-example")
        driver.execute_script("arguments[0].value += '\\nПояснение после JSON {}'", driver.find_element(By.ID, "class-response"))
        click(By.ID, "class-build")
        assert "Матрица построена" in driver.find_element(By.ID, "class-status").text
        assert "проверка сотрудником" in driver.find_element(By.ID, "class-artifact").text

        open_step(7, "Сначала распознайте")
        driver.find_element(By.ID, "safe-response").send_keys("Ответ без таблицы")
        click(By.ID, "safe-build")
        assert "Не найдена таблица" in driver.find_element(By.ID, "safe-status").text
        legacy_answer = """| Уровень | Категория сведений | Значимость | Допустимый контур | Передача | Хранение | Решение | Нормативное основание |
|---|---|---|---|---|---|---|---|
| Государственная тайна | Сведения, отнесённые к гостайне | Высшая | Специализированный защищённый контур | Запрещена без санкции | По режиму гостайны | Уполномоченное подразделение | Закон РФ № 5485-1 |

**НЕ ДЕЛАТЬ**
- Вводить в сервис фрагменты закрытых сведений

**СДЕЛАТЬ**
- Обратиться в режимно-секретный орган

**ВОПРОСЫ СПЕЦИАЛИСТУ**
- Какой уровень защиты требуется?"""
        driver.execute_script("arguments[0].value = arguments[1]", driver.find_element(By.ID, "safe-response"), legacy_answer)
        click(By.ID, "safe-build")
        assert "Предварительное заключение извлечено" in driver.find_element(By.ID, "safe-status").text
        assert not driver.find_elements(By.ID, "safe-level")
        assert driver.find_element(By.ID, "safe-situation").is_displayed()
        assert "Сравнить цены" in driver.find_element(By.CSS_SELECTOR, ".scenario-tabs").text
        expected_tones = {"price": "green", "birthday": "amber", "appeal": "amber", "health": "red", "memo": "red", "secret": "red"}
        for scenario, tone in expected_tones.items():
            click(By.CSS_SELECTOR, f'[data-security="{scenario}"]')
            click(By.ID, "safe-example")
            click(By.ID, "safe-build")
            assert "Предварительное заключение извлечено" in driver.find_element(By.ID, "safe-status").text
            assert driver.find_elements(By.CSS_SELECTOR, f".security-card.{tone}")
            artifact_text = driver.find_element(By.ID, "safe-artifact").text
            assert "Не делать" in artifact_text and "Сделать" in artifact_text
            assert "Вопросы уполномоченному специалисту" in artifact_text
            assert "Можно продолжить" in artifact_text
            assert "Только при выполнении условий" in artifact_text
            assert "Остановиться и согласовать" in artifact_text
            assert "Передача" in artifact_text
        assert len(driver.find_elements(By.CSS_SELECTOR, ".route-legend > div")) == 3
        assert "обучающими примерами" in driver.find_element(By.CSS_SELECTOR, ".safety-note").text

        open_step(9, "презентацию защиты")
        click(By.ID, "pilot-example")
        click(By.ID, "pilot-build")
        assert "интерактивная HTML-презентация сформированы" in driver.find_element(By.ID, "pilot-status").text
        assert "Вопросы к подрядчику" in driver.find_element(By.ID, "pilot-artifact").text
        assert "Стоп-условия" in driver.find_element(By.ID, "pilot-artifact").text
        assert len(driver.find_elements(By.CSS_SELECTOR, ".slide-card")) == 6
        assert len(driver.find_elements(By.CSS_SELECTOR, ".slide-card.active")) == 1
        assert driver.find_element(By.ID, "pilot-slide-counter").text == "1 / 6"
        click(By.ID, "pilot-slide-next")
        assert driver.find_element(By.ID, "pilot-slide-counter").text == "2 / 6"
        driver.find_element(By.ID, "pilot-slider").send_keys("\ue014")
        assert driver.find_element(By.ID, "pilot-slide-counter").text == "3 / 6"
        download = driver.find_element(By.ID, "pilot-download")
        assert download.get_attribute("href").startswith("blob:")
        assert download.get_attribute("download") == "pasport_pilota_presentation.html"
        pilot_sections = driver.find_elements(By.CSS_SELECTOR, ".pilot-flow > section")
        assert len(pilot_sections) == 2
        assert abs(pilot_sections[0].rect["x"] - pilot_sections[1].rect["x"]) < 2
        assert abs(pilot_sections[0].rect["width"] - pilot_sections[1].rect["width"]) < 2
        assert len(driver.find_elements(By.CSS_SELECTOR, ".pilot-fields > .field")) == 5
        assert driver.execute_script("return document.documentElement.scrollWidth <= document.documentElement.clientWidth")

        driver.set_window_size(820, 1100)
        driver.get(f"{BASE}/?step=9")
        wait.until(lambda d: d.find_element(By.CSS_SELECTOR, ".pilot-fields"))
        click(By.ID, "pilot-example")
        click(By.ID, "pilot-build")
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".slide-card")) == 6)
        assert driver.execute_script("return document.documentElement.scrollWidth <= document.documentElement.clientWidth")
        field_widths = [item.rect["width"] for item in driver.find_elements(By.CSS_SELECTOR, ".pilot-fields > .field")]
        assert max(field_widths) - min(field_widths) < 2
        panel_right = driver.find_element(By.CSS_SELECTOR, ".pilot-output").rect["x"] + driver.find_element(By.CSS_SELECTOR, ".pilot-output").rect["width"]
        assert all(card.rect["x"] + card.rect["width"] <= panel_right for card in driver.find_elements(By.CSS_SELECTOR, ".slide-card"))

        assert len(driver.find_elements(By.CSS_SELECTOR, ".journey small")) == 9
        assert len(driver.find_elements(By.CSS_SELECTOR, ".site-footer a")) >= 8

        pilot_data = json.loads(driver.find_element(By.ID, "pilot-response").get_attribute("value"))
        presentation_html = driver.execute_script("return buildPilotPresentationHtml(arguments[0])", pilot_data["slides"])
        assert "@page{size:A4 landscape" in presentation_html
        assert "@media print" in presentation_html
        assert "break-after:page" in presentation_html
        assert presentation_html.count('<section class="slide') == 6
        with tempfile.TemporaryDirectory() as temp_dir:
            presentation_path = Path(temp_dir) / "presentation.html"
            presentation_path.write_text(presentation_html, encoding="utf-8")
            driver.set_window_size(1280, 900)
            driver.get(presentation_path.as_uri())
            wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".slide")) == 6)
            assert len(driver.find_elements(By.CSS_SELECTOR, ".slide.active")) == 1
            click(By.ID, "next")
            assert driver.find_element(By.ID, "counter").text == "2 / 6"
            driver.find_element(By.ID, "deck").send_keys("\ue014")
            assert driver.find_element(By.ID, "counter").text == "3 / 6"
            driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"media": "print"})
            assert all(driver.execute_script("return getComputedStyle(arguments[0]).display", slide) == "flex" for slide in driver.find_elements(By.CSS_SELECTOR, ".slide"))
            assert driver.execute_script("return getComputedStyle(arguments[0]).backgroundColor", driver.find_element(By.CSS_SELECTOR, ".slide")) == "rgb(255, 255, 255)"
            assert driver.execute_script("return getComputedStyle(arguments[0]).color", driver.find_element(By.CSS_SELECTOR, ".slide")) == "rgb(0, 0, 0)"
            assert driver.execute_script("return getComputedStyle(arguments[0]).breakAfter", driver.find_element(By.CSS_SELECTOR, ".slide")) == "page"
            pdf_result = driver.execute_cdp_cmd("Page.printToPDF", {"preferCSSPageSize": True, "printBackground": True})
            pdf = PdfReader(io.BytesIO(base64.b64decode(pdf_result["data"])))
            assert len(pdf.pages) == 6
            assert all(float(page.mediabox.width) > float(page.mediabox.height) for page in pdf.pages)
            driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"media": "screen"})

        severe = [entry for entry in driver.get_log("browser") if entry["level"] == "SEVERE"]
        assert not severe, severe
        print("9 sequential steps: passed")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
