"""Тесты структуры кастомизации дашборда и оформления:
проверяют удаление плавающей панели кастомизации dashCustomBar,
удаление загромождающей кнопки Restore из шапки Macro Engine,
наличие плашки восстановления скрытых карточек dashRestoreBanner,
наличие ручек перемещения (card-drag-handle),
аккуратное оформление кнопки Done без неонового свечения,
ограничение курсора grab строго шапками карточек,
эффекты захвата и перетаскивания (ghost, cradle, drop target),
а также раздел Contributors.
"""

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
GLASS_HTML = ROOT_DIR / "ui" / "concept-glass" / "index.html"
GLASS_CSS = ROOT_DIR / "ui" / "concept-glass" / "style.css"
GLASS_JS = ROOT_DIR / "ui" / "concept-glass" / "app.js"
README_EN = ROOT_DIR / "README.md"
README_RU = ROOT_DIR / "README.ru.md"


def test_inner_sub_custom_bar_is_removed():
    """Ловит баг появления лишней внутренней плашки кастомизации подблоков (LBL_SUB_SECTIONS)
    внутри карточки управления, которая загромождала интерфейс.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert "runSubCustomBar" not in html, "Элемент runSubCustomBar должен быть полностью удален из разметки"
    assert "runSubCustomToggles" not in html, "Контейнер runSubCustomToggles должен быть удален"
    assert "runSubAutoToggles" not in html, "Контейнер runSubAutoToggles должен быть удален"


def test_floating_custom_bar_is_removed():
    """Ловит баг появления всплывающей плавающей плашки Customize:
    плашка убрана целиком, так как перекрывалась окном Roblox и была громоздкой.
    Кастомизация теперь интуитивно управляется прямо на карточках (кнопка Done/Customize, ручки grip, крестики).
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert "dashCustomBar" not in html, "Плавающая панель dashCustomBar должна быть полностью удалена из HTML"
    assert "dashCardToggles" not in html, "Контейнер dashCardToggles должен быть удален"

    js = GLASS_JS.read_text(encoding="utf-8")
    assert "dashCustomBar" not in js, "Все ссылки на dashCustomBar должны быть удалены из app.js"


def test_restore_banner_and_clean_macro_header():
    """Ловит баг каши и загромождения в шапке карточки Macro Engine:
    постоянная кнопка Restore удалена из шапки, а при скрытии карточек
    появляется плашка восстановления dashRestoreBanner в боковой колонке.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert "btnRestoreHiddenCards" not in html, (
        "Постоянная кнопка Restore не должна загромождать шапку Macro Engine"
    )
    assert "dashRestoreBanner" in html, (
        "В боковой колонке должна присутствовать плашка dashRestoreBanner для возврата скрытых карточек"
    )
    assert "btnRestoreAllCards" in html, "Плашка должна содержать кнопку восстановления всех карточек"

    css = GLASS_CSS.read_text(encoding="utf-8")
    assert ".dash-restore-banner" in css, "В CSS должны быть стили для плашки .dash-restore-banner"
    assert ".restore-chip" in css, "В CSS должны быть стили для чипов восстановления карточек"


def test_done_button_is_clean_and_not_glowing():
    """Ловит баг светящейся или кричащей кнопки Done:
    кнопка должна быть аккуратной, солидной, чуть большего размера, но без неонового свечения (glow).
    """
    css = GLASS_CSS.read_text(encoding="utf-8")
    assert ".edit-layout-btn.is-active" in css
    block = css.split(".edit-layout-btn.is-active")[1].split("}")[0]
    # Высота не менее 30px (чуть больше стандартных 24-26px)
    assert "height: 30px" in block or "height: 32px" in block
    # Без неонового радиального свечения
    assert "0 0 " not in block, "Кнопка Done не должна иметь яркого неонового свечения (0 0 ...)"


def test_card_drag_handle_and_header_only_cursor():
    """Ловит баг появления лишнего текста Move (кнопочного вида) и ложного курсора grab на теле карточки:
    ручка захвата должна быть интуитивной иконкой без надписей (Move),
    а тело карточки строго сохраняет cursor: default.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert "card-drag-handle" in html, "В HTML должны присутствовать ручки card-drag-handle"
    assert "card-drag-grip" in html, "В HTML должны быть иконки grip"
    assert "drag-handle-hint" not in html, "Текст Move должен быть полностью удален из ручек"
    assert ">Move<" not in html, "Надписи Move не должно быть в разметке"

    css = GLASS_CSS.read_text(encoding="utf-8")
    assert ".card-drag-handle" in css, "В CSS должны быть стили для .card-drag-handle"
    assert "margin-left: -8px" in css, "Ручка card-drag-handle должна быть сдвинута ближе к левому краю (margin-left: -8px)"
    # Тело карточки обязано иметь cursor: default, а не grab
    assert "cursor: default !important;" in css, "В CSS тело карточки .dash-card:not(.is-static) должно иметь cursor: default"
    # Шапки карточек должны иметь cursor: grab
    assert ".run-card-top," in css and ".card-head," in css and ".stats-head-row" in css, (
        "Курсор захвата должен быть явно определен для шапок карточек"
    )

    js = GLASS_JS.read_text(encoding="utf-8")
    assert ".run-card-top, .card-head, .stats-head-row, .card-drag-grip, .card-drag-handle" in js, (
        "В app.js drag должен начинаться строго из зоны шапки карточки или ручки card-drag-handle"
    )


def test_clean_macro_engine_header_and_no_task_queue_subtitle():
    """Ловит баги оформления Macro Engine:
    1) Бейдж IDLE убран из шапки Macro Engine.
    2) Иконка убрана из шапки Macro Engine (так как в других карточках иконок в заголовке нет).
    3) Подпись 'Task queue ready · Press Start (F1)' под Task Queue убрана.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    eyebrow = html.split('<div class="run-card-eyebrow">')[1].split('</div>')[0]
    assert "runStateBadge" not in html, "Бейдж IDLE (runStateBadge) должен быть удален из шапки Macro Engine"
    assert "<svg" not in eyebrow or "card-drag-grip" in eyebrow, "В заголовке Macro Engine не должно быть декоративной иконки"
    assert 'href="#i-activity"' not in eyebrow, "Иконка i-activity должна быть удалена из заголовка Macro Engine"
    assert "task_queue_ready" not in html, "Подпись task_queue_ready под Task Queue должна быть удалена"


def test_card_pickup_drag_effects_without_blue_neon_glow():
    """Ловит баг искусственного ИИ-шного голубого неонового свечения при взятии карточки:
    перетаскивание выполнено в благородном темном стекле (glass) в стилистике макроса
    без кричащих ореолов (0 0 40px rgba(56, 189, 248...)).
    """
    css = GLASS_CSS.read_text(encoding="utf-8")
    assert ".dash-drag-card-ghost" in css, "В CSS должен быть определен стиль .dash-drag-card-ghost"
    # Проверяем отсутствие навязчивого голубого неонового свечения
    ghost_block = css.split(".dash-drag-card-ghost {")[1].split("}")[0]
    assert "rgba(56, 189, 248" not in ghost_block, "В .dash-drag-card-ghost не должно быть голубого неонового свечения"
    assert ".dash-card.is-drag-source" in css, "В CSS должно быть оформлено исходное место карточки .is-drag-source"
    assert ".dash-slot.drop-target" in css, "В CSS должна быть подсветка целевого слота .drop-target"


def test_sub_blocks_have_same_drag_style_as_cards():
    """Ловит баг расхождения стилей перетаскивания основных карточек и подблоков:
    для подблоков также создается плавающий стеклянный клон subGhost,
    а стили оформлены в единой стилистике без стрелочек.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert "sub-btn-up" not in html, "Стрелки вверх sub-btn-up не должны присутствовать в HTML"
    assert "sub-btn-down" not in html, "Стрелки вниз sub-btn-down не должны присутствовать в HTML"

    # Все 4 подблока должны присутствовать и содержать ручку с классом grip
    for sub_id in ("streak", "meta", "queue", "automations"):
        assert f'data-sub-id="{sub_id}"' in html, f"Подблок {sub_id} должен быть в разметке"

    # В CSS и JS должны быть стили и клон для перемещения подблоков с превью обмена
    css = GLASS_CSS.read_text(encoding="utf-8")
    assert ".sub-block-placeholder" in css, "В CSS должен быть определен стиль .sub-block-placeholder"
    assert ".sub-block-drag-ghost" in css, "В CSS должен быть определен стиль .sub-block-drag-ghost"
    assert ".run-sub-block.is-swap-displaced" in css, "В CSS должен быть определен класс смещения целевого блока .is-swap-displaced"
    assert "transition: transform" in css, "В CSS должна быть плавная анимация transform для подблоков"

    js = GLASS_JS.read_text(encoding="utf-8")
    assert "subGhost" in js, "В app.js должно быть создание плавающего клона subGhost для подблоков"
    assert "renderPhysics" in js, "В app.js должна быть плавная физика перемещения для subGhost"
    assert "currentSwapTarget" in js, "В app.js должен быть расчет целевого блока для Live Swap Preview"
    assert "is-swap-displaced" in js, "В app.js должно быть переключение класса is-swap-displaced для смены мест"


