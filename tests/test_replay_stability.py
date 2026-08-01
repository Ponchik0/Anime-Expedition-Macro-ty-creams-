"""УСТОЙЧИВОСТЬ ПОВТОРА: заслонка, подтверждение исхода, тишина, серия поражений.

Четыре разные дыры, через которые повтор молча переставал работать, а снаружи
выглядел живым:

1. Играл в СПРЯТАННОЕ окно. Заслонка «только при активном окне» спрашивала
   один лишь фокус, а встроенная игра прячется на любом экране кроме Панели —
   фокус при этом остаётся на окне макроса, и повтор жал кнопки в никуда.
2. Засчитывал исход по ОДНОМУ кадру. Захват ловит и кадры анимации, и
   полупрозрачные наложения; ложная победа портит винрейт навсегда.
3. МОЛЧАЛ, когда эталоны переставали совпадать. Всю ночь крутится, исходов
   ноль, и об этом никто не узнаёт до утра.
4. Не имел ПРЕДОХРАНИТЕЛЯ. Сломавшаяся запись сливала матч за матчем ровно
   так же бодро, как раньше выигрывала.
"""
import time
import types

import pytest

import main
from core import replay
from core import replay_result
from core import settings as cfg

HWND = 4242


# ── 1. Заслонка: играем только когда игру ВИДНО и она в фокусе ────────────

class _Inp:
    def __init__(self):
        self.downs = []

    def move_abs(self, x, y):
        pass

    def button_down(self, b):
        self.downs.append(b)

    def button_up(self, b):
        pass

    def key_down(self, vk):
        pass

    def key_up(self, vk):
        pass


EVENTS = [{"t": 0.0, "kind": "down", "code": "left", "x": 10, "y": 20},
          {"t": 200.0, "kind": "up", "code": "left", "x": 10, "y": 20}]


def test_replay_stops_when_the_game_is_hidden_behind_another_screen(monkeypatch):
    """Ушёл в Настройки — встроенная игра спрятана, а фокус остался на окне
    макроса. Раньше повтор считал это «игра активна» и продолжал жать."""
    fake = _Inp()
    visible = {"on": True}
    monkeypatch.setattr(replay, "_inp", fake)
    monkeypatch.setattr(replay, "_timer_precision", lambda on: None)
    monkeypatch.setattr(replay, "_game_focused", lambda hwnd: True)   # фокус ЕСТЬ всегда
    monkeypatch.setattr(replay.wm, "is_window_visible", lambda hwnd: visible["on"])
    monkeypatch.setattr(replay.wm, "get_window_rect_screen", lambda hwnd: (0, 0, 1152, 756))

    p = replay.Player(lambda: HWND)
    assert p.start(EVENTS, "забег", loops=0, require_focus=True, duration_ms=200.0)
    time.sleep(0.15)
    assert fake.downs, "пока игру видно — играем"
    played = len(fake.downs)

    visible["on"] = False              # уехали на другой экран, игру спрятали
    time.sleep(0.5)                    # больше двух кругов
    assert len(fake.downs) == played, "в спрятанную игру жать нельзя"

    visible["on"] = True               # вернулись на Панель
    time.sleep(0.3)
    assert len(fake.downs) > played, "вернулись — повтор обязан продолжить"
    p.stop()


def test_the_focus_gate_can_still_be_turned_off(monkeypatch):
    """Галку «только при активном окне» снимают осознанно — тогда играем
    всегда, и новая проверка видимости не должна это отменять."""
    fake = _Inp()
    monkeypatch.setattr(replay, "_inp", fake)
    monkeypatch.setattr(replay, "_timer_precision", lambda on: None)
    monkeypatch.setattr(replay.wm, "is_window_visible", lambda hwnd: False)
    monkeypatch.setattr(replay, "_game_focused", lambda hwnd: False)
    monkeypatch.setattr(replay.wm, "get_window_rect_screen", lambda hwnd: (0, 0, 1152, 756))

    p = replay.Player(lambda: HWND)
    assert p.start(EVENTS, "забег", loops=1, require_focus=False, duration_ms=200.0)
    time.sleep(0.3)
    p.stop()
    assert fake.downs


# ── 2. Исход засчитывается только после подтверждения ─────────────────────

@pytest.fixture
def watcher(monkeypatch):
    screen = {"banner": None, "end_button": False, "relaxed": None}
    results = []

    def find_image(hwnd, name, **kw):
        if name == replay_result.MATCH_END_BUTTON_NAME:
            return {"score": 0.95} if screen["end_button"] else None
        relaxed = kw.get("threshold") == replay_result.MATCH_RESULT_RELAXED_THRESHOLD
        want = screen["relaxed"] if relaxed else screen["banner"]
        return {"score": 0.95} if name == want else None

    monkeypatch.setattr(replay_result.vision, "find_image", find_image)
    monkeypatch.setattr(replay_result.vision, "save_window_screenshot", lambda h, p: None)
    monkeypatch.setattr(replay_result._replay, "game_active", lambda hwnd: True)
    monkeypatch.setattr(replay_result, "POLL_INTERVAL", 0.02)

    w = replay_result.ResultWatcher(lambda: HWND, lambda *a: results.append(a))
    yield w, screen, results
    w.stop()


