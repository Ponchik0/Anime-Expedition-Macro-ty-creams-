"""Режим «Повтор»: точная запись и воспроизведение действий игрока.

ЗАЧЕМ ЭТО, если есть автоматический режим. Автомат ходит по меню игры,
узнаёт кнопки по картинкам и проверяет результат — он умнее, но требует
настройки: шаблоны, координаты, сценарии. «Повтор» не знает об игре ничего.
Сыграл руками один матч — макрос повторяет ровно это, тик в тик. Ставить
нечего, настраивать нечего.

Формат записи (Recordings/<имя>.json):
    {"base_w": 1152, "base_h": 756, "duration": 187400.0, "created": "...",
     "events": [...]}
    событие: {"t": 1234.5, "kind": "down|up|move|wheel", "code": "left|W|...",
              "x": 612, "y": 430}
    t — миллисекунды от начала записи (АБСОЛЮТНОЕ смещение, не пауза).
    x/y — координаты в клиентской области окна игры, а не экрана.
    duration — полная длина записи в миллисекундах, ВКЛЮЧАЯ ожидание после
    последнего действия (см. граблю №5 ниже).

=============================================================================
ГРАБЛИ, НА КОТОРЫЕ УЖЕ НАСТУПИЛИ (см. docs/from_ahk.md, раздел 11)
=============================================================================

1. ЧАСЫ. Только time.perf_counter(). Системный тик Windows — ~15.6 мс, и на
   нём «клик через 5 мс» неотличим от «клик через 20 мс». Вся точность
   повтора держится на часах высокого разрешения.

2. РАСПИСАНИЕ АБСОЛЮТНОЕ, а не «спать между событиями». Если считать срок
   следующего события как «сейчас + пауза», то каждое опоздание планировщика
   (а их сотни) прибавляется к общей сумме: записанная минута превращается в
   полторы, и всё разъезжается с игрой. Здесь у каждого события своё
   смещение от начала круга, и опоздание не копится.

3. ОТСТАЛИ БОЛЬШЕ ЧЕМ НА КРУГ — пропущенное НЕ отыгрываем. Иначе макрос
   пытается догнать расписание и вываливает в игру сотни действий очередью.
   Просто начинаем круг с текущего момента.

4. АВТОПОВТОР ЗАЖАТОЙ КЛАВИШИ СХЛОПЫВАЕТСЯ. Зажатая W — это одно действие
   «держу», а не двести нажатий. Пишем только переходы состояния.

5. ЖДАТЬ — ЭТО ТОЖЕ ДЕЙСТВИЕ, и оно обязано попасть в запись. Длина круга
   раньше бралась как «время последнего события», то есть всё, что человек
   делал ПОСЛЕ последнего нажатия, из записи выпадало. А типичная запись
   именно так и устроена: в начале матча расставил юнитов — и дальше просто
   ждёшь конца, ничего не нажимая. Круг тогда кончался на последней
   расстановке, и повтор начинал следующий заход прямо посреди идущего боя.
   Поэтому рекордер отдельно считает ПОЛНУЮ длину (Recorder.duration_ms), она
   же лежит в файле как "duration", и круг повтора считается по ней.
   Тем же самым отличается «ждал в игре» от «отлучился»: часы записи стоят,
   пока Roblox не на экране (см. game_active), так что хвост ожидания — это
   ровно то время, что человек просидел В ИГРЕ и ничего не нажимал.

Плюс шестое, чего в AHK не было, но нужно здесь: клики по собственному окну
макроса в запись не попадают. Наше окно висит поверх игры, и нажатие на
кнопку «Запись» иначе попало бы в файл — запись выключала бы сама себя.

7. ОКНО ИГРЫ СПРАШИВАЕМ КАЖДЫЙ ТИК, И ЗАПИСЬ, И ПОВТОР. Roblox посреди
   ночного прогона перезапускается — сам, от вылета, или его перезапускает
   сторож. Плеер брал hwnd один раз на старте круга и дальше слал нажатия в
   мёртвое окно до самого «Стоп»: снаружи это «макрос работает, а в игре
   ничего не происходит». Теперь окно переспрашивается, а при смене — всё
   зажатое отпускается, масштаб пересчитывается под новый размер и круг
   начинается заново (продолжать с середины расписания в свежезапущенном
   Roblox бессмысленно: там главное меню, а не тот момент боя, где прервали).
   Пока окна нет вовсе — расписание заморожено: без hwnd клиентские
   координаты некуда пересчитывать, и клики ушли бы на рабочий стол.
"""
from __future__ import annotations

import ctypes
import json
import os
import re
import threading
import time
from datetime import datetime

from core import constants
from core import window as wm

try:                                    # Windows-путь, основной
    from core import _input_win as _inp
