"""Тесты для механики Portals, Autoplay и сопутствующих расширений блоков/детекта.

Проверяет:
1. Поиск средней карточки порталов (_find_middle_portal_card):
   - Меньше 3 карточек -> None (ждём полного появления).
   - 3 и более карточек -> выбор средней по оси X (полю cx).
2. Разрешение координат порталов (_portal_task_point):
   - Корректные координаты из задачи для слота лобби/выбора.
   - Возврат None при отсутствии или некорректных значениях.
3. Переключение автоплея (_settle_autoplay_for_match):
   - Включение автоплея при auto_play='autoplay'.
   - Выключение автоплея при auto_play='macro'.
   - Пропуск переключения при переходе из chooser в порталах (состояние сохраняется).
4. Счётчик в блоках детекта (_eval_counter / _counter_limit):
   - Чтение лимита из задачи через limit_from_task.
   - Фолбэк на собственный limit блока при отсутствии поля в задаче.
   - Бесконечный цикл при limit <= 0.
   - Ограничение проходов: ровно N раз True (THEN), затем False (ELSE).
5. Расширения блоков (BlockOps):
   - Пропуск блоков в _run_prestart_blocks при совпадении режима задачи с skip_modes.
   - Разрешение координат клика по coord_key из конфигурации runner._coords в _run_click_block.
"""
import threading
from unittest.mock import MagicMock, patch
import pytest

from core import detect
from core import vision
from core.runner_blocks import BlockOps
from core.runner import MacroRunner


class DummyBlockRunner(BlockOps):
    def __init__(self, task=None, coords=None):
        self.logs = []
        self._task = task or {}
        self._coords = coords or {}
        self._mouse = MagicMock()
        self.stop_requested = False
        self.pause_requested = False

    def _log(self, msg):
        self.logs.append(msg)

    def _checkpoint(self, stop_event=None):
        return False

    def _release_quick_place_shift(self):
        pass


# ---------------------------------------------------------------------------
# 1. Поиск средней карточки порталов
# ---------------------------------------------------------------------------

@patch("core.vision.find_image_all")
def test_find_middle_portal_card_requires_at_least_three_cards(mock_find):
    """Ловит баг клика по неполному набору карточек выбора портала.

    Если на экране отрисовались ещё не все 3 карточки (например, анимация
    появления показала только 1 или 2), кликать нельзя — координаты средней
    карточки будут неверными, и макрос выберет не тот портал.
    """
    runner = MacroRunner.__new__(MacroRunner)
    mock_find.return_value = []
    assert runner._find_middle_portal_card(12345) is None

    mock_find.return_value = [{"cx": 200, "cy": 300}]
    assert runner._find_middle_portal_card(12345) is None

    mock_find.return_value = [{"cx": 200, "cy": 300}, {"cx": 600, "cy": 300}]
    assert runner._find_middle_portal_card(12345) is None


@patch("core.vision.find_image_all")
def test_choose_portal_card_picks_randomly_and_offsets_click(mock_find):
    """Проверяет случайный выбор карты портала из трех предложенных и смещение клика в тело карты.

    Ловит баг жестко фиксированного выбора всегда средней карты, о котором просил пользователь
    («ну и порталы между 3 чтоб выбирался рандомно ваще»), а также проверяет, что координаты клика
    смещаются на +60px по Y прямо в кликабельное тело карты, а _cards отсортированы слева направо.
    """
    runner = MacroRunner.__new__(MacroRunner)
    left = {"cx": 250, "cy": 400, "score": 0.9}
    mid = {"cx": 500, "cy": 400, "score": 0.95}
    right = {"cx": 750, "cy": 400, "score": 0.92}

    mock_find.return_value = [right, left, mid]
    with patch("random.choice", side_effect=lambda x: x[1]):
        chosen = runner._choose_portal_card(12345)
        assert chosen is not None
        assert chosen["cx"] == 500
        assert chosen["cy"] == 460  # 400 + 60px в тело карты
        assert chosen["_cards"] == [left, mid, right]
        assert chosen["_index"] == 2

    with patch("random.choice", side_effect=lambda x: x[0]):
        chosen_left = runner._choose_portal_card(12345)
        assert chosen_left["cx"] == 250
        assert chosen_left["cy"] == 460
        assert chosen_left["_index"] == 1