def test_contributors_contain_only_cweamy():
    """Ловит баг случайного сохранения сторонних контрибьюторов в разделе Credits/Contributors:
    в репозитории должен быть указан только оригинальный автор Cweamy.
    """
    en_text = README_EN.read_text(encoding="utf-8")
    ru_text = README_RU.read_text(encoding="utf-8")

    assert "## Contributors" in en_text
    assert "https://github.com/Cweamy" in en_text
    assert "Ponchik0" not in en_text.split("## Contributors")[-1], (
        "В разделе Contributors в README.md не должно быть упоминания Ponchik0"
    )

    assert "## Contributors" in ru_text
    assert "https://github.com/Cweamy" in ru_text
    assert "Ponchik0" not in ru_text.split("## Contributors")[-1], (
        "В разделе Contributors в README.ru.md не должно быть упоминания Ponchik0"
    )


def test_tier_resizer_removed_and_streak_spacing_balanced():
    """Ловит баги:
    1) Неработающий разделитель tierResizer (пользователь не мог уменьшать/увеличивать нижний ярус).
    2) Назойливые всплывающие подсказки браузера 'Drag to move card' на ручках перемещения карточек.
    3) Дисбаланс отступов вокруг плашки Streak (она была прижата к кнопкам Restart/VIP Rejoin,
       но имела тройной отступ до карточки с метаданными задачи).
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert "tierResizer" not in html, "Неработающий #tierResizer должен быть полностью удален из разметки"
    assert 'title="Drag to move card"' not in html, "Подсказки 'Drag to move card' должны быть удалены из ручек"

    js = GLASS_JS.read_text(encoding="utf-8")
    assert "tierResizer" not in js, "Все обращения к #tierResizer должны быть удалены из app.js"

    css = GLASS_CSS.read_text(encoding="utf-8")
    assert ".dash-resizer-tier" not in css, "Селектор .dash-resizer-tier должен быть удален из CSS"

    # Проверка сбалансированных отступов для гармоничного смещения Streak чуть ниже
    assert "margin-bottom: 10px;" in css, "Кнопки быстрых действий должны иметь отступ снизу 10px для воздуха перед Streak"
    assert ".run-meta-grid {" in css
    meta_block = css.split(".run-meta-grid {")[1].split("}")[0]
    assert "margin-top: 0;" in meta_block, "У run-meta-grid должен быть убран margin-top, чтобы расстояние от Streak было ровным"

    assert ".run-telemetry-strip {" in css
    streak_block = css.split(".run-telemetry-strip {")[1].split("}")[0]
    assert "margin-bottom: 0;" in streak_block, "У run-telemetry-strip должен быть убран margin-bottom: 6px"


def test_action_insertion_and_mini_queue_macro_tag():
    """Ловит баги:
    1) Отсутствие возможности вставить действие между шагами в готовом сценарии
       (кнопка +, модалка быстрого выбора действия, вызов openInsertActionModal).
    2) Отсутствие отображения привязанного макросценария в Upcoming Queue на дашборде.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert "insertActionModal" in html, "Модалка #insertActionModal должна присутствовать в разметке"
    assert "insertActionGrid" in html, "Контейнер #insertActionGrid должен присутствовать в разметке"

    js = GLASS_JS.read_text(encoding="utf-8")
    assert 'data-act="insert"' in js, "Кнопка вставки действия data-act='insert' должна рендериться на блоках"
    assert "openInsertActionModal" in js, "Функция openInsertActionModal должна быть объявлена в app.js"
    assert "tag-macro" in js, "Upcoming Queue должен рендерить тег привязанного макроса task.macro"

    css = GLASS_CSS.read_text(encoding="utf-8")
    assert ".insert-action-grid" in css, "Стили .insert-action-grid должны присутствовать в CSS"
    assert ".mini-tag.tag-macro" in css, "Стили .mini-tag.tag-macro должны присутствовать в CSS"


def test_scenario_builder_drag_drop_placeholder_and_index():
    """Ловит баг сброса блоков в самый низ при перетаскивании (Pre Start setup, Battle и др.):
    раньше было жестко зашито list.push(), из-за чего при перемещении на любое место карточка
    всегда улетала в самый конец колонки.
    Теперь рассчитывается точный целевой индекс getDropIndex по координате Y курсора,
    отображается живой плейсхолдер места вставки .block-drop-placeholder,
    а вставка выполняется через splice(dropIndex, 0, ...) с аккуратной очисткой плейсхолдеров.
    """
    css = GLASS_CSS.read_text(encoding="utf-8")
    assert ".block-drop-placeholder" in css, "В CSS должны быть стили для плейсхолдера .block-drop-placeholder"
    assert "dashed" in css.split(".block-drop-placeholder")[1].split("}")[0], (
        "Плейсхолдер должен иметь пунктирную границу (dashed)"
    )

    js = GLASS_JS.read_text(encoding="utf-8")
    assert "function getDropIndex(col, clientY)" in js, "В app.js должна быть функция расчета индекса вставки getDropIndex"
    assert "block-drop-placeholder" in js, "В app.js должно быть создание и удаление .block-drop-placeholder"
    assert "list.splice(dropIndex, 0, newBlock)" in js, "Дроп из палитры должен вставляться по dropIndex через splice"
    assert "list.splice(dropIndex, 0, moved)" in js, "Перемещение блока должно вставляться по dropIndex через splice"