except Exception:                       # pragma: no cover — macOS/Linux
    _inp = None

# Опрос в 4 мс: заметно чаще, чем человек успевает щёлкнуть (самый короткий
# осмысленный клик — десятки миллисекунд), и при этом дёшево. В core.paths
# для WASD стоит 30 мс, но там и цена промаха другая: пропущенный шаг ходьбы
# не страшен, пропущенный клик — испорченная запись.
POLL_INTERVAL = 0.004

# Курсор пишем не чаще, чем раз в 16 мс: чаще бессмысленно (игра всё равно
# рисует 60 кадров в секунду), а размер файла растёт линейно.
MOVE_INTERVAL = 0.016
# И только если он реально сдвинулся дальше, чем на пару пикселей — иначе
# дрожание руки на мыши забивает запись тысячами бесполезных точек.
MOVE_MIN_DIST = 2

RECORDINGS_DIR = os.path.join(constants.APP_DIR, "Recordings")

# Пауза перед ПЕРВЫМ действием повтора.
#
# ЗАЧЕМ. Между «нажал Играть» и «игра действительно на экране» проходит
# заметное время: окно списка закрывается, экран уезжает на Панель, окно
# Roblox возвращают из спрятанного состояния (ShowWindow) и оно ловит фокус.
# Раньше расписание стартовало в тот же миг, и первые события круга уходили в
# никуда — а это ровно те события, которыми расставляют юнитов, то есть
# терялся не «кусочек начала», а весь смысл забега.
#
# На паузе отсчёт заморожен: снял паузу — досчитали остаток, а не начали
# играть сразу.
START_DELAY_MS = 2000

# Кнопки мыши. Виртуальные коды — те же, что у клавиш, поэтому опрашиваются
# одним и тем же GetAsyncKeyState.
_MOUSE = {0x01: "left", 0x02: "right", 0x04: "middle", 0x05: "x1", 0x06: "x2"}

# Клавиши под наблюдением. Перебирать все 256 кодов каждые 4 мс незачем —
# берём то, чем реально играют.
def _watched_keys() -> dict:
    keys = {}
    for c in range(ord("A"), ord("Z") + 1):
        keys[c] = chr(c)
    for c in range(ord("0"), ord("9") + 1):
        keys[c] = chr(c)
    for i in range(12):
        keys[0x70 + i] = f"F{i + 1}"
    keys.update({
        0x20: "space", 0x09: "tab", 0x0D: "enter", 0x1B: "esc",
        0x10: "shift", 0x11: "ctrl", 0x12: "alt",
        0x25: "left_arrow", 0x26: "up_arrow", 0x27: "right_arrow", 0x28: "down_arrow",
        0x08: "backspace", 0x2E: "delete",
    })
    for i in range(10):
        keys[0x60 + i] = f"num{i}"
    return keys


WATCHED_KEYS = _watched_keys()
_VK_BY_NAME = {name: vk for vk, name in WATCHED_KEYS.items()}
# Отдельно — регистронезависимая карта. Хоткеи в настройках лежат строчными
# ("f8"), а имена клавиш здесь заглавными ("F8"): без этого сопоставление
# молча не находило ни одного совпадения.
_VK_BY_LOWER = {name.lower(): vk for name, vk in _VK_BY_NAME.items()}


def _timer_precision(on: bool) -> None:
    """Просим у Windows миллисекундный тик таймера.

    Без этого system-таймер будит поток раз в ~15.6 мс, и sleep(0.004)
    превращается в sleep(0.015) — воспроизведение начинает «плыть».
    Обязательно возвращаем обратно: иначе ноутбук зря жжёт батарею.
    """
    try:
        if on:
            ctypes.windll.winmm.timeBeginPeriod(1)
        else:
            ctypes.windll.winmm.timeEndPeriod(1)
    except Exception:
        pass


def _client_xy(hwnd: int):
    """Позиция курсора в клиентских координатах окна игры.

    Именно клиентских, а не экранных: окно можно подвинуть, и запись,
    снятая до переноса, обязана остаться рабочей.
    """
    pt = ctypes.wintypes.POINT() if hasattr(ctypes, "wintypes") else None
    try:
        from ctypes import wintypes
        pt = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        if hwnd:
            ctypes.windll.user32.ScreenToClient(hwnd, ctypes.byref(pt))
        return int(pt.x), int(pt.y)
    except Exception:
        return 0, 0


def _window_at_cursor() -> int:
    """Окно непосредственно под курсором — возможно, дочернее."""
    try:
        from ctypes import wintypes
        pt = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return int(ctypes.windll.user32.WindowFromPoint(pt) or 0)
    except Exception:
        return 0