# ---------------------------------------------------------------------------
# 2. Разрешение координат порталов
# ---------------------------------------------------------------------------

def test_portal_task_point_reads_from_task_or_returns_none():
    """Проверяет чтение координат слота портала из параметров задачи.

    В порталах координаты слота уникальны для каждого типа задачи (lobby/chooser)
    и хранятся в задаче. Если координаты не заданы или испорчены, возвращается None.
    """
    # Валидные числа
    task_int = {"portal_lobby_x": 450, "portal_lobby_y": 320}
    assert MacroRunner._portal_task_point(task_int, "lobby") == (450, 320)

    # Строковые значения
    task_str = {"portal_chooser_x": "550", "portal_chooser_y": "380"}
    assert MacroRunner._portal_task_point(task_str, "chooser") == (550, 380)

    # Отсутствующие ключи
    empty_task = {}
    assert MacroRunner._portal_task_point(empty_task, "lobby") is None

    # Некорректные значения
    junk_task = {"portal_lobby_x": "invalid", "portal_lobby_y": 100}
    assert MacroRunner._portal_task_point(junk_task, "lobby") is None


# ---------------------------------------------------------------------------
# 3. Переключение автоплея
# ---------------------------------------------------------------------------

def test_settle_autoplay_turns_on_when_requested():
    """Проверяет включение Autoplay перед боем, если в задаче auto_play='autoplay'."""
    runner = MacroRunner.__new__(MacroRunner)
    runner._ensure_autoplay = MagicMock()
    stop_event = threading.Event()

    task = {"auto_play": "autoplay"}
    runner._settle_autoplay_for_match(12345, stop_event, task)

    runner._ensure_autoplay.assert_called_once_with(12345, stop_event, True)


def test_settle_autoplay_turns_off_when_macro():
    """Проверяет отключение Autoplay, если в задаче auto_play='macro'."""
    runner = MacroRunner.__new__(MacroRunner)
    runner._ensure_autoplay = MagicMock()
    stop_event = threading.Event()

    task = {"auto_play": "macro"}
    runner._settle_autoplay_for_match(12345, stop_event, task)

    runner._ensure_autoplay.assert_called_once_with(12345, stop_event, False)


def test_settle_autoplay_skips_when_came_from_chooser():
    """Пропускает переключение автоплея в цепочке порталов (состояние игры сохраняется)."""
    runner = MacroRunner.__new__(MacroRunner)
    runner.logs = []
    runner._log = lambda msg: runner.logs.append(msg)
    runner._ensure_autoplay = MagicMock()
    runner._portal_entered_from = "chooser"
    stop_event = threading.Event()

    task = {"mode": "portals", "auto_play": "autoplay"}
    result = runner._settle_autoplay_for_match(12345, stop_event, task)

    assert result is True
    runner._ensure_autoplay.assert_not_called()
    assert any("Came straight from the portal chooser" in log for log in runner.logs)


# ---------------------------------------------------------------------------
# 4. Счётчик в блоках детекта (limit_from_task)
# ---------------------------------------------------------------------------

def test_counter_detect_limit_from_task():
    """Проверяет получение лимита повторов из задачи (limit_from_task).

    В порталах шаблон один для любого количества повторов. Лимит забирается из
    поля задачи (например, extract_after). Первые N раз блок возвращает True
    (ветка THEN продолжать прогон), на N+1 раз — False (ветка ELSE выйти в лобби).
    """
    class DummyCtx:
        def __init__(self, task):
            self.task = task
            self.counters = {}

    ctx = DummyCtx({"extract_after": 2})
    block = {"counter_id": "portal_counter", "limit_from_task": "extract_after", "limit": 99}

    assert detect._eval_counter(ctx, block) is True
    assert detect._eval_counter(ctx, block) is True
    assert detect._eval_counter(ctx, block) is False


