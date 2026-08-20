"""EXPEDITION ЗАВИСАЛА НАВСЕГДА, И ЗАБЕГИ ШЛИ БЕЗ ЮНИТОВ.

Живой лог, с которого всё началось:

    Wave Continue found (x=575) -- clicking it.
    Follow-up Continue found at (493, 413) -- clicking it.
    Found "nav_start_game" again mid-run -- clicking it.
    Wave Continue found (x=575) -- clicking it.
    Follow-up Continue found at (493, 413) -- clicking it.
    Found "nav_start_game" again mid-run -- clicking it.
    ... и так до бесконечности

Все три строки с ОДНИМИ И ТЕМИ ЖЕ координатами — экран не менялся вообще.
Матч не заканчивался никогда, а значит Pre Start больше не отрабатывал, и
каждый следующий заход шёл без юнитов: гарантированный слив.

Две дыры, обе закрыты здесь:

1. Ветка Expedition в _wait_for_match_result делала `continue` и ПРОСКАКИВАЛА
   мимо страховки конца матча, которая есть у Story/Raid. То есть понять, что
   забег кончился, Expedition могла только по совпадению эталона «defeat» — не
   совпал, и всё, других способов нет.
   Но втащить туда всю страховку нельзя: её вторая половина срабатывает на
   видимую кнопку старта, а в Expedition та ЗАКОННО висит посреди забега.
   Берём только половину с «Repeat Stage».

2. Само пере-нажатие кнопки старта было ничем не ограничено. Теперь если она
   всплывает раз за разом, а до чекпойнта дело не доходит — выходим в лобби и
   заходим заново, то есть Pre Start снова расставит юнитов.
"""
import threading
import types

import pytest

from core import runner as runner_module
from core import vision
from core.runner_constants import (EXTRACT_CONFIRM_SETTLE, EXP_STUCK_START_GAME_CLICKS,
                                    MATCH_END_BUTTON_NAME, RESULT_UNKNOWN)

HWND = 777


class _Runner(runner_module.MacroRunner):
    def __init__(self):
        self.logs = []
        self._expedition_extract_count = 0
        self._expedition_extract_accept_at = 1
        self._exp_start_game_reclicks = 0
        self._exp_stuck = False
        self._exp_stuck_shot = None
        self._exp_last_sighting_at = 0.0
        self._battle_started_at = 0.0
        self._coords = {"screen_middle_x": 576, "screen_middle_y": 378}
        self._keyboard = types.SimpleNamespace(tap=lambda vk: None)
        self._mouse = types.SimpleNamespace(click=lambda x, y: None)

    def _log(self, message):
        self.logs.append(message)

    def _debug_save(self, *a, **kw):
        return None

    def _save_debug_screenshot_unconditional(self, *a, **kw):
        return None

    def _checkpoint(self, stop_event):
        return False


@pytest.fixture
def rig(monkeypatch):
    monkeypatch.setattr(runner_module.wm, "get_window_rect_screen", lambda hwnd: (0, 0, 1152, 756))
    from core import runner_expedition
    monkeypatch.setattr(runner_expedition.wm, "get_window_rect_screen", lambda hwnd: (0, 0, 1152, 756))
    monkeypatch.setattr(runner_expedition.vision, "click_match", lambda *a, **kw: None)
    return _Runner()


# ── 1. Страховка конца матча ──────────────────────────────────────────────

def test_expedition_now_notices_the_result_screen_without_a_banner(rig, monkeypatch):
    """Экран результата на месте («Repeat Stage»), а баннер не совпал.
    Раньше Expedition этого не замечала вовсе и висела до таймаута."""
    def find_image(hwnd, name, threshold=None, **kw):
        if name == MATCH_END_BUTTON_NAME:
            return {"score": 0.95}
        return None                     # ни «victory», ни «defeat» не совпадают

    monkeypatch.setattr(runner_module.vision, "find_image", find_image)

    ended = rig._match_ended_without_a_banner(HWND, allow_start_game_fallback=False)
    assert ended == RESULT_UNKNOWN, "матч кончился — это надо заметить"


