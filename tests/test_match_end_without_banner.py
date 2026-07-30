"""Матч кончился, а баннер не распознан — «не работает переигровка».

Конец матча определялся ровно по двум картинкам: баннерам «Victory» и «Defeat».
Не совпал ни один — и другого признака конца матча не было ВООБЩЕ: макрос
опрашивал экран полные 30 минут (MATCH_RESULT_TIMEOUT), стоя на уже законченном
матче, а потом объявлял задачу сломанной и сжигал попытку восстановления. Со
стороны это ровно «игра кончилась, а переигровки нет».

Шаблоны баннеров сняты на настройках автора движка, так что дыра открывается не
от поломки, а от другого разрешения или качества графики.

Второй признак — кнопка «Repeat Stage»: она есть только на экране результата
(в бою на её месте живой «Leave Stage», а это отдельное имя поиска).
"""
import threading

import pytest

from core import runner as runner_module
from core import vision
from core.runner import MacroRunner
from core.runner_constants import RESULT_UNKNOWN


class _Mouse:
    def move_to(self, x, y):
        pass

    def click(self, *a, **kw):
        pass


def _runner(monkeypatch, on_screen, scores=None, battle_age=999.0):
    """`on_screen` -- какие имена картинок «видны»; `scores` -- с каким счётом;
    `battle_age` -- сколько секунд идёт бой (для порога на «Start Game»)."""
    runner = MacroRunner.__new__(MacroRunner)
    runner._mouse = _Mouse()
    runner.logs = []
    runner._log = runner.logs.append
    runner.shots = []
    runner._save_debug_screenshot_unconditional = \
        lambda _h, name: runner.shots.append(name) or f"debug/{name}.png"
    runner.searched = []
    runner._battle_started_at = 1000.0
    monkeypatch.setattr(runner_module.time, "time", lambda: 1000.0 + battle_age)

    scores = scores or {}

    def find_image(hwnd, name, region=None, threshold=vision.DEFAULT_THRESHOLD, **kw):
        runner.searched.append((name, threshold))
        if name not in on_screen:
            return None
        # Баннер «есть на экране», но со своим счётом: обычный порог он может и
        # не пройти -- ровно это и воспроизводит реальную жалобу.
        score = scores.get(name, 0.99)
        if score < threshold:
            return None
        return {"x": 0, "y": 0, "w": 10, "h": 10, "cx": 5, "cy": 5, "score": score}

    monkeypatch.setattr(runner_module.vision, "find_image", find_image)
    return runner


# ── Кнопка повтора как признак конца матча ────────────────────────────────

def test_nothing_on_screen_means_the_match_is_still_going(monkeypatch):
    """Самый частый случай: ни панели результата, ни кнопки старта -- бой идёт.
    Ничего решать не надо."""
    runner = _runner(monkeypatch, on_screen=set())

    assert runner._match_ended_without_a_banner(1) is None
    # Баннеры перепроверять незачем -- их уже искали в основном цикле.
    assert "victory" not in [n for n, _ in runner.searched]


def test_a_missing_repeat_template_disables_only_that_half(monkeypatch):
    """Нет картинки кнопки повтора -- падать нельзя; проверка «Start Game»
    (это путь raid) обязана остаться рабочей."""
    runner = _runner(monkeypatch, on_screen={"nav_start_game"})

    real_find = runner_module.vision.find_image

    def find_image(hwnd, name, **kw):
        if name == "repeat_stage":
            raise vision.TemplateNotFound("no repeat_stage.png")
        return real_find(hwnd, name, **kw)

    monkeypatch.setattr(runner_module.vision, "find_image", find_image)

    assert runner._match_ended_without_a_banner(1) == runner_module.RESULT_ROUND_ENDED


# ── RAID: экрана результата нет, снова висит «Start Game» ─────────────────

def test_start_game_after_a_real_battle_means_the_round_ended(monkeypatch):
    """Так устроен raid: экрана результата с «Repeat Stage» нет, раунд просто
    кончился и этап готов к следующему забегу."""
    runner = _runner(monkeypatch, on_screen={"nav_start_game"})

    assert runner._match_ended_without_a_banner(1) == runner_module.RESULT_ROUND_ENDED
    assert any("Раунд кончился" in m for m in runner.logs)