def test_counter_detect_fallback_to_own_limit():
    """Проверяет фолбэк на limit блока при отсутствии поля задачи."""
    class DummyCtx:
        def __init__(self, task):
            self.task = task
            self.counters = {}

    ctx = DummyCtx({})
    block = {"counter_id": "test_c", "limit_from_task": "extract_after", "limit": 1}

    assert detect._eval_counter(ctx, block) is True
    assert detect._eval_counter(ctx, block) is False


def test_counter_detect_infinite_when_zero_or_missing_limit():
    """Проверяет бесконечный цикл, если лимит не задан или равен 0."""
    class DummyCtx:
        def __init__(self, task):
            self.task = task
            self.counters = {}

    ctx = DummyCtx({})
    block = {"counter_id": "infinite_c"}

    for _ in range(10):
        assert detect._eval_counter(ctx, block) is True


# ---------------------------------------------------------------------------
# 5. Расширения блоков (BlockOps: skip_modes и coord_key)
# ---------------------------------------------------------------------------

def test_block_ops_skips_when_mode_in_skip_modes():
    """Проверяет пропуск блока в бою, если текущий режим задачи входит в skip_modes."""
    runner = DummyBlockRunner()
    runner._current_task = {"mode": "portals"}
    runner._battle_block_index = 0
    runner._battle_block_state = {}

    block = {
        "type": "click",
        "skip_modes": ["portals", "tower"],
        "params": {"x": 100, "y": 100},
    }
    stop_event = threading.Event()

    runner._run_click_block = MagicMock()
    runner._run_battle_blocks_tick(hwnd=999, stop_event=stop_event, battle_blocks=[block], first_repeat=True)

    # Блок пропущен: индекс увеличен, клик не вызывался
    assert runner._battle_block_index == 1
    runner._run_click_block.assert_not_called()


def test_block_ops_executes_when_mode_not_in_skip_modes():
    """Проверяет исполнение блока в бою, если текущий режим задачи не в skip_modes."""
    runner = DummyBlockRunner()
    runner._current_task = {"mode": "story"}
    runner._battle_block_index = 0
    runner._battle_block_state = {}

    block = {
        "type": "click",
        "skip_modes": ["portals"],
        "params": {"x": 100, "y": 100},
    }
    stop_event = threading.Event()

    runner._run_click_block = MagicMock()
    runner._run_battle_blocks_tick(hwnd=999, stop_event=stop_event, battle_blocks=[block], first_repeat=True)

    runner._run_click_block.assert_called_once_with(999, stop_event, block, 1)


@patch("core.runner_blocks.wm.get_window_rect_screen", return_value=(10, 20, 1000, 800))
def test_block_ops_click_resolves_coord_key(mock_rect):
    """Проверяет клик по именованному ключу coord_key из настроек Macro Coordinates."""
    coords = {"portal_exit_x": 456, "portal_exit_y": 789}
    runner = DummyBlockRunner(coords=coords)
    stop_event = threading.Event()

    block = {
        "type": "click",
        "params": {"coord_key": "portal_exit"},
    }

    runner._run_click_block(hwnd=999, stop_event=stop_event, block=block, block_num=1)

    runner._mouse.click.assert_called_once_with(10 + 456, 20 + 789)
    assert any("clicking (456, 789)" in log for log in runner.logs)


def test_block_ops_click_skips_when_coord_key_not_configured():
    """Проверяет пропуск клика, если coord_key не настроен в конфигурации."""
    runner = DummyBlockRunner(coords={})
    stop_event = threading.Event()

    block = {
        "type": "click",
        "params": {"coord_key": "portal_exit"},
    }

    runner._run_click_block(hwnd=999, stop_event=stop_event, block=block, block_num=1)

    runner._mouse.click.assert_not_called()
    assert any("coord_key 'portal_exit' not set" in log for log in runner.logs)


# ---------------------------------------------------------------------------
# 6. Валидация вкладки порталов и переходов
# ---------------------------------------------------------------------------

@patch("core.vision.find_image_any", return_value=(None, None))
@patch("core.vision.portal_tab_blue_fraction")
def test_portal_tab_is_selected_with_explicit_coords(mock_blue, mock_find):
    """Проверяет распознавание активной вкладки порталов по явным координатам.

    Ловит баг, когда на экране пользователя шаблон selected не совпадает
    из-за масштабирования или темы, но точка вкладки откалибрована и синяя.
    """
    mock_blue.return_value = 0.20
    assert vision.portal_tab_is_selected(12345, coords=(227, 246)) is True

    mock_blue.return_value = 0.00
    assert vision.portal_tab_is_selected(12345, coords=(227, 246)) is False


