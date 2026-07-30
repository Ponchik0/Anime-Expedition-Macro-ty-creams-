"""Смерть в Expedition до точки извлечения не должна ломать задачу.

Из реального лога (задача «School Grounds» x999, extract_after=1):

  [21:59:35] Expedition run failed -- Defeat screen found (score 1.00).
  [21:59:45] "repeat_stage" not found within 8s -- stopping.
  [21:59:45] "Repeat Stage" not found -- can't continue this task's repeats, stopping.
  [21:59:45] Task 1/1 hit a problem mid-run -- recovering to the lobby.

Кнопки «Repeat Stage» на экране поражения в Expedition просто нет. Макрос
искал её восемь секунд, не находил, объявлял задачу СЛОМАННОЙ и сжигал
попытку восстановления -- три смерти подряд, и задача снималась целиком,
хотя ничего не сломалось: забег проигран и его надо переиграть.
"""
import threading

import pytest

from core import runner as runner_module
from core.runner import MacroRunner


class _Mouse:
    def move_to(self, x, y):
        pass


def _runner(monkeypatch, repeat_stage_found: bool):
    runner = MacroRunner.__new__(MacroRunner)
    runner._mouse = _Mouse()
    runner._coords = dict(runner_module.DEFAULT_COORDS)
    runner.logs = []
    runner._log = runner.logs.append
    runner._checkpoint = lambda _stop: False
    runner._set_status = lambda **_kw: None
    runner._note_win_for_crafting = lambda *_a: None
    runner._release_quick_place_shift = lambda: None
    runner._dismiss_reward_card_if_found = lambda _hwnd: False
    runner._clear_result_obtainment_modal = lambda *_a: True
    runner._finish_match_result_background = lambda *_a, **_k: None
    runner._wait_for_image_gone = lambda *_a, **_k: True
    runner._force_fresh_reentry = False
    runner._act4_wants_in = False

    runner.nav = []

    def click_and_verify_gone(_hwnd, _stop, name, _timeout, success_name=None):
        runner.nav.append(name)
        if name == "repeat_stage":
            return repeat_stage_found
        return True  # leave_stage всегда срабатывает

    runner._click_and_verify_gone = click_and_verify_gone
    runner.returned_to_lobby = []
    runner._click_return_to_lobby_if_found = \
        lambda *_a: runner.returned_to_lobby.append(True) or True

    monkeypatch.setattr(runner_module.wm, "get_window_rect_screen", lambda _h: (0, 0, 1152, 756))
    monkeypatch.setattr(runner_module.time, "sleep", lambda _s: None)
    return runner


def _handle(runner, mode, result, repeat=True):
    task = {"mode": mode, "map": "School Grounds", "macro": "exp", "repeat": 999}
    return runner._handle_match_result(
        1, threading.Event(), task, result, "4m 36s", webhook=None, repeat=repeat)


def test_expedition_defeat_leaves_to_lobby_instead_of_hunting_repeat_stage(monkeypatch):
    """Главное: задача НЕ считается сломанной, «Repeat Stage» вообще не
    ищется, и следующий повтор помечен как «заходить заново с лобби»."""
    runner = _runner(monkeypatch, repeat_stage_found=False)

    ok = _handle(runner, "expedition", "loss")

    assert ok is True, "поражение в Expedition снова ломает задачу"
    assert "repeat_stage" not in runner.nav, f"впустую искали кнопку повтора: {runner.nav}"
    assert runner.nav == ["leave_stage"]
    assert runner.returned_to_lobby == [True]
    assert runner._force_fresh_reentry is True


def test_expedition_win_still_uses_repeat_stage(monkeypatch):
    """Победа (извлечение прошло) -- обычный быстрый повтор этапа, как раньше."""
    runner = _runner(monkeypatch, repeat_stage_found=True)

    ok = _handle(runner, "expedition", "win")

    assert ok is True
    assert runner.nav == ["repeat_stage"]
    assert runner._force_fresh_reentry is False


def test_other_modes_keep_repeating_on_a_defeat(monkeypatch):
    """В Story/Raid кнопка повтора на экране поражения есть -- поведение
    менять нельзя."""
    runner = _runner(monkeypatch, repeat_stage_found=True)

    ok = _handle(runner, "story", "loss")

    assert ok is True
    assert runner.nav == ["repeat_stage"]
    assert runner._force_fresh_reentry is False


def test_missing_repeat_stage_falls_back_to_the_lobby_in_any_mode(monkeypatch):
    """Страховка шире Expedition: не нашлась кнопка повтора -- выходим в лобби
    и заходим заново, а не объявляем задачу сломанной."""
    runner = _runner(monkeypatch, repeat_stage_found=False)

    ok = _handle(runner, "story", "loss")

    assert ok is True, "не найденная кнопка повтора снова ломает задачу"
    assert runner.nav == ["repeat_stage", "leave_stage"]
    assert runner._force_fresh_reentry is True