def _is_child(parent: int, child: int) -> bool:
    """Потомок ли child окна parent (на любую глубину)."""
    try:
        return bool(ctypes.windll.user32.IsChild(parent, child))
    except Exception:
        return False


def _root_of(hwnd: int) -> int:
    """Окно верхнего уровня, к которому принадлежит hwnd."""
    try:
        return int(ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd)   # GA_ROOT
    except Exception:
        return int(hwnd or 0)


def _cursor_over_gui(gui_hwnd: int, game_hwnd: int) -> bool:
    """Курсор над окном макроса — и НЕ над игрой.

    ВАЖНО, почему мало сравнить корневое окно с нашим. В обычном режиме окно
    Roblox ВСТРОЕНО в наше (SetParent, см. core/dock.py), поэтому для любой
    точки внутри игры GetAncestor(GA_ROOT) возвращает hwnd макроса. Проверка
    «корень == наше окно» тогда истинна всё время, пока курсор в игре, — и
    запись молча теряет все клики и весь путь курсора, оставляя одни клавиши
    (клавиши этой проверкой не гасятся). Ровно этот баг и был.

    Поэтому сначала спрашиваем, не в игре ли курсор: игра может быть нашим
    потомком, и тогда это всё равно ввод в игру, а не клик по нашей кнопке.
    """
    if not gui_hwnd:
        return False
    h = _window_at_cursor()
    if not h:
        return False
    if game_hwnd and (h == game_hwnd or _is_child(game_hwnd, h)):
        return False
    return _root_of(h) == gui_hwnd


def _game_focused(hwnd: int) -> bool:
    """Активно ли окно игры — с той же поправкой на встроенный режим.

    GetForegroundWindow всегда возвращает окно ВЕРХНЕГО УРОВНЯ. Когда игра
    встроена в наше окно, оно верхнего уровня никогда не бывает, и сравнение
    «активное == hwnd игры» не совпадает ни разу: галка «играть только при
    активном окне» заморозила бы повтор навсегда.
    """
    if not hwnd:
        return False
    try:
        if wm.is_foreground(hwnd):
            return True
        root = _root_of(hwnd)
        return bool(root) and root != hwnd and wm.is_foreground(root)
    except Exception:
        return True             # не смогли спросить — не блокируем повтор


def _game_on_screen(hwnd: int) -> bool:
    """Видно ли окно игры прямо сейчас.

    Отдельно от фокуса, и вот почему. В обычном режиме игра встроена в наше
    окно, и на любом экране кроме Панели макрос её ПРЯЧЕТ (hide_game ->
    ShowWindow(SW_HIDE), см. switchScreen в ui/app.js). Фокус при этом
    остаётся на окне макроса, то есть формально «окно игры активно» — хотя
    игры на экране нет вовсе и человек возится в настройках. Проверка
    видимости — то, что отличает эти два случая.
    """
    if not hwnd:
        return False
    try:
        return bool(wm.is_window_visible(hwnd))
    except Exception:
        return True             # не смогли спросить — не мешаем записи


def game_active(hwnd: int) -> bool:
    """Идёт ли ввод именно в игру: окно есть, видно и активно."""
    return bool(hwnd) and _game_on_screen(hwnd) and _game_focused(hwnd)


def safe_name(name: str) -> str:
    name = (name or "").strip() or datetime.now().strftime("rec_%Y-%m-%d_%H-%M-%S")
    return re.sub(r'[\\/:*?"<>|]', "_", name)[:80]