def test_a_visible_start_button_does_not_end_an_expedition_run(rig, monkeypatch):
    """ГЛАВНОЕ ОГРАНИЧЕНИЕ ПРАВКИ. В Expedition кнопка старта законно висит
    посреди забега — если считать её концом раунда, живые забеги обрывались бы
    на каждом чекпойнте. Для Story/Raid поведение обязано остаться прежним."""
    def find_image(hwnd, name, threshold=None, **kw):
        if name == MATCH_END_BUTTON_NAME:
            return None                 # экрана результата нет
        return None

    monkeypatch.setattr(runner_module.vision, "find_image", find_image)
    monkeypatch.setattr(rig, "_find_start_game_button",
                        lambda hwnd: ("nav_start_game", {"score": 1.0}))

    assert rig._match_ended_without_a_banner(HWND, allow_start_game_fallback=False) is None

    # А для Story/Raid та же ситуация по-прежнему означает «раунд кончился».
    assert rig._match_ended_without_a_banner(HWND) is not None


# ── 2. Предохранитель от петли ────────────────────────────────────────────

def _only_start_game(monkeypatch, rig):
    """Экран, на котором ВСЕГДА висит кнопка старта и больше ничего."""
    from core import runner_expedition
    monkeypatch.setattr(rig, "_find_start_game_button",
                        lambda hwnd: ("nav_start_game", {"score": 1.0}))
    monkeypatch.setattr(runner_expedition.vision, "find_image",
                        lambda hwnd, name, **kw: None)


def test_the_start_button_loop_eventually_gives_up(rig, monkeypatch):
    """Кнопка всплывает раз за разом, чекпойнтов нет — надо сдаться и уйти в
    лобби, а не долбиться в неё до утра."""
    _only_start_game(monkeypatch, rig)
    stop = threading.Event()

    for _ in range(EXP_STUCK_START_GAME_CLICKS + 1):
        assert rig._check_expedition_wave_result(HWND, stop) is None

    assert rig._exp_start_game_reclicks > EXP_STUCK_START_GAME_CLICKS
    assert any("застряли" in m for m in rig.logs), rig.logs
    # Флагом, а не возвратом: None здесь означает «опрашивай дальше», и выйти
    # им из ожидания матча невозможно — забег досидел бы до 30-минутного
    # таймаута, продолжая долбиться в тот же экран.
    assert rig._exp_stuck is True, "ожидание матча должно быть прервано флагом"


def test_the_stuck_flag_ends_the_match_wait_and_pings_discord(rig, monkeypatch):
    """Проверка сквозная: флаг обязан оборвать ожидание матча и уйти в
    уведомление, иначе предохранитель только перестаёт жать кнопку, а забег
    всё равно висит до таймаута."""
    sent = []
    rig._exp_stuck = True
    rig._exp_stuck_shot = None
    rig._battle_leave_requested = False
    rig._battle_status_minute = None
    rig._pause_event = threading.Event()
    rig._retry_pending_placements = lambda *a: None
    rig._tick_loop_phases = lambda *a: None
    rig._infinite_wave_limit = lambda task: None
    rig._set_status = lambda **kw: None
    rig._check_expedition_wave_result = lambda hwnd, stop: None
    rig._send_event_webhook = lambda *a, **kw: sent.append(a[2])
    monkeypatch.setattr(runner_module.vision, "find_image", lambda *a, **kw: None)

    out = rig._wait_for_match_result(HWND, threading.Event(), mode="expedition",
                                      webhook={"url": "x", "enabled": True}, task={})

    assert out is None, "ожидание матча обязано закончиться, а не крутиться дальше"
    assert any("застряла" in t for t in sent), sent
    assert rig._exp_stuck is False, "флаг снимается, иначе следующий матч оборвётся сразу"