def test_start_game_right_after_the_start_is_not_the_end_of_a_round(monkeypatch):
    """Кнопка старта видна и в первые секунды боя -- пока не прожалась до
    конца. Без порога по времени это читалось бы как «раунд кончился» сразу
    после старта, и задача крутилась бы вхолостую."""
    runner = _runner(monkeypatch, on_screen={"nav_start_game"}, battle_age=3.0)

    assert runner._match_ended_without_a_banner(1) is None


def test_the_confirm_variant_of_the_start_button_counts_too(monkeypatch):
    """nav_start_game_confirm -- вторая кнопка старта («Start Anyway»), её
    _find_start_game_button ищет наравне с основной."""
    runner = _runner(monkeypatch, on_screen={"nav_start_game_confirm"})

    assert runner._match_ended_without_a_banner(1) == runner_module.RESULT_ROUND_ENDED


def test_the_result_screen_wins_over_the_start_button(monkeypatch):
    """Если экран результата ЕСТЬ -- он и решает: там настоящий исход, а не
    догадка. Кнопку старта проверяем только когда панели нет."""
    runner = _runner(monkeypatch, on_screen={"repeat_stage", "victory", "nav_start_game"},
                     scores={"victory": 0.85})

    assert runner._match_ended_without_a_banner(1) == "win"


# ── Исход всё-таки определяется, просто мягче ─────────────────────────────

@pytest.mark.parametrize("banner,expected", [("victory", "win"), ("defeat", "loss")])
def test_a_weak_banner_is_still_classified(monkeypatch, banner, expected):
    """Панель результата на экране -- значит баннер там тоже есть, просто не
    дотянул до обычного порога 0.90. Перепроверяем мягче, а не сдаёмся."""
    runner = _runner(monkeypatch, on_screen={"repeat_stage", banner}, scores={banner: 0.84})

    assert runner._match_ended_without_a_banner(1) == expected
    assert any("ослабленном пороге" in m for m in runner.logs)
    # И статистика не пострадала: исход настоящий, не выдуманный.
    assert runner.shots == [], "зря сохранили скриншот при опознанном исходе"


def test_victory_wins_over_defeat_when_both_somehow_match(monkeypatch):
    """Порядок проверки задан: победа проверяется первой. Иначе выигранный
    матч мог бы уехать в статистику как поражение и разогнать предохранитель
    серии поражений."""
    runner = _runner(monkeypatch, on_screen={"repeat_stage", "victory", "defeat"},
                     scores={"victory": 0.82, "defeat": 0.88})

    assert runner._match_ended_without_a_banner(1) == "win"


def test_a_banner_below_even_the_relaxed_floor_is_not_guessed(monkeypatch):
    """0.70 -- это уже не «почти совпал», а совсем другое место на экране.
    Придумывать по нему исход нельзя."""
    runner = _runner(monkeypatch, on_screen={"repeat_stage", "victory"}, scores={"victory": 0.70})

    assert runner._match_ended_without_a_banner(1) == RESULT_UNKNOWN


# ── Исход неизвестен, но матч точно кончился ──────────────────────────────

def test_an_unrecognised_result_is_reported_as_ended(monkeypatch):
    """Главное поведение: матч признан законченным, фарм продолжится."""
    runner = _runner(monkeypatch, on_screen={"repeat_stage"})

    assert runner._match_ended_without_a_banner(1) == RESULT_UNKNOWN


def test_an_unrecognised_result_saves_a_screenshot_and_says_what_to_do(monkeypatch):
    """Без скриншота человек не сможет добавить нужную вырезку, а без прямой
    подсказки -- не поймёт, что вообще надо что-то делать."""
    runner = _runner(monkeypatch, on_screen={"repeat_stage"})

    runner._match_ended_without_a_banner(1)

    assert runner.shots == ["match_result_unknown"]
    message = " ".join(runner.logs)
    assert "Менеджер картинок" in message
    assert "НЕ пойдёт в статистику" in message


def test_ended_is_not_a_loss(monkeypatch):
    """Отдельное значение, а не «loss»: врать в статистику и в предохранитель
    серии поражений (он закрывает Roblox через taskkill) нельзя."""
    assert RESULT_UNKNOWN not in ("win", "loss")


def test_an_unknown_outcome_does_not_feed_the_expedition_loss_check(monkeypatch):
    """Проверка «умер до чекпойнта» обязана реагировать только на настоящее
    поражение -- иначе нераспознанный матч влиял бы на предохранитель."""
    runner = _runner(monkeypatch, on_screen=set())
    runner._expedition_extract_count = 0

    assert runner._is_early_expedition_loss({"mode": "expedition"}, RESULT_UNKNOWN) is False
    assert runner._is_early_expedition_loss({"mode": "expedition"}, "loss") is True