# ============================================================== ЗАПИСЬ =====
class Recorder:
    """Пишет ввод игрока опросом состояния клавиш в фоновом потоке.

    Опрос, а не системный хук: GetAsyncKeyState читает НАСТОЯЩЕЕ физическое
    состояние клавиш независимо от того, какое окно в фокусе. Хук пришлось бы
    вешать с циклом сообщений и он ловил бы в том числе наш собственный ввод
    при воспроизведении. Тот же приём уже используется в core/paths.py.
    """

    def __init__(self, get_game_hwnd, get_gui_hwnd=None, log=None, get_hotkeys=None):
        self._get_game = get_game_hwnd
        self._get_gui = get_gui_hwnd or (lambda: 0)
        self._log = log or (lambda m: None)
        # Свои управляющие клавиши в запись попадать НЕ должны. Иначе F8,
        # которым запись и останавливают, окажется в файле — а при повторе
        # макрос нажмёт его сам и выключит себе запись. Ровно эта защита
        # была в старом AHK-макросе (IsControlKey).
        self._get_hotkeys = get_hotkeys or (lambda: {})
        self._thread = None
        self._stop = threading.Event()
        self._events = []
        self._t0 = 0.0
        self._lock = threading.Lock()
        self.base_w = 0
        self.base_h = 0
        # Запись идёт, но игра сейчас не активна — ввод не пишем, часы стоят.
        # Панель показывает это словами: иначе «пишется, а счётчик не растёт»
        # неотличимо от поломки.
        self.waiting = False
        # Момент, с которого стоят часы (игра не активна). Поле, а не локальная
        # переменная цикла, потому что его читает elapsed_ms — а её спрашивают
        # из другого потока, пока запись идёт.
        self._idle_since = None
        # Полная длина записи в миллисекундах, включая ожидание после
        # последнего действия. Проставляется потоком записи на выходе.
        self.duration_ms = 0.0

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def elapsed_ms(self) -> float:
        """Сколько времени уже лежит в записи — по часам записи, а не по
        последнему событию.

        Именно это число надо показывать человеку: он сидит в игре и ЖДЁТ
        конца матча, ничего не нажимая. Счётчик, замерший на времени
        последней расстановки, выглядел бы как «ожидание не пишется» — хотя
        пишется как раз оно (грабля №5 в шапке файла)."""
        if not self.running:
            return self.duration_ms
        idle = self._idle_since          # читаем один раз: поток записи его меняет
        now = idle if idle is not None else time.perf_counter()
        return max(0.0, round((now - self._t0) * 1000.0, 1))

    @property
    def count(self) -> int:
        with self._lock:
            # Движение курсора считаем отдельно: точек тысячи, и показывать
            # человеку «записано 38 214 действий» — значит пугать без повода.
            return sum(1 for e in self._events if e["kind"] != "move")

    def start(self) -> bool:
        if self.running or _inp is None:
            return False
        hwnd = self._get_game() or 0
        try:
            _, _, self.base_w, self.base_h = wm.get_window_rect_screen(hwnd) if hwnd else (0, 0, 0, 0)
        except Exception:
            self.base_w = self.base_h = 0
        self._events = []
        self._stop.clear()
        self.waiting = False
        self._idle_since = None
        self.duration_ms = 0.0
        self._t0 = time.perf_counter()
        _timer_precision(True)
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> list:
        if not self.running:
            return list(self._events)
        self._stop.set()
        self._thread.join(timeout=2.0)
        self._thread = None
        self.waiting = False
        _timer_precision(False)
        with self._lock:
            return list(self._events)

    def _push(self, kind, code, x=0, y=0):
        with self._lock:
            self._events.append({
                "t": round((time.perf_counter() - self._t0) * 1000.0, 1),
                "kind": kind, "code": code, "x": int(x), "y": int(y),
            })

    def _loop(self):
        held = set()            # что сейчас зажато — источник схлопывания автоповтора
        last_move = 0.0
        last_xy = (-9999, -9999)
        # Виртуальные коды своих хоткеев — их пропускаем при записи.
        skip_vks = set()
        try:
            for key in (self._get_hotkeys() or {}).values():
                vk = _VK_BY_LOWER.get(str(key).strip().lower())
                if vk is not None:
                    skip_vks.add(vk)
        except Exception:
            pass

        # Момент, когда игра перестала быть активной, живёт в self._idle_since
        # (его же читает elapsed_ms). Пока он не None, часы записи стоят —
        # см. ниже, зачем.
        self._idle_since = None

        while not self._stop.is_set():
            hwnd = self._get_game() or 0
            # hwnd окон спрашиваем каждый тик: окно игры может смениться
            # (перезапуск Roblox), а наше — появиться позже начала записи.
            gui_hwnd = self._get_gui() or 0

            # --- пишем ТОЛЬКО когда ввод идёт в игру ---
            # Иначе в запись попадает всё подряд: переписка в браузере, пароль,
            # набранный в другом окне, возня в настройках макроса. При повторе
            # это вываливается в Roblox как нажатия — в лучшем случае мусор.
            if not game_active(hwnd):
                if self._idle_since is None:
                    # Всё зажатое закрываем СРАЗУ: иначе в файле останется
                    # «down» без пары, и при повторе клавиша залипнет в игре до
                    # конца круга. Координаты 0,0 — это «не двигай курсор,
                    # просто отпусти» (см. Player._play), как и в таком же
                    # закрытии на остановке записи.
                    for vk in list(held):
                        name = _MOUSE.get(vk) or WATCHED_KEYS.get(vk)
                        if name:
                            self._push("up", name, 0, 0)
                    held.clear()
                    self._idle_since = time.perf_counter()
                    self.waiting = True
                time.sleep(0.05)      # не в игре — опрашивать 250 раз в секунду незачем
                continue

            if self._idle_since is not None:
                # Часы записи двигаем вперёд на всё время отсутствия. Расписание
                # у нас абсолютное (см. шапку файла), и без этой поправки отлучка
                # на минуту превратилась бы при повторе в минуту, когда макрос
                # просто стоит и ничего не делает.
                self._t0 += time.perf_counter() - self._idle_since
                self._idle_since = None
                self.waiting = False
                last_xy = (-9999, -9999)   # вернулись — первую точку пути пишем сразу

            # Курсор над нашим окном (но не над игрой внутри него) — ничего
            # не пишем. Окно макроса висит поверх игры, и клик по кнопке
            # «Запись» иначе попал бы в файл.
            over_own = _cursor_over_gui(gui_hwnd, hwnd)

            x, y = _client_xy(hwnd)

            # --- кнопки мыши и клавиши, один проход ---
            for vk, name in list(_MOUSE.items()) + list(WATCHED_KEYS.items()):
                if vk in skip_vks:
                    continue          # свой хоткей — в запись не пишем
                try:
                    down = _inp.is_key_down(vk)
                except Exception:
                    continue
                was = vk in held
                if down and not was:
                    if over_own and vk in _MOUSE:
                        continue                     # клик по своему окну не пишем
                    held.add(vk)
                    self._push("down", name, x, y)
                elif not down and was:
                    held.discard(vk)
                    self._push("up", name, x, y)
                # down and was -> автоповтор, пропускаем: это одно «держу»

            # --- путь курсора ---
            now = time.perf_counter()
            if not over_own and now - last_move >= MOVE_INTERVAL:
                if abs(x - last_xy[0]) + abs(y - last_xy[1]) >= MOVE_MIN_DIST:
                    self._push("move", "", x, y)
                    last_xy = (x, y)
                last_move = now

            time.sleep(POLL_INTERVAL)

        # Остановились, не вернувшись в игру: незачтённую отлучку списываем,
        # иначе она попала бы в полную длину как «ожидание в игре».
        if self._idle_since is not None:
            self._t0 += time.perf_counter() - self._idle_since
            self._idle_since = None

        # Всё, что осталось зажатым на момент остановки, закрываем — иначе в
        # записи будет «down» без пары, и при повторе клавиша залипнет в игре.
        for vk in list(held):
            name = _MOUSE.get(vk) or WATCHED_KEYS.get(vk)
            if name:
                self._push("up", name, 0, 0)

        # Полная длина круга — до момента остановки, а не до последнего
        # нажатия (грабля №5 в шапке файла). Ставится ПОСЛЕДНЕЙ строкой:
        # stop() читает её сразу после join, и к этому моменту часы уже
        # выправлены, а всё зажатое закрыто.
        self.duration_ms = max(
            round((time.perf_counter() - self._t0) * 1000.0, 1),
            self._events[-1]["t"] if self._events else 0.0,
        )