@patch("core.vision.find_image_any")
@patch("core.vision.portal_tab_blue_fraction")
def test_portal_tab_is_selected_with_relaxed_template_search(mock_blue, mock_find):
    """Проверяет поиск вкладки по шаблонам с пониженным порогом и проверкой цвета."""
    mock_find.return_value = ({"x": 200, "y": 240, "w": 60, "h": 25}, "portal_tab")
    mock_blue.return_value = 0.35
    assert vision.portal_tab_is_selected(12345) is True

    # Тот же шаблон, но цвет серый (невыбранная вкладка) -> False
    mock_blue.return_value = 0.02
    assert vision.portal_tab_is_selected(12345) is False


def test_portal_anchor_verifies_portal_tab_selected_via_color():
    """Проверяет, что _portal_anchor вызывает portal_tab_is_selected для portal_tab_selected.

    Ловит баг, когда _portal_anchor требовал прямого совпадения шаблона
    portal_tab_selected через find_image, из-за чего portal_tab_is_selected
    вообще никогда не вызывался при отсутствии альтернативных шаблонов на диске.
    """
    runner = MacroRunner.__new__(MacroRunner)
    runner._mouse = MagicMock()
    runner._coords = {"portal_tab_x": 227, "portal_tab_y": 246}

    with patch("core.runner.wm.get_window_rect_screen", return_value=(0, 0, 1152, 756)), \
         patch("core.vision.portal_tab_is_selected", return_value=True) as mock_selected, \
         patch("time.sleep"):
        res = runner._portal_anchor(12345, ("portal_tab_selected",), timeout=0)
        assert res == "portal_tab_selected"
        mock_selected.assert_called_once_with(12345, coords=(227, 246))


def test_portal_step_confirms_when_unselected_tab_disappears():
    """Ловит баг зацикливания и сброса задачи при открытии вкладки Portals.

    Когда макрос нажимает на серую вкладку portal_tab, игра переключается на
    порталы, и серая вкладка пропадает. Даже если шаблон portal_tab_selected
    не определился, факт исчезновения невыбранной вкладки portal_tab после клика
    подтверждает, что переключение произошло успешно.
    """
    runner = MacroRunner.__new__(MacroRunner)
    runner.logs = []
    runner._log = lambda msg: runner.logs.append(msg)
    runner._set_status = MagicMock()
    runner._checkpoint = MagicMock(return_value=False)
    runner._interruptible_sleep = MagicMock()
    runner._mouse = MagicMock()
    runner._portal_anchor = MagicMock(return_value=None)  # якорь не увидел selected

    stop_event = threading.Event()

    with patch("core.vision.wait_for_image", return_value={"score": 1.0, "x": 100, "y": 200, "w": 50, "h": 20, "cx": 125, "cy": 210}), \
         patch("core.runner.wm.activate_window", return_value=True), \
         patch("core.vision.click_match"), \
         patch("core.vision.find_image", return_value=None):  # после клика portal_tab исчез!
        res = runner._portal_step(12345, stop_event, "portal_tab", "portal_tab", "Opening the Portals tab",
                                  expect=("portal_tab_selected", "portal_inventory"))
        assert res is True
        assert any("no longer unselected" in log for log in runner.logs)


def test_portal_step_skips_click_when_portal_tab_already_selected():
    """Проверяет пропуск клика, если вкладка Portals уже выбрана при открытии Items."""
    runner = MacroRunner.__new__(MacroRunner)
    runner.logs = []
    runner._log = lambda msg: runner.logs.append(msg)
    runner._set_status = MagicMock()
    runner._portal_anchor = MagicMock(return_value="portal_tab_selected")

    stop_event = threading.Event()
    with patch("core.vision.wait_for_image") as mock_wait:
        res = runner._portal_step(12345, stop_event, "portal_tab", "portal_tab", "Opening the Portals tab",
                                  expect=("portal_tab_selected", "portal_inventory"))
        assert res is True
        mock_wait.assert_not_called()
        assert any("already done" in log for log in runner.logs)


