"""Режим «Повтор»: точная запись и воспроизведение действий игрока.

ЗАЧЕМ ЭТО, если есть автоматический режим. Автомат ходит по меню игры,
узнаёт кнопки по картинкам и проверяет результат — он умнее, но требует
настройки: шаблоны, координаты, сценарии. «Повтор» не знает об игре ничего.
Сыграл руками один матч — макрос повторяет ровно это, тик в тик. Ставить
нечего, настраивать нечего.

Формат записи (Recordings/<имя>.json):
    {"base_w": 1152, "base_h": 756, "created": "...", "events": [...]}
    событие: {"t": 1234.5, "kind": "down|up|move|wheel", "code": "left|W|...",
              "x": 612, "y": 430}
    t — миллисекунды от начала записи (АБСОЛЮТНОЕ смещение, не пауза).
    x/y — координаты в клиентской области окна игры, а не экрана.

=============================================================================
ЧЕТЫРЕ ГРАБЛИ, НА КОТОРЫЕ УЖЕ НАСТУПИЛИ (см. docs/from_ahk.md, раздел 11)
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

Плюс пятое, чего в AHK не было, но нужно здесь: клики по собственному окну
макроса в запись не попадают. Наше окно висит поверх игры, и нажатие на
кнопку «Запись» иначе попало бы в файл — запись выключала бы сама себя.
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


def _root_window_at_cursor() -> int:
    try:
        from ctypes import wintypes
        pt = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        h = ctypes.windll.user32.WindowFromPoint(pt)
        if not h:
            return 0
        root = ctypes.windll.user32.GetAncestor(h, 2)   # GA_ROOT
        return int(root or h)
    except Exception:
        return 0


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

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

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
        gui_hwnd = self._get_gui() or 0
        # Виртуальные коды своих хоткеев — их пропускаем при записи.
        skip_vks = set()
        try:
            for key in (self._get_hotkeys() or {}).values():
                vk = _VK_BY_LOWER.get(str(key).strip().lower())
                if vk is not None:
                    skip_vks.add(vk)
        except Exception:
            pass

        while not self._stop.is_set():
            hwnd = self._get_game() or 0

            # Курсор над нашим окном — ничего не пишем. Окно макроса висит
            # поверх игры, и клик по кнопке «Запись» иначе попал бы в файл.
            over_own = bool(gui_hwnd) and _root_window_at_cursor() == gui_hwnd

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

        # Всё, что осталось зажатым на момент остановки, закрываем — иначе в
        # записи будет «down» без пары, и при повторе клавиша залипнет в игре.
        for vk in list(held):
            name = _MOUSE.get(vk) or WATCHED_KEYS.get(vk)
            if name:
                self._push("up", name, 0, 0)


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

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, events: list, name: str = "", loops: int = 0,
              base_w: int = 0, base_h: int = 0, require_focus: bool = True) -> bool:
        """loops=0 — крутить, пока не остановят."""
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
        _timer_precision(True)
        self._thread = threading.Thread(
            target=self._loop, args=(events, loops, base_w, base_h, require_focus), daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        if not self.running:
            self.state = "idle"
            return
        self._stop.set()
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

    def _loop(self, events, loops, base_w, base_h, require_focus):
        total_ms = events[-1]["t"] if events else 0.0
        # Круг за кругом без разрыва, но не быстрее 50 мс: иначе запись из
        # одного клика с «повторять бесконечно» превратится в тысячу кликов
        # в секунду и завесит и игру, и интерфейс.
        cycle = max(total_ms, 50.0)

        hwnd = self._get_game() or 0
        kx = ky = 1.0
        try:
            if hwnd and base_w and base_h:
                _, _, cw, ch = wm.get_window_rect_screen(hwnd)
                if cw and ch:
                    kx, ky = cw / base_w, ch / base_h
        except Exception:
            pass

        t0 = time.perf_counter()
        held_since = None

        while not self._stop.is_set():
            # Пауза и «жду окно игры» замораживают часы расписания.
            waiting = self._pause.is_set()
            if not waiting and require_focus:
                # ИСПРАВЛЕНО: функция называется is_foreground, а не
                # is_window_focused. Из-за неверного имени hasattr всегда
                # давал False, и галка «играть только при активном окне
                # Roblox» молча не работала — запись игралась в любое окно.
                try:
                    waiting = not wm.is_foreground(hwnd)
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
                t0 += cycle / 1000.0
                # Отстали больше чем на круг — начинаем с этого момента,
                # пропущенное НЕ отыгрываем (грабля №3 в шапке файла).
                if (time.perf_counter() - t0) * 1000.0 > cycle:
                    t0 = time.perf_counter()
                continue

            ev = events[self.index]
            if now_ms < ev["t"]:
                # Спим до срока ближайшего события, но мелкими шагами, чтобы
                # стоп и пауза срабатывали без задержки.
                time.sleep(min(0.004, max(0.0, (ev["t"] - now_ms) / 1000.0)))
                continue

            self._play(ev, hwnd, kx, ky)
            self.index += 1

        self._release_all()
        _timer_precision(False)
        self.state = "idle"


# ================================================== ХРАНЕНИЕ ЗАПИСЕЙ =======
def _ensure_dir():
    os.makedirs(RECORDINGS_DIR, exist_ok=True)


def save(name: str, events: list, base_w: int = 0, base_h: int = 0) -> str:
    _ensure_dir()
    name = safe_name(name)
    path = os.path.join(RECORDINGS_DIR, name + ".json")
    payload = {
        "base_w": base_w, "base_h": base_h,
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
    events = data.get("events") or []
    acts = sum(1 for e in events if e.get("kind") != "move")
    moves = len(events) - acts
    ms = events[-1]["t"] if events else 0
    return {"actions": acts, "moves": moves, "seconds": round(ms / 1000.0, 1)}


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
    path = os.path.join(RECORDINGS_DIR, safe_name(name) + ".json")
    try:
        os.remove(path)
        return True
    except Exception:
        return False


def rename(old: str, new: str) -> bool:
    _ensure_dir()
    src = os.path.join(RECORDINGS_DIR, safe_name(old) + ".json")
    dst = os.path.join(RECORDINGS_DIR, safe_name(new) + ".json")
    if not os.path.exists(src) or os.path.exists(dst):
        return False
    try:
        os.rename(src, dst)
        return True
    except Exception:
        return False
