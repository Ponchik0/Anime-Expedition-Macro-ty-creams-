"""Расстановка юнита: что считать клеткой и как понять, что клик прошёл.

Оба сюжета взяты из реального лога забега по Expedition, где юниты не
появлялись на поле, а журнал при этом рапортовал «placed»:

  Place Unit "dps": ближайшая клетка в 18px от заданной точки — жду...
  Place Unit "dps": нужная клетка так и не освободилась — ставлю в 18px, offset (18, 17)
  Place Unit "dps": placed at (564, 320) (Pre Start)

«offset (18, 17)» -- это угол области поиска: годился ОДИН белый пиксель, и
им оказывался белый текст/частица/кромка платформы. Клик уходил на 25px мимо
клетки, юнит не ставился, а проверки после клика не было вовсе.
"""
import threading

import numpy as np
import pytest

from core import ocr, runner_blocks
from core.runner_blocks import BlockOps
from core.runner_constants import (DEFAULT_COORDS, PLACE_CONFIRM_ATTEMPTS,
                                   PLACE_HIGHLIGHT_MIN_PIXELS, PLACE_SEARCH_BOX_SIZE)


class _Runner(BlockOps):
    def __init__(self):
        self.logs = []
        self.clicks = []
        self._mouse = self
        self._keyboard = self
        self._coords = dict(DEFAULT_COORDS)
        self._placement_tally = {"ok": 0, "failed": 0, "failed_names": []}

    def _log(self, msg):
        self.logs.append(msg)

    def _checkpoint(self, _stop_event):
        return False

    # --- мышь/клавиатура одним объектом: тестам нужны только клики ---
    def click(self, x=None, y=None, **_kw):
        self.clicks.append((int(x), int(y)))

    def move_to(self, x, y):
        pass

    def nudge(self, dx=1, dy=0):
        pass

    def tap(self, *_a, **_k):
        pass


def _canvas():
    """Пустой (небелый) кадр размером с игровое окно."""
    from core.config import FIXED_WIN_H, FIXED_WIN_W
    return np.zeros((FIXED_WIN_H, FIXED_WIN_W, 3), np.uint8)


def _patch_screen(monkeypatch, screen):
    """Захват поверх готового кадра -- как настоящий, с вырезкой.

    ДВА ШВА, А НЕ ОДИН: с версии 0.18 кадр берётся через
    _capture_place_search_region, и путь там разный -- Windows читает
    содержимое окна (vision.capture_window_region_bgr), macOS снимает экран
    (ocr.capture_region), потому что подсветка выпадает из
    CGWindowListCreateImage. Окно фальшивой игры стоит в (0, 0), поэтому числа
    в обоих швах одни и те же, и подделка у них общая. Подставить только один
    значило бы проверять одну платформу из двух."""
    def capture_region(x, y, w, h):
        return screen[y:y + h, x:x + w]

    monkeypatch.setattr(ocr, "capture_region", capture_region)
    monkeypatch.setattr(runner_blocks, "capture_region", capture_region, raising=False)
    monkeypatch.setattr(runner_blocks.vision, "capture_window_region_bgr",
                        lambda _hwnd, region: capture_region(*region))


def _blob(screen, cx, cy, size=9):
    """Пятно РОВНО с центром в (cx, cy). Сторона нечётная намеренно: при чётной
    центр масс попадает на полпикселя и тест превращается в проверку
    округления вместо проверки логики."""
    half = size // 2
    screen[cy - half:cy + half + 1, cx - half:cx + half + 1] = 255


# ---------------------------------------------------------------------------
# Что считать клеткой
# ---------------------------------------------------------------------------

def test_stray_white_pixel_no_longer_beats_a_real_highlight(monkeypatch):
    """Регрессия. Одиночный белый пиксель у самого края области поиска (текст,
    частица, кромка платформы) раньше выигрывал у настоящей подсветки просто
    потому, что оказывался ближе. Клик уходил на край -- юнит не ставился."""
    screen = _canvas()
    spot = (576, 378)
    screen[378 + 17, 576 + 18] = 255          # тот самый «offset (18, 17)»
    _blob(screen, 576 + 10, 378 + 4)          # настоящая подсветка чуть дальше
    _patch_screen(monkeypatch, screen)

    offset = _Runner()._scan_place_search_box(0, 0, 0, *spot)

    assert offset == (10, 4), f"ожидался центр пятна, получено {offset}"


def test_cursor_already_on_the_highlight_does_not_move(monkeypatch):
    """Подсветка обычно КРУПНЕЕ области поиска: её «центр» -- это центр
    области, а не позиция курсора. Если точка уже белая, смещения быть не
    должно, иначе точный клик уезжает без причины."""
    screen = _canvas()
    screen[:, :] = 255
    _patch_screen(monkeypatch, screen)

    assert _Runner()._scan_place_search_box(0, 0, 0, 576, 378) == (0, 0)