# ── Цена страховки ────────────────────────────────────────────────────────

def test_the_check_is_rate_limited(monkeypatch):
    """Поиск шаблона по всему окну не бесплатный, а баннеры и так ищутся
    дважды в секунду. Проверка кнопки идёт раз в MATCH_END_CHECK_EVERY
    опросов -- константа обязана остаться больше единицы, иначе цена опроса
    вырастет в полтора раза на каждом забеге."""
    assert runner_module.MATCH_END_CHECK_EVERY > 1
    assert runner_module.MATCH_RESULT_RELAXED_THRESHOLD < vision.DEFAULT_THRESHOLD


# ── Обработка результата: тот же путь, что у победы и поражения ───────────

def _result_runner(monkeypatch):
    runner = MacroRunner.__new__(MacroRunner)
    runner._mouse = _Mouse()
    runner._coords = dict(runner_module.DEFAULT_COORDS)
    runner.logs = []
    runner._log = runner.logs.append
    runner._checkpoint = lambda _s: False
    runner._set_status = lambda **_kw: None
    runner._note_win_for_crafting = lambda *_a: None
    runner._release_quick_place_shift = lambda: None
    runner._dismiss_reward_card_if_found = lambda _h: False
    runner._clear_result_obtainment_modal = lambda *_a: True
    runner._wait_for_image_gone = lambda *a, **k: True
    runner._capture_result_screenshot = lambda _h: None
    runner._force_fresh_reentry = False
    runner._act4_wants_in = False
    runner._placement_tally = {}
    runner._expedition_extract_count = 0

    runner.recorded = []
    runner._finish_match_result_background = lambda *a, **k: runner.recorded.append(a)
    runner.events = []
    runner._send_event_webhook = lambda _w, _t, title, *a, **k: runner.events.append(title)
    runner.nav = []
    runner._click_and_verify_gone = lambda _h, _s, name, _t, success_name=None: \
        runner.nav.append(name) or True
    runner._click_return_to_lobby_if_found = lambda *_a: True

    monkeypatch.setattr(runner_module.wm, "get_window_rect_screen", lambda _h: (0, 0, 1152, 756))
    monkeypatch.setattr(runner_module.time, "sleep", lambda _s: None)
    return runner


def test_an_unknown_outcome_still_clicks_repeat_stage(monkeypatch):
    """Ради этого всё и делалось: переигровка должна продолжиться."""
    runner = _result_runner(monkeypatch)

    ok = runner._handle_match_result(1, threading.Event(), {"mode": "raid", "map": "Spirit City"},
                                      RESULT_UNKNOWN, "5m 0s", webhook=None, repeat=True)

    assert ok is True
    assert runner.nav == ["repeat_stage"]


def test_an_unknown_outcome_is_kept_out_of_the_stats(monkeypatch):
    """Записать «победа» или «поражение» тут значило бы соврать: счётчики,
    винрейт и предохранитель серии поражений считают по этим числам."""
    runner = _result_runner(monkeypatch)

    runner._handle_match_result(1, threading.Event(), {"mode": "raid", "map": "Spirit City"},
                                 RESULT_UNKNOWN, "5m 0s", webhook=None, repeat=True)

    assert runner.recorded == [], "нераспознанный матч уехал в статистику"
    assert runner.events == ["Итог матча не распознан"], "человеку не сказали, что баннер не читается"


@pytest.mark.parametrize("result", ["win", "loss"])
def test_a_known_outcome_is_recorded_as_before(monkeypatch, result):
    runner = _result_runner(monkeypatch)

    runner._handle_match_result(1, threading.Event(), {"mode": "raid", "map": "Spirit City"},
                                 result, "5m 0s", webhook=None, repeat=True)

    assert len(runner.recorded) == 1
    assert runner.recorded[0][0] == result
    assert runner.events == []


def test_an_unknown_outcome_on_the_last_repeat_leaves_the_stage(monkeypatch):
    runner = _result_runner(monkeypatch)

    ok = runner._handle_match_result(1, threading.Event(), {"mode": "raid", "map": "Spirit City"},
                                      RESULT_UNKNOWN, "5m 0s", webhook=None, repeat=False)

    assert ok is True
    assert runner.nav == ["leave_stage"]