def test_a_few_start_button_sightings_are_still_normal(rig, monkeypatch):
    """Она законно появляется между волнами — предохранитель не должен
    срабатывать на обычном забеге."""
    _only_start_game(monkeypatch, rig)
    stop = threading.Event()

    for _ in range(EXP_STUCK_START_GAME_CLICKS - 1):
        rig._check_expedition_wave_result(HWND, stop)

    assert not any("застряли" in m for m in rig.logs), rig.logs


def test_reaching_a_checkpoint_clears_the_stuck_counter(rig, monkeypatch):
    """Дошли до настоящего чекпойнта — забег движется, счёт застревания
    обнуляется. Иначе длинный забег со многими волнами упёрся бы в порог сам
    по себе."""
    _only_start_game(monkeypatch, rig)
    stop = threading.Event()
    for _ in range(EXP_STUCK_START_GAME_CLICKS - 1):
        rig._check_expedition_wave_result(HWND, stop)
    assert rig._exp_start_game_reclicks > 0

    # Настоящий чекпойнт по шаблонному пути.
    from core import runner_expedition
    rig._expedition_color_buttons = False
    rig._expedition_extract_accept_at = 99          # не извлекаемся, просто считаем
    monkeypatch.setattr(rig, "_find_start_game_button", lambda hwnd: (None, None))
    monkeypatch.setattr(rig, "_dismiss_reward_card_if_found", lambda hwnd: False)
    monkeypatch.setattr(rig, "_click_and_verify_gone", lambda *a, **kw: False)
    monkeypatch.setattr(runner_expedition.vision, "find_image",
                        lambda hwnd, name, **kw: {"score": 0.95} if name == "exp_extract" else None)

    rig._check_expedition_wave_result(HWND, stop)
    assert rig._exp_start_game_reclicks == 0, "чекпойнт обязан сбросить счётчик"


def test_extract_waits_for_the_reward_transition_before_calling_it_a_failed_click(rig, monkeypatch):
    """Confirm исчезает раньше, чем сама игра убирает нижний чекпойнт.

    Раньше цветной путь ждал лишь 0.8 с, видел ещё живую кнопку Continue и
    переходил к следующему чекпойнту, хотя эвакуация могла уже загружаться.
    Здесь фиксируем общий интервал ожидания шаблонной и цветной веток.
    """
    from core import runner_expedition

    waits = []
    calls = {"confirm": 0, "checkpoint": 0}

    def find_color_run(hwnd, band, color, minimum):
        if band == runner_expedition.EXP_COLOR_CONTINUE_BAND and color == runner_expedition._exp_red:
            return {"cx": 513, "cy": 588}      # исходный Extract
        if band == runner_expedition.EXP_COLOR_CONFIRM_BAND and color == runner_expedition._exp_red:
            calls["confirm"] += 1
            return {"cx": 576, "cy": 540} if calls["confirm"] == 1 else None
        if band == runner_expedition.EXP_COLOR_CONTINUE_BAND and color == runner_expedition._exp_green:
            calls["checkpoint"] += 1
            return {"cx": 637, "cy": 406}      # переход ещё не дорисовался
        return None

    monkeypatch.setattr(runner_expedition.vision, "find_color_run", find_color_run)
    monkeypatch.setattr(runner_expedition.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(rig, "_interruptible_sleep", lambda seconds, stop: waits.append(seconds))
    # Одной полной попытки достаточно для проверки ожидания; следующую не
    # запускаем, потому что она не относится к этой регрессии.
    checkpoint_calls = {"count": 0}

    def checkpoint_after_first_attempt(stop):
        checkpoint_calls["count"] += 1
        # Внутри первой попытки _checkpoint вызывается дважды: перед кликом
        # Extract и в поиске confirm. Третья проверка — уже начало второй
        # попытки, её и используем для остановки тестовой заглушки.
        return checkpoint_calls["count"] >= 3

    monkeypatch.setattr(rig, "_checkpoint", checkpoint_after_first_attempt)

    assert rig._extract_via_mirrored_button(HWND, threading.Event(), 0, 0, 576,
                                            {"cx": 637, "cy": 406}) is False
    assert waits == [EXTRACT_CONFIRM_SETTLE]
    assert calls["checkpoint"] == 1