def test_a_highlight_bigger_than_the_search_box_is_not_read_as_drift(monkeypatch):
    """РЕГРЕССИЯ ПО ЖИВОМУ ЛОГУ: «ближайшая клетка в 15px — жду, пока
    освободится нужная», хотя клетка свободна.

    Подсветка клетки КРУПНЕЕ области поиска 38x38, поэтому в коробку попадает
    только её кусок. Центр масс куска — это центр обрезка, а не центр клетки,
    и он уезжает на 11-16px. Снаружи это неотличимо от занятой клетки: макрос
    трижды ждал освобождения и ставил юнита со сносом.

    Выдавало ошибку то, что три замера подряд на одной точке давали 16, 18 и
    12 пикселей: у занятой клетки смещение не пляшет.

    Здесь подсветка накрывает курсор и выходит за края коробки, а ровно в
    точке курсора — тёмная дырка: так рисуется и сам курсор, и призрак юнита
    под ним, из-за чего уровень 1 («белый ровно под курсором») не срабатывал.
    """
    screen = _canvas()
    spot = (576, 378)
    # Пятно 80x80 — заведомо шире коробки 38x38 в обе стороны.
    screen[378 - 40:378 + 41, 576 - 40:576 + 41] = 255
    screen[378 - 1:378 + 2, 576 - 1:576 + 2] = 0        # дырка под курсором
    _patch_screen(monkeypatch, screen)

    offset = _Runner()._scan_place_search_box(0, 0, 0, *spot)

    assert offset == (0, 0), (
        f"курсор внутри подсветки — сноса быть не должно, получено {offset}")


def test_a_genuinely_occupied_tile_still_reports_drift(monkeypatch):
    """Обратная сторона правки: настоящий снос ловить всё ещё надо.

    Под курсором подсветки нет вовсе (клетка занята), а свободная клетка —
    рядом и целиком помещается в коробку. Вот это и есть тот случай, ради
    которого заведено ожидание освобождения."""
    screen = _canvas()
    spot = (576, 378)
    _blob(screen, 576 + 13, 378 - 11, size=9)    # соседняя свободная клетка
    _patch_screen(monkeypatch, screen)

    assert _Runner()._scan_place_search_box(0, 0, 0, *spot) == (13, -11)


def test_a_clipped_blob_falls_back_to_the_nearest_pixel(monkeypatch):
    """Пятно упирается в край коробки и курсора НЕ накрывает: центру масс
    такого огрызка верить нельзя — он выдуман. Берём ближайший белый пиксель:
    грубее, но это настоящая точка настоящей подсветки."""
    screen = _canvas()
    spot = (576, 378)
    # Полоса от левого края коробки и дальше влево, курсор не задевает.
    screen[378 - 30:378 + 31, 576 - 60:576 - 9] = 255
    _patch_screen(monkeypatch, screen)

    dx, dy = _Runner()._scan_place_search_box(0, 0, 0, *spot)
    # Ближайший белый пиксель — ровно на кромке полосы, в 10px слева.
    assert (dx, dy) == (-10, 0), f"ожидался ближайший пиксель полосы, получено {(dx, dy)}"


def test_lone_pixel_still_works_when_there_is_no_blob(monkeypatch):
    """Страховка от перестраховки: если в чьей-то сборке подсветка рисуется
    рябью из отдельных точек, расстановка обязана работать как раньше."""
    screen = _canvas()
    screen[378 - 5, 576 + 4] = 255
    _patch_screen(monkeypatch, screen)

    assert _Runner()._scan_place_search_box(0, 0, 0, 576, 378) == (4, -5)


def test_thin_white_line_is_not_taken_for_a_tile(monkeypatch):
    """Штрих буквы/тонкая кромка проходят по площади, но не по габаритам --
    и не должны становиться «центром клетки»."""
    screen = _canvas()
    # Полоска 1px шириной и заведомо достаточной площади.
    screen[378 - 8:378 + 8, 576 + 12] = 255
    assert 16 > PLACE_HIGHLIGHT_MIN_PIXELS  # площади хватает, габаритов нет
    _patch_screen(monkeypatch, screen)

    offset = _Runner()._scan_place_search_box(0, 0, 0, 576, 378)

    # Пятном не признана -- сработал откат к ближайшему пикселю, а не центр.
    assert offset == (12, 0), f"полоску приняли за клетку: {offset}"


def test_nothing_white_is_still_nothing(monkeypatch):
    _patch_screen(monkeypatch, _canvas())
    assert _Runner()._scan_place_search_box(0, 0, 0, 576, 378) is None


