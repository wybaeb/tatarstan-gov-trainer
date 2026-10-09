(function () {
  const registry = new Map();

  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  }[char]));

  const copyIcon = '<svg viewBox="0 0 20 20" aria-hidden="true"><rect x="7" y="3" width="10" height="12" rx="2"></rect><path d="M13 17H5a2 2 0 0 1-2-2V7"></path></svg>';
  const arrowIcon = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M7 4h9v9"></path><path d="M16 4 8 12"></path><path d="M12 16H4V8"></path></svg>';

  function valueOf(field) {
    if (typeof field.value === 'function') return field.value();
    const control = field.elementId && document.getElementById(field.elementId);
    return control ? control.value : (field.value ?? '');
  }

  function plainText(config, mode) {
    let text = config.template;
    config.fields.forEach((field) => {
      const value = mode === 'template' ? `[${field.label}]` : valueOf(field);
      text = text.split(`[[${field.key}]]`).join(value || `[${field.label}]`);
    });
    return text;
  }

  function richText(config, mode) {
    let text = escapeHtml(config.template);
    config.fields.forEach((field) => {
      const raw = mode === 'template' ? `[${field.label}]` : valueOf(field);
      const missing = !raw;
      const value = raw || `[${field.label}]`;
      const css = mode === 'template' || missing ? 'prompt-variable' : 'prompt-value';
      text = text.split(`[[${field.key}]]`).join(`<mark class="${css}">${escapeHtml(value)}</mark>`);
    });
    return text;
  }

  function markup(config) {
    registry.set(config.id, { ...config, mode: config.mode || 'filled' });
    return `<section class="prompt-composer" id="${config.id}" aria-label="${escapeHtml(config.title || 'Подготовленный запрос')}">
      <header class="prompt-toolbar">
        <div>
          <span class="prompt-eyebrow">${escapeHtml(config.eyebrow || 'Запрос к ИИ')}</span>
          <strong>${escapeHtml(config.title || 'Подготовленный запрос')}</strong>
        </div>
        <div class="prompt-toolbar-actions">
          <div class="segmented" role="group" aria-label="Вид запроса">
            <button type="button" data-prompt-mode="filled" class="active">С заполнением</button>
            <button type="button" data-prompt-mode="template">Шаблон</button>
          </div>
          <button type="button" class="icon-button prompt-copy" aria-label="Скопировать запрос" title="Скопировать запрос">${copyIcon}</button>
        </div>
      </header>
      <pre class="prompt-preview" data-prompt-preview></pre>
      <footer class="prompt-footer">
        <span class="prompt-legend"><i></i><span data-prompt-legend>Выделено то, что подставлено из полей</span></span>
        <div class="prompt-footer-actions">
          <button type="button" class="button secondary prompt-copy">${copyIcon}<span>Скопировать</span></button>
          <a class="button prompt-open" href="${escapeHtml(config.openUrl || 'https://gosprompt.ru/') }" target="_blank" rel="noopener">Открыть ГосПромпт ${arrowIcon}</a>
        </div>
      </footer>
      <div class="status prompt-status" aria-live="polite"></div>
    </section>`;
  }

  function bind(id) {
    const root = document.getElementById(id);
    const config = registry.get(id);
    if (!root || !config) return;

    const render = () => {
      root.querySelector('[data-prompt-preview]').innerHTML = richText(config, config.mode);
      root.querySelector('[data-prompt-legend]').textContent = config.mode === 'template'
        ? 'Выделены места, которые нужно заменить'
        : 'Выделено то, что подставлено из полей';
      root.querySelectorAll('[data-prompt-mode]').forEach((button) => {
        button.classList.toggle('active', button.dataset.promptMode === config.mode);
      });
    };

    root.querySelectorAll('[data-prompt-mode]').forEach((button) => {
      button.addEventListener('click', () => {
        config.mode = button.dataset.promptMode;
        render();
      });
    });

    root.querySelectorAll('.prompt-copy').forEach((button) => {
      button.addEventListener('click', async () => {
        const status = root.querySelector('.prompt-status');
        try {
          await navigator.clipboard.writeText(plainText(config, config.mode));
          status.textContent = 'Запрос скопирован';
          status.className = 'status prompt-status ok';
        } catch (_) {
          status.textContent = 'Не удалось скопировать автоматически. Выделите текст запроса.';
          status.className = 'status prompt-status bad';
        }
      });
    });

    config.fields.forEach((field) => {
      const controls = field.selector
        ? document.querySelectorAll(field.selector)
        : [field.elementId && document.getElementById(field.elementId)].filter(Boolean);
      controls.forEach((control) => {
        control.addEventListener('input', render);
        control.addEventListener('change', render);
      });
    });
    render();
  }

  window.PromptComposer = { markup, bind, text: (id) => {
    const config = registry.get(id);
    return config ? plainText(config, config.mode) : '';
  } };
}());