def test_scenario_builder_walk_path_picker_and_recording_hud():
    """Ловит баг невозможности удобно выбрать или записать маршрут движения (Walk / Walk Path):
    раньше было пустое текстовое поле без списка доступных путей и без кнопки записи.
    Теперь в модалке есть выпадающий список сохраненных маршрутов (bmPathSelect),
    кнопка быстрой записи на WASD (bmBtnRecordPath),
    плавающий HUD процесса записи (#recPopout) и окно сохранения имени пути (#savePathModal).
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert "recPopout" in html, "В index.html должен быть плавающий индикатор записи #recPopout"
    assert "savePathModal" in html, "В index.html должно быть модальное окно сохранения пути #savePathModal"
    assert "btnStopPathRec" in html, "В index.html должна быть кнопка остановки записи #btnStopPathRec"

    css = GLASS_CSS.read_text(encoding="utf-8")
    assert ".rec-popout-glass" in css, "В CSS должны быть стили плавающего HUD .rec-popout-glass"
    assert ".rec-popout-dot" in css, "В CSS должен быть пульсирующий индикатор записи .rec-popout-dot"

    js = GLASS_JS.read_text(encoding="utf-8")
    assert "savedWalkPaths" in js, "В app.js должен быть список сохраненных маршрутов savedWalkPaths"
    assert "refreshSavedWalkPaths" in js, "В app.js должна быть функция обновления путей refreshSavedWalkPaths"
    assert "startPathRecordingFlow" in js, "В app.js должна быть функция старта записи startPathRecordingFlow"
    assert "stopPathRecordingFlow" in js, "В app.js должна быть функция остановки записи stopPathRecordingFlow"
    assert "bmPathSelect" in js, "В модалке редактирования должен формироваться выпадающий список bmPathSelect"
    assert "bmBtnRecordPath" in js, "В модалке редактирования должна быть кнопка bmBtnRecordPath"


def test_mini_queue_manage_and_skip_buttons():
    """Ловит баг неработающих кнопок Manage и Skip в блоке Upcoming Queue на дашборде:
    раньше кнопка Manage ошибочно пыталась переключить устаревший хэш #tabTasks вместо экрана 'tasks',
    а кнопка Skip не имела корректного обработчика или дублировалась.
    Теперь Manage вызывает прямой переход setScreen('tasks'),
    а Skip вызывает skipCurrentTask с обращением к pywebview.api.skip_current_task() и ротацией задач.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert "btnMiniQueueManage" in html, "Кнопка #btnMiniQueueManage должна быть в HTML"
    assert "btnMiniQueueSkip" in html, "Кнопка #btnMiniQueueSkip должна быть в HTML"

    js = GLASS_JS.read_text(encoding="utf-8")
    assert 'setScreen("tasks")' in js, "Кнопка Manage должна переключать экран на tasks через setScreen('tasks')"
    assert "#tabTasks" not in js, "Устаревший хэш #tabTasks не должен использоваться"
    assert "btnMiniQueueSkip" in js, "Кнопка #btnMiniQueueSkip должна быть привязана в app.js"
    assert "skipCurrentTask" in js, "Функция skipCurrentTask должна быть объявлена и обрабатывать пропуск задачи"


def test_process_log_expand_button_and_binding():
    """Ловит баг отсутствия кнопки расширения Process Log в HTML:
    в коде app.js был предусмотрен обработчик logExpand, разворачивающий журнал
    процесса на всю ширину нижнего яруса, однако в index.html кнопка отсутствовала.
    Теперь кнопка #logExpand присутствует в шапке карточки лога и привязана в app.js.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert 'id="logExpand"' in html, "Кнопка #logExpand должна присутствовать в шапке Process Log"

    js = GLASS_JS.read_text(encoding="utf-8")
    assert 'logExpand' in js, "Обработчик развертывания logExpand должен быть в app.js"
    assert 'is-expanded' in js, "Логика переключения класса is-expanded должна присутствовать"


def test_appearance_pickers_persistence_and_binding():
    """Ловит баг отсутствия персистентности настроек внешнего вида (тема, плотность, углы, анимация):
    раньше функция bindPicker вешала клик, но не сохраняла значение в localStorage
    и не восстанавливала сохраненный выбор при перезапуске приложения.
    Теперь bindPicker сохраняет ключ ae_ в localStorage и восстанавливает активный класс при инициализации.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert 'id="themePicker"' in html, "Контейнер темы #themePicker должен быть в HTML"
    assert 'id="densitySeg"' in html, "Сегмент плотности #densitySeg должен быть в HTML"
    assert 'id="cornersSeg"' in html, "Сегмент скруглений #cornersSeg должен быть в HTML"
    assert 'id="motionSeg"' in html, "Сегмент анимаций #motionSeg должен быть в HTML"

    js = GLASS_JS.read_text(encoding="utf-8")
    assert 'localStorage.setItem("ae_" + attr, val)' in js, "bindPicker должен сохранять настройки в localStorage"
    assert 'localStorage.getItem("ae_" + attr)' in js, "bindPicker должен считывать сохраненные настройки из localStorage"


def test_resource_modals_and_action_buttons():
    """Ловит баг неработающих кнопок во вкладке Ресурсы:
    кнопки Choose sprites, Configure paths и Story maps не имели обработчиков и модалок.
    Теперь для них созданы специализированные модалки #craftingSpritesModal, #fuelPathsModal,
    #challengeMapsModal, а в app.js привязаны обработчики открытия, сохранения и записи WASD.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert 'id="btnCraftingSprites"' in html, "Кнопка #btnCraftingSprites должна быть в HTML"
    assert 'id="btnFuelPaths"' in html, "Кнопка #btnFuelPaths должна быть в HTML"
    assert 'id="btnChallengeMaps"' in html, "Кнопка #btnChallengeMaps должна быть в HTML"

    assert 'id="craftingSpritesModal"' in html, "Модалка #craftingSpritesModal должна быть в HTML"
    assert 'id="fuelPathsModal"' in html, "Модалка #fuelPathsModal должна быть в HTML"
    assert 'id="challengeMapsModal"' in html, "Модалка #challengeMapsModal должна быть в HTML"

    js = GLASS_JS.read_text(encoding="utf-8")
    assert 'btnCraftingSprites' in js, "Кнопка #btnCraftingSprites должна быть привязана в app.js"
    assert 'btnFuelPaths' in js, "Кнопка #btnFuelPaths должна быть привязана в app.js"
    assert 'btnChallengeMaps' in js, "Кнопка #btnChallengeMaps должна быть привязана в app.js"
    assert 'set_crafting_item_enabled' in js, "Вызовы API крафта должны быть в app.js"
    assert 'set_fuel_path' in js, "Вызовы API путей топлива должны быть в app.js"
    assert 'set_challenge_map_macro' in js, "Вызовы API карт испытаний должны быть в app.js"


def test_scenario_phase_descriptions_and_guide():
    """Ловит баг непонятных фаз и блоков сценария:
    пользователь не понимал, какая фаза за что отвечает и что делают действия.
    Теперь в интерфейсе есть:
    - Сворачиваемая плашка-руководство #scenGuideCard с объяснением шагов 1-2-3 (Pre Start, Battle, Loop A & B).
    - Описания под заголовками колонок .scen-col-desc.
    - Умные подсказки к действиям getSmartHint (слот удочки 74,670, озеро 150,500, центр/подсечка 576,601).
    - Поле для пользовательских заметок к блокам #bmComment и отображение .block-comment / .block-smart-hint.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert 'id="scenGuideCard"' in html, "Плашка руководства по сценариям #scenGuideCard должна присутствовать в HTML"
    assert 'id="btnToggleScenGuide"' in html, "Кнопка сворачивания #btnToggleScenGuide должна присутствовать"
    assert 'class="scen-col-desc"' in html, "Подзаголовки колонок .scen-col-desc должны присутствовать"

    css = GLASS_CSS.read_text(encoding="utf-8")
    assert '.scen-guide-card' in css, "Стили для .scen-guide-card должны быть в style.css"
    assert '.scen-col-desc' in css, "Стили для .scen-col-desc должны быть в style.css"
    assert '.block-comment' in css, "Стили для .block-comment должны быть в style.css"
    assert '.block-smart-hint' in css, "Стили для .block-smart-hint должны быть в style.css"

    js = GLASS_JS.read_text(encoding="utf-8")
    assert 'function getSmartHint' in js, "Функция getSmartHint должна присутствовать в app.js"
    assert 'initScenarioGuideToggle' in js, "Функция initScenarioGuideToggle должна присутствовать в app.js"
    assert 'block-comment' in js, "Отображение block-comment должно быть в app.js"
    assert 'bmComment' in js, "Поле заметки bmComment должно быть в модалке редактирования блока"
    assert 'bmApplySmartHint' in js, "Кнопка вставки умной подсказки bmApplySmartHint должна быть в app.js"


