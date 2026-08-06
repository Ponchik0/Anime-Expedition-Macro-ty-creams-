"""ИСХОД МАТЧА В РЕЖИМЕ «ПОВТОР»: победа/поражение, история, отчёт.

Повтор об игре не знает ничего — он крутит записанные нажатия. Чтобы забег
попадал в историю и в счётчики так же, как у автомата, за экраном следит
отдельный наблюдатель (core/replay_result.py).

Главное, что здесь проверяется, — ЗАПОР. Экран результата висит секундами, а
опрос идёт раз в полторы секунды: без запора один матч засчитался бы столько
раз, сколько опросов успело пройти, то есть десяток побед за один забег.
"""
import os
import time
from types import SimpleNamespace

import pytest

from core import replay_result

HWND = 4242


@pytest.fixture
def rig(monkeypatch):
    """Экран, которым управляет тест: screen["banner"] — что сейчас видно."""
    screen = {"banner": None, "missing": set()}
    results = []

    def best_match_in_gray_multiscale(shot, name, template_dir=None, stop_at=None):
        if name in screen["missing"]:
            raise replay_result.vision.TemplateNotFound(name)
        return {"score": 0.99, "x": 100, "y": 100} if name == screen["banner"] else None

    monkeypatch.setattr(replay_result.vision, "capture_game_gray",
                        lambda hwnd, region=None: SimpleNamespace(size=1))
    monkeypatch.setattr(replay_result.vision, "best_match_in_gray_multiscale", best_match_in_gray_multiscale)
    monkeypatch.setattr(replay_result.vision, "save_window_screenshot", lambda hwnd, path: None)
    monkeypatch.setattr(replay_result._replay, "game_active", lambda hwnd: True)
    monkeypatch.setattr(replay_result, "POLL_INTERVAL", 0.02)

    w = replay_result.ResultWatcher(lambda: HWND, lambda *a: results.append(a))
    yield w, screen, results
    w.stop()


def _settle(seconds=0.15):
    time.sleep(seconds)


def test_a_victory_banner_is_counted_once(rig):
    """Баннер висит на экране всё время — матч всё равно один."""
    w, screen, results = rig
    w.start("забег")
    screen["banner"] = "victory"
    _settle(0.3)

    assert len(results) == 1, f"один матч должен дать один исход, а не {len(results)}"
    assert results[0][0] == "win"
    assert w.matches == 1


def test_the_next_match_counts_only_after_the_banner_clears(rig):
    """Второй матч засчитывается, лишь когда экран результата ушёл и пришёл
    снова. Именно уход баннера и отделяет один забег от следующего."""
    w, screen, results = rig
    w.start("забег")
    screen["banner"] = "victory"
    _settle()
    assert len(results) == 1

    screen["banner"] = None          # экран результата закрылся, идёт новый матч
    _settle()
    assert len(results) == 1, "пустой экран не должен ничего засчитывать"

    screen["banner"] = "defeat"
    _settle()
    assert len(results) == 2
    assert results[1][0] == "loss"


def test_the_duration_is_measured_per_match_not_since_start(rig):
    """Длина второго матча считается от первого исхода, а не от запуска
    повтора — иначе круги показывали бы нарастающую сумму."""
    w, screen, results = rig
    w.start("забег")
    time.sleep(0.25)
    screen["banner"] = "victory"
    _settle()
    screen["banner"] = None
    _settle()
    screen["banner"] = "victory"
    _settle()

    assert len(results) == 2
    # Обе длины — строки вида «0s»/«1m 2s»; важно, что вторая не накопительная.
    assert results[1][1] in ("0s", "1s"), f"длина второго матча накопилась: {results[1][1]}"


def test_nothing_is_counted_while_the_game_is_off_screen(rig, monkeypatch):
    """Игры не видно — смотреть нечего. Иначе исход мог бы «увидеться» на
    снимке спрятанного окна."""
    w, screen, results = rig
    monkeypatch.setattr(replay_result._replay, "game_active", lambda hwnd: False)
    w.start("забег")
    screen["banner"] = "victory"
    _settle(0.25)
    assert not results


