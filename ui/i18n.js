/* ============================================================================
   Перевод интерфейса. Русский по умолчанию, переключатель RU/EN в шапке.
   ============================================================================

   ПОЧЕМУ ТАК, А НЕ ЧЕРЕЗ data-i18n НА КАЖДОМ ЭЛЕМЕНТЕ.
   Разметка — 2200 строк, и половину экранов app.js рисует на лету через
   innerHTML. Расставить атрибуты руками значило бы перелопатить и разметку,
   и генераторы, то есть ровно тот код, который сейчас работает. Вместо
   этого словарь применяется к готовому DOM: обходим текстовые узлы и
   подписи, подменяем ТОЛЬКО точные совпадения из словаря.

   Что это даёт:
     • ноль правок в index.html и app.js;
     • неизвестная строка просто остаётся английской — интерфейс не ломается,
       а словарь можно дополнять по мере надобности;
     • динамика (карточки задач, блоки сценария, строки настроек) переводится
       тем же проходом через MutationObserver.

   ЧЕГО НЕ ТРОГАЕМ. Журнал процесса — это вывод самого макроса, там имена
   юнитов, координаты и названия шаблонов; переводить его нельзя, иначе
   строку не сопоставить с кодом. Плюс всё, что помечено data-no-i18n.

   ОРИГИНАЛЫ хранятся в WeakMap, поэтому переключение обратно на английский
   возвращает ровно исходный текст, а не обратный перевод.
   ========================================================================= */
