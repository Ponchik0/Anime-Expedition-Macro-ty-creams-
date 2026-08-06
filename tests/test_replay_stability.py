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
    """Экран задаётся СЧЁТАМИ эталонов, а не «нашлось/не нашлось»: наблюдатель
    теперь и сам решает по счёту, а не по одному порогу."""
    screen = {"victory": 0.0, "defeat": 0.0,
              replay_result.MATCH_END_BUTTON_NAME: 0.0, "spot": (100, 100),
              "wander": False}
    results = []

    def best_match_in_gray_multiscale(shot, name, template_dir=None, stop_at=None):
        score = screen.get(name, 0.0)
        if not score:
            return None
        x, y = screen["spot"]
        if screen["wander"]:
            # Пятно уползает на каждый опрос — так ведёт себя случайное
            # совпадение на движущейся картинке боя, но не баннер.
            screen["spot"] = (x + 90, y + 90)
        return {"score": score, "x": x, "y": y}

    monkeypatch.setattr(replay_result.vision, "capture_game_gray",
                        lambda hwnd, region=None: types.SimpleNamespace(size=1))
    monkeypatch.setattr(replay_result.vision, "best_match_in_gray_multiscale", best_match_in_gray_multiscale)
    monkeypatch.setattr(replay_result.vision, "save_window_screenshot", lambda h, p: None)
    monkeypatch.setattr(replay_result._replay, "game_active", lambda hwnd: True)
    monkeypatch.setattr(replay_result, "POLL_INTERVAL", 0.02)

    w = replay_result.ResultWatcher(lambda: HWND, lambda *a: results.append(a))
    yield w, screen, results
    w.stop()


def test_a_confident_banner_counts_from_the_very_first_frame(watcher):
    """ЭТО И БЫЛА ЦЕНА НОЧИ. Требование «два совпадения подряд» стояло на любом
    совпадении, включая уверенное. У живого человека баннер брал порог со счётом
    0.90-0.91 при пороге 0.90 — на таком зазоре кадры мерцают, и любой единичный
    промах обнулял подтверждение. За десять часов засчитался ОДИН матч из сотни.

    Автомат в этом месте засчитывает первое попадание (_wait_for_result в
    core/runner.py), и повтор обязан делать то же самое."""
    w, screen, results = watcher
    w.start("забег")
    screen["victory"] = replay_result.STRONG_THRESHOLD
    time.sleep(replay_result.POLL_INTERVAL * 3)
    screen["victory"] = 0.0            # мелькнул и пропал
    time.sleep(0.15)

    assert len(results) == 1, "уверенное совпадение засчитывается сразу"
    assert results[0][0] == "win"


def test_a_single_weak_frame_is_not_enough_to_count_a_match(watcher):
    """Совпадение НИЖЕ уверенного порога может быть и кадром анимации, и
    полупрозрачным наложением. Ложная победа портит винрейт навсегда, поэтому
    слабому нужно подтверждение."""
    w, screen, results = watcher
    assert replay_result.CONFIRM_SIGHTINGS >= 2

    w.start("забег")
    screen["victory"] = 0.85           # полоса «почти»
    time.sleep(replay_result.POLL_INTERVAL * 0.6)
    screen["victory"] = 0.0
    time.sleep(0.2)

    assert not results, "мелькнувший слабый кадр не должен становиться матчем"


def test_a_weak_banner_that_holds_its_place_is_counted(watcher):
    """Слабое совпадение, которое держится НА ОДНОМ МЕСТЕ, — это настоящий
    баннер, просто эталон не дотягивает до порога. Ровно этот случай и терялся:
    у автомата тут страховка по кнопке «Repeat Stage», а повтор молчал."""
    w, screen, results = watcher
    w.start("забег")
    screen["victory"] = 0.85
    time.sleep(0.2)

    assert len(results) == 1
    assert results[0][0] == "win"


def test_a_weak_match_that_wanders_is_ignored(watcher):
    """А вот слабое совпадение, которое ПОЛЗЁТ по экрану, — это случайное пятно
    похожей яркости посреди боя. Настоящий баннер стоит на месте; место и есть
    то, что отличает одно от другого, раз счёт уже не отличает."""
    w, screen, results = watcher
    w.start("забег")
    screen["wander"] = True
    screen["victory"] = 0.85
    time.sleep(0.3)

    assert not results


# ── 2b. Вторая примета конца матча (как у автомата) ───────────────────────

def test_the_result_panel_alone_ends_the_match_without_faking_a_result(watcher):
    """Баннер не читается вовсе, но на экране кнопка «Repeat Stage» — матч
    кончился, и притворяться, что ничего не было, нельзя. Автомат отвечает на
    это RESULT_UNKNOWN: забег засчитан кончившимся, в статистику не идёт.

    Прежде повтор в этом месте не делал НИЧЕГО — и сотня таких матчей за ночь
    выглядела снаружи как полная тишина."""
    w, screen, results = watcher
    logs = []
    w._log = logs.append
    w.start("забег")
    screen[replay_result.MATCH_END_BUTTON_NAME] = 0.95
    time.sleep(0.2)

    assert not results, "исход неизвестен — в статистику писать нечего"
    assert w.unknown == 1, "но сам факт конца матча посчитан"
    assert any("не распознал" in m for m in logs), logs


# ── 3. Сторож тишины ──────────────────────────────────────────────────────

def test_silence_is_repeated_not_said_once_and_forgotten(watcher):
    """ВТОРАЯ ЦЕНА ТОЙ ЖЕ НОЧИ. Сторож ругался один раз за затишье и сбрасывался
    только распознанным исходом — то есть в единственном случае, ради которого
    написан, выдавал одно сообщение на пятнадцатой минуте и молчал следующие
    десять часов. Повторяем, удваивая паузу."""
    w, screen, _ = watcher
    shouts = []
    w._on_silence = lambda shot=None, detail="": shouts.append(detail)
    w._log = lambda m: None
    w._silence_limit = lambda: 0.05

    w.start("забег")
    time.sleep(0.35)
    assert len(shouts) >= 2, f"о тишине надо напоминать, а не сказать один раз: {shouts}"


def test_the_silence_message_reports_scores_instead_of_guessing(watcher):
    """Прежний текст перечислял версии, и в живом случае промахнулся мимо обеих:
    эталоны совпадали, просто на сотую ниже порога. Счёт отвечает на это сразу."""
    w, screen, _ = watcher
    shouts = []
    w._on_silence = lambda shot=None, detail="": shouts.append(detail)
    w._log = lambda m: None
    w._silence_limit = lambda: 0.05

    # Ниже даже мягкого порога — исходом это не станет, но цифру человек
    # обязан увидеть: «0.78 при пороге 0.90» и есть ответ, чего не хватает.
    screen["victory"] = 0.78
    w.start("забег")
    time.sleep(0.2)

    assert shouts and "victory 0.78" in shouts[0], shouts


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
