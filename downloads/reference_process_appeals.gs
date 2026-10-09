/** Эталон преподавателя. Выполняйте на копии обезличенной учебной таблицы. */
function processTrainingAppeals() {
  const book = SpreadsheetApp.getActive();
  const source = book.getSheetByName('Выгрузка');
  const data = source.getDataRange().getValues();
  const output = [[...data[0], 'Длительность, дней', 'Соблюдение срока']];
  const seen = new Set();

  for (let i = 1; i < data.length; i++) {
    const raw = data[i];
    const key = raw.map(v => `${String(v).length}:${String(v)}`).join('|');
    if (!String(raw[0]).trim() || seen.has(key)) continue;
    seen.add(key);
    const row = [...raw];
    const registered = parseTrainingDate_(raw[1]);
    const completed = parseTrainingDate_(raw[2]);
    row[1] = registered || '';
    row[2] = completed || '';
    row[3] = normalizeTrainingChannel_(raw[3]);
    const duration = registered && completed ? Math.round((completed - registered) / 86400000) : '';
    row.push(duration, duration !== '' && duration <= Number(raw[6]) ? 1 : 0);
    output.push(row);
  }

  source.clearContents();
  source.getRange(1, 1, output.length, output[0].length).setValues(output);
  source.getRange(2, 2, output.length - 1, 2).setNumberFormat('dd.mm.yyyy');

  let summary = book.getSheetByName('Сводка');
  if (summary) book.deleteSheet(summary);
  summary = book.insertSheet('Сводка');
  const rows = buildSummary_(output, 3, 'Канал');
  const categories = buildSummary_(output, 4, 'Категория');
  summary.getRange(1, 1, rows.length, 4).setValues(rows);
  summary.getRange(rows.length + 3, 1, categories.length, 4).setValues(categories);
  summary.getRange(2, 4, rows.length - 1, 1).setNumberFormat('0.0%');
  summary.insertChart(summary.newChart().asColumnChart()
    .addRange(summary.getRange(1, 1, rows.length, 1))
    .addRange(summary.getRange(1, 4, rows.length, 1))
    .setOption('title', 'Доля завершённых в срок по каналам')
    .setPosition(1, 6, 0, 0).build());
}

function parseTrainingDate_(value) {
  if (value instanceof Date) return value;
  const text = String(value || '').trim();
  if (!text || text.toLowerCase() === 'н/д') return null;
  const parts = text.includes('.') ? text.split('.') : text.split('-');
  if (parts.length !== 3) return null;
  return text.includes('.')
    ? new Date(Number(parts[2]), Number(parts[1]) - 1, Number(parts[0]))
    : new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
}

function normalizeTrainingChannel_(value) {
  const text = String(value || '').trim().toLowerCase().replaceAll('ё', 'е');
  if (text.includes('портал')) return 'Портал';
  if (text === 'кц' || text.includes('контакт') || text.includes('горяч')) return 'Контакт-центр';
  if (text.includes('пись') || text.includes('почт')) return 'Письменное обращение';
  if (text.includes('прием') || text.includes('очн')) return 'Личный приём';
  return 'Требуется уточнение';
}

function buildSummary_(data, column, title) {
  const groups = new Map();
  data.slice(1).forEach(row => {
    const key = String(row[column]);
    const value = groups.get(key) || {total: 0, completed: 0, onTime: 0};
    value.total++;
    if (String(row[5]).toLowerCase() === 'завершено') value.completed++;
    value.onTime += Number(row[10]) || 0;
    groups.set(key, value);
  });
  return [[title, 'Обращений', 'Завершено', 'Доля в срок'], ...[...groups].map(([key, v]) => [key, v.total, v.completed, v.onTime / v.total])];
}