def test_last_repeat_leaves_the_stage_as_before(monkeypatch):
    """Последний повтор задачи и так уходил в лобби -- проверка ничего не
    должна была здесь изменить."""
    runner = _runner(monkeypatch, repeat_stage_found=True)

    ok = _handle(runner, "expedition", "loss", repeat=False)

    assert ok is True
    assert runner.nav == ["leave_stage"]


@pytest.mark.parametrize("mode,result,expected", [
    ("expedition", "loss", True),
    ("expedition", "win", False),
    ("story", "loss", False),
])
def test_fresh_reentry_flag_is_reset_between_matches(monkeypatch, mode, result, expected):
    """Флаг обязан сбрасываться на каждом результате: решение прошлого матча
    не должно заставлять следующий заходить заново без причины."""
    runner = _runner(monkeypatch, repeat_stage_found=True)
    runner._force_fresh_reentry = True  # остаток от предыдущего матча

    _handle(runner, mode, result)

    assert runner._force_fresh_reentry is expected


# ── Смерть до первого чекпойнта не должна перезапускать Roblox ─────────────
# Фейлсейф «три поражения подряд на одной карте» закрывал Roblox через
# taskkill и присылал красное уведомление. В Expedition проиграть до точки
# извлечения -- норма, и на задаче с repeat=999 это шло по кругу.

@pytest.mark.parametrize("mode,result,sightings,expected", [
    # Не дошли до чекпойнта -- в серию не идёт.
    ("expedition", "loss", 0, True),
    # Дошли и всё равно проиграли -- считается как раньше.
    ("expedition", "loss", 1, False),
    ("expedition", "loss", 2, False),
    # Победа -- не поражение.
    ("expedition", "win", 0, False),
    # Другие режимы проверка не касается: там нет ни чекпойнтов, ни причины.
    ("story", "loss", 0, False),
    ("raid", "loss", 0, False),
])
def test_early_expedition_loss_detection(monkeypatch, mode, result, sightings, expected):
    runner = _runner(monkeypatch, repeat_stage_found=True)
    runner._expedition_extract_count = sightings

    assert runner._is_early_expedition_loss({"mode": mode}, result) is expected


def test_early_expedition_loss_survives_a_missing_task(monkeypatch):
    """Задача может быть None на путях восстановления -- проверка не должна
    падать, иначе поражение уронит весь прогон."""
    runner = _runner(monkeypatch, repeat_stage_found=True)
    runner._expedition_extract_count = 0

    assert runner._is_early_expedition_loss(None, "loss") is False


# ── Такт боя: сторож бездействия больше не убивает длинный забег ──────────

def _battle_runner(monkeypatch, mode_extract_count=0):
    runner = _runner(monkeypatch, repeat_stage_found=True)
    runner.status = []
    runner._set_status = lambda **kw: runner.status.append(kw.get("action"))
    runner._battle_status_minute = None
    runner._expedition_extract_count = mode_extract_count
    runner._expedition_extract_accept_at = 2
    return runner


def test_battle_status_pulses_once_per_minute(monkeypatch):
    """Раз в минуту, а не каждый опрос: _set_status считает прогрессом только
    изменившуюся строку, поэтому чаще незачем."""
    runner = _battle_runner(monkeypatch)
    clock = {"t": 5000.0}
    monkeypatch.setattr(runner_module.time, "time", lambda: clock["t"])
    runner._battle_started_at = clock["t"]

    runner._pulse_battle_status("story")       # 0-я минута
    runner._pulse_battle_status("story")       # тот же миг -- ничего нового
    clock["t"] += 61
    runner._pulse_battle_status("story")       # 1-я минута

    assert runner.status == ["Бой: 0 мин", "Бой: 1 мин"]


def test_battle_status_shows_expedition_checkpoints(monkeypatch):
    """Номер волны в Expedition не читается, поэтому чекпойнты извлечения --
    единственный признак продвижения, который там вообще есть."""
    runner = _battle_runner(monkeypatch, mode_extract_count=1)
    monkeypatch.setattr(runner_module.time, "time", lambda: 5000.0)
    runner._battle_started_at = 5000.0

    runner._pulse_battle_status("expedition")

    assert runner.status == ["Бой: 0 мин, чекпойнт 1/2"]


def test_battle_status_outlives_the_stall_watchdog(monkeypatch):
    """Главное: за время, которого хватало сторожу (STALL_TIMEOUT_MIN), такт
    обязан отбить не одну отметку -- иначе длинный забег снова остановит
    прогон с диагнозом «завис»."""
    runner = _battle_runner(monkeypatch)
    clock = {"t": 0.0}
    monkeypatch.setattr(runner_module.time, "time", lambda: clock["t"])
    runner._battle_started_at = 0.0

    for _ in range(runner_module.STALL_TIMEOUT_MIN + 5):
        runner._pulse_battle_status("expedition")
        clock["t"] += 60

    assert len(runner.status) == runner_module.STALL_TIMEOUT_MIN + 5
    assert len(set(runner.status)) == len(runner.status), "строка действия повторилась — сторож счёл бы это простоем"