def test_a_single_frame_is_not_enough_to_count_a_match(watcher):
    """Один совпавший кадр — это может быть анимация или наложение. Ложная
    победа портит винрейт навсегда, поэтому нужно подтверждение."""
    w, screen, results = watcher
    assert replay_result.CONFIRM_SIGHTINGS >= 2

    # Ставим баннер ровно на один опрос и тут же убираем.
    w.start("забег")
    screen["banner"] = "victory"
    time.sleep(replay_result.POLL_INTERVAL * 0.6)
    screen["banner"] = None
    time.sleep(0.2)

    assert not results, "мелькнувший кадр не должен становиться матчем"


def test_a_banner_that_stays_is_counted(watcher):
    w, screen, results = watcher
    w.start("забег")
    screen["banner"] = "defeat"
    time.sleep(0.2)
    assert len(results) == 1
    assert results[0][0] == "loss"


# ── 2b. Вторая примета конца матча (как у автомата) ───────────────────────

def test_a_weak_banner_is_recognised_when_the_result_panel_is_up(watcher):
    """Баннер не дотянул до обычного порога, но кнопка «Repeat Stage» на
    экране — значит панель результата точно есть, и баннер там тоже есть,
    просто слабый. Автомат в этом месте перепроверяет мягче, и повтор обязан
    делать ровно то же самое."""
    w, screen, results = watcher
    w.start("забег")
    screen["banner"] = None            # обычным порогом не находится
    screen["end_button"] = True        # но панель результата на экране
    screen["relaxed"] = "victory"      # мягким — находится
    time.sleep(0.2)

    assert len(results) == 1
    assert results[0][0] == "win"


def test_without_the_result_panel_a_weak_banner_is_ignored(watcher):
    """Мягкий порог включается ТОЛЬКО когда панель результата видно. Иначе он
    ловил бы похожие пятна прямо посреди боя."""
    w, screen, results = watcher
    w.start("забег")
    screen["banner"] = None
    screen["end_button"] = False
    screen["relaxed"] = "victory"
    time.sleep(0.2)
    assert not results


# ── 3. Сторож тишины ──────────────────────────────────────────────────────

def test_silence_is_reported_once_not_every_poll(watcher):
    """Ругаться надо один раз на затишье. Сообщение раз в полторы секунды
    всю ночь — это не предупреждение, а мусор в журнале."""
    w, screen, _ = watcher
    shouts = []
    w._on_silence = lambda: shouts.append(1)
    w._log = lambda m: None
    monkeypatched_limit = 0.05
    w._silent_too_long = lambda since: (time.perf_counter() - since) >= monkeypatched_limit

    w.start("забег")
    time.sleep(0.25)                   # много опросов подряд
    assert len(shouts) == 1, f"о тишине должны сказать один раз, а не {len(shouts)}"


def test_the_silence_threshold_scales_with_the_recording_length(watcher):
    """У записи на три минуты и на сорок «давно ничего не было» — очень разное
    время. Нижняя граница не даёт короткой записи ругаться сразу."""
    w, _, _ = watcher
    w.start("короткая", cycle_seconds=60)
    now = time.perf_counter()
    assert not w._silent_too_long(now - replay_result.SILENCE_MIN_SECONDS + 10)
    assert w._silent_too_long(now - replay_result.SILENCE_MIN_SECONDS - 1)

    w.stop()
    w.start("длинная", cycle_seconds=40 * 60)
    now = time.perf_counter()
    # Три круга по сорок минут — два часа; нижняя граница тут ни при чём.
    assert not w._silent_too_long(now - 60 * 60)
    assert w._silent_too_long(now - 40 * 60 * replay_result.SILENCE_CYCLES - 1)


# ── 4. Предохранитель серии поражений ─────────────────────────────────────

@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "SETTINGS_FILE", str(tmp_path / "settings.json"))
    a = main.Api.__new__(main.Api)
    a._session_wins = a._session_losses = 0
    a._replay_loss_streak = 0
    a._run_status = {"action": "-", "mode": "Повтор"}
    a.logs = []
    a.push_log = a.logs.append
    a.get_webhook_settings = lambda: {}          # вебхук выключен
    a._player = types.SimpleNamespace(stop=lambda: a.logs.append("STOPPED"), name="забег")
    return a


def test_a_loss_streak_stops_the_replay(api):
    """Сломавшаяся запись сливает матч за матчем всю ночь. Автомат от этого
    защищён, у повтора защиты не было вовсе."""
    cfg.update({"replay_loss_streak_stop": 3})
    for _ in range(2):
        api._check_replay_loss_streak("loss", "забег")
    assert "STOPPED" not in api.logs, "двух поражений мало"

    api._check_replay_loss_streak("loss", "забег")
    assert "STOPPED" in api.logs, "на третьем прогон обязан встать"


def test_a_win_resets_the_streak(api):
    """Считается только НЕПРЕРЫВНАЯ серия — иначе предохранитель срабатывал бы
    на обычном невезении."""
    cfg.update({"replay_loss_streak_stop": 3})
    api._check_replay_loss_streak("loss", "забег")
    api._check_replay_loss_streak("loss", "забег")
    api._check_replay_loss_streak("win", "забег")
    api._check_replay_loss_streak("loss", "забег")
    api._check_replay_loss_streak("loss", "забег")
    assert "STOPPED" not in api.logs


def test_zero_turns_the_safeguard_off(api):
    cfg.update({"replay_loss_streak_stop": 0})
    for _ in range(20):
        api._check_replay_loss_streak("loss", "забег")
    assert "STOPPED" not in api.logs


def test_garbage_in_the_setting_falls_back_to_the_default(api):
    cfg.update({"replay_loss_streak_stop": "много"})
    assert api._replay_loss_limit() == 5