def test_activate_portal_falls_back_to_portal_select():
    """Ловит баг, когда кнопка на карточке портала называется Select, а не Activate.

    В некоторых версиях игры кнопка подтверждения портала из инвентаря имеет
    надпись «Select» (шаблон portal_select), а не «Activate». Макрос обязан
    распознавать и кликать оба варианта.
    """
    runner = MacroRunner.__new__(MacroRunner)
    runner.logs = []
    runner._log = lambda msg: runner.logs.append(msg)
    runner._portal_step = MagicMock(return_value=True)
    runner._checkpoint = MagicMock(return_value=False)

    stop_event = threading.Event()
    with patch("core.vision.find_image", side_effect=lambda hwnd, name: True if name == "portal_select" else None):
        res = runner._activate_portal(12345, stop_event, "the inventory")
        assert res is True
        first_call_args = runner._portal_step.call_args_list[0]
        assert first_call_args[0][2] == "portal_select"


def test_portal_tab_step_does_not_skip_when_unselected_tab_is_on_screen():
    """Ловит баг, когда макрос ошибочно считал вкладку Portals выбранной при открытой вкладке Items.

    Если открыто меню Items и выбрана вкладка Items, на экране видна серая вкладка
    portal_tab. _portal_anchor ни в коем случае не должен возвращать portal_tab_selected,
    а _portal_step обязан выполнить клик по portal_tab, а не пропускать его.
    """
    runner = MacroRunner.__new__(MacroRunner)
    runner.logs = []
    runner._log = lambda msg: runner.logs.append(msg)
    runner._set_status = MagicMock()
    runner._mouse = MagicMock()
    runner._checkpoint = MagicMock(return_value=False)
    runner._interruptible_sleep = MagicMock()

    stop_event = threading.Event()

    # Сначала anchor вызывается для проверки "уже открыто" (timeout=0).
    # Должен вернуть None, чтобы не пропустить клик.
    # После клика anchor вызывается с timeout > 0 и должен вернуть успешное подтверждение.
    anchor_calls = []
    def fake_anchor(hwnd, names, timeout, stop_ev):
        anchor_calls.append((names, timeout))
        if timeout == 0:
            return None  # Не открыто, клик обязателен!
        return "portal_tab_selected"  # После клика подтверждено!

    runner._portal_anchor = fake_anchor

    with patch("core.vision.wait_for_image", return_value={"x": 50, "y": 120, "w": 140, "h": 30, "cx": 120, "cy": 135, "score": 1.0}), \
         patch("core.runner.wm.activate_window", return_value=True), \
         patch("core.vision.click_match") as mock_click:
        res = runner._portal_step(12345, stop_event, "portal_tab", "portal_tab", "Opening the Portals tab",
                                  expect=("portal_tab_selected", "portal_inventory"))
        assert res is True
        mock_click.assert_called_once()
        assert not any("already done" in log for log in runner.logs)
        assert any('found "portal_tab"' in log for log in runner.logs)


def test_activate_portal_falls_back_to_nav_start_game():
    """Ловит баг, когда кнопка старта на экране пати определяется как nav_start_game вместо portal_start.

    Если кнопка Start в лобби портала имеет иную графику (совпадающую с nav_start_game),
    макрос должен использовать nav_start_game для второго шага запуска портала.
    """
    runner = MacroRunner.__new__(MacroRunner)
    runner.logs = []
    runner._log = lambda msg: runner.logs.append(msg)
    runner._portal_step = MagicMock(return_value=True)
    runner._portal_anchor = MagicMock(return_value=None)
    runner._checkpoint = MagicMock(return_value=False)

    stop_event = threading.Event()
    def fake_find(hwnd, name):
        if name == "portal_activate":
            return True
        if name == "nav_start_game":
            return True
        return None

    with patch("core.vision.find_image", side_effect=fake_find):
        res = runner._activate_portal(12345, stop_event, "the inventory")
        assert res is True
        assert runner._portal_step.call_count == 2
        second_call_args = runner._portal_step.call_args_list[1]
        assert second_call_args[0][2] == "nav_start_game"


