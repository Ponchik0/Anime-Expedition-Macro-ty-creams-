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
    // 'Clear' уже ниже, в блоке журнала: ключи здесь глобальные, и второй
    // такой же просто затирал бы первый.
    'Sure?': 'Точно?',
    'Replay': 'Повтор',
    // Метка «чем забег был» в строке истории. Story/Raid/Expedition/Challenge —
    // имена режимов из самой игры, их не переводим ('Challenge' уже есть ниже,
    // в блоке своего экрана, и намеренно оставлен как есть).
    'Daily Challenge': 'Дневной челлендж',
    'What this run actually was': 'Чем этот забег был на самом деле',
    'Save stats and run history to PDF': 'Сохранить статистику и историю в PDF',
    'Erase run history and the win/loss counters': 'Стереть историю забегов и счётчики побед/поражений',
    'Played back from a recording, not the automatic run':
      'Забег отыгран повтором записи, а не автоматом',

    // --- Дашборд: управление ---
    'Controls': 'Управление',
    // --- Блок «что сделает Старт» над кнопками ---
    'Scenario': 'Сценарий',
    'Recording': 'Запись',
    'Task queue is empty': 'Очередь задач пуста',
    'No recording picked yet': 'Запись не выбрана',
    'no scenario set': 'сценарий не задан',
    'endless loops': 'кругов без конца',
    'Runs alongside the selected mode': 'Работает вместе с выбранным режимом',
    'Crafting': 'Крафт',
    'Bounty': 'Баунти',
    'Fuel': 'Топливо',
    'Auto Fuel': 'Авто-топливо',
    'Tower': 'Башня',
    'Portals': 'Порталы',
    'East Town': 'Восточный город',
    'Start': 'Старт',
    'Pause': 'Пауза',
    'Stop': 'Стоп',
    'Start Macro': 'Запустить макрос',
    'Stop Macro': 'Остановить макрос',
    'Pause / Resume Macro': 'Пауза / продолжить',
    'Process Log': 'Журнал',
    'Pop Out': 'В окно',
    'Copy Logs': 'Скопировать логи',
    'Clear': 'Очистить',
    'new': 'новых',

    // --- Экран ожидания ---
    'Waiting for Roblox': 'Жду Roblox',
    // Два шага подключения и подсказка под ними. Строка про «dock in
    // automatically» стояла в разметке с самого начала, но в словарь заведена
    // не была — и оставалась английской прямо под русской строкой на первом
    // же экране, который видит человек.
    'Roblox is running': 'Roblox запущен',
    'Window docked': 'Окно встроено',
    "Launch Roblox, it'll dock in automatically": 'Запусти Roblox — окно встроится само',
    'Roblox found, docking it now': 'Roblox найден, встраиваю окно',
    "Roblox isn't responding yet — check that it's actually running":
      'Roblox пока не отвечает — проверь, запущен ли он',
    'Launch Roblox': 'Запустить Roblox',
    'Skip': 'Пропустить',
    'Roblox Window': 'Здесь окно Roblox',
    'Waiting for Roblox window...': 'Ожидание окна Roblox...',
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
    'Portal': 'Портал',
    'Portal Name': 'Имя портала',
    'The portal to search for in the Inventory > Portals tab (the search query, e.g. "summer")':
      'Имя портала для поиска во вкладке Инвентарь > Порталы (поисковый запрос, напр. "summer")',
    'Select the event to enter: Infinite & Fishing, or Portal Mode':
      'Выберите событие: Бесконечность и рыбалка или Режим порталов',
    'Select the event to enter': 'Выберите событие',
    'Infinite & Fishing': 'Бесконечность и рыбалка',
    'Portal Mode': 'Режим порталов',
    'Macro Operation (Must be Autoplay)': 'Сценарий (обязательна автоигра)',
    'Portals Then Exit': 'Порталов до выхода',
    'Portal in lobby': 'Портал в лобби',
    'Portal in chooser': 'Портал после забега',
    'Plays The Map': 'Кто проходит карту',
    'Auto Play': 'Автоигра',
    'Choose game mode': 'Выберите режим игры',
    'Select game mode: Story, Raid, Expedition, Event, Tournament, Tower, or Portals':
      'Выберите режим игры: Сюжет, Рейд, Экспедиция, Событие, Турнир, Башня или Порталы',
    'Number of times to run this task': 'Сколько раз выполнить эту задачу',
    'How many portals to run before exiting to the lobby -- 0 keeps going until you stop the task (maximum 9999)':
      'Сколько порталов пройти до выхода в лобби — 0 крутит до ручной остановки (максимум 9999)',
    'Required. The portal to click in Items > Portals, used when starting or re-entering from the lobby.':
      'Обязательно. Портал в панели Предметы → Порталы при старте из лобби.',
    'Required. The portal to click on the post-run chooser, used to go straight into the next run.':
      'Обязательно. Портал на экране выбора после забега для прямого перехода в следующий забег.',
    "Macro: the template's blocks play the round (Auto Play is switched off). Auto Play: the game plays it -- your Macro Operation still runs alongside.":
      'Макрос: блоки сценария играют раунд (автоигра выключена). Автоигра: играет сама игра — блоки сценария работают параллельно.',
    "Macro: the template's blocks play the round. Auto Play: the game's Auto Play button is switched on -- your Macro Operation still runs alongside it.":
      'Макрос: блоки сценария играют раунд. Автоигра: кнопка автоигры включена — блоки сценария работают параллельно.',
    'Stop On Failure': 'Остановить при сбое',
    'Stop macro if this task fails or encounters an error':
      'Остановить макрос, если эта задача завершилась ошибкой или сбоем',
    'After Completion': 'После завершения',
    'Enable custom action after task completes all repeats':
      'Включить особое действие после выполнения всех повторов задачи',
    'Auto Transition': 'Автопереход',
    'Enable or disable transition to next task after all repeats':
      'Включить или выключить переход к следующей задаче после всех повторов',
    'Action On Finish': 'Действие',
    'What to do when this task finishes cleanly':
      'Что делать после завершения повторов этой задачи',
    'Next in queue': 'Следующая по очереди',
    'Stop macro': 'Остановить макрос',
    'Repeat this task': 'Повторять задачу (зациклить)',
    'Jump to task': 'Перейти к задаче…',
    'Target Task': 'Перейти к задаче',
    'Task to jump to after completion': 'Задача, на которую перейти после завершения',
    'Select task...': 'Выберите задачу…',
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
    'All Templates': 'Все сценарии',
    'Single Template': 'Один сценарий',
    'Select Templates': 'Выбрать сценарии',
    'Check templates to share:': 'Отметь, чем поделиться:',
    'Place Unit': 'Поставить юнита',
    'Set Position': 'Задать точку',
    'Keep Placing': 'Ставить до упора',
    'Verify Placement': 'Проверять установку',
    'Verify placement': 'Проверять установку',
    'Ignore Highlight': 'Без подсветки',
    'Recover Phantom': 'Восстанавливать фантомов',
    'Max attempts': 'Попыток',
    'Retry delay (s)': 'Пауза (с)',
    'Checks': 'Проверок',
    'Check every (s)': 'Интервал (с)',
    'Use Roblox Screen': 'Снимок из игры',
    // Снимок по умолчанию для режима: снял кадр один раз -- и он
    // подставляется сам, пока работаешь со сценарием этого режима.
    'Mode': 'Режим',
    'Set as Default Snapshot': 'Сделать снимком по умолчанию',
    "Save the frame on screen as this mode's default snapshot":
      'Сохранить показанный кадр как снимок по умолчанию для выбранного режима',
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
    // Пришло с апстримом 0.18: перереролл карточек до мифика.
    'Auto Mythic Bounty': 'Авто-мифик в заданиях',
    'Rerolls each eligible card until its card title verifies as Mythic.':
      'Перекручивает каждую подходящую карточку, пока её название не подтвердится как Mythic.',
    'Mythic Reroll Safety Limit': 'Предел перекруток на мифик',
    'Maximum rerolls for one card before Auto Bounty leaves it unclaimed. Allowed range: 1–100.':
      'Сколько раз перекручивать одну карточку, прежде чем авто-задания оставят её незабранной. Допустимо от 1 до 100.',
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
    'Press a key...': 'Нажми клавишу…',
    'Reset to default key (press Esc while capturing to unbind)':
      'Вернуть исходную клавишу (Esc во время ожидания — снять привязку)',
    'Recordings Panel': 'Список записей',
    'Slides your recordings out over the right column of the Dashboard -- the game stays where it is. Start a recording from there and the list steps aside on its own.':
      'Выдвигает список записей поверх правой колонки Панели — игра остаётся на месте. Начал оттуда запись — список уходит сам.',

    // --- Настройки: вебхук ---
    'Webhook URL': 'Ссылка вебхука',
    'Delivery': 'Доставка',
    'Not linked': 'Не подключён',
    'Send Test': 'Отправить тест',
    'Silent Mode': 'Тихий режим',
    'No notification ping.': 'Без звука и упоминания.',
    'Discord User ID': 'Discord ID для пинга',
    'Paste Clipboard': 'Вставить из буфера',
    'Progress Updates': 'Уведомления о ходе очереди',
    'Send task and challenge start/finish notifications.':
      'Присылать отметки о начале и конце каждой задачи и каждого челленджа.',
    'Periodic Status': 'Сводка по часам',
    'Sends a summary to Discord on a timer: matches for the period, session and all-time record, streaks, and what the macro is doing right now. Off by default.':
      'Присылает в Discord сводку по таймеру: матчи за промежуток, счёт сессии и за всё время, серии и то, чем макрос занят прямо сейчас. Отвечает на «как там дела», не дожидаясь следующего матча. По умолчанию выключено.',
    'Only While Running': 'Только во время прогона',
    'The timer only counts while a run is going, so a macro stopped for the night stays quiet instead of piling up summaries. Default on.':
      'Таймер тикает только пока идёт прогон: остановил на ночь — сводки не приходят, а не сыплются пачкой утром. По умолчанию включено.',
    'Summary On Stop': 'Итог при остановке',
    'One final summary the moment a run ends -- whether you stopped it or it ran out of loops. Default on.':
      'Одна итоговая сводка в момент, когда прогон закончился — кнопкой или сам, отыграв все круги. По умолчанию включено.',
    'Send Now': 'Отправить сейчас',

    // --- Настройки: отладка ---
    // Пришло с апстримом 0.18: живая проверка блока Detect и пипетка кнопки
    // Teams.
    // Итог проверки версии, случаи без подставленных номеров.
    'Updates are switched off in this build.': 'Обновления в этой сборке выключены.',
    "Couldn't check: the update repository has no releases yet.":
      'Проверить не вышло: в репозитории обновлений ещё нет ни одного релиза.',
    "Couldn't check: the update repository is private, renamed or deleted.":
      'Проверить не вышло: репозиторий обновлений недоступен — приватный, переименован или удалён.',
    "Couldn't check: GitHub is unreachable.":
      'Проверить не вышло: до GitHub не достучаться — нет сети или он не отвечает.',
    "Couldn't check: no answer from the update server.":
      'Проверить не вышло: сервер обновлений не ответил.',
    'Test Detect': 'Проверить Detect',
    'Waiting for test...': 'Жду проверки...',
    'Teams Button Click': 'Точка нажатия кнопки Teams',
    'Optional manual point inside the Teams button. Pick the lower/inner part if the image-match center misses; Auto uses the detected image center.':
      'Необязательная своя точка внутри кнопки Teams. Ставь ближе к низу и внутрь, если центр найденной картинки промахивается; «Авто» бьёт в центр найденного.',
    'Health Check': 'Проверка окружения',
    'Run Health Check': 'Проверить окружение',

    // --- Обновление: окно и сигнал в шапке ---
    'Update Available': 'Доступно обновление',
    'Update & Restart': 'Обновить и перезапустить',
    'Starting download...': 'Начинаю скачивание…',

    // --- Первый запуск: чек-лист окружения (#onboarding-modal) ---
    // Экран, который человек видит РАНЬШЕ всего остального, оставался целиком
    // английским. Списки рисует app.js через innerHTML, поэтому ключи здесь —
    // это ровно строки из INGAME_REQUIREMENTS и MACHINE_REQUIREMENTS,
    // переведённые наблюдателем на лету.
    //
    // НАЗВАНИЯ НАСТРОЕК ROBLOX НЕ ПЕРЕВОДИМ намеренно: «UI Scale»,
    // «Auto Sprint», «Show Match and Rewards», «Auto Vote Start» — это подписи
    // в самой игре, и человек ищет их там глазами. Переведёшь — он не найдёт
    // их в меню. Переводим только объяснения, зачем это нужно.
    'A one-time checklist -- these are the things that cause almost every "it doesn\'t work". You can close this at any time; the same list lives in':
      'Разовый список — это то, из-за чего почти всегда «не работает». Окно можно закрыть в любой момент, тот же список лежит в',
    'Settings > Debug': 'Настройки → Отладка',

    'Set these in Roblox': 'Выстави это в Roblox',
    "only you can — the macro can't see into the game":
      'кроме тебя некому — макрос не видит, что внутри игры',
    'Every reference image was captured at 1. At any other scale the macro is hunting for buttons that are the wrong size.':
      'Все эталоны сняты при значении 1. При другом масштабе макрос ищет кнопки не того размера.',
    'The built-in walk paths are timed for sprint speed. With this off your character stops short, and units place in the wrong spot or not at all.':
      'Встроенные маршруты рассчитаны на скорость спринта. Без него персонаж не доходит, и юниты встают не туда или не встают вовсе.',
    'It covers the part of the screen the macro reads after a match.':
      'Она закрывает ту часть экрана, которую макрос читает после боя.',
    'The macro votes at the right moment itself. Left on, rounds start before Pre Start has run.':
      'Макрос голосует сам в нужный момент. Если оставить включённым, бой начнётся раньше, чем отработает Pre Start.',

    'On this computer': 'На этом компьютере',
    'Health Check verifies these for you': 'проверку окружения макрос делает сам',
    'not checked': 'не проверено',
    'Windows display scale at 100%': 'Масштаб экрана Windows — 100%',
    'Settings > Display. Any other scale shifts every click.':
      'Параметры → Дисплей. Любой другой масштаб смещает каждый клик.',
    'Same elevation as Roblox': 'Те же права, что у Roblox',
    "Don't run one as Administrator without the other -- Windows silently drops clicks upward.":
      'Не запускай что-то одно от администратора: Windows молча гасит клики снизу вверх.',
    'Accessibility and Input Monitoring granted': 'Выданы «Универсальный доступ» и «Мониторинг ввода»',
    'System Settings > Privacy & Security, then restart the app. Without them clicks do nothing.':
      'Системные настройки → Конфиденциальность и безопасность, потом перезапустить приложение. Без них клики не проходят.',
    'Screen Recording granted': 'Выдана «Запись экрана»',
    'Without it every capture comes back black.': 'Без неё каждый снимок экрана приходит чёрным.',
    'Room for side-by-side': 'Хватает ширины для окна рядом',
    'Needs ~1564 logical points of width -- pick a "More Space" scaled resolution on small MacBooks.':
      'Нужно около 1564 логических точек по ширине — на маленьких MacBook выбери разрешение «Больше пространства».',
    'Assets folder next to the app': 'Папка Assets лежит рядом с приложением',
    'It holds every reference image the macro searches for.':
      'В ней лежат все эталоны, которые макрос ищет на экране.',
    'Text reading (optional)': 'Чтение текста (не обязательно)',
    'Only used for stats and reward reading. Install Tesseract later from Settings > General if you want those.':
      'Нужно только для чтения статистики и наград. Tesseract можно поставить позже из «Настройки → Общие».',
    'Diagnostics': 'Диагностика',
    'Export Failure Report': 'Выгрузить отчёт об ошибке',
    'Macro Coordinates': 'Координаты макроса',
    'Reward Reader': 'Чтение наград',
    'Read Rewards': 'Прочитать награды',
    'Game Stats': 'Статистика матча',
    'Read Game Stats': 'Прочитать статистику',
    'Preview Region': 'Показать область',
    'Enter Matchmaking Region': 'Область кнопки матчмейкинга',
    'Portal: Portals Sub-Tab': 'Портал: вкладка «Порталы»',
    'Click point on the Portals sub-tab inside the Items panel.': 'Точка клика по вкладке «Порталы» в панели предметов.',
    'Portal: Activate Button': 'Портал: кнопка активации',
    'Click point on the Activate portal button on the confirmation screen.': 'Точка клика по кнопке «Активировать» на экране подтверждения портала.',
    'Portal: Start Run': 'Портал: старт забега',
    'Click point on the green Start button on the party screen Activate opens. Nothing teleports until this is pressed. Normally found by image; this is the fallback. Default (681, 519).':
      'Точка клика по зелёной кнопке старта на экране группы. Игра не телепортирует, пока кнопка не нажата. Обычно находится по картинке; это запасная точка. По умолчанию (681, 519).',
    'Portal: Select Next Portal': 'Портал: выбор следующего портала',
    'Click point on the gold Select button on the post-run portal chooser. Fires while the counter is below its limit (continues the loop).':
      'Точка клика по кнопке выбора на экране порталов после забега. Срабатывает, пока счётчик не достиг лимита.',
    'Portal: Exit to Lobby': 'Портал: выход в лобби',
    'Click point on the Exit to Lobby button on the post-run screen. Fires once the counter has run its configured N portals (or the single-portal template\'s one).':
      'Точка клика по кнопке выхода в лобби после забега. Срабатывает, когда отработано заданное число порталов.',
    'Auto Play Button': 'Кнопка автоигры',
    'Click point on the in-match Auto Play button, used by a task\'s "Plays The Map" setting. Normally found by image (both states ship art); this is the fallback. Default (1123, 485).':
      'Точка клика по кнопке автоигры в бою для параметра «Кто проходит карту». Обычно находится по картинке; это запасная точка. По умолчанию (1123, 485).',
    'Portal: Close Panel (top-left)': 'Портал: закрыть панель (вверху слева)',
    'Click point on the lobby\'s close button, top-left. Not part of the route: it is clicked before a retry to shut an Items/Portals panel a failed attempt left open, so the retry starts from a clean lobby. Default (3, 3).':
      'Точка клика по кнопке закрытия в лобби (вверху слева). Нажимается перед повторной попыткой, чтобы закрыть открытую панель предметов/порталов. По умолчанию (3, 3).',
    'Capture the Roblox screen and click the Portals sub-tab': 'Захватить экран Roblox и кликнуть по вкладке «Порталы»',
    'Capture the Roblox screen and click the Activate button': 'Захватить экран Roblox и кликнуть по кнопке «Активировать»',
    "Capture the Roblox screen and click the party screen's Start button": 'Захватить экран Roblox и кликнуть по кнопке Start на экране группы',
    'Capture the Roblox screen and click the Select button': 'Захватить экран Roblox и кликнуть по кнопке Select',
    'Capture the Roblox screen and click the Exit to Lobby button': 'Захватить экран Roblox и кликнуть по кнопке Exit to Lobby',
    'Capture the Roblox screen and click the Auto Play button': 'Захватить экран Roblox и кликнуть по кнопке Auto Play',
    "Capture the Roblox screen and click the lobby's close button": 'Захватить экран Roblox и кликнуть по кнопке закрытия в лобби',
    'Roblox Window': 'Окно Roblox',
    'Game Resolution': 'Разрешение игры',
    'Custom...': 'Кастомное...',
    'Sets the docked Roblox client window size. Standard is 1152×756. Choose 1024×768 or custom for smaller screens or laptops. The macro automatically compensates template matching and click coordinates.':
      'Задаёт размер встроенного окна Roblox. Стандарт — 1152×756. Выбери 1024×768 или кастомное для небольших экранов или ноутбуков. Макрос автоматически компенсирует поиск картинок и клики.',
    'Select Roblox Window': 'Выбрать окно Roblox',
    'Attach Selected Roblox': 'Прикрепить выбранное окно',
    'Un-Attach Roblox': 'Открепить Roblox',
    'Attach': 'Прикрепить',
    'Un-Attach': 'Открепить',
    'Camera Setup': 'Настройка камеры',
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
    'Accent': 'Акцент',
    'Background': 'Фон интерфейса',
    'Customization': 'Кастомизация',
    'Остановить — ': 'Остановить — ',
    ', той же клавишей, что начал.': ', той же клавишей, что начал.',
    'Background, accent colour and how densely everything is packed. Contrast of every combination is verified -- nothing here can make the interface unreadable.':
      'Фон, цвет акцента и плотность интерфейса. Контраст каждого сочетания проверен численно — сделать интерфейс нечитаемым отсюда нельзя.',
    'Accent': 'Акцент',
    'Update Available': 'Доступно обновление',
    'Update & Restart': 'Обновить и перезапустить',
    'Starting download...': 'Начинаю загрузку...',
    'Preparing update...': 'Готовлю обновление...',
    'Restarting...': 'Перезапускаюсь...',
    'Later': 'Позже',
    'Checking...': 'Проверяю...',
    'Installing...': 'Устанавливаю...',
    'Installed': 'Установлено',
    'Failed': 'Не удалось',
    'Density': 'Плотность',
    'Corners': 'Скругления',
    'Text contrast': 'Контраст текста',
    'Animations': 'Анимации',
    'Status colors': 'Цвета статусов',
    'Preview': 'Образец',
    'how it will look': 'как это будет выглядеть',
    'text field': 'поле ввода',
    'Dark, Black, Slate, Light, Space, Semi Gold, Semi Silver, or Liquid Glass.':
      'Тёплый тёмный, чёрный (для OLED), холодный тёмный или светлый. Контраст каждого проверен — читаться будет везде.',
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
    'Drag': 'Перетаскивание',
    'From Position': 'Начало',
    'To Position': 'Конец',
    'Steps': 'Шаги',
    'Duration (ms)': 'Длительность (мс)',
    'Pick the drag START on a map or your Roblox screen':
      'Выбрать НАЧАЛО перетаскивания на карте или экране Roblox',
    'Pick the drag END on a map or your Roblox screen':
      'Выбрать КОНЕЦ перетаскивания на карте или экране Roblox',
    'How many interpolated moves the held drag makes -- more = smoother':
      'Сколько промежуточных шагов делает зажатая мышь (больше = плавнее)',
    'How long the whole drag takes -- slower registers better in-game':
      'Сколько миллисекунд длится перетаскивание (медленнее надежнее распознается игрой)',
    'Send Key': 'Нажать клавишу',
    'Detect': 'Если увидит картинку',
    'Counter Detect': 'Детект счётчика',
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

    // --- Ресурсы: карточки, Заправка, Challenge, Bounty (из апстрима) ---
    // Пришло вместе с обновлениями автора и в разметке по-английски, как и
    // всё остальное: словарь -- единственное место, где интерфейс переводится
    // (см. шапку файла).
    'Auto Fuel': 'Автозаправка',
    'Enable Auto Fuel': 'Включить автозаправку',
    'Include in Auto Fuel': 'Заправлять автоматически',
    'Auto Fuel Walking Paths': 'Маршруты автозаправки',
    'Fuel amount': 'Сколько заливать',
    'Next refill:': 'Следующая заправка:',
    'Refill this resource': 'Заправить этот ресурс',
    'Reset Fuel Timer': 'Сбросить таймер заправки',
    'Test Auto Refuel': 'Проверить автозаправку',
    'Makes every enabled resource ready for an immediate refill.':
      'Помечает все включённые ресурсы как готовые к заправке прямо сейчас.',
    'Resource Drill': 'Буровая',
    'Gold Mine': 'Золотая шахта',
    'No resources': 'Ресурсов нет',
    'Waiting': 'Ждёт',
    'Ready': 'Готово',
    'Enabled': 'Включено',
    'Enable Daily Challenge': 'Включить ежедневный Challenge',
    'Enable Regular Challenge': 'Включить обычный Challenge',
    'Reset Challenge Status Now': 'Сбросить статус Challenge',
    'Challenge Play Mode': 'Режим игры для Challenge',
    'Solo or Matchmaking for Daily and Regular Challenge.':
      'Один или с игроками — для ежедневного и обычного Challenge.',
    "Set to 1 if today's Daily Challenge was already completed manually":
      'Поставь 1, если сегодняшний ежедневный Challenge уже пройден вручную',
    'Bounty Story Maps': 'Карты Story для Bounty',
    'Solo or Matchmaking for bounty stages.':
      'Один или с игроками — для этапов Bounty.',
    'Complete supported Bounty Board objectives before other automation.':
      'Выполнять поддержанные цели с доски заданий раньше остальной автоматики.',
    'Auto Upgrade (In Game)': 'Авто-апгрейд (в игре)',

    // --- Автомагазин (апстрим 0.17.0) ---
    'Auto Shop': 'Автомагазин',
    'Enable Auto Shop': 'Включить автомагазин',
    'Runs enabled shops at safe Task Queue boundaries and resets daily progress at 00:00 UTC.':
      'Заходит во включённые магазины между задачами очереди и обнуляет дневной прогресс в 00:00 UTC.',
    'Gold Shop': 'Магазин за золото',
    'Choose how many to buy on each pass. Numeric quantities repeat on later passes until sold out.':
      'Сколько покупать за один заход. Числовое количество докупается в следующие заходы, пока товар не кончится.',
    'Items are checked in this order. Max buys the remaining stock once.':
      'Товары проверяются в этом порядке. «Макс.» выкупает остаток за один заход.',
    "Couldn't load Auto Shop settings.": 'Не удалось прочитать настройки автомагазина.',
    'Reset Today': 'Сбросить за сегодня',
    // Max/Number — переключатель «сколько брать». Те же две кнопки стоят в
    // Заправке и в Крафте, и там они значат ровно то же самое, поэтому
    // перевод общий и безопасный.
    'Max': 'Макс.',
    'Number': 'Число',
    'Qty': 'Кол-во',
    // Состояния товара в списке автомагазина.
    'Out of stock': 'Нет в наличии',
    'Max inventory': 'Инвентарь полон',
    'Failed today': 'Сегодня не вышло',
    'Verifying': 'Проверяю',
    'Retry scheduled': 'Повтор запланирован',
    'Pending': 'В очереди',
    'Complete': 'Готово',

    // --- Перезапуск Roblox по времени и мягкая проверка панели команды ---
    'Periodic Roblox Refresh': 'Перезапуск Roblox по времени',
    'Restart Roblox after the selected number of hours to clear long-session memory buildup. It waits for a completed match and safe lobby boundary, so it does not interrupt a match or add FPS polling. Off by default.':
      'Перезапускать Roblox раз в указанное число часов, чтобы сбросить память, накопленную за долгую сессию. Ждёт конца боя и возврата в лобби, поэтому бой не прерывает и ничего не опрашивает лишний раз. По умолчанию выключено.',
    'hours': 'ч',
    'Loose Team Panel Detection': 'Мягкая проверка панели команды',
    'If Team Loadout keeps failing to open on your setup, this widens the OCR check that confirms it. Off by default -- the wider match can misfire on the previous screen.':
      'Если панель команды упорно не открывается, эта галка расширяет проверку текста, подтверждающую её. По умолчанию выключено: расширенная проверка может сработать на предыдущем экране.',
    'Refills at safe Task Queue boundaries: Max after 8 hours, or numeric amounts based on their fuel duration.':
      'Заправляет между задачами очереди: «Макс.» — через 8 часов, числовые количества — по времени их горения.',

    // --- Блок «Запись» (TinyTask автора) ---
    'Save Recorded Input': 'Сохранить записанный ввод',
    'Recording name...': 'Название записи…',
    'Save Recording': 'Сохранить запись',
    'Pick saved recording...': 'Выбери сохранённую запись…',
    'Recording mouse + keyboard input inside the game window':
      'Пишу мышь и клавиатуру внутри окна игры',

    // --- Блок «Проверка»: самоповтор условия ---
    'Loop': 'Цикл',
    'Until found': 'Пока не найдётся',
    'Polls this condition until it is found.': 'Проверяет условие, пока не найдёт.',
    'Max searches': 'Сколько раз искать',
    'Retry every': 'Повторять каждые',
    '0 searches = unlimited. After a limit, Else runs. Then runs once per match.':
      '0 — без ограничения. Когда попытки кончились, идёт ветка «не нашлось». Ветка «нашлось» выполняется один раз на совпадение.',
  };

  // ------------------------------------------------------- ДИНАМИЧЕСКИЕ СТРОКИ
  // Точного совпадения у них быть не может: внутрь подставлены числа. Список
  // намеренно короткий и узкий -- только то, что приходит из Python готовой
  // строкой (main.Api._apply_update_background) и показывается в интерфейсе,
  // поэтому словарём его не покрыть. Шаблон обязан быть привязан к началу и
  // концу строки, иначе под него начнёт попадать что попало.
  // Односложные состояния, которые app.js СКЛЕИВАЕТ в подписи карточек
  // ресурсов (renderChallengeResourceCard, renderFuelTimers). Отдельным
  // словарём, потому что переводятся они только ВНУТРИ таких строк: сами по
  // себе 'Off' и 'Complete' встречаются в интерфейсе и в других смыслах.
  const RU_STATE = {
    'Off': 'выкл', 'Ready': 'готов', 'Complete': 'пройден',
    'Waiting': 'ждёт', 'Disabled': 'выключено',
  };
  const state = s => RU_STATE[s] || s;

  const RU_PATTERNS = [
    [/^Downloading update\.\.\. ([\d.]+) \/ ([\d.]+) MB$/, 'Загружаю обновление... $1 / $2 МБ'],
    [/^Downloading update\.\.\. ([\d.]+) MB$/, 'Загружаю обновление... $1 МБ'],
    // Подпись карточки Challenge: "Daily: Off | Regular: #1 3/5, #2 Off".
    // Номера слотов и счётчики остаются как есть -- это данные, а не слова.
    [/^Daily: ([\w ]+) \| Regular: (.+)$/,
      (_, daily, regular) => `Ежедневный: ${state(daily)} | Обычный: `
        + regular.split(', ').map(part => part.replace(/\b(Off|Ready)$/, m => state(m))).join(', ')],
    // Подпись карточки Заправки: "Resource Drill: 03:12:45 | Gold Mine: Off".
    // Таймер обратного отсчёта проходит через state() без изменений.
    [/^(Resource Drill|Gold Mine): (\S+) \| (Resource Drill|Gold Mine): (\S+)$/,
      (_, a, av, b, bv) => `${RU[a]}: ${state(av)} | ${RU[b]}: ${state(bv)}`],
    // Подпись карточки Автомагазина: "Gold Shop: 3 enabled | 1 complete".
    [/^Gold Shop: (\d+) enabled \| (\d+) complete$/,
      'Магазин за золото: включено $1 | готово $2'],
    // Строка товара: "Daily max: 5 |" и хвост "| 2/3 attempts" -- это ДВА
    // соседних текстовых узла, между ними лежит span с состоянием, поэтому и
    // шаблона два, а не один на всю подпись.
    [/^Daily max: (\d+) \|$/, 'Дневной максимум: $1 |'],
    [/^\| (\d+)\/3 attempts$/, '| попыток: $1 из 3'],
    // Подвал табло: матчи, кончившиеся без распознанного баннера. Появляется,
    // только когда такие были, — поэтому шаблон, а не строка со всегда-нулём.
    [/^(\d+) unrecognised this session$/, 'не распознано за сессию: $1'],
    // Итог проверки версии. Номера версий подставляются, поэтому шаблоны:
    // «у тебя последняя» и «вышла новее» обязаны звучать по-разному, иначе
    // проверка снова станет неотличима от неудавшейся.
    [/^Update available: (\S+) to (\S+)$/, 'Вышло обновление: $1 → $2'],
    [/^You're on the latest version \((\S+)\)\.$/, 'У тебя последняя версия ($1).'],
  ];

  // Единая точка перевода: сначала точное совпадение, потом шаблоны.
  // null -- перевода нет, строка остаётся английской (см. шапку файла).
  function translate(key) {
    const exact = RU[key];
    if (exact) return exact;
    for (const [re, out] of RU_PATTERNS) {
      if (re.test(key)) return key.replace(re, out);
    }
    return null;
  }

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
        const hit = translate(key);
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
          const hit = translate(norm(src));
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
