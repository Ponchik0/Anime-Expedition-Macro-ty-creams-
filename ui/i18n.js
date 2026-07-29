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
    'Record': 'Запись',
    'Start/stop recording your own play. Press it while you are IN the game -- that is the point: the macro then repeats exactly what you did.':
      'Начать и остановить запись своей игры. Жать надо, НАХОДЯСЬ В ИГРЕ — в этом весь смысл: макрос потом повторит ровно то, что ты сделал.',
    'Проверка связи': 'Проверка связи',

    // === ДОБИВКА ПЕРЕВОДА ==============================================
    // Собрано сверкой разметки со словарём: что видно на экранах, но
    // оставалось английским. Длинные описания в глубине «Отладки» пока
    // не тронуты — ими пользуются редко, а переводить их наспех хуже,
    // чем оставить как есть.
    '> Waiting for macro to start...': '> Жду запуска макроса…',
    'Anime Expeditions': 'Anime Expeditions',
    '1 item': '1 элемент',
    'Camera': 'Камера',
    'Challenge': 'Challenge',
    'Camera Setup 2': 'Настройка камеры 2',
    'Camera Setup 3': 'Настройка камеры 3',
    'Assign a Macro Operation to each Story map the challenge can land on.': 'Назначь сценарий каждой карте Story, на которую может выпасть Challenge.',
    'Assign the Macro Operation Auto Bounty should use for each Story destination.': 'Назначь сценарий, которым авто-задания будут играть каждую карту Story.',
    'After every N qualifying wins, leaves to the Crafting area, crafts your chosen sprites, then returns and carries on.': 'После каждых N подходящих побед уходит в зону крафта, крафтит выбранные спрайты и возвращается к делу.',
    'Checks the Event Bounty Board before Challenge and runs supported Clear Wave or Hard objectives.': 'Смотрит доску заданий перед Challenge и выполняет те цели, которые умеет: Clear Wave и Hard.',
    '. Counts reset at 00:00 UTC without restarting the macro.': '. Счётчики обнуляются в 00:00 UTC, перезапускать макрос не нужно.',
    'Captures Roblox, saves it to the debug folder.': 'Снимает кадр из Roblox и кладёт в папку debug.',
    'Captures the region above and logs each item. Pick a stage below to test against its known rewards.': 'Снимает область выше и пишет каждый предмет в журнал. Выбери стадию ниже, чтобы сверить с её наградами.',
    'Captures the region above and logs the four values.': 'Снимает область выше и пишет в журнал четыре значения.',
    'Choose the Roblox window to use manually. Nothing attaches automatically.': 'Выбрать окно Roblox вручную. Автоматически ничего не прикрепляется.',
    'Detach the currently docked Roblox window from the macro window.': 'Открепить окно Roblox от окна макроса.',
    'Click points for the 3 Regular Challenge stage rows.': 'Точки клика для трёх строк стадий Regular Challenge.',
    'Click points on the stage-detail panel\'s Normal/Hard toggle.': 'Точки клика по переключателю Normal/Hard на панели стадии.',
    'Detect the wave Continue/Extract buttons by their color instead of image search -- much faster and immune to art changes.': 'Определять кнопки Continue и Extract по цвету, а не поиском картинки — заметно быстрее и не ломается от смены оформления.',
    'Bundles the latest debug screenshots, log tail, settings (webhook redacted) and a health check into one zip you can attach to a bug report.': 'Собирает в один архив свежие снимки, хвост журнала, настройки (ссылка вебхука вырезана) и проверку окружения — удобно приложить к сообщению об ошибке.',
    'Browse every image the macro searches for, and capture new ones from your Roblox screen -- add a crop whenever a search fails.': 'Показывает все картинки, которые макрос ищет, и позволяет снять новые со своего экрана. Не нашлась кнопка — добавь свою вырезку.',
    'A one-time checklist -- these are the things that cause almost every "it doesn\'t work". You can reopen it any time.': 'Список на один раз: здесь то, из-за чего почти всегда и бывает «не работает». Открыть заново можно в любой момент.',
    'Dark, Black, Slate, Light, Space, Semi Gold, Semi Silver, or Liquid Glass.': 'Тема в этой сборке одна и подобрана целиком.',
    'Click to check for updates': 'Версия макроса',
    'Load tasks (and their macros) from a shared .json file': 'Загрузить задачи и их сценарии из файла .json',
    'Save this queue + its macros to a .json file to back up or share': 'Сохранить очередь и сценарии в файл .json',
    'Saved task queues on this machine': 'Сохранённые очереди на этом компьютере',
    'Replace the queue above with the selected preset': 'Заменить очередь выбранным набором',
    'Save the current queue under the name on the left': 'Сохранить текущую очередь под именем слева',
    'Delete the selected preset': 'Удалить выбранный набор',
    'Open the folder these presets are saved in': 'Открыть папку с наборами',
    'Clear the editor and start a new template': 'Очистить редактор и начать новый сценарий',
    'Delete the loaded template': 'Удалить загруженный сценарий',
    'Load templates from a shared .json file': 'Загрузить сценарии из файла .json',
    'Save every template to a .json file to back up or share': 'Сохранить все сценарии в файл .json',
    'Jump to the newest line': 'К последней строке',
    'Open logs in their own window': 'Открыть журнал отдельным окном',
    'Clear logs': 'Очистить журнал',

    // --- Проверка эталонов ---
    'Template Check': 'Проверка эталонов',
    'Scores every reference image against what is on screen RIGHT NOW. Catches the buttons that almost match but miss the threshold -- the ones that stall a run at 3am. Open a game screen, press Run, read the Process Log. Read-only: no clicks, safe while the macro runs.':
      'Сравнивает все эталонные картинки с тем, что на экране ПРЯМО СЕЙЧАС, и показывает счёт каждой. Ловит кнопки, которые почти совпадают, но не берут порог, — именно они роняют прогон ночью. Открой нужный экран игры, нажми «Запустить» и смотри журнал. Только чтение: ни одного клика, можно запускать во время работы макроса.',

    // === СПРАВКА (модалка «Справка») ===================================
    'Help & Troubleshooting FAQ': 'Справка и решение проблем',
    'Is this macro safe? Why does VirusTotal show 1 virus detection?': 'Безопасен ли макрос? Почему VirusTotal показывает одно срабатывание?',
    'Yes, the macro is safe and open-source.': 'Да, макрос безопасен, исходники открыты.',
    // Текст поменялся, когда убирали ссылку на репозиторий автора —
    // ключ обновлён под новую формулировку.
    'PyInstaller executables often trigger false positives in basic antivirus scans. The whole thing is open source and can be run straight from source.': 'Программы, собранные из Python через PyInstaller, регулярно вызывают ложные срабатывания у антивирусов — это известная особенность самого способа сборки, а не признак вредоноса. Весь код открыт и его можно запускать прямо из исходников.',
    'How do I farm Raid Act 3 or Act 2 instead of Act 1?': 'Как фармить Raid Act 3 или Act 2 вместо Act 1?',
    '1. Open the': '1. Открой вкладку',
    'tab in the top menu.': 'в навигации справа.',
    '2. Add a task and set': '2. Добавь задачу и поставь',
    'Mode': 'Режим',
    '3. In the': '3. В списке',
    'Stage': 'Стадия',
    'dropdown, choose': 'выбери',
    '(Act 3) or': '(Act 3) или',
    '(Act 2).': '(Act 2).',
    '4. Pick': '4. Выбери',
    'under Play Mode.': 'в поле «Режим игры».',
    'Why does the macro stay on the same version after updating?': 'Почему после обновления остаётся старая версия?',
    'A running background process might lock the executable file from being overwritten.': 'Запущенный в фоне процесс держит файл занятым, и перезаписать его не выходит.',
    'Fix:': 'Решение:',
    'Close all macro processes in Task Manager, or unpack a fresh copy of the macro into a new folder.': 'Закрой все процессы макроса в диспетчере задач или распакуй свежую копию в новую папку.',
    'Why does Image Manager show a black screen or background only?': 'Почему в менеджере картинок чёрный экран или один фон?',
    'This happens when Windows Display Scaling is above 100% or GPU settings interfere with screen captures.': 'Так бывает, когда масштаб экрана в Windows выше 100% или настройки видеокарты мешают захвату кадра.',
    '1. Open': '1. Открой',
    'Settings > Capture': 'Настройки → Отладка',
    'in the macro.': 'в макросе.',
    '2. Turn on': '2. Включи',
    'Hardware Capture Fix (Windows.Graphics.Capture)': 'Захват через Windows.Graphics.Capture',
    'and restart the macro.': 'и перезапусти макрос.',
    '3. Set Roblox to Windowed Mode instead of Fullscreen.': '3. Переведи Roblox в оконный режим вместо полноэкранного.',
    'Why is the camera pointing UP instead of DOWN?': 'Почему камера смотрит ВВЕРХ, а не вниз?',
    'Inverted camera controls in Roblox cause this behavior.': 'Причина — инверсия камеры в настройках самого Roblox.',
    'Open Roblox settings (': 'Открой настройки Roblox (',
    '), turn off': '), выключи',
    'Invert Camera Y-Axis': 'Invert Camera Y-Axis',
    ', and set': ', а',
    'Camera Mode': 'Camera Mode',
    'Default (Classic)': 'поставь Default (Classic)',
    'Why are units failing to place or being removed?': 'Почему юниты не ставятся или пропадают?',
    'Defense nodes in Expeditions clear placed phantom units by design.': 'В Expedition точки защиты сами убирают «фантомных» юнитов — так задумано игрой.',
    'For standard stages, open': 'На обычных стадиях открой',
    ', select your': ', выбери свой блок',
    'block, and enable': 'и включи',
    'to retry placement automatically until confirmed.': '— тогда макрос будет переставлять юнита, пока установка не подтвердится.',

    // --- Приватный сервер ---
    'Private Server': 'Приватный сервер',
    'Paste a VIP / private server link and the macro will join it instead of the public lobby. Leave it empty to use the public lobby. Stored only on this PC.':
      'Вставь ссылку на VIP или приватный сервер — макрос будет заходить туда, а не в общее лобби. Оставишь пустым — пойдёт в общее лобби, как раньше. Ссылка хранится только на этом компьютере и никуда не отправляется.',

    // === ЭКРАН СЦЕНАРИЕВ ==================================================
    // Самый непонятный экран приложения. Сценарий — это список действий,
    // которые макрос делает в матче: кого поставить, когда апгрейдить,
    // чего дождаться. Он собирается перетаскиванием блоков слева в одну из
    // четырёх фаз справа. Переведено всё, включая подсказки в пустых фазах:
    // именно они объясняют, чем фазы отличаются друг от друга.

    // --- группы блоков в палитре ---
    'Units': 'Юниты',
    'Timing': 'Время и ожидание',
    'Setup': 'Управление игрой',
    'Logic': 'Условия',

    // --- сами блоки ---
    'Upgrade Unit': 'Апгрейд юнита',
    'Sell Unit': 'Продать юнита',
    'Auto Upgrade Unit': 'Авто-апгрейд',
    'Target Priority': 'Приоритет цели',
    'Walk': 'Пройти по пути',
    'Wait (ms)': 'Пауза (мс)',
    'Wait for Wave': 'Дождаться волны',
    'Leave at Minute': 'Выйти на минуте',
    'Setting': 'Настройка игры',
    'Click': 'Клик',
    'Send Key': 'Нажать клавишу',
    'Detect': 'Если увидит картинку',
    'Walk Path': 'Путь ходьбы',
    'Auto': 'Авто',
    'Custom': 'Свой',
    'Sprint': 'Бегом',
    'Runs Once': 'Один раз',
    'Once': 'Один раз',
    'Drag a block into a phase below, drag rows to reorder.':
      'Перетащи блок в нужную фазу справа. Порядок строк меняется тем же перетаскиванием — сверху вниз, как макрос их и выполнит.',

    // --- фазы ---
    'Pre Start': 'До боя',
    'Battle': 'В бою',
    'Loop A': 'Цикл А',
    'Loop B': 'Цикл Б',
    'Combat': 'бой',
    'Repeats': 'повторяется',

    // --- подсказки в пустых фазах: они и объясняют смысл каждой фазы ---
    'Drag Place Unit, Setting, Auto Upgrade Unit, Click, or Wait blocks here -- only those are possible before the match starts.':
      'Выполняется ОДИН раз, до нажатия «Start Game»: расставить юнитов, настроить камеру, пройти по карте. Сюда можно только «Поставить юнита», «Настройка игры», «Авто-апгрейд», «Клик» и «Пауза» — остального до начала боя ещё нет.',
    'Drag blocks here -- upgrades, sells, waits, clicks, anything goes mid-battle.':
      'Выполняется ОДИН раз после начала боя, сверху вниз. Годится любой блок: апгрейды, продажа, ожидания, клики.',
    'Drag blocks here -- this list repeats over and over during the match. Pair a Detect block with a Wait to "watch for an image, then act".':
      'Повторяется по кругу весь бой, пока матч не кончится. Сюда кладут то, что нужно делать постоянно. Связка «Если увидит картинку» + «Пауза» даёт правило «дождись картинки — сделай действие». Циклов два, чтобы развести разные задачи: например, в А — апгрейды, в Б — реакция на события.',

    // --- панель сценария сверху ---
    'Template name': 'Название сценария',
    'Team Loadout': 'Состав команды',
    'No Team': 'Без состава',
    'Blocks': 'Блоки',
    'A macro operation is what the bot does inside one match: which units to place, when to upgrade, what to wait for. Drag blocks from the left into a phase.':
      'Сценарий — это то, что макрос делает внутри одного матча: кого поставить, когда апгрейдить, чего дождаться. Перетащи блоки слева в нужную фазу.',

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