# ====================================================== ВОСПРОИЗВЕДЕНИЕ =====
class Player:
    """Крутит запись по абсолютному расписанию.

    Состояния: idle / running / paused. Пауза замораживает часы расписания,
    а не пропускает события — иначе после снятия паузы всё пропущенное
    выпалило бы одной очередью.
    """

    def __init__(self, get_game_hwnd, log=None):
        self._get_game = get_game_hwnd
        self._log = log or (lambda m: None)
        self._thread = None
        self._stop = threading.Event()
        self._pause = threading.Event()
        self.state = "idle"
        self.loop_num = 0
        self.index = 0
        self.total = 0
        self.name = ""
        self._down = set()
        # Сколько миллисекунд осталось до первого действия. Отдельным полем, а
        # не локальной переменной потока: его читает панель, чтобы показать
        # обратный отсчёт («2… 1… начали»). Ноль — отсчёт кончился или его не
        # было вовсе.
        self.countdown_ms = 0.0

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, events: list, name: str = "", loops: int = 0,
              base_w: int = 0, base_h: int = 0, require_focus: bool = True,
              duration_ms: float = 0.0, start_delay_ms: float = 0.0) -> bool:
        """loops=0 — крутить, пока не остановят.

        duration_ms — полная длина записи вместе с ожиданием в конце. Именно
        она задаёт длину круга; без неё круг кончался бы на последнем
        нажатии, и следующий заход начинался бы посреди ещё идущего матча
        (грабля №5 в шапке файла).

        start_delay_ms — пауза перед первым действием ПЕРВОГО круга (см.
        START_DELAY_MS). Только перед первым: между кругами пауза не нужна,
        игра там уже на экране, а лишнее ожидание сдвигало бы расписание."""
        if self.running or _inp is None or not events:
            return False
        self.name = name
        self.total = len(events)
        self.index = 0
        self.loop_num = 1
        self._down = set()
        self._stop.clear()
        self._pause.clear()
        self.state = "running"
        self.countdown_ms = max(0.0, float(start_delay_ms or 0.0))
        _timer_precision(True)
        self._thread = threading.Thread(
            target=self._loop,
            args=(events, loops, base_w, base_h, require_focus, duration_ms), daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        if not self.running:
            self.countdown_ms = 0.0
            self.state = "idle"
            return
        # Флаг остановки ПЕРВЫМ, и только потом обнуление отсчёта. В обратном
        # порядке между «отсчёт кончился» и «велено стоять» оставалась щель, в
        # которую расписание успевало выпустить первое нажатие уже после того,
        # как человек нажал «Стоп».
        self._stop.set()
        self.countdown_ms = 0.0
        self._thread.join(timeout=2.0)
        self._thread = None
        self._release_all()
        _timer_precision(False)
        self.state = "idle"

    def toggle_pause(self) -> bool:
        if not self.running:
            return False
        if self._pause.is_set():
            self._pause.clear()
            self.state = "running"
        else:
            self._pause.set()
            self.state = "paused"
            # На паузе ничего не должно оставаться зажатым.
            self._release_all()
        return True

    def _release_all(self):
        for code in list(self._down):
            try:
                if code in _MOUSE.values():
                    _inp.button_up(code if code in ("left", "right", "middle") else "left")
                else:
                    vk = _VK_BY_NAME.get(code)
                    if vk is not None:
                        _inp.key_up(vk)
            except Exception:
                pass
        self._down.clear()

    def _play(self, ev, hwnd, kx, ky):
        kind, code = ev["kind"], ev["code"]
        if kind in ("move", "down", "up") and (ev["x"] or ev["y"]):
            # Клиентские координаты обратно в экранные — ровно обратная
            # операция к записи, поэтому клик попадает туда же, где был.
            try:
                from ctypes import wintypes
                pt = wintypes.POINT(int(ev["x"] * kx), int(ev["y"] * ky))
                if hwnd:
                    ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))
                _inp.move_abs(pt.x, pt.y)
            except Exception:
                pass
        if kind == "move":
            return
        is_mouse = code in _MOUSE.values()
        try:
            if kind == "down":
                if is_mouse:
                    _inp.button_down(code if code in ("left", "right", "middle") else "left")
                else:
                    vk = _VK_BY_NAME.get(code)
                    if vk is None:
                        return
                    _inp.key_down(vk)
                self._down.add(code)
            elif kind == "up":
                if is_mouse:
                    _inp.button_up(code if code in ("left", "right", "middle") else "left")
                else:
                    vk = _VK_BY_NAME.get(code)
                    if vk is None:
                        return
                    _inp.key_up(vk)
                self._down.discard(code)
        except Exception:
            pass

    @staticmethod
    def _scale_for(hwnd, base_w, base_h):
        """Множители пересчёта координат записи под текущее окно игры.

        Отдельным методом, потому что считать это приходится не только на
        старте: окно игры может смениться посреди прогона (перезапуск Roblox),
        и у нового окна свой размер."""
        try:
            if hwnd and base_w and base_h:
                _, _, cw, ch = wm.get_window_rect_screen(hwnd)
                if cw and ch:
                    return cw / base_w, ch / base_h
        except Exception:
            pass
        return 1.0, 1.0

    def _loop(self, events, loops, base_w, base_h, require_focus, duration_ms=0.0):
        total_ms = events[-1]["t"] if events else 0.0
        # Круг за кругом без разрыва, но не быстрее 50 мс: иначе запись из
        # одного клика с «повторять бесконечно» превратится в тысячу кликов
        # в секунду и завесит и игру, и интерфейс.
        # duration_ms больше total_ms ровно на хвост ожидания — то время в
        # конце записи, когда человек уже ничего не нажимал, а просто ждал
        # конца матча. Круг обязан его выждать. В записях, снятых до появления
        # этого поля, его нет — тогда всё как раньше, по последнему событию.
        cycle = max(total_ms, float(duration_ms or 0.0), 50.0)

        hwnd = self._get_game() or 0
        kx, ky = self._scale_for(hwnd, base_w, base_h)
        # Видели ли мы окно игры хоть раз за этот прогон. Нужно, чтобы отличить
        # «Roblox перезапускают прямо сейчас» от «повтор запущен вообще без
        # окна» — второе бывает только в тестах, и замирать там не надо.
        seen_window = bool(hwnd)

        # Пауза перед первым действием (см. START_DELAY_MS). Идёт ДО того, как
        # засечён t0: расписание обязано начинаться с первого настоящего
        # события, иначе пауза съела бы начало записи вместо того, чтобы его
        # уберечь. Отсчёт покадровый, а не одним sleep, чтобы «Стоп» срабатывал
        # сразу, а пауза его замораживала.
        while self.countdown_ms > 0 and not self._stop.is_set():
            if self._pause.is_set():
                time.sleep(0.02)
                continue
            step = time.perf_counter()
            time.sleep(min(0.05, self.countdown_ms / 1000.0))
            if self._pause.is_set():
                # Паузу нажали ПОСРЕДИ шага — шаг не засчитываем. Иначе после
                # нажатия отсчёт всё равно проматывал бы последние 50 мс, и
                # «на паузе время стоит» было бы неправдой. Отбрасываем в
                # безопасную сторону: отсчёт может выйти чуть длиннее, но
                # никогда не короче — а короче здесь и есть та самая беда,
                # ради которой пауза заведена.
                continue
            self.countdown_ms = max(0.0, self.countdown_ms - (time.perf_counter() - step) * 1000.0)
        self.countdown_ms = 0.0

        t0 = time.perf_counter()
        held_since = None

        while not self._stop.is_set():
            # ОКНО ИГРЫ СПРАШИВАЕМ КАЖДЫЙ ТИК, а не один раз на старте.
            #
            # ЗАЧЕМ. Roblox посреди ночного прогона перезапускается — сам, от
            # вылета, или его перезапускает сторож. hwnd старого окна после
            # этого мёртв, и повтор до самого «Стоп» слал нажатия в никуда:
            # снаружи это выглядит как «макрос работает, а в игре ничего не
            # происходит». Рекордер hwnd переспрашивал всегда, плеер — нет,
            # и вот ровно эта разница и была дырой.
            now_hwnd = self._get_game() or 0
            if now_hwnd != hwnd:
                # Всё зажатое относилось к СТАРОМУ окну — отпускаем, иначе
                # клавиша осталась бы висеть нажатой в системе.
                self._release_all()
                hwnd = now_hwnd
                kx, ky = self._scale_for(hwnd, base_w, base_h)
                if hwnd:
                    seen_window = True
                    # Круг начинаем заново. Продолжать с середины расписания в
                    # свежезапущенном Roblox бессмысленно: там сейчас главное
                    # меню, а не тот момент боя, на котором нас прервали.
                    self.index = 0
                    t0 = time.perf_counter()
                    self._log("[Повтор] Окно Roblox сменилось — начинаю круг заново.")

            # Пауза и «жду окно игры» замораживают часы расписания.
            waiting = self._pause.is_set()
            # Окно игры пропало посреди прогона — ждём, пока появится новое.
            # Жать в это время нельзя: без hwnd клиентские координаты записи
            # некуда пересчитывать, и клики ушли бы по тем же числам прямо на
            # рабочий стол, в браузер или во что там открыто.
            if not waiting and seen_window and not hwnd:
                waiting = True
            if not waiting and require_focus:
                # ИСПРАВЛЕНО: функция называется is_foreground, а не
                # is_window_focused. Из-за неверного имени hasattr всегда
                # давал False, и галка «играть только при активном окне
                # Roblox» молча не работала — запись игралась в любое окно.
                # И ещё раз исправлено: спрашивать надо _game_focused, потому
                # что встроенное окно игры активным не бывает никогда.
                #
                # И В ТРЕТИЙ РАЗ, теперь про game_active вместо _game_focused.
                # Одного фокуса мало ровно по той же причине, по которой его
                # мало рекордеру (см. _game_on_screen): в обычном режиме игра
                # ВСТРОЕНА в наше окно, и на любом экране кроме Панели макрос
                # её ПРЯЧЕТ. Фокус при этом остаётся на окне макроса, то есть
                # _game_focused говорит «да» — хотя игры на экране нет вовсе и
                # человек возится в настройках. Повтор в это время продолжал
                # жать кнопки: клики уходили в спрятанное окно, а расписание
                # ехало дальше как ни в чём не бывало. Заслонка обязана быть
                # той же самой, что у записи: видно И в фокусе.
                try:
                    waiting = not game_active(hwnd)
                except Exception:
                    waiting = False
            if waiting:
                if held_since is None:
                    held_since = time.perf_counter()
                time.sleep(0.02)
                continue
            if held_since is not None:
                t0 += time.perf_counter() - held_since
                held_since = None

            now_ms = (time.perf_counter() - t0) * 1000.0

            if self.index >= len(events):
                if loops and self.loop_num >= loops:
                    break
                self.loop_num += 1
                self.index = 0
                # Масштаб пересчитываем раз в круг. Окно игры может изменить
                # размер и НЕ сменив hwnd — вышли из полноэкранного режима,
                # переключили «вырез», подвинули границу. Проверка на смену
                # окна такое не ловит, а координаты после этого бьют мимо.
                # Раз в круг, а не каждый тик: это вызов в Windows, а круг —
                # это минуты.
                kx, ky = self._scale_for(hwnd, base_w, base_h)
                t0 += cycle / 1000.0
                # Отстали больше чем на круг — начинаем с этого момента,
                # пропущенное НЕ отыгрываем (грабля №3 в шапке файла).
                if (time.perf_counter() - t0) * 1000.0 > cycle:
                    t0 = time.perf_counter()
                continue

            ev = events[self.index]
            if now_ms < ev["t"]:
                # Спим до срока ближайшего события, но мелкими шагами, чтобы
                # стоп и пауза срабатывали без задержки. Когда до события ещё
                # далеко (хвост ожидания — это минуты), шаг крупнее: 20 мс
                # человек всё равно не заметит, а будить поток 250 раз в
                # секунду ради пустого ожидания незачем.
                left = max(0.0, (ev["t"] - now_ms) / 1000.0)
                time.sleep(min(left, 0.02 if left > 0.05 else 0.004))
                continue

            self._play(ev, hwnd, kx, ky)
            self.index += 1

        self._release_all()
        _timer_precision(False)
        self.state = "idle"