def test_scenario_template_comments():
    """Ловит баг отсутствия пояснений в предустановленных шаблонах:
    шаблоны должны содержать понятные комментарии к каждому блоку.
    """
    import json
    inf_summer_path = ROOT_DIR / "Templates" / "Inf Summer.json"
    data = json.loads(inf_summer_path.read_text(encoding="utf-8"))
    blocks = data.get("blocks", {})
    prestart = blocks.get("prestart", [])
    assert len(prestart) > 0, "Prestart блоки должны присутствовать"
    assert any("comment" in b for b in prestart), "В prestart блоках должны быть комментарии-пояснения"


def test_action_explanation_covers_all_blocks_and_auto_signs():
    """Ловит баг неподписанных действий у создаваемых игроками сценариев и неполной локализации:
    - Все 15 типов блоков должны поддерживаться функцией getActionExplanation.
    - При добавлении блока из палитры или модалки вставки блок автоматически
      получает понятную человеку подпись в newBlock.comment.
    - Пользователь может редактировать подпись через поле bmComment и кнопку bmApplySmartHint.
    - Переключение языка динамически обновляет подсказки title и плейсхолдеры.
    """
    js = GLASS_JS.read_text(encoding="utf-8")
    assert "function getActionExplanation" in js, "Функция getActionExplanation должна быть определена в app.js"
    assert "function getSmartHint" in js, "getSmartHint должен оставаться для обратной совместимости"

    # Все 15 типов блоков в getActionExplanation
    all_15_types = [
        "place_unit", "upgrade_unit", "auto_upgrade_unit", "sell_unit", "target_priority",
        "walk_path", "walk", "wait_ms", "wait_wave", "leave_at_minute",
        "click", "drag", "send_key", "record", "detect"
    ]
    for b_type in all_15_types:
        assert f't === "{b_type}"' in js, f"Тип блока '{b_type}' обязан обрабатываться в getActionExplanation"

    # Автоподпись при создании
    assert "newBlock.comment = getActionExplanation" in js, (
        "Создаваемые блоки должны автоматически подписываться через getActionExplanation"
    )

    # Динамическая локализация title и placeholder
    assert 'data-i18n-title' in js, "applyLang должен обновлять data-i18n-title"
    assert 'data-i18n-placeholder' in js, "applyLang должен обновлять data-i18n-placeholder"

    # Проверка модалок в HTML
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert 'data-i18n="modal_edit_block"' in html
    assert 'data-i18n="modal_insert_action"' in html
    assert 'data-i18n="modal_save_path_title"' in html
    assert 'data-i18n-placeholder="ph_scen_name"' in html


