"""ЖДАТЬ — ТОЖЕ ЧАСТЬ ЗАПИСИ.

Типичная запись матча устроена так: в начале расставил юнитов, а дальше
сидишь и ждёшь конца, ничего не нажимая. Длина круга бралась как «время
последнего события», поэтому всё это ожидание из записи выпадало: круг
кончался на последней расстановке, и повтор шёл на следующий заход прямо
посреди идущего боя.

Теперь рекордер отдельно считает полную длину (`Recorder.duration_ms`), она
лежит в файле как "duration", и по ней же считается длина круга повтора.
Отличать «ждал в игре» от «отлучился» умеет старая заслонка: часы записи
стоят, пока Roblox не на экране (см. tests/test_replay_focus_gate.py), и
здесь проверяется, что хвост ожидания эту разницу наследует.

Настоящие вызовы Windows подменены: тест должен идти и на CI, где нет ни
Roblox, ни курсора.
"""
import time

import pytest

from core import replay

GAME = 2002
GUI = 1001
VK_W = ord("W")

SETTLE = 0.12          # с запасом больше и опроса (4 мс), и паузы простоя (50 мс)


class _FakeInput:
    """Вместо core._input_win: физическое состояние клавиш задаёт тест."""

    def __init__(self):
        self.down = set()

    def is_key_down(self, vk):
        return vk in self.down


@pytest.fixture
def rig(monkeypatch):
    fake = _FakeInput()
    active = {"on": True}
    monkeypatch.setattr(replay, "_inp", fake)
    monkeypatch.setattr(replay, "_timer_precision", lambda on: None)
    monkeypatch.setattr(replay, "game_active", lambda hwnd: active["on"])
    monkeypatch.setattr(replay, "_cursor_over_gui", lambda gui, game: False)
    monkeypatch.setattr(replay, "_client_xy", lambda hwnd: (10, 20))
    monkeypatch.setattr(replay.wm, "get_window_rect_screen", lambda hwnd: (0, 0, 1152, 756))

    rec = replay.Recorder(lambda: GAME, lambda: GUI)
    yield rec, fake, active
    if rec.running:
        rec.stop()


def _tap(rec, fake, vk=VK_W):
    fake.down.add(vk)
    time.sleep(SETTLE)
    fake.down.discard(vk)
    time.sleep(SETTLE)


# ── Хвост ожидания попадает в запись ──────────────────────────────────────

def test_waiting_after_the_last_action_lands_in_the_recording(rig):
    """Главный случай: расставил юнитов и досидел до конца матча."""
    rec, fake, _ = rig
    rec.start()
    _tap(rec, fake)                    # «расставили юнита»
    events = rec.stop()

    last = events[-1]["t"]
    assert rec.duration_ms >= last, "полная длина не может быть короче последнего события"
    # Ждали примерно SETTLE после отпускания клавиши — этого достаточно,
    # чтобы отличить «хвост есть» от «хвоста нет».
    assert rec.duration_ms - last >= 50, (
        f"ожидание после последнего действия потерялось: {rec.duration_ms} vs {last}")


def test_a_recording_of_pure_waiting_still_has_length(rig):
    """Ни одного нажатия — но время всё равно посчитано."""
    rec, _, _ = rig
    rec.start()
    time.sleep(0.3)
    rec.stop()
    assert rec.duration_ms >= 250


def test_time_spent_outside_the_game_is_not_counted_as_waiting(rig):
    """Отлучка — не ожидание. Часы записи на ней стоят, и хвост не растёт."""
    rec, fake, active = rig
    rec.start()
    _tap(rec, fake)
    active["on"] = False               # ушли из игры и там же остановили запись
    time.sleep(0.4)
    events = rec.stop()

    last = events[-1]["t"]
    assert rec.duration_ms - last < 250, (
        f"время вне игры утекло в хвост ожидания: {rec.duration_ms} vs {last}")


def test_the_live_clock_keeps_running_while_you_wait(rig):
    """Счётчик на панели идёт по часам записи, а не по последнему действию.

    Иначе он замирает на времени последней расстановки, и «пишу ожидание»
    неотличимо от «запись зависла»."""
    rec, fake, _ = rig
    rec.start()
    _tap(rec, fake)
    first = rec.elapsed_ms
    time.sleep(0.25)
    assert rec.elapsed_ms - first >= 150

    rec.stop()
    # После остановки — это уже итоговая длина, а не бегущие часы.
    assert rec.elapsed_ms == rec.duration_ms