# ================================================== ХРАНЕНИЕ ЗАПИСЕЙ =======
def _ensure_dir():
    os.makedirs(RECORDINGS_DIR, exist_ok=True)


def path_for(name: str) -> str:
    return os.path.join(RECORDINGS_DIR, safe_name(name) + ".json")


def exists(name: str) -> bool:
    """Есть ли такая запись. Проверка занятости имени при переименовании —
    именно так, а не через load(): читать весь файл ради ответа «да/нет»
    незачем, а в большой записи это сотни тысяч событий."""
    return os.path.exists(path_for(name))


def save(name: str, events: list, base_w: int = 0, base_h: int = 0,
         duration_ms: float = 0.0) -> str:
    _ensure_dir()
    name = safe_name(name)
    path = os.path.join(RECORDINGS_DIR, name + ".json")
    last = events[-1]["t"] if events else 0.0
    payload = {
        "base_w": base_w, "base_h": base_h,
        # Полная длина круга вместе с ожиданием в конце. Не меньше времени
        # последнего события — иначе повтор обрезал бы сам себя.
        "duration": round(max(float(duration_ms or 0.0), float(last)), 1),
        "created": datetime.now().isoformat(timespec="seconds"),
        "events": events,
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(tmp, path)          # атомарно: обрыв записи не оставит огрызок
    return name


def load(name: str) -> dict:
    path = os.path.join(RECORDINGS_DIR, safe_name(name) + ".json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not isinstance(data.get("events"), list):
            return {}
        return data
    except Exception:
        return {}


def stats(data: dict) -> dict:
    """Сводка по записи: действий, точек пути, длина круга и его хвост.

    seconds — ПОЛНАЯ длина круга, а не время последнего нажатия: ожидание в
    конце (расставил юнитов и досидел до конца матча) — такая же часть
    записи, как и клики. tail — сколько из них пришлось на это ожидание;
    показывается человеку отдельно, потому что «42 действия · 3:07» и «42
    действия · 3:07, из них 2:40 ждём» — это две очень разные записи."""
    events = data.get("events") or []
    acts = sum(1 for e in events if e.get("kind") != "move")
    moves = len(events) - acts
    last = float(events[-1]["t"]) if events else 0.0
    # Записи, снятые до появления "duration", длятся до последнего события.
    ms = max(float(data.get("duration") or 0.0), last)
    return {"actions": acts, "moves": moves,
            "seconds": round(ms / 1000.0, 1),
            "tail": round(max(0.0, ms - last) / 1000.0, 1)}


def listing() -> list:
    _ensure_dir()
    out = []
    for fn in sorted(os.listdir(RECORDINGS_DIR)):
        if not fn.endswith(".json"):
            continue
        name = fn[:-5]
        data = load(name)
        if not data:
            continue
        st = stats(data)
        out.append({"name": name, "created": data.get("created", ""), **st})
    return out


def delete(name: str) -> bool:
    try:
        os.remove(path_for(name))
        return True
    except Exception:
        return False


def rename(old: str, new: str) -> bool:
    _ensure_dir()
    src, dst = path_for(old), path_for(new)
    if not os.path.exists(src):
        return False
    # dst может оказаться ТЕМ ЖЕ файлом: на Windows регистр в именах не
    # различается, и смена одного лишь регистра («забег» -> «Забег») иначе
    # выглядела бы как «имя занято». os.rename такую замену делает штатно.
    if os.path.normcase(src) != os.path.normcase(dst) and os.path.exists(dst):
        return False
    try:
        os.rename(src, dst)
        return True
    except Exception:
        return False