def test_rec_popout_hud_hidden_on_launch_and_safe_lifecycle():
    """Ловит баг ложного отображения плавающего HUD записи (#recPopout) при запуске приложения:
    ранее правило .rec-popout-glass { display: flex } в CSS переопределяло HTML-атрибут [hidden],
    из-за чего плашка 'Запись движения WASD' появлялась на дашборде сразу после старта макроса,
    даже когда никакой сценарий не запущен.
    Теперь:
    1. В index.html задан явный защитный inline style="display: none;".
    2. В CSS объявлены правила [hidden] и .rec-popout-glass[hidden] с display: none !important.
    3. В app.js на этапе загрузки initRecPopout принудительно скрывается.
    4. При переключении экранов и отмене записи вызывается popout.style.display = 'none'.
    5. В Api.__init__ (main.py) сбрасываются любые остаточные процессы записи.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    assert 'id="recPopout"' in html
    assert 'hidden' in html
    assert 'style="display: none;"' in html

    css = GLASS_CSS.read_text(encoding="utf-8")
    assert ".rec-popout-glass[hidden]" in css
    assert "display: none !important" in css

    js = GLASS_JS.read_text(encoding="utf-8")
    assert "initRecPopout" in js
    assert "initRecPopout.style.display = \"none\"" in js

    main_code = (ROOT_DIR / "main.py").read_text(encoding="utf-8")
    assert "_paths.cancel_recording()" in main_code
    assert "_input_record.cancel_recording()" in main_code


def test_scenario_card_actions_elevated_and_text_wrapping():
    """Ловит баг смещения кнопок действий в середину/низ карточки и обрезания текста действий:
    1. Ранее .block имел align-items: center и колонку действий справа, из-за чего кнопки
       (+ edit dup del) сползали вниз при наличии длинных описаний и забирали 100px ширины.
       Теперь .block-acts спозиционирован абсолютно в правом верхнем углу (top: 6px, right: 6px),
       выглядит компактно и аккуратно.
    2. Ранее .block-comment, .block-smart-hint, .block-main strong и span имели
       white-space: nowrap и text-overflow: ellipsis, что обрезало текст до 'Пауза перед э...'
       и 'Ожидание 1.0 сек п...'.
       Теперь текст плавно переносится на несколько строк (white-space: normal, word-break: break-word)
       без обрезания многоточием.
    3. .scen-cols имеет минимальную ширину колонок 230px с горизонтальной прокруткой,
       чтобы карточки не сжимались в узкие полоски на экранах разного разрешения.
    """
    css = GLASS_CSS.read_text(encoding="utf-8")

    # Смещение кнопок выше в правый верхний угол
    assert "position: relative" in css
    assert "position: absolute" in css
    assert "top: 6px" in css
    assert "right: 6px" in css

    # Полное отображение текстов без многоточия
    assert "word-break: break-word" in css
    assert "white-space: normal" in css

    # Проверка .block-comment на перенос строк
    block_comment_idx = css.find(".block-comment {")
    assert block_comment_idx != -1
    block_comment_chunk = css[block_comment_idx:block_comment_idx + 400]
    assert "white-space: normal" in block_comment_chunk
    assert "text-overflow: ellipsis" not in block_comment_chunk

    # Проверка ширины колонок сценариев
    assert "minmax(230px, 1fr)" in css


def test_full_bilingual_coverage_for_modals_and_cards():
    """Ловит баги неполной локализации динамических модалок, карточек сценариев и вкладок:
    1. Ранее модалка редактирования блока openBlockModal содержала захардкоженные английские
       названия полей (Unit Name, Hotkey, Coordinate X, Retry placement, Wait Duration и др.)
       даже при активном русском языке.
    2. Карточки действий в renderScenarioView выводили фиксированные английские слова
       (Then, Else, None, action(s), once, record on run, тултипы кнопок), а комментарии
       типовых действий не переводились при переключении языка интерфейса.
    3. В index.html вкладки ресурсов (Auto Fuel, Auto Shop, Auto Challenge), горячие клавиши
       и кнопки отладки не имели data-i18n разметки.
    4. Кнопки с иконками (#blockDelete, #blockSave, #savePathConfirm) теряли svg-иконки
       при вызове applyLang из-за прямого присваивания textContent на родительскую кнопку.
    5. Словари STR.en и STR.ru должны оставаться строго симметричными (0 расхождений в ключах).
    """
    js = GLASS_JS.read_text(encoding="utf-8")
    html = GLASS_HTML.read_text(encoding="utf-8")

    # 1. Проверка билингвальности openBlockModal
    assert 'isRu ? "Имя юнита" : "Unit Name"' in js
    assert 'isRu ? "Горячая клавиша (1-6)" : "Hotkey (1-6)"' in js
    assert 'isRu ? "Координата X" : "Coordinate X"' in js
    assert 'isRu ? "Повторять установку до успеха" : "Retry placement until successful"' in js
    assert 'isRu ? "Длительность ожидания (мс)" : "Wait Duration (ms)"' in js
    assert 'isRu ? "Номер целевой волны" : "Target Wave Number"' in js
    assert 'isRu ? "Минута выхода из матча" : "Match Duration (minutes)"' in js
    assert 'isRu ? "Номер юнита #" : "Unit #"' in js
    assert 'isRu ? "Количество улучшений" : "Upgrades Count"' in js
    assert 'isRu ? "Приоритет цели" : "Priority"' in js
    assert 'isRu ? "Сильнейший (Strongest)" : "Strongest"' in js
    assert 'isRu ? "Клавиша" : "Key"' in js
    assert 'isRu ? "Имя шаблона картинки" : "Template Image"' in js
    assert 'isRu ? "Выполнять один раз за матч (пропускать в циклах)" : "Run once per match (ignore in subsequent loops)"' in js

    # 2. Проверка словаря типовых комментариев и двустороннего перевода
    assert "const KNOWN_COMMENTS = {" in js
    assert "function translateComment(" in js
    assert '"Пауза перед экипировкой": "Pause before equipping"' in js
    assert 'dispComment = translateComment(b.comment, isRu)' in js

    # 3. Проверка билингвальности карточек блоков сценария
    assert 'isRu ? "Тогда" : "Then"' in js
    assert 'isRu ? "Иначе" : "Else"' in js
    assert 'isRu ? "действ." : "action(s)"' in js
    assert 'isRu ? "1 раз" : "once"' in js
    assert 'isRu ? "запись при старте" : "record on run"' in js
    assert 'isRu ? "Вставить действие после" : "Insert action after"' in js
    assert 'isRu ? "Редактировать" : "Edit"' in js
    assert 'isRu ? "Дублировать" : "Duplicate"' in js
    assert 'isRu ? "Удалить" : "Delete"' in js
    assert 'isRu ? `4 фазы · ${totalCount} блоков` : `4 phases · ${totalCount} blocks`' in js

    # 4. Проверка разметки data-i18n в index.html
    assert 'data-i18n="res_crafting_title"' in html
    assert 'data-i18n="res_fuel_title"' in html
    assert 'data-i18n="res_shop_title"' in html
    assert 'data-i18n="res_challenge_title"' in html
    assert 'data-i18n="hk_macro_start"' in html
    assert 'data-i18n="hk_reset_default"' in html
    assert 'data-i18n="set_diag_screenshot"' in html
    assert 'data-i18n="set_diag_report"' in html

    # 5. Проверка сохранения svg-иконок в кнопках модалок через вложенный span
    assert '<button class="btn btn-danger-ghost btn-sm" id="blockDelete"><svg class="ic"><use href="#i-trash"/></svg><span data-i18n="btn_delete">Delete</span></button>' in html
    assert '<button class="btn btn-primary btn-sm" id="blockSave"><svg class="ic"><use href="#i-check"/></svg><span data-i18n="btn_save">Save</span></button>' in html
    assert '<button class="btn btn-primary btn-sm" id="savePathConfirm"><svg class="ic"><use href="#i-check"/></svg><span data-i18n="btn_save_path">Save Path</span></button>' in html

    # 6. Проверка поддержки HTML-тегов (<kbd>) функцией applyLang
    assert 'val.includes("<") && val.includes(">")' in js


def test_inner_cards_bilingual_translation_and_defaults():
    """Ловит баг отсутствия русского перевода внутри карточек:
    1. Инициализация языка по умолчанию должна быть русской ('ru') с проверкой
       localStorage (ui_lang / ae_lang), а не жестко захардкоженным английским 'en'.
    2. Плейсхолдер пустой колонки сценария должен переводиться динамически через
       data-empty-hint ('Перетащите блоки сюда' / 'Drop blocks here'), а не быть
       статическим текстом в CSS.
    3. Метаданные параметров внутри карточек сценариев (BLOCK_DEFS) должны переводиться:
       - target_priority: Сильнейший, Слабейший, Первый, Последний, Ближайший;
       - detect: один раз, цикл, таймаут;
       - walk_path: авто, на месте, свой;
       - walk: по умолчанию.
    4. При смене языка (applyLang) обязаны динамически перерисовываться карточки задач
       (renderRealTasks), конструктор задач (renderTaskBuilder) и мини-очередь (renderMiniQueue).
    5. Карточки в очереди задач должны выводить русские названия режимов (Сюжет, Рейд, Турнир и т.д.),
       склонения (1 задача, 2 задачи, 5 задач), метки повторов, таймеров и этапов.
    6. Конструктор задач должен содержать русские подписи полей и выпадающих списков
       ('В одиночку', 'Подбор игроков', 'Обычный', 'Сложный', 'Кошмар' и т.д.).
    """
    js = GLASS_JS.read_text(encoding="utf-8")
    css = GLASS_CSS.read_text(encoding="utf-8")

    # 1. Русский язык по умолчанию и чтение из localStorage
    assert 'let LANG = "ru";' in js
    assert 'localStorage.getItem("ui_lang")' in js

    # 2. Динамический плейсхолдер пустой колонки
    assert 'content: attr(data-empty-hint);' in css
    assert 'colEl.setAttribute("data-empty-hint", isRu ? "Перетащите блоки сюда" : "Drop blocks here");' in js

    # 3. Перевод параметров блоков сценариев (BLOCK_DEFS)
    assert 'const pMap = { Strongest: "Сильнейший", First: "Первый", Last: "Последний", Weakest: "Слабейший", Closest: "Ближайший" };' in js
    assert 'const modeMap = { single: "один раз", loop: "цикл", timeout: "таймаут" };' in js
    assert 'const modeMap = { auto: "авто", none: "на месте", custom: "свой" };' in js
    assert 'const defName = LANG === "ru" ? "по умолчанию" : "default";' in js

    # 4. Перерисовка динамических карточек в applyLang()
    apply_lang_start = js.find("function applyLang() {")
    assert apply_lang_start != -1
    apply_lang_body = js[apply_lang_start:apply_lang_start + 1200]
    assert "renderRealTasks(realTasksList);" in apply_lang_body
    assert "renderTaskBuilder();" in apply_lang_body
    assert "renderMiniQueue(" in apply_lang_body

    # 5. Билингвальность очереди задач (renderRealTasks)
    assert 'TASK_DATA[task.mode]?.labelRu' in js
    assert "len === 1 ? 'задача'" in js
    assert "len > 1 && len < 5 ? 'задачи' : 'задач'" in js
    assert 'isRu ? `повторов <b class="mono">×${task.repeat}</b>`' in js
    assert 'isRu ? `сценарий <b>${task.macro}</b>`' in js
    assert 'isRu ? "Стандартное выполнение"' in js

    # 6. Билингвальность конструктора задач (renderTaskBuilder)
    assert 'isRu ? "Режим игры" : "Game Mode"' in js
    assert 'isRu ? "Количество повторов" : "Repeat Count"' in js
    assert 'isRu ? "Поисковый запрос портала" : "Portal Query"' in js
    assert 'isRu ? "Сложность" : "Difficulty"' in js
    assert 'isRu ? "Остановить после волны" : "Stop After Wave"' in js
    assert 'isRu ? "Сценарий макроса" : "Macro Operation"' in js
    assert 'isRu ? "Управление боем" : "Combat Control"' in js
    assert 'isRu ? "В одиночку" : "Solo"' in js
    assert 'isRu ? "Подбор игроков" : "Matchmaking"' in js
    assert 'isRu ? "Бесконечный режим и рыбалка" : "Infinite & Fishing"' in js
    assert 'isRu ? "Режим портала" : "Portal Mode"' in js


def test_walk_recording_polish_hotkey_modal_and_task_drag_smoothness():
    """Ловит баги оформления карточек записи, скрытия модалки за Roblox, хоткея и резкого драга:
    1. Все SVG-символы, используемые кнопками Import (#i-download), Export (#i-share)
       и модалками (#i-close, #i-chevron-right), обязаны быть объявлены в <defs>.
    2. Эмодзи '🔴' полностью удалён из заголовков, описаний и карточек сценария,
       и заменён на анимированный пульсирующий индикатор .rec-dot-pulse и стильный бейдж.
    3. При завершении записи движения (stopPathRecordingFlow) экран переключается
       на 'scenarios' и вызывается hide_game() ДО показа savePathModal, чтобы модалка
       не блокировалась и не оказывалась погребена под нативным окном Roblox.
    4. Поле ввода названия маршрута savePathInput оформлено в теме приложения
       через .glass-input-wrap и .glass-input с иконкой i-route, а не сырой белый инпут.
    5. Запись движения WASD имеет отдельный бинд (toggle_walk_record = 'alt+9')
       в HOTKEY_DEFAULTS, зарегистрированный в main.py и не пишущийся в маршрут.
    6. Драг карточек задач (initTaskReordering) создаёт плавный плавающий клон .task-drag-ghost,
       а при завершении перетаскивания реально синхронизирует и сохраняет порядок realTasksList.
    """
    import re
    from main import HOTKEY_DEFAULTS, HOTKEY_LABELS, Api

    js = GLASS_JS.read_text(encoding="utf-8")
    css = GLASS_CSS.read_text(encoding="utf-8")
    html = GLASS_HTML.read_text(encoding="utf-8")

    # 1. Проверка наличия всех используемых SVG-иконок
    defs = set(re.findall(r'<symbol\s+id="([^"]+)"', html))
    uses = set(re.findall(r'href="#([^"]+)"', html))
    missing = uses - defs
    assert "i-download" in defs, "Символ i-download должен быть объявлен в <defs>"
    assert "i-share" in defs, "Символ i-share должен быть объявлен в <defs>"
    assert "i-chevron-right" in defs, "Символ i-chevron-right должен быть объявлен в <defs>"
    assert "i-close" in defs, "Символ i-close должен быть объявлен в <defs>"
    assert len(missing) == 0, f"Все используемые в HTML SVG-символы должны быть в <defs>, не хватает: {missing}"

    # 2. Отсутствие круглого красного эмодзи в разметке и коде
    assert "🔴" not in js, "Эмодзи 🔴 должен быть удален из js-кода карточек и бейджей"
    assert "🔴" not in html, "Эмодзи 🔴 не должен присутствовать в HTML-разметке"
    assert ".rec-dot-pulse" in css, "В CSS должен быть определен стиль .rec-dot-pulse"
    assert "recDotPulse" in css, "В CSS должна быть определена анимация пульсации @keyframes recDotPulse"

    # 3. Защита от перекрытия модалки сохранения нативным окном Roblox
    assert 'setScreen("scenarios");' in js
    assert 'if (window.pywebview?.api?.hide_game)' in js
    stop_flow_idx = js.find("async function stopPathRecordingFlow()")
    assert stop_flow_idx != -1
    stop_flow_chunk = js[stop_flow_idx:stop_flow_idx + 2500]
    set_screen_pos = stop_flow_chunk.find('setScreen("scenarios")')
    save_modal_pos = stop_flow_chunk.find('saveModal.hidden = false')
    assert set_screen_pos != -1 and save_modal_pos != -1
    assert set_screen_pos < save_modal_pos, (
        "setScreen('scenarios') обязан вызываться ДО saveModal.hidden = false, "
        "иначе нативное окно Roblox перекроет модалку сохранения"
    )

    # 4. Стилизация поля ввода savePathInput
    assert 'class="glass-input-wrap"' in html
    assert 'class="glass-input"' in html
    assert ".glass-input-wrap" in css
    assert ".glass-input" in css
    assert ".glass-input-ic" in css

    # 5. Хоткей записи маршрута WASD
    assert "toggle_walk_record" in HOTKEY_DEFAULTS
    assert HOTKEY_DEFAULTS["toggle_walk_record"] == "alt+9"
    assert "toggle_walk_record" in HOTKEY_LABELS
    assert hasattr(Api, "hotkey_toggle_walk_record")
    assert "startWalkRecordHotkey" in js
    assert "stopWalkRecordHotkey" in js

    # 6. Плавный драг задач и синхронизация realTasksList
    assert ".task-drag-ghost" in css
    assert "task-drag-ghost" in js
    assert "realTasksList = newIds.map(id => taskMap.get(id))" in js


def test_modal_close_buttons_use_cross_icon_and_danger_hover():
    """Ловит баг непонятных и вводящих в заблуждение иконок закрытия модальных окон:
    ранее в кнопках закрытия модалок (Edit Block, Insert Action, Sprites, Paths, Maps)
    ошибочно стояла иконка окна (#i-window), что выглядело как 'открыть в окне' или свернуть,
    а не закрыть. Теперь:
    1. Все модальные кнопки закрытия (blockModalClose, insertActionClose, savePathClose,
       craftingSpritesClose, fuelPathsClose, challengeMapsClose) используют понятный крестик (#i-close).
    2. Ни одна кнопка закрытия не использует #i-window.
    3. Кнопки закрытия снабжены классом btn-danger-hover и стилем деликатного красного ховера в CSS.
    4. Локализация data-i18n-title="btn_close" переводит подсказку на русский ('Закрыть') и английский ('Close').
    """
    import re

    html = GLASS_HTML.read_text(encoding="utf-8")
    js = GLASS_JS.read_text(encoding="utf-8")
    css = GLASS_CSS.read_text(encoding="utf-8")

    modal_close_ids = [
        "blockModalClose",
        "insertActionClose",
        "savePathClose",
        "craftingSpritesClose",
        "fuelPathsClose",
        "challengeMapsClose",
    ]

    for btn_id in modal_close_ids:
        # Проверяем, что кнопка присутствует в разметке
        pattern = rf'<button[^>]*id="{btn_id}"[^>]*>[\s\S]*?</button>'
        match = re.search(pattern, html)
        assert match is not None, f"Кнопка закрытия модалки #{btn_id} должна быть в HTML"
        btn_html = match.group(0)

        # 1. Должна использовать крестик #i-close
        assert 'href="#i-close"' in btn_html, (
            f"Кнопка #{btn_id} обязана использовать векторный крестик href=\"#i-close\""
        )
        # 2. Не должна использовать иконку окна #i-window
        assert 'href="#i-window"' not in btn_html, (
            f"Кнопка #{btn_id} не должна использовать иконку окна #i-window"
        )
        # 3. Должна иметь класс btn-danger-hover для интуитивного красного подсвета при наведении
        assert "btn-danger-hover" in btn_html, (
            f"Кнопка #{btn_id} должна иметь класс btn-danger-hover"
        )
        # 4. Должна иметь data-i18n-title="btn_close"
        assert 'data-i18n-title="btn_close"' in btn_html, (
            f"Кнопка #{btn_id} должна иметь data-i18n-title=\"btn_close\""
        )

    # 5. Проверка наличия перевода btn_close в app.js
    assert 'btn_close: "Close"' in js, "В словаре DICT.en должен быть ключ btn_close: 'Close'"
    assert 'btn_close: "Закрыть"' in js, "В словаре DICT.ru должен быть ключ btn_close: 'Закрыть'"

    # 6. Проверка стилей ховера в CSS
    assert ".btn-danger-hover:hover" in css, "В style.css должен быть определен стиль .btn-danger-hover:hover"


def test_multikey_hotkey_recording_and_clear_buttons():
    """Ловит баги записи многоклавишных комбинаций хоткеев и отсутствия кнопки сброса:
    1. Ранее при нажатии Alt обработчик мгновенно сохранял одиночный Alt из-за { once: true }.
       Теперь при нажатии модификатора (Alt/Ctrl/Shift) отображается промежуточное состояние 'Alt + ...',
       а комбинация сохраняется только при нажатии целевой клавиши (например, Alt+9 или Alt+F5).
    2. У каждого поля назначения хоткея добавлена кнопка-крестик data-hotkey-clear для быстрого сброса бинда.
    3. Дефолты в main.py и интерфейсе: auto_restart_loop -> Alt+F5, vip_rejoin -> Alt+F6, open_replay -> F10.
    4. В CSS присутствуют правила для .hotk-bind-wrap, .hotk-clear-btn и .kbd-btn.is-listening.
    """
    import main

    html = GLASS_HTML.read_text(encoding="utf-8")
    js = GLASS_JS.read_text(encoding="utf-8")
    css = GLASS_CSS.read_text(encoding="utf-8")

    # 1. Проверка обновленных стандартных хоткеев
    assert main.HOTKEY_DEFAULTS["auto_restart_loop"] == "alt+f5"
    assert main.HOTKEY_DEFAULTS["vip_rejoin"] == "alt+f6"
    assert main.HOTKEY_DEFAULTS["open_replay"] == "f10"

    # 2. Наличие кнопок сброса data-hotkey-clear для действий
    hotkey_actions = [
        "macro_start", "macro_stop", "macro_pause", "debug_screenshot",
        "toggle_game", "auto_restart_loop", "vip_rejoin",
        "toggle_record", "open_replay", "toggle_walk_record"
    ]
    for act in hotkey_actions:
        assert f'data-hotkey="{act}"' in html, f"Кнопка data-hotkey=\"{act}\" должна присутствовать"
        assert f'data-hotkey-clear="{act}"' in html, f"Кнопка сброса data-hotkey-clear=\"{act}\" должна присутствовать"

    # 3. Логика записи комбинаций в app.js
    assert 'isMod = ["Control", "Alt", "Shift", "Meta"].includes(e.key)' in js
    assert 'btn.textContent = activeMods.join("+") + " + ...";' in js
    assert 'data-hotkey-clear' in js
    assert 'pywebview.api.set_hotkey(action, "")' in js

    # 4. Стили в CSS
    assert ".hotk-bind-wrap" in css
    assert ".hotk-clear-btn" in css
    assert ".kbd-btn.is-listening" in css


def test_f10_recordings_drawer_and_defaults():
    """Ловит баги открытия списка записей и работы шторки по F10:
    1. Шторка #recDrawer и затемнение #recDrawerBackdrop присутствуют в HTML.
    2. Кнопка закрытия шторки #recDrawerClose использует векторный крестик #i-close и класс btn-danger-hover.
    3. Шторка имеет анимацию выезда от правого края: transform: translateX(100%) -> transform: translateX(0).
    4. При открытии шторки вызывается pywebview.api.hide_game(), чтобы нативное окно Roblox
       не рисовалось поверх списка записей.
    5. Функция window.toggleRecordingsOverlay привязана к toggleRecordingsDrawer.
    6. В app.js зарегистрирован перехват F10 и Escape для открытия и закрытия шторки.
    7. Добавлены переводы для элементов шторки в DICT.en и DICT.ru.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    js = GLASS_JS.read_text(encoding="utf-8")
    css = GLASS_CSS.read_text(encoding="utf-8")

    # 1. HTML разметка шторки
    assert 'id="recDrawerBackdrop"' in html
    assert 'id="recDrawer"' in html
    assert 'id="recDrawerClose"' in html
    assert 'id="recDrawerSearch"' in html
    assert 'id="recDrawerList"' in html
    assert 'id="btnDrawerToggleMode"' in html
    assert 'id="btnDrawerDone"' in html

    # 2. Крестик закрытия шторки
    assert '<button class="icon-btn btn-danger-hover" id="recDrawerClose"' in html
    assert 'href="#i-close"' in html

    # 3. CSS стили шторки от правого края
    assert ".rec-drawer {" in css
    assert "transform: translateX(100%);" in css
    assert ".rec-drawer.is-open {" in css
    assert "transform: translateX(0);" in css
    assert ".rec-drawer-backdrop" in css

    # 4. Скрытие игры и функции шторки в JS
    assert "openRecordingsDrawer" in js
    assert "closeRecordingsDrawer" in js
    assert "toggleRecordingsDrawer" in js
    assert "renderRecordingsDrawer" in js
    assert "selectDrawerRecording" in js
    assert "hide_game" in js

    # 5. Привязка хоткеев и toggleRecordingsOverlay
    assert "window.toggleRecordingsOverlay = function() {" in js
    assert 'e.key === "F10"' in js
    assert "toggleRecordingsDrawer();" in js

    # 6. Переводы
    assert 'drawer_recordings_title: "Recordings"' in js
    assert 'drawer_recordings_title: "Записи"' in js


def test_dashboard_mini_queue_enabled_filtering_and_styling():
    """Ловит баг отображения отключенных задач на дашборде и каши при разном масштабе:
    1. Функция renderMiniQueue фильтрует задачи по task.enabled !== false,
       так что выключенные в списке задачи не засоряют предстоящую очередь на Панели.
    2. Счетчик miniQueueCount отображает число именно активных задач.
    3. При отсутствии активных задач показывается аккуратное пустое состояние.
    4. В CSS для .mini-queue-item:nth-child(even) задано чередование строк (зебра)
       для читаемости при любом масштабе.
    5. Для .mini-queue-list задан адаптивный max-height с прокруткой без переполнения карточки.
    """
    js = GLASS_JS.read_text(encoding="utf-8")
    css = GLASS_CSS.read_text(encoding="utf-8")

    # 1. Фильтрация активных задач
    assert "allTasks.filter(t => t && t.enabled !== false)" in js

    # 2. Стили зебры и прокрутки в CSS
    assert ".mini-queue-item:nth-child(even)" in css
    assert ".mini-queue-list {" in css
    assert "overflow-y: auto;" in css
    assert "clamp(" in css


def test_rec_drawer_header_harmonious_styling():
    """Ловит баг 'висящего' в случайном месте счетчика записей в шторке F10:
    1. Вместо растянутого section-label с justify-content: space-between
       используется компактный .rec-drawer-title-row с inline-выравниванием.
    2. Счетчик #recDrawerCount оформлен как аккуратный стеклянный бейдж .rec-drawer-count-badge
       непосредственно рядом с названием 'Записи'.
    3. Иконка, текст заголовка и бейдж выровнены по одной линии по центру.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    css = GLASS_CSS.read_text(encoding="utf-8")

    assert '<div class="rec-drawer-title-row">' in html
    assert '<span class="rec-drawer-title-text"' in html
    assert '<span class="rec-drawer-count-badge mono" id="recDrawerCount">0</span>' in html

    assert ".rec-drawer-title-row {" in css
    assert ".rec-drawer-count-badge {" in css
    assert "border-radius: 999px;" in css


def test_quick_actions_default_kbd_badges_and_dynamic_sync():
    """Ловит баг некорректных или статичных подписей хоткеев на кнопках Quick Actions:
    1. По стандарту на кнопках дашборда указаны Alt+F5 для Auto-Restart и Alt+F6 для VIP Rejoin.
    2. В loadHotkeys() значения в #kbdAutoRestart и #kbdVipRejoin динамически обновляются
       из настроек привязок.
    """
    html = GLASS_HTML.read_text(encoding="utf-8")
    js = GLASS_JS.read_text(encoding="utf-8")

    assert '<kbd class="btn-kbd" id="kbdAutoRestart">Alt+F5</kbd>' in html
    assert '<kbd class="btn-kbd" id="kbdVipRejoin">Alt+F6</kbd>' in html

    assert 'const kbdRestart = $("#kbdAutoRestart");' in js
    assert 'const kbdVip = $("#kbdVipRejoin");' in js


def test_window_manager_pid_filtering_prevents_browser_docking(monkeypatch):
    """Ловит баг прикрепления окна Roblox к браузеру Chrome/Edge:
    WindowManager(GUI_TITLE, pid=os.getpid()) обязан фильтровать окна по PID,
    чтобы окно браузера с вкладкой 'Anime Expeditions' не было ошибочно
    распознано как окно самого макроса.
    """
    import os
    import sys
    from core.window import get_window_manager

    # Проверяем Windows-реализацию
    if sys.platform == "win32":
        from core import window_win

        fake_chrome_hwnd = 1001
        fake_macro_hwnd = 2002
        current_pid = os.getpid()
        chrome_pid = current_pid + 999

        # Моделируем перечисление окон: сначала идет Chrome с вкладкой "Anime Expeditions",
        # затем настоящее окно макроса "Anime Expeditions"
        def fake_enum_windows(callback, lparam):
            # Первое окно: Chrome
            callback(fake_chrome_hwnd, lparam)
            # Второе окно: макрос
            callback(fake_macro_hwnd, lparam)

        def fake_is_window_visible(hwnd):
            return True

        def fake_get_window_text_length(hwnd):
            return 100

        def fake_get_window_text(hwnd, buf, maxlen):
            if hwnd == fake_chrome_hwnd:
                buf.value = "Anime Expeditions | Play on Roblox - Google Chrome"
            else:
                buf.value = "Anime Expeditions"
            return len(buf.value)

        def fake_get_window_pid(hwnd):
            return chrome_pid if hwnd == fake_chrome_hwnd else current_pid

        monkeypatch.setattr(window_win.user32, "EnumWindows", fake_enum_windows)
        monkeypatch.setattr(window_win.user32, "IsWindowVisible", fake_is_window_visible)
        monkeypatch.setattr(window_win.user32, "GetWindowTextLengthW", fake_get_window_text_length)
        monkeypatch.setattr(window_win.user32, "GetWindowTextW", fake_get_window_text)
        monkeypatch.setattr(window_win, "get_window_pid", fake_get_window_pid)

        # Без pid: найдет первое окно (Chrome!) - моделируем старый баг
        wm_unfiltered = get_window_manager("Anime Expeditions")
        assert wm_unfiltered.find() == fake_chrome_hwnd, "Без фильтрации по pid возвращается Chrome"

        # С pid: проигнорирует Chrome и найдет строго окно текущего процесса макроса!
        wm_filtered = get_window_manager("Anime Expeditions", pid=current_pid)
        assert wm_filtered.find() == fake_macro_hwnd, "С pid обязан возвращаться строго HWND процесса макроса"


def test_language_persistence_and_settings_sync(monkeypatch):
    """Ловит баг сброса языка интерфейса при перезапуске и рассинхронизацию с settings.json.
    Проверяет, что main.Api.get_settings возвращает 'lang' и 'use_glass_ui',
    а фронтенд сохраняет язык через pywebview.api.set_setting.
    """
    import main
    from core import settings

    monkeypatch.setattr(settings, "load", lambda: {"lang": "en", "use_glass_ui": True})
    api = main.Api()
    st = api.get_settings()
    assert st.get("lang") == "en", "Api.get_settings обязан отдавать сохраненный язык"
    assert st.get("use_glass_ui") is True, "Api.get_settings обязан отдавать use_glass_ui"

    js_code = GLASS_JS.read_text(encoding="utf-8")
    assert 'set_setting("lang", LANG)' in js_code or "set_setting('lang', LANG)" in js_code, (
        "Обработчик переключения языка обязан сохранять выбор через set_setting('lang', ...)"
    )


def test_scenarios_screen_always_rerenders_with_active_lang():
    """Ловит баг отображения карточек сценариев на русском при активном английском языке.
    Проверяет, что при переходе на экран 'scenarios' вызывается renderScenarioView(),
    а в словаре KNOWN_COMMENTS присутствуют все основные фразы шаблонов.
    """
    js_code = GLASS_JS.read_text(encoding="utf-8")
    assert 'if (typeof renderScenarioView === "function") renderScenarioView();' in js_code, (
        "setScreen('scenarios') обязан вызывать renderScenarioView() для актуализации языка карточек"
    )
    assert '"Пауза перед экипировкой"' in js_code, "KNOWN_COMMENTS обязан содержать 'Пауза перед экипировкой'"
    assert '"Взять удочку (Слот 1 хотбара)"' in js_code, "KNOWN_COMMENTS обязан содержать 'Взять удочку (Слот 1 хотбара)'"
    assert '"Первый заброс удочки в озеро"' in js_code, "KNOWN_COMMENTS обязан содержать 'Первый заброс удочки в озеро'"