def test_the_live_clock_stops_while_the_game_is_away(rig):
    rec, _, active = rig
    rec.start()
    time.sleep(SETTLE)
    active["on"] = False
    time.sleep(SETTLE)
    frozen = rec.elapsed_ms
    time.sleep(0.25)
    assert abs(rec.elapsed_ms - frozen) < 1e-6, "часы обязаны стоять вне игры"


# ── Файл записи ───────────────────────────────────────────────────────────

def test_the_saved_file_keeps_the_full_length(tmp_path, monkeypatch):
    monkeypatch.setattr(replay, "RECORDINGS_DIR", str(tmp_path))
    events = [{"t": 0.0, "kind": "down", "code": "left", "x": 1, "y": 2},
              {"t": 40.0, "kind": "up", "code": "left", "x": 1, "y": 2}]
    replay.save("забег", events, 1152, 756, duration_ms=180_000.0)

    data = replay.load("забег")
    assert data["duration"] == 180_000.0
    st = replay.stats(data)
    assert st["actions"] == 2
    assert st["seconds"] == 180.0
    # Три минуты записи, из которых нажимали только первые 40 мс.
    assert st["tail"] == pytest.approx(180.0, abs=0.1)


def test_an_old_recording_without_duration_still_reads(tmp_path, monkeypatch):
    """Записи, снятые до появления поля, длятся до последнего события —
    ровно как раньше, и хвоста у них нет."""
    monkeypatch.setattr(replay, "RECORDINGS_DIR", str(tmp_path))
    events = [{"t": 0.0, "kind": "down", "code": "left", "x": 0, "y": 0},
              {"t": 2_500.0, "kind": "up", "code": "left", "x": 0, "y": 0}]
    st = replay.stats({"events": events})
    assert st["seconds"] == 2.5
    assert st["tail"] == 0.0


def test_a_bogus_duration_never_shortens_the_recording(tmp_path, monkeypatch):
    """duration меньше последнего события — запись всё равно доиграет до
    конца, а не обрежет сама себя."""
    monkeypatch.setattr(replay, "RECORDINGS_DIR", str(tmp_path))
    events = [{"t": 5_000.0, "kind": "down", "code": "left", "x": 0, "y": 0}]
    replay.save("кривая", events, 0, 0, duration_ms=10.0)
    assert replay.load("кривая")["duration"] == 5_000.0


# ── Повтор выжидает хвост ─────────────────────────────────────────────────

def test_replay_waits_out_the_tail_before_the_next_loop(monkeypatch):
    """Второй круг не начинается, пока не вышло время ожидания.

    Это и есть цена вопроса: без хвоста повтор жал бы «играть» заново, не
    дождавшись конца текущего матча."""
    played = []

    class _Inp:
        def move_abs(self, x, y):
            pass

        def button_down(self, b):
            played.append(time.perf_counter())

        def button_up(self, b):
            pass

        def key_down(self, vk):
            pass

        def key_up(self, vk):
            pass

    monkeypatch.setattr(replay, "_inp", _Inp())
    monkeypatch.setattr(replay, "_timer_precision", lambda on: None)
    monkeypatch.setattr(replay, "_game_focused", lambda hwnd: True)
    monkeypatch.setattr(replay, "_client_xy", lambda hwnd: (0, 0))

    events = [{"t": 0.0, "kind": "down", "code": "left", "x": 0, "y": 0},
              {"t": 10.0, "kind": "up", "code": "left", "x": 0, "y": 0}]

    p = replay.Player(lambda: 0)
    t0 = time.perf_counter()
    assert p.start(events, "хвост", loops=2, require_focus=False, duration_ms=400.0)
    deadline = time.perf_counter() + 3.0
    while p.running and time.perf_counter() < deadline:
        time.sleep(0.01)
    p.stop()

    assert len(played) == 2, f"должно быть ровно два круга, а не {len(played)}"
    gap = (played[1] - played[0]) * 1000.0
    assert gap >= 350, f"второй круг начался через {gap:.0f} мс вместо ~400"
    assert (time.perf_counter() - t0) < 2.0, "и при этом не завис"