def test_a_missing_template_is_reported_once_and_never_crashes(rig):
    """Нет эталона — исход просто не распознаётся, повтор при этом крутится.
    Ругаемся один раз, а не каждые полторы секунды весь забег."""
    w, screen, results = rig
    logs = []
    w._log = logs.append
    screen["missing"] = {"victory", "defeat"}
    w.start("забег")
    _settle(0.3)

    assert not results
    assert len([m for m in logs if "victory" in m]) == 1, logs


def test_restarting_right_away_does_not_lose_the_watcher(rig):
    """Остановил повтор и тут же запустил снова.

    Прежний наблюдатель уходит сам, но проверяет это раз в такт — то есть
    какое-то время ещё жив. Раньше start() в этот момент молча отказывал, и
    история по такому прогону не писалась ВООБЩЕ: повтор крутится, а победы и
    поражения мимо."""
    w, screen, results = rig
    assert w.start("первый")
    assert w.running

    # Не дожидаясь, пока прошлый поток заметит остановку, стартуем заново.
    assert w.start("второй"), "повторный запуск обязан пройти"
    assert w.running
    assert w.name == "второй"
    assert w.matches == 0, "счётчик матчей у нового прогона свой"

    screen["banner"] = "victory"
    _settle(0.2)
    assert len(results) == 1, "новый прогон должен писать историю"


def test_the_handler_blowing_up_does_not_kill_the_watcher(rig):
    """Сорвалась запись исхода — наблюдатель обязан жить дальше: иначе один
    сбой сети в уведомлении молча выключал бы всю статистику до конца прогона."""
    boom = {"n": 0}

    def on_result(*a):
        boom["n"] += 1
        raise RuntimeError("вебхук не ушёл")

    w, screen, _ = rig
    w._on_result = on_result
    w.start("забег")
    screen["banner"] = "victory"
    _settle()
    screen["banner"] = None
    _settle()
    screen["banner"] = "defeat"
    _settle()

    assert boom["n"] == 2, "после сбоя наблюдатель должен продолжить работу"
    assert w.running


# ── Отчёт в PDF ───────────────────────────────────────────────────────────

def test_the_pdf_report_builds_with_cyrillic_names(tmp_path):
    """Главное, ради чего отчёт рисуется Pillow, а не OpenCV: имена записей
    задаёт человек, и они русские."""
    from core import report_pdf
    path = str(tmp_path / "отчёт.pdf")
    report_pdf.build(path, stats={
        "session_wins": 7, "session_losses": 3, "all_time_wins": 40,
        "all_time_losses": 12, "runs_per_hour": "6.5", "version": "0.17.0",
        "results": [True, False, True, True],
    }, history=[
        {"result": "win", "map": "Запись «Забег на Мардженте»", "duration": "3m 4s",
         "source": "replay", "when": "01.08.2026 14:32"},
        {"result": "loss", "map": "Marjenta", "duration": "2m 9s",
         "source": "auto", "when": "01.08.2026 14:20"},
    ])
    assert os.path.getsize(path) > 1000
    with open(path, "rb") as f:
        assert f.read(5) == b"%PDF-"


def test_the_pdf_report_survives_an_empty_history(tmp_path):
    """Свежая установка: ни одного забега — отчёт всё равно должен собраться."""
    from core import report_pdf
    path = str(tmp_path / "empty.pdf")
    report_pdf.build(path, stats={}, history=[])
    assert os.path.getsize(path) > 1000


def test_a_long_history_spills_onto_more_pages(tmp_path):
    """Пятьдесят строк на одну страницу не влезают — отчёт обязан продолжиться
    на следующей, а не обрезаться."""
    from core import report_pdf
    path = str(tmp_path / "long.pdf")
    history = [{"result": "win" if i % 2 else "loss", "map": f"Забег {i}",
                "duration": "1m 0s", "source": "replay", "when": "01.08.2026 12:00"}
               for i in range(50)]
    report_pdf.build(path, stats={"session_wins": 25, "session_losses": 25}, history=history)
    # Число страниц напрямую не прочесть без парсера PDF, но многостраничный
    # файл заведомо тяжелее одностраничного пустого.
    assert os.path.getsize(path) > 3000
