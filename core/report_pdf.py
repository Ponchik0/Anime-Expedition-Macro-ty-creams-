"""Отчёт по забегам в PDF — статистика и история одним файлом.

ЗАЧЕМ. История забегов живёт в settings.json и обрезается по RUN_HISTORY_LIMIT:
это бегущий журнал, а не архив. Чтобы сохранить итог сессии (или показать его
кому-то), нужен снимок наружу — и такой, который открывается везде и выглядит
как отчёт, а не как выгрузка.

ПОЧЕМУ PILLOW, А НЕ OPENCV. Карточка уведомления (core/status_card.py) рисуется
через cv2.putText, и это правильно ровно потому, что она вся на английском:
шрифты Hershey у OpenCV векторные и кириллицы в них нет вовсе — русский текст
вышел бы рядом квадратиков. Здесь же и подписи русские, и имена записей их
задаёт человек. Pillow рисует настоящим TrueType, и он же умеет сохранять
страницы прямо в PDF — то есть ни новой зависимости на отрисовку, ни отдельной
библиотеки на сам PDF не нужно.

ПАЛИТРА И ВЁРСТКА — те же, что у карточки в уведомлении: тёмный фон, плашки с
цветным контуром, зелёное/красное на победу и поражение, сетка активности в
стиле вклада на GitHub. Отчёт и уведомление должны читаться как один макрос.
"""
from __future__ import annotations

import os
import time
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

# A4 при 150 точках на дюйм. Достаточно, чтобы текст был резким и на экране, и
# на печати, и при этом файл остаётся в несколько сотен килобайт.
DPI = 150
PAGE_W, PAGE_H = 1240, 1754
MARGIN = 70

# RGB (у status_card тот же набор, но в порядке BGR — там OpenCV).
BG = (18, 20, 24)
PANEL = (32, 36, 44)
LINE = (52, 58, 70)
EMPTY = (40, 44, 52)
TEXT = (238, 238, 238)
MUTED = (142, 146, 156)
GREEN = (96, 210, 96)
RED = (232, 86, 86)
PURPLE = (176, 130, 214)
GOLD = (236, 198, 72)
BRAND = (226, 130, 150)

# Шрифты берём системные: класть свои в репозиторий ради одного отчёта — лишние
# мегабайты в сборке. Порядок — от «есть на любой Windows» к запасным вариантам
# для macOS и Linux, где отчёт тоже должен собираться.
_FONT_CANDIDATES = {
    "regular": ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    "bold": ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf",
             "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
}
_FONT_DIRS = ("C:/Windows/Fonts", "")


def _font(kind: str, size: int):
    for name in _FONT_CANDIDATES[kind]:
        for folder in _FONT_DIRS:
            try:
                return ImageFont.truetype(os.path.join(folder, name) if folder else name, size)
            except OSError:
                continue
    # Ни одного TrueType не нашлось — отчёт всё равно должен собраться, просто
    # встроенным шрифтом Pillow.
    try:
        return ImageFont.load_default(size=size)
    except TypeError:                     # Pillow старее 10.1 — размер не принимает
        return ImageFont.load_default()


class _Page:
    """Одна страница отчёта: холст, курсор по вертикали и мелкие примитивы.

    Курсор нужен потому, что длина отчёта заранее не известна — история может
    быть на пять строк, а может на пятьдесят. Блоки просто просят место сверху
    вниз, а `room` отвечает, влезет ли следующий; не влез — заводим страницу.
    """

    def __init__(self):
        self.img = Image.new("RGB", (PAGE_W, PAGE_H), BG)
        self.d = ImageDraw.Draw(self.img)
        self.y = MARGIN

    @property
    def inner_w(self) -> int:
        return PAGE_W - MARGIN * 2

    def room(self, height: int) -> bool:
        return self.y + height <= PAGE_H - MARGIN

    def text(self, x, y, s, font, fill=TEXT, anchor=None):
        self.d.text((x, y), str(s), font=font, fill=fill, anchor=anchor)

    def label(self, s, size=15):
        """Заголовок раздела: мелкие капсы приглушённым цветом."""
        self.text(MARGIN, self.y, str(s).upper(), _font("bold", size), MUTED)
        self.y += size + 14

    def panel(self, x, y, w, h, accent=None):
        self.d.rounded_rectangle((x, y, x + w, y + h), radius=10, fill=PANEL,
                                 outline=accent or LINE, width=2)

    def rule(self):
        self.d.line((MARGIN, self.y, PAGE_W - MARGIN, self.y), fill=LINE, width=1)
        self.y += 1

    def ellipsize(self, s, font, max_w) -> str:
        """Обрезает строку по ширине с многоточием. Имена записей задаёт
        человек, и длинное имя иначе уехало бы в соседнюю колонку."""
        s = str(s)
        if self.d.textlength(s, font=font) <= max_w:
            return s
        while s and self.d.textlength(s + "…", font=font) > max_w:
            s = s[:-1]
        return s + "…"