def test_activate_portal_exits_early_if_match_already_started():
    """Ловит баг повторного клика по Start, если матч начался мгновенно после нажатия Activate.

    Если сразу после нажатия Activate Portal игра перешла в бой (появился HUD матча
    из PORTAL_IN_MATCH_IMAGES), макрос не должен пытаться искать и кликать кнопку Start,
    а обязан завершить шаг успешно.
    """
    runner = MacroRunner.__new__(MacroRunner)
    runner.logs = []
    runner._log = lambda msg: runner.logs.append(msg)
    runner._portal_step = MagicMock(return_value=True)
    # После нажатия Activate на экране сразу виден autoplay_on
    runner._portal_anchor = MagicMock(return_value="autoplay_on")
    runner._checkpoint = MagicMock(return_value=False)

    stop_event = threading.Event()
    with patch("core.vision.find_image", side_effect=lambda hwnd, name: True if name == "portal_activate" else None):
        res = runner._activate_portal(12345, stop_event, "the inventory")
        assert res is True
        # Только 1 вызов _portal_step (Activate), второй (Start) пропущен
        assert runner._portal_step.call_count == 1


def test_run_click_block_skips_autoplay_when_already_on():
    """Ловит баг выключения AutoPlay на 2+ забегах или при повторном клике.

    В Roblox клик по кнопке Auto Play переключает состояние (toggle).
    Если автоплей уже активен ('autoplay_on'), клик по координатам автоплея
    должен быть пропущен, иначе автобой выключится и матч сольется.
    """
    runner = DummyBlockRunner(coords={"autoplay_x": 1123, "autoplay_y": 485})
    runner._autoplay_state = MagicMock(return_value="on")
    stop_event = threading.Event()

    block = {"type": "click", "params": {"x": 1119, "y": 474}}
    with patch("core.window.get_window_rect_screen", return_value=(0, 0, 1152, 756)):
        runner._run_click_block(12345, stop_event, block, 1)

    runner._mouse.click.assert_not_called()
    assert any("Auto Play is already active" in log for log in runner.logs)


def test_run_click_block_clicks_autoplay_when_off():
    """Проверяет, что при выключенном AutoPlay клик штатно выполняется для включения."""
    runner = DummyBlockRunner(coords={"autoplay_x": 1123, "autoplay_y": 485})
    runner._autoplay_state = MagicMock(return_value="off")
    stop_event = threading.Event()

    block = {"type": "click", "params": {"x": 1119, "y": 474}}
    with patch("core.window.get_window_rect_screen", return_value=(100, 200, 1152, 756)):
        runner._run_click_block(12345, stop_event, block, 1)

    runner._mouse.click.assert_called_once_with(100 + 1119, 200 + 474)
    assert not any("Auto Play is already active" in log for log in runner.logs)


def test_autoplay_state_prefers_higher_score():
    """Ловит баг ложного 'on', когда совпали оба шаблона (on и off), но у off балл выше."""
    runner = MacroRunner.__new__(MacroRunner)

    def fake_find_image(_hwnd, name, **_kwargs):
        if name == "autoplay_on":
            return {"score": 0.84}
        if name == "autoplay_off":
            return {"score": 0.95}
        return None

    with patch("core.vision.find_image", side_effect=fake_find_image):
        assert runner._autoplay_state(12345) == "off"