(function () {
  'use strict';

  // ------------------------------------------------------------------ СЛОВАРЬ
  // Ключ — точный английский текст, как он стоит в разметке.
  const RU = {
    // --- Навигация и шапка ---
    'Dashboard': 'Панель',
    'Task': 'Задачи',
    'Macro Manager': 'Сценарии',
    'Resource': 'Ресурсы',
    'Settings': 'Настройки',
    'Help & FAQ': 'Справка',
    'Session': 'Сессия',
    'All Time': 'Всего',
    'Minimize': 'Свернуть',
    'Close': 'Закрыть',
    'Time this session / all-time total': 'Время за сессию / за всё время',

    // --- Дашборд: состояние ---
    'Status Readout': 'Состояние',
    'Action': 'Действие',
    'Idle': 'Ожидание',
    'Current Task': 'Текущая задача',
    'Repeat': 'Повторов',
    'Map': 'Карта',
    'Last Run': 'Последний забег',
    'Runs / Hour': 'Забегов в час',
    'Time Until Challenge': 'До Challenge',
    'Disabled': 'Выключено',
    '▾ details': '▾ подробнее',
    'Hover for more detail': 'Наведи, чтобы увидеть подробности',
    'Mode': 'Режим',
    'Stage': 'Стадия',
    'Difficulty': 'Сложность',
    'Play Mode': 'Режим игры',
    'Macro': 'Сценарий',

    // --- Дашборд: табло ---
    'Scoreboard': 'Счёт',
    'Wins': 'Победы',
    'Losses': 'Поражения',
    'Win Rate': 'Процент побед',
    'all-time': 'за всё время',
    'lifetime record': 'за всё время',
    '0 total runs': 'забегов нет',
    'Run History': 'История забегов',
    'No runs yet': 'Забегов ещё не было',

    // --- Дашборд: управление ---
    'Controls': 'Управление',
    'Start': 'Старт',
    'Pause': 'Пауза',
    'Stop': 'Стоп',
    'Start Macro': 'Запустить макрос',
    'Stop Macro': 'Остановить макрос',
    'Pause / Resume Macro': 'Пауза / продолжить',
    'Process Log': 'Журнал',
    'Pop Out': 'В окно',
    'Clear': 'Очистить',
    'Clear logs': 'Очистить журнал',
    'Open logs in their own window': 'Открыть журнал отдельным окном',
    'Jump to the newest line': 'К последней строке',
    'new': 'новых',

    // --- Экран ожидания ---
    'Waiting for Roblox': 'Жду Roblox',
    'Launch Roblox': 'Запустить Roblox',
    'Skip': 'Пропустить',
    'Skip Waiting': 'Пропустить ожидание',
    'Use the panel before Roblox docks.': 'Открыть интерфейс, не дожидаясь Roblox.',

    // --- Задачи ---
    'Task Queue': 'Очередь задач',
    'Task Builder': 'Конструктор задачи',
    '+ Add Task': '+ Добавить задачу',
    'Clear All': 'Очистить всё',
    'Solo': 'Один',
    'Matchmaking': 'С игроками',
    'Normal': 'Обычная',
    'Hard': 'Сложная',
    'Infinite': 'Бесконечная',
    'Mastery': 'Мастерство',
    'Import Settings': 'Импорт настроек',
    'Export Settings': 'Экспорт настроек',
    'Import File': 'Импорт из файла',
    'Export File': 'Экспорт в файл',
    'Import Now': 'Импортировать',
    'Preset name': 'Название набора',
    'No saved presets': 'Сохранённых наборов нет',
    'Load...': 'Загрузить…',
    'Save': 'Сохранить',
    'Delete': 'Удалить',
    'New': 'Новый',
    'Map (optional)': 'Карта (необязательно)',

    // --- Сценарии (Macro Manager) ---
    'Macro Operation': 'Сценарий',
    'Current Template': 'Текущий сценарий',
    'Template name': 'Название сценария',
    'All Templates': 'Все сценарии',
    'Single Template': 'Один сценарий',
    'Select Templates': 'Выбрать сценарии',
    'Check templates to share:': 'Отметь, чем поделиться:',
    'Blocks': 'Блоки',
    'Place Unit': 'Поставить юнита',
    'Set Position': 'Задать точку',
    'Keep Placing': 'Ставить до упора',
    'Use Roblox Screen': 'Снимок из игры',
    'Use as region': 'Взять как область',
    'Save Crop': 'Сохранить вырезку',
    '← Maps': '← Карты',
    '← Library': '← Библиотека',
    'Editor': 'Редактор',
    'Save Path': 'Сохранить путь',
    'Path name...': 'Название пути…',
    'Save Recorded Path': 'Сохранить записанный путь',
    'Stop Recording': 'Остановить запись',
    'Test Pre Start': 'Проверить Pre Start',
    'Test Battle': 'Проверить бой',
    'Test Pre Start / Battle': 'Проверить Pre Start / бой',
    'Macro Operation Test': 'Проверка сценария',
    'Run Test Tick': 'Прогнать один тик',
    'Default Auto Walk': 'Ходьба по умолчанию',
    'Test Walking Path': 'Проверить путь',
    'Share Code': 'Код для обмена',
    'Share via Code / Link': 'Поделиться кодом или ссылкой',
    'Import Code / Link': 'Импорт по коду или ссылке',
    'Export Code': 'Экспорт кода',
    'Import Code': 'Импорт кода',
    'Copy Code': 'Скопировать код',
    'Generating code...': 'Готовлю код…',
    'Size: 0 chars': 'Размер: 0 символов',
    'Discard': 'Отменить',
    'No selection': 'Ничего не выбрано',
    'Filter names...': 'Фильтр по названию…',

    // --- Ресурсы ---
    'Auto Challenge': 'Авто-Challenge',
    'Enable Challenge': 'Включить Challenge',
    'Challenge Stage Slots': 'Слоты Challenge',
    'Challenge Story Maps': 'Карты Story для Challenge',
    'Reset Counts Now': 'Сбросить счётчики',
    'Reset Progress': 'Сбросить прогресс',
    'UTC game day:': 'Игровые сутки (UTC):',
    'Auto Bounty': 'Авто-задания',
    'Enable Auto Bounty': 'Включить авто-задания',
    'Auto Crafting': 'Авто-крафт',
    'Enable Auto Crafting': 'Включить авто-крафт',
    'Craft every': 'Крафтить каждые',
    'Choose sprites': 'Выбери спрайты',
    'Sprites to Craft': 'Что крафтить',
    'Wins that count:': 'Какие победы считаются:',
    'victories. Progress:': 'побед. Прогресс:',
    'Test Crafting': 'Проверить крафт',
    'Run Now': 'Запустить сейчас',

    // --- Настройки: разделы ---
    'All': 'Все',
    'General': 'Общее',
    'Hotkeys': 'Горячие клавиши',
    'Keybinds': 'Горячие клавиши',
    'Webhook': 'Webhook',
    'Debug': 'Отладка',
    'Search settings...': 'Поиск…',
    'Reset to Defaults': 'Сбросить к значениям по умолчанию',

    // --- Настройки: общее ---
    'Start Minimized': 'Запускать свёрнутым',
    'Launch minimized to the taskbar.': 'Открываться сразу в панель задач.',
    'Auto-Reopen Roblox': 'Перезапускать Roblox',
    'Macro Speed': 'Скорость макроса',
    'Action Delay': 'Задержка между действиями',
    'Image Search': 'Поиск по картинкам',
    'Image Manager': 'Менеджер картинок',
    'Open Assets Folder': 'Открыть папку Assets',
    'Reload Vision Images': 'Перечитать картинки',
    'Flicker-Free Capture': 'Захват без мерцания',
    'Compact Strip': 'Компактная полоса',
    'Toggle Game Visibility': 'Показать/скрыть игру',
    'Debug Screenshot': 'Снимок для отладки',
    'Back to dashboard (F7)': 'Вернуться на панель (F7)',
    'Switch to/from Dashboard.': 'Переключение на панель и обратно.',
    "Same as the Dashboard's Start button.": 'То же, что кнопка «Старт» на панели.',
    "Same as the Dashboard's Stop button.": 'То же, что кнопка «Стоп» на панели.',
    "Same as the Dashboard's Pause button.": 'То же, что кнопка «Пауза» на панели.',
    'Unbound': 'Не назначено',
    'Not set': 'Не задано',

    // --- Настройки: вебхук ---
    'Webhook URL': 'Ссылка вебхука',
    'Delivery': 'Доставка',
    'Not linked': 'Не подключён',
    'Send Test': 'Отправить тест',
    'Silent Mode': 'Тихий режим',
    'No notification ping.': 'Без звука и упоминания.',
    'Discord User ID': 'Discord ID для пинга',
    'Paste Clipboard': 'Вставить из буфера',

    // --- Настройки: отладка ---
    'Health Check': 'Проверка окружения',
    'Run Health Check': 'Проверить окружение',
    'Diagnostics': 'Диагностика',
    'Export Failure Report': 'Выгрузить отчёт об ошибке',
    'Macro Coordinates': 'Координаты макроса',
    'Reward Reader': 'Чтение наград',
    'Read Rewards': 'Прочитать награды',
    'Game Stats': 'Статистика матча',
    'Read Game Stats': 'Прочитать статистику',
    'Preview Region': 'Показать область',
    'Enter Matchmaking Region': 'Область кнопки матчмейкинга',
    'Roblox Window': 'Окно Roblox',
    'Select Roblox Window': 'Выбрать окно Roblox',
    'Attach Selected Roblox': 'Прикрепить выбранное окно',
    'Un-Attach Roblox': 'Открепить Roblox',
    'Attach': 'Прикрепить',
    'Un-Attach': 'Открепить',
    'Camera Setup': 'Настройка камеры',
    'Camera Mode': 'Режим камеры',
    'Invert Camera Y-Axis': 'Инвертировать ось Y',
    'Force Rejoin': 'Принудительный реджойн',
    'Rejoin Now': 'Перезайти сейчас',
    'Wave Monitor': 'Монитор волн',
    'Open Monitor': 'Открыть монитор',
    'Install Tesseract OCR': 'Установить Tesseract OCR',
    'Install': 'Установить',
    'Pathing': 'Пути ходьбы',
    'Scroll Power': 'Сила прокрутки',
    'Scroll Attempts': 'Попыток прокрутки',
    'Story Map Setup': 'Настройка карт Story',
    'Story Map Search': 'Поиск карты Story',
    'Story Card': 'Карточка Story',
    'Story Stage Rows': 'Строки стадий Story',
    'Raid Act Rows': 'Строки актов Raid',
    'Team Loadout Rows': 'Строки состава',
    'Difficulty Buttons': 'Кнопки сложности',
    'Story maps': 'Карты Story',
    'Neutral Clicks': 'Нейтральные клики',
    'Expedition Wave Check': 'Проверка волны в Expedition',
    'Expedition Camera Zoom': 'Зум камеры в Expedition',
    'Debug Match Screenshots': 'Снимки матча для отладки',
    'Display Scale Warning': 'Предупреждение о масштабе',
    'Capture Roblox': 'Снять кадр из Roblox',
    'Capture': 'Снять',
    'Preview': 'Просмотр',
    'Read': 'Прочитать',
    'Run': 'Запустить',
    'Set': 'Задать',
    'Reset': 'Сбросить',
    'Open': 'Открыть',
    'Open Folder': 'Открыть папку',
    'Pick': 'Выбрать',
    'Retake': 'Переснять',
    'Load': 'Загрузить',
    'Import': 'Импорт',
    'Export': 'Экспорт',
    'Select All': 'Выбрать всё',
    'Row H': 'Высота строки',
    'Width': 'Ширина',
    'Height': 'Высота',
    'Corner': 'Угол',
    'Middle': 'Центр',
    'Vision': 'Зрение',
    'System': 'Система',
    'Input': 'Ввод',
    'Control': 'Управление',
    'Support': 'Поддержка',
    'Discord': 'Discord',
    'GitHub repository': 'репозиторий на GitHub',
    'GitHub Releases': 'релизы на GitHub',
    'Reload': 'Перезагрузить',
    'Got it': 'Понятно',
    'Later': 'Позже',
    'Close': 'Закрыть',
    'Get Started': 'Начать',
    'Paste': 'Вставить',
    'Esc': 'Esc',
    'Live': 'В работе',
    'PRESET': 'НАБОР',
    'Default (Classic)': 'Обычный',
    'Accent': 'Акцент',
    'Background': 'Фон',

    // --- Пустые состояния: должны объяснять, что делать ---
    'No tasks yet -- click "+ Add Task" to queue one.':
      'Задач пока нет. Нажми «+ Добавить задачу», чтобы поставить первую в очередь.',
    'Select a task on the left to edit it.': 'Выбери задачу слева, чтобы настроить её.',
    "Couldn't load Challenge settings.": 'Не удалось прочитать настройки Challenge.',
    "Couldn't load Auto Bounty settings.": 'Не удалось прочитать настройки авто-заданий.',
    'Waiting for macro to start...': 'Жду запуска макроса…',

    // --- Пояснения к настройкам, смысл которых неочевиден ---
    'If Roblox closes or crashes mid-run, reopen the game and pick the run back up automatically -- so an unattended run survives a crash instead of sitting there stopped. Skipped when other Roblox windows are open (reopening would close them). Default on.':
      'Если Roblox вылетит посреди забега — заново открыть игру и продолжить с того же места. Нужно, чтобы ночной прогон пережил вылет, а не встал до утра. Не сработает, если открыты другие окна Roblox: их бы закрыло. По умолчанию включено.',
    'Opens/closes the Image Manager from anywhere -- capture a missing crop the moment a search fails, no digging through Settings.':
      'Открывает менеджер картинок из любого места. Пригодится, когда поиск не нашёл кнопку: можно сразу снять недостающую вырезку, не лазая по настройкам.',
    'Collapse the dashboard to a small always-on-top control bar (and back).':
      'Свернуть интерфейс в узкую полосу поверх всех окон — и обратно.',
    "Same as Settings > Debug > Screenshot's Capture button.":
      'То же, что кнопка «Снять» в разделе «Отладка».',
    'Launch minimized to the taskbar.': 'Открываться сразу свёрнутым в панель задач.',

    // --- Довесок: то, что осталось видно по-английски на экране настроек ---
    'Server Settings > Integrations > Webhooks.': 'Настройки сервера → Интеграции → Вебхуки.',
    'Optional, pings you on results.': 'Необязательно. Будет упоминать тебя в сообщениях о результате.',
    'Open-Source Security & False Positives:': 'Об антивирусах и ложных срабатываниях:',
    'This macro is 100% free and open-source. Heuristic false positives (e.g. 1/70 on VirusTotal) are common for Python PyInstaller executables. You can inspect the entire source code on GitHub anytime.':
      'Макрос бесплатный и с открытым исходным кодом. Единичные срабатывания антивирусов (например, 1 из 70 на VirusTotal) — обычное дело для программ, собранных из Python через PyInstaller. Исходники можно посмотреть на GitHub в любой момент.',
    'Software Updates': 'Обновления',
    'Check GitHub for the latest releases, bug fixes, and feature updates.':
      'Проверять на GitHub новые версии и исправления.',
    'Check for Updates': 'Проверить обновления',
  };

  // Журнал отсекаем ПО ID, а не по классу .rp-log-list: тот же класс носит
  // список истории забегов, который переводить как раз нужно.
  // Подписи рельса уже заданы по-русски в разметке.
  const SKIP_SELECTOR = '#log-list, #rail, [data-no-i18n]';
  const ATTRS = ['placeholder', 'title', 'data-tooltip'];

  let lang = localStorage.getItem('ui_lang') || 'ru';
  const origText = new WeakMap();   // текстовый узел -> исходная строка
  const origAttr = new WeakMap();   // элемент -> { attr: исходная строка }

  const norm = (s) => s.replace(/\s+/g, ' ').trim();

  function translateTextNodes(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        const el = node.parentElement;
        if (!el || el.closest(SKIP_SELECTOR)) return NodeFilter.FILTER_REJECT;
        const tag = el.tagName;
        if (tag === 'SCRIPT' || tag === 'STYLE') return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const nodes = [];
    for (let n = walker.nextNode(); n; n = walker.nextNode()) nodes.push(n);

    for (const node of nodes) {
      if (!origText.has(node)) origText.set(node, node.nodeValue);
      const src = origText.get(node);
      const key = norm(src);
      if (lang === 'ru') {
        const hit = RU[key];
        // Сохраняем окружающие пробелы: во многих местах текст лежит рядом
        // с иконкой, и склеивание без пробела выглядит как опечатка.
        if (hit && node.nodeValue !== hit) {
          const lead = src.match(/^\s*/)[0];
          const tail = src.match(/\s*$/)[0];
          node.nodeValue = lead + hit + tail;
        }
      } else if (node.nodeValue !== src) {
        node.nodeValue = src;
      }
    }
  }

  function translateAttrs(root) {
    const els = root.querySelectorAll('[' + ATTRS.join('],[') + ']');
    for (const el of els) {
      if (el.closest(SKIP_SELECTOR)) continue;
      let saved = origAttr.get(el);
      if (!saved) { saved = {}; origAttr.set(el, saved); }
      for (const a of ATTRS) {
        if (!el.hasAttribute(a)) continue;
        if (!(a in saved)) saved[a] = el.getAttribute(a);
        const src = saved[a];
        if (lang === 'ru') {
          const hit = RU[norm(src)];
          if (hit) el.setAttribute(a, hit);
        } else {
          el.setAttribute(a, src);
        }
      }
    }
  }

  function apply(root) {
    root = root || document.body;
    if (!root || root.nodeType !== 1) return;
    try {
      translateTextNodes(root);
      translateAttrs(root);
    } catch (e) { /* перевод никогда не должен ронять интерфейс */ }
  }

  // Динамика: app.js перерисовывает списки через innerHTML. Догоняем их
  // одним отложенным проходом, а не на каждую вставку узла.
  let pending = null;
  function scheduleApply() {
    if (pending) return;
    pending = requestAnimationFrame(() => { pending = null; apply(document.body); });
  }

  function setLang(next) {
    lang = next;
    localStorage.setItem('ui_lang', lang);
    apply(document.body);
    updateToggle();
  }

  function updateToggle() {
    const btn = document.getElementById('lang-toggle');
    if (btn) {
      btn.textContent = lang === 'ru' ? 'RU' : 'EN';
      btn.setAttribute('title', lang === 'ru'
        ? 'Язык интерфейса: русский. Нажми, чтобы вернуть английский.'
        : 'Interface language: English. Click to switch to Russian.');
    }
  }

  function mountToggle() {
    if (document.getElementById('lang-toggle')) return;
    const badge = document.getElementById('ver-badge');
    if (!badge || !badge.parentElement) return;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'lang-toggle';
    btn.className = 'ver-badge-btn no-drag';
    btn.setAttribute('data-no-i18n', '');   // сам переключатель не переводим
    btn.addEventListener('click', () => setLang(lang === 'ru' ? 'en' : 'ru'));
    badge.parentElement.insertBefore(btn, badge);
    updateToggle();
  }

  function init() {
    mountToggle();
    apply(document.body);
    new MutationObserver(scheduleApply).observe(document.body, {
      childList: true, subtree: true, characterData: true,
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.i18n = { setLang, apply, get lang() { return lang; } };
})();