def _tile(page: _Page, x, y, w, h, accent, title, value, sub=""):
    """Плашка со статистикой: подпись капсами, крупное цветное число, сноска."""
    page.panel(x, y, w, h, accent)
    page.text(x + 20, y + 18, str(title).upper(), _font("bold", 14), MUTED)
    page.text(x + 20, y + 44, value, _font("bold", 40), accent)
    if sub:
        page.text(x + 20, y + h - 32, sub, _font("regular", 15), MUTED)


def _tile_row(page: _Page, tiles, height=132, gap=18):
    """Ряд плашек во всю ширину, поровну. Возвращает высоту ряда."""
    n = len(tiles)
    w = (page.inner_w - gap * (n - 1)) // n
    for i, (accent, title, value, sub) in enumerate(tiles):
        _tile(page, MARGIN + i * (w + gap), page.y, w, height, accent, title, value, sub)
    page.y += height
    return height


def _activity_grid(page: _Page, results, cells=40, cols=20):
    """Сетка последних исходов в стиле вклада на GitHub: зелёная клетка —
    победа, красная — поражение, тусклая — место, где забега ещё не было.
    Слева направо от старых к новым, как и на карточке уведомления.

    Рядов ровно столько, сколько нужно данным. Фиксированная рамка на все
    `cells` смотрелась бы честнее по замыслу, но при четырнадцати забегах
    давала целый ряд пустых клеток под заполненным — и читалось это не как
    «место на будущее», а как не дорисовавшийся отчёт."""
    cell, gap = 24, 6
    data = list(results or [])[-cells:]
    rows = max(1, (len(data) + cols - 1) // cols)
    cells = rows * cols
    for i in range(cells):
        cx = MARGIN + (i % cols) * (cell + gap)
        cy = page.y + (i // cols) * (cell + gap)
        color = (GREEN if data[i] else RED) if i < len(data) else EMPTY
        page.d.rounded_rectangle((cx, cy, cx + cell, cy + cell), radius=5, fill=color)
    page.y += rows * (cell + gap) - gap


# Колонки истории. Ширины фиксированы (кроме названия, которое забирает
# остаток), иначе таблица «дышала» бы от страницы к странице.
_COL_MODE = 150
_COL_TIME = 130
_COL_WHEN = 210


def _history_header(page: _Page):
    f = _font("bold", 14)
    x = MARGIN
    page.text(x, page.y, "ИСХОД", f, MUTED)
    page.text(x + 90, page.y, "РЕЖИМ", f, MUTED)
    page.text(x + 90 + _COL_MODE, page.y, "КАРТА / ЗАПИСЬ", f, MUTED)
    page.text(PAGE_W - MARGIN - _COL_WHEN - _COL_TIME, page.y, "ДЛИНА", f, MUTED)
    page.text(PAGE_W - MARGIN - _COL_WHEN, page.y, "КОГДА", f, MUTED)
    page.y += 26
    page.rule()
    page.y += 8


_ROW_H = 40


def _history_row(page: _Page, run: dict):
    is_win = run.get("result") == "win"
    color = GREEN if is_win else RED
    y = page.y
    # Значок исхода — залитая плашка с W/L, тот же язык, что и в интерфейсе.
    page.d.rounded_rectangle((MARGIN, y, MARGIN + 30, y + 26), radius=7, fill=color)
    page.text(MARGIN + 15, y + 13, "W" if is_win else "L", _font("bold", 15), BG, anchor="mm")

    # Чем забег БЫЛ, а не «автомат/повтор»: Story и Challenge — это оба
    # «автомат», но в отчёте по ним смотрят как раз затем, чтобы отличить одно
    # от другого. У забегов, записанных до появления поля, вида нет — тогда
    # честнее сказать «автомат/повтор», чем выдумать режим.
    f = _font("regular", 17)
    replay = run.get("source") == "replay"
    kind = run.get("kind") or ("Повтор" if replay else "Автомат")
    page.text(MARGIN + 90, y + 4, page.ellipsize(kind, f, _COL_MODE - 12), f,
              BRAND if replay else MUTED)

    name_x = MARGIN + 90 + _COL_MODE
    name_w = PAGE_W - MARGIN - _COL_WHEN - _COL_TIME - name_x - 20
    page.text(name_x, y + 4, page.ellipsize(run.get("map") or "-", f, name_w), f, TEXT)
    page.text(PAGE_W - MARGIN - _COL_WHEN - _COL_TIME, y + 4, run.get("duration") or "-", f, MUTED)
    page.text(PAGE_W - MARGIN - _COL_WHEN, y + 4, run.get("when") or "-", f, MUTED)
    page.y += _ROW_H


def _header(page: _Page, version: str, generated: str):
    page.d.rounded_rectangle((MARGIN, page.y, PAGE_W - MARGIN, page.y + 108),
                             radius=12, fill=PANEL, outline=BRAND, width=2)
    page.text(MARGIN + 28, page.y + 22, "Отчёт по забегам", _font("bold", 38), TEXT)
    sub = "Anime Expeditions" + (f" · v{version}" if version else "")
    page.text(MARGIN + 30, page.y + 72, f"{sub} · собран {generated}", _font("regular", 17), MUTED)
    page.y += 108 + 34


def _footer(page: _Page, number: int, total: int):
    page.text(PAGE_W // 2, PAGE_H - MARGIN + 22, f"{number} / {total}",
              _font("regular", 14), MUTED, anchor="mm")


def _rate(w: int, l: int) -> str:
    return f"{round(w / (w + l) * 100)}%" if (w + l) else "-"


def render_pages(*, stats: dict, history: list) -> list:
    """Страницы отчёта как список картинок Pillow.

    Отделено от build() затем, чтобы вёрстку можно было посмотреть глазами и
    проверить тестом, не разбирая готовый PDF: PDF без стороннего растеризатора
    обратно в картинку не превратить, и любая ошибка вёрстки была бы видна
    только человеку, открывшему файл.
    """
    stats = stats or {}
    history = list(history or [])
    sw, sl = int(stats.get("session_wins") or 0), int(stats.get("session_losses") or 0)
    aw, al = int(stats.get("all_time_wins") or 0), int(stats.get("all_time_losses") or 0)
    version = stats.get("version") or ""
    generated = datetime.now().strftime("%d.%m.%Y %H:%M")

    pages = [_Page()]
    page = pages[0]
    _header(page, version, generated)

    # ── Сессия ───────────────────────────────────────────────────────────
    page.label("Эта сессия")
    _tile_row(page, [
        (GREEN,  "Победы",         str(sw), f"из {sw + sl} матчей" if sw + sl else "матчей не было"),
        (RED,    "Поражения",      str(sl), ""),
        (PURPLE, "Процент побед",  _rate(sw, sl), ""),
        (GOLD,   "Забегов в час",  str(stats.get("runs_per_hour") or "-"), ""),
    ])
    page.y += 30

    # ── За всё время ─────────────────────────────────────────────────────
    page.label("За всё время")
    _tile_row(page, [
        (GREEN,  "Победы",        str(aw), ""),
        (RED,    "Поражения",     str(al), ""),
        (PURPLE, "Процент побед", _rate(aw, al), ""),
        (GOLD,   "Всего забегов", str(aw + al), ""),
    ])
    page.y += 30

    # ── Активность ───────────────────────────────────────────────────────
    page.label("Активность")
    _activity_grid(page, stats.get("results"))
    page.y += 34

    # ── История ──────────────────────────────────────────────────────────
    page.label(f"История забегов · {len(history)}" if history else "История забегов")
    if not history:
        page.text(MARGIN, page.y, "Забегов ещё не было.", _font("regular", 17), MUTED)
    else:
        _history_header(page)
        for run in history:
            # Не влезло — новая страница, и шапка таблицы на ней повторяется:
            # иначе вторая страница читалась бы как столбик чисел без названий.
            if not page.room(_ROW_H):
                page = _Page()
                pages.append(page)
                page.label("История забегов · продолжение")
                _history_header(page)
            _history_row(page, run)

    for i, p in enumerate(pages, 1):
        _footer(p, i, len(pages))
    return [p.img for p in pages]


def build(path: str, *, stats: dict, history: list) -> str:
    """Собирает отчёт и сохраняет его в `path`. Возвращает путь.

    `stats` — то же, что отдаёт Api._run_stats_snapshot; `history` — строки
    истории забегов, новые сверху, каждая с уже готовым человеческим "when".
    """
    images = render_pages(stats=stats, history=history)
    images[0].save(path, "PDF", save_all=True, append_images=images[1:], resolution=DPI)
    return path


def default_filename() -> str:
    return f"AnimeExpeditions-забеги-{time.strftime('%Y%m%d-%H%M%S')}.pdf"