def test_choose_portal_card_uses_game_results_fallback():
    """Проверяет запасной механизм выбора карт портала по кнопке Game Results.

    Ловит баг, когда на экране выбора 3 порталов шаблоны фонарей конкретного тира
    (например, T4 Sky Ruins или T2/T3/T5) не совпали с эталоном, из-за чего макрос
    не выбирал портал и ждал полного истечения 5-секундного таймера автовыбора игры.
    Кнопка Game Results гарантированно распознается, а координаты 3 карт вычисляются
    строго относительно неё.
    """
    runner = MacroRunner.__new__(MacroRunner)
    gr_match = {"cx": 449, "cy": 451, "score": 0.99, "w": 105, "h": 28, "x": 397, "y": 437}

    with patch("core.vision.find_image_all", return_value=[]), \
         patch("core.vision.find_image", side_effect=lambda hwnd, name, threshold=None: gr_match if name == "Game_results" else None):
        with patch("random.choice", side_effect=lambda x: x[1]):  # средняя
            chosen_mid = runner._choose_portal_card(12345)
            assert chosen_mid is not None
            assert chosen_mid["cx"] == 449
            assert chosen_mid["cy"] == 451 - 147  # 304
            assert chosen_mid["_index"] == 2
            assert chosen_mid["_via"] == "Game_results"

        with patch("random.choice", side_effect=lambda x: x[0]):  # левая
            chosen_left = runner._choose_portal_card(12345)
            assert chosen_left["cx"] == 449 - 305  # 144
            assert chosen_left["cy"] == 451 - 147
            assert chosen_left["_index"] == 1

        with patch("random.choice", side_effect=lambda x: x[2]):  # правая
            chosen_right = runner._choose_portal_card(12345)
            assert chosen_right["cx"] == 449 + 305  # 754
            assert chosen_right["cy"] == 451 - 147
            assert chosen_right["_index"] == 3


def test_find_all_in_gray_scans_multiple_variants():
    """Проверяет, что find_all_in_gray сканирует все доступные варианты шаблонов.

    Ловит баг, когда find_all_in_gray проверял только templates[0], из-за чего
    карты тира T4 (хранившиеся в _t4) или альтернативные варианты кнопок игнорировались.
    """
    import numpy as np
    from core import vision

    # Создаем поле с текстурными кнопками (ненулевая дисперсия)
    haystack = np.zeros((100, 200), dtype=np.uint8)

    tpl1 = np.zeros((20, 20), dtype=np.uint8)
    tpl1[5:15, 5:15] = 200
    tpl1[8:12, 8:12] = 100

    tpl2 = np.zeros((20, 20), dtype=np.uint8)
    tpl2[3:17, 3:17] = 250
    tpl2[7:13, 7:13] = 50

    haystack[20:40, 20:40] = tpl1
    haystack[20:40, 120:140] = tpl2

    with patch("core.vision.load_template_grays", return_value=[(tpl1, None), (tpl2, None)]):
        matches = vision.find_all_in_gray(haystack, "dummy_button", threshold=0.80)
        # Должны найтись ОБЕ кнопки: и tpl1, и tpl2
        assert len(matches) == 2
        xs = sorted(m["cx"] for m in matches)
        assert xs[0] == 30   # 20 + 10
        assert xs[1] == 130  # 120 + 10


def test_portal_mode_ends_match_promptly_when_chooser_showing():
    """Проверяет, что при появлении пост-ран экрана порталов матч сразу признается победой.

    Ловит баг долгого ожидания/зависания после боя в режиме порталов, когда баннер Victory
    уже исчез или не показался, но пост-ран экран (portal_select / chooser) уже на экране.
    """
    runner = MacroRunner.__new__(MacroRunner)
    runner._coords = {}
    runner._battle_leave_requested = False
    runner.logs = []
    runner._log = lambda msg: runner.logs.append(msg)
    runner._set_status = lambda *args, **kwargs: None
    runner._checkpoint = MagicMock(return_value=False)
    runner._infinite_wave_limit = MagicMock(return_value=None)
    runner._retry_pending_placements = lambda *args: None
    runner._pulse_battle_status = lambda *args: None
    runner._choose_portal_card = MagicMock(return_value=None)
    runner._portal_chooser_showing = MagicMock(return_value=True)

    with patch("core.runner.MATCH_END_CHECK_EVERY", 1), \
         patch("core.vision.find_image", return_value=None), \
         patch("time.time", side_effect=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]):
        stop_event = threading.Event()
        # В цикле боя при mode="portals" и chooser_showing должен сразу вернуть "win"
        outcome = runner._wait_for_match_result(
            12345, stop_event, battle_blocks=[], first_repeat=False, task={"mode": "portals"}
        )
        assert outcome == "win"
        assert any("Post-run portal screen is already visible" in log for log in runner.logs)