def test_short_capture_near_the_edge_does_not_index_out_of_range(monkeypatch):
    """Снимок бывает МЕНЬШЕ запрошенного (масштаб дисплея, DPI, урезанное
    окно). У точки под правым/нижним краем индекс внутри такого снимка
    вылезает за его границы -- без ограничения это IndexError посреди
    расстановки, то есть упавший забег."""
    side = PLACE_SEARCH_BOX_SIZE - 10
    small = np.full((side, side, 3), 255, np.uint8)
    monkeypatch.setattr(ocr, "capture_region", lambda x, y, w, h: small)
    monkeypatch.setattr(runner_blocks, "capture_region", lambda x, y, w, h: small, raising=False)
    monkeypatch.setattr(runner_blocks.vision, "capture_window_region_bgr",
                        lambda _hwnd, _region: small)

    assert _Runner()._scan_place_search_box(0, 0, 0, 1150, 750) == (0, 0)


# ---------------------------------------------------------------------------
# Прошёл ли клик
# ---------------------------------------------------------------------------

def test_placement_is_confirmed_when_the_tile_goes_dark(monkeypatch):
    """Клетку занял юнит -> подсветка под курсором погасла -> клик прошёл."""
    screen = _canvas()
    screen[:, :] = 255
    _patch_screen(monkeypatch, screen)
    monkeypatch.setattr(runner_blocks.time, "sleep", lambda _s: None)
    runner = _Runner()

    # Гасим пятачок под курсором ровно в момент клика -- так ведёт себя игра.
    def click(x=None, y=None, **_kw):
        runner.clicks.append((int(x), int(y)))
        screen[378 - 2:378 + 3, 576 - 2:576 + 3] = 0

    runner.click = click

    assert runner._click_place_spot(1, threading.Event(), 0, 0, 576, 378, "dps") is True
    assert runner.clicks == [(576, 378)], "лишние клики при успешной расстановке"


def test_click_that_never_registers_is_retried_then_reported(monkeypatch):
    """Регрессия. Подсветка не погасла -- значит юнит остался в руке. Раньше
    это всё равно записывалось как «placed»."""
    screen = _canvas()
    screen[:, :] = 255  # подсветка не гаснет никогда
    _patch_screen(monkeypatch, screen)
    monkeypatch.setattr(runner_blocks.time, "sleep", lambda _s: None)
    # Сдавшись, расстановка закрывает возможную панель юнита -- ей нужно окно.
    monkeypatch.setattr(runner_blocks.wm, "get_window_rect_screen", lambda _h: (0, 0, 1152, 756))
    runner = _Runner()

    landed = runner._click_place_spot(1, threading.Event(), 0, 0, 576, 378, "dps")

    assert landed is False
    on_tile = [c for c in runner.clicks if c == (576, 378)]
    assert len(on_tile) == PLACE_CONFIRM_ATTEMPTS, f"перещёлкиваний: {len(on_tile)}"
    assert any("не погасла" in m or "did not clear" in m for m in runner.logs), runner.logs


def test_quick_place_never_reclicks(monkeypatch):
    """При удержанном Shift юнит остаётся выбранным, и повторный клик поставил
    бы ВТОРОГО. Поэтому в цепочке quick-place только сообщаем, не перещёлкиваем."""
    screen = _canvas()
    screen[:, :] = 255
    _patch_screen(monkeypatch, screen)
    monkeypatch.setattr(runner_blocks.time, "sleep", lambda _s: None)
    runner = _Runner()

    landed = runner._click_place_spot(1, threading.Event(), 0, 0, 576, 378, "dps",
                                      allow_retry=False)

    assert landed is False
    assert runner.clicks == [(576, 378)], f"поставили дубль: {runner.clicks}"


# ---------------------------------------------------------------------------
# Итог фазы
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("outcomes,expected_options", [
    ([True, True], ("расставлено юнитов 2/2", "placed units 2/2")),
    ([True, False], ("расставлено 1, не встало 1", "placed 1, failed 1")),
    ([False, False], ("НИ ОДИН юнит не встал", "NO units placed")),
])
def test_phase_summary_says_what_actually_happened(outcomes, expected_options):
    runner = _Runner()
    runner._reset_placement_tally()
    for i, landed in enumerate(outcomes):
        runner._note_placement(f"unit{i}", landed)

    runner._log_placement_tally()

    assert any(any(exp in m for exp in expected_options) for m in runner.logs), runner.logs


def test_phase_summary_stays_quiet_with_no_placements():
    runner = _Runner()
    runner._reset_placement_tally()
    runner._log_placement_tally()
    assert runner.logs == []
