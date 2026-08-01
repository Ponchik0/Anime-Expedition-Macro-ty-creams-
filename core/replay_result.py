"""Исход матча в режиме «Повтор»: победа/поражение, статистика, уведомление.

ЗАЧЕМ ОТДЕЛЬНЫЙ МОДУЛЬ, если всё это уже умеет автомат. Автомат знает исход
потому, что сам довёл забег до экрана результата: он щёлкал по меню, ждал
телепорт, следил за боем — и в нужный момент посмотрел на баннер. Повтор об
игре не знает НИЧЕГО, он просто крутит записанные нажатия. Поэтому и смотреть
за экраном ему надо иначе: не «в конце матча», а всё время, пока крутится
запись, и не мешая расписанию.

Что делает наблюдатель:
    • раз в полторы секунды ищет «victory»/«defeat» теми же эталонами, что и
      автомат (Assets/ui) — своих картинок не заводит, чтобы Менеджер картинок
      правил оба режима сразу;
    • поймал баннер — отдаёт исход наружу (там он идёт в историю забегов, в
      счётчики сессии и в уведомление) и ЗАПИРАЕТСЯ до тех пор, пока баннер не
      уйдёт с экрана. Без этого запора один матч посчитался бы столько раз,
      сколько опросов успело пройти, пока висит экран результата, — то есть
      десяток побед за один забег;
    • длину матча считает от предыдущего исхода, а не от начала повтора: круг
      второй и дальше должны показывать своё время, а не сумму с начала.

Чего он НЕ делает: не кликает. Ни одного нажатия отсюда в игру не уходит —
экран результата закроет сама запись, она этому и обучена. Наблюдатель только
смотрит.

ЕСЛИ ЭТАЛОНЫ НЕ СОВПАДАЮТ. Тогда исход просто не распознается и в историю
ничего не попадёт — повтор при этом крутится как ни в чём не бывало. Это то же
ограничение, что и у автомата (см. _match_ended_without_a_banner в
core/runner.py), и лечится тем же: Настройки → Общие → Менеджер картинок.
"""
from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timezone

from core import replay as _replay
from core import vision
from core.runner_constants import MATCH_END_BUTTON_NAME, MATCH_RESULT_RELAXED_THRESHOLD

# Опрос экрана. Полторы секунды — компромисс: экран результата висит секундами,
# так что не пропустим, а сравнение картинок стоит заметно дороже, чем ожидание
# в расписании повтора, и частить им незачем.
POLL_INTERVAL = 1.5

# Баннеры исхода. Имена — те же, что ищет автомат.
BANNERS = (("victory", "win"), ("defeat", "loss"))

# ПОДТВЕРЖДЕНИЕ ВТОРЫМ ОПРОСОМ. Один совпавший кадр — этого мало: захват окна
# ловит и промежуточные кадры анимации, и полупрозрачные наложения, и просто
# неудачный момент перерисовки. Ложное срабатывание тут стоит дорого — оно
# пишет в статистику победу, которой не было, и портит винрейт навсегда. Экран
# результата висит секундами, так что подтверждение стоит всего один опрос.
CONFIRM_SIGHTINGS = 2

# Сторож тишины: столько кругов подряд без единого распознанного исхода — и
# что-то не так (игра обновилась, кнопка съехала, запись больше не подходит).
# Не останавливаем — просто говорим вслух, потому что длинная запись с одним
# матчем на три круга это законный случай.
SILENCE_CYCLES = 3
# Но не раньше этого времени: у короткой записи три круга — это минута, и
# ругаться через минуту после старта было бы просто шумом.
SILENCE_MIN_SECONDS = 15 * 60


def format_duration(seconds: float) -> str:
    """«3m 12s» / «47s» — тот же вид, что у автомата (_format_duration)."""
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    return f"{m}m {s}s" if m else f"{s}s"


class ResultWatcher:
    """Фоновый наблюдатель за экраном во время повтора.

    on_result(result, duration_str, screenshot_path) вызывается из ЭТОГО
    потока: он ничего не блокирует у повтора, но и держать его долго не стоит —
    отправка уведомления внутри обработчика это уже делает сама, на своём
    потоке.
    """

    def __init__(self, get_hwnd, on_result, log=None, while_running=None, on_silence=None):
        self._get_hwnd = get_hwnd
        self._on_result = on_result
        self._log = log or (lambda m: None)
        # Сторож тишины зовёт это, когда исходов долго нет. Отдельным
        # обработчиком, а не отправкой прямо отсюда: наблюдатель не должен
        # знать ни про настройки вебхука, ни про то, что там за адрес.
        self._on_silence = on_silence or (lambda: None)
        # Длина круга записи в секундах — из неё считается, сколько тишины
        # считать подозрительной. Ноль — считаем только по нижней границе.
        self._cycle_seconds = 0.0
        # Повтор может кончиться сам — когда отыграно заданное число кругов, а
        # не по кнопке «Стоп». Без этой проверки наблюдатель остался бы
        # опрашивать экран до закрытия приложения и засчитывал бы в статистику
        # матчи, которые человек играет уже руками.
        self._while_running = while_running or (lambda: True)
        self._thread = None
        self._stop = threading.Event()
        self.name = ""
        # Сколько исходов поймано за этот запуск — панель показывает это как
        # «матчей за прогон», чтобы было видно, что наблюдатель вообще живой.
        self.matches = 0

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _silent_too_long(self, since: float) -> bool:
        """Пора ли ругаться на затянувшуюся тишину.

        Порог считается от ДЛИНЫ КРУГА, а не фиксированным числом минут: у
        записи на три минуты и у записи на сорок «давно ничего не было» —
        это очень разное время. Нижняя граница нужна, чтобы короткая запись не
        начала ругаться через минуту после старта."""
        limit = max(SILENCE_MIN_SECONDS, self._cycle_seconds * SILENCE_CYCLES)
        return (time.perf_counter() - since) >= limit

    def start(self, name: str = "", cycle_seconds: float = 0.0) -> bool:
        if self.running:
            return False
        self.name = name
        try:
            self._cycle_seconds = max(0.0, float(cycle_seconds or 0.0))
        except (TypeError, ValueError):
            self._cycle_seconds = 0.0
        self.matches = 0
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        if not self.running:
            return
        self._stop.set()
        self._thread.join(timeout=3.0)
        self._thread = None

    def _banner(self, hwnd: int, missing: set, threshold=None):
        """Какой баннер сейчас на экране: "win"/"loss"/None.

        `missing` копит имена эталонов, которых нет на диске: ругаться о них
        надо один раз, а не каждые полторы секунды все полчаса забега."""
        for image_name, result in BANNERS:
            try:
                kw = {"threshold": threshold} if threshold else {}
                if vision.find_image(hwnd, image_name, **kw) is not None:
                    return result
            except vision.TemplateNotFound:
                if image_name not in missing:
                    missing.add(image_name)
                    self._log(f'[Повтор] Нет эталона «{image_name}» — исход матча '
                              f'распознаваться не будет. Добавь свою вырезку: '
                              f'Настройки → Общие → Менеджер картинок.')
            except Exception:
                pass                      # разовый сбой захвата — не повод падать
        return None

    def _find(self, hwnd: int, missing: set):
        """Исход на экране прямо сейчас, с той же страховкой, что у автомата.

        ВТОРАЯ ПРИМЕТА КОНЦА МАТЧА. Баннеры «Victory»/«Defeat» нарезаны на
        настройках автора движка и совпадают не у всех: другое качество
        графики, другое разрешение — и порог не дотягивается. Но экран
        результата при этом на месте, и на нём есть кнопка «Repeat Stage»,
        которой в бою не бывает (там на её месте живой «Leave Stage» — это
        другое имя поиска). Раз панель на экране, баннер там ТОЖЕ есть, просто
        слабый: перепроверяем его мягким порогом.

        Автомат делает ровно это (см. _match_ended_without_a_banner в
        core/runner.py), и разводить две разные логики распознавания одного и
        того же экрана нельзя — расходятся."""
        found = self._banner(hwnd, missing)
        if found is not None:
            return found
        try:
            end_button = vision.find_image(hwnd, MATCH_END_BUTTON_NAME)
        except vision.TemplateNotFound:
            return None                   # шаблона кнопки нет — страховки просто не будет
        except Exception:
            return None
        if end_button is None:
            return None
        return self._banner(hwnd, missing, threshold=MATCH_RESULT_RELAXED_THRESHOLD)

    def _loop(self):
        missing = set()
        armed = True                      # готов засчитать следующий исход
        since = time.perf_counter()       # начало текущего матча
        pending = None                    # исход, увиденный раз и ждущий подтверждения
        seen = 0                          # сколько опросов подряд его видно
        complained = False                # о тишине ругались? (один раз на затишье)
        while not self._stop.is_set():
            try:
                if not self._while_running():
                    break
            except Exception:
                break
            hwnd = self._get_hwnd() or 0
            # Смотреть, когда игры нет на экране, нечего: захват вернул бы либо
            # ошибку, либо чужое окно. Заодно это не даёт засчитать исход,
            # который «увиделся» на скриншоте спрятанного окна.
            if not hwnd or not _replay.game_active(hwnd):
                self._stop.wait(POLL_INTERVAL)
                continue

            found = self._find(hwnd, missing)

            if found is None:
                # Баннер ушёл — снова готовы ловить. Именно так и отделяется
                # один матч от следующего.
                armed = True
                pending, seen = None, 0
            elif not armed:
                pass                      # этот матч уже засчитан, ждём, когда экран уйдёт
            elif found != pending:
                # Первое совпадение. Само по себе оно ничего не значит: захват
                # ловит и кадры анимации, и полупрозрачные наложения. Ждём
                # подтверждения следующим опросом (см. CONFIRM_SIGHTINGS).
                pending, seen = found, 1
            elif seen + 1 < CONFIRM_SIGHTINGS:
                seen += 1
            else:
                armed = False
                pending, seen = None, 0
                complained = False        # исход есть — затишье кончилось
                self.matches += 1
                duration = format_duration(time.perf_counter() - since)
                since = time.perf_counter()
                shot = self._capture(hwnd)
                self._log(f'[Повтор] {"Победа" if found == "win" else "Поражение"} '
                          f'— матч {self.matches} за прогон, {duration}.')
                try:
                    self._on_result(found, duration, shot)
                except Exception as exc:
                    self._log(f"[Повтор] Не вышло записать исход матча: {exc}")
                    if shot:
                        try:
                            os.remove(shot)
                        except OSError:
                            pass

            # СТОРОЖ ТИШИНЫ. Крутится давно, а ни одного исхода не распознано —
            # почти наверняка что-то сломалось: игра обновилась, кнопка съехала,
            # запись больше не подходит. Останавливать не берёмся (длинная
            # запись с одним матчем на несколько кругов — законный случай), но
            # молчать нельзя: ради этого макрос и оставляют на ночь.
            if not complained and self._silent_too_long(since):
                complained = True
                self._log(f"[Повтор] За {format_duration(time.perf_counter() - since)} "
                          f"ни одного распознанного исхода. Обычно это значит, что "
                          f"эталоны «victory»/«defeat» перестали совпадать — проверь "
                          f"Настройки → Общие → Менеджер картинок.")
                self._on_silence()

            self._stop.wait(POLL_INTERVAL)

    def _capture(self, hwnd) -> str:
        """Снимок экрана результата во временный файл — его прикладывает
        уведомление. None, если снять не вышло: уведомление тогда уйдёт без
        картинки, но уйдёт."""
        try:
            import tempfile
            fd, path = tempfile.mkstemp(prefix="ae_replay_", suffix=".png")
            os.close(fd)
            saved = vision.save_window_screenshot(hwnd, path)
            if saved:
                return saved
            try:
                os.remove(path)
            except OSError:
                pass
        except Exception:
            pass
        return None


# ==================================================== УВЕДОМЛЕНИЕ ==========
def _tree_rows(rows) -> str:
    """Строки-ветки для одного поля эмбеда: «├ **Ключ:** `значение`», последняя
    на уголке «└». Ровно тот же вид, что у уведомления автомата
    (MacroRunner._tree_rows) — уведомления двух режимов обязаны читаться как
    одно, а не как два разных макроса."""
    rows = [r for r in rows if r is not None]
    return "\n".join(
        f'{"└" if i == len(rows) - 1 else "├"} **{label}:** `{value}`'
        for i, (label, value) in enumerate(rows))


def _format_elapsed(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def send_notice(webhook_cfg: dict, title: str, text: str, warning: bool = True,
                log=None) -> None:
    """Короткое уведомление без карточки и скриншота — «что-то идёт не так».

    Отдельно от send_webhook, потому что это принципиально другое сообщение:
    у него нет ни исхода, ни длины матча, ни статистики. Пришивать его к
    карточке результата значило бы рисовать победу там, где её не было.
    """
    log = log or (lambda m: None)
    url = (webhook_cfg or {}).get("url")
    if not url or not webhook_cfg.get("enabled"):
        return
    from core import webhook as webhook_module

    embed = {
        "title": title,
        "color": 0xE3B158 if warning else 0x6E7684,
        "description": text,
        "footer": {"text": "Anime Expeditions · Повтор"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    mention_id = (webhook_cfg or {}).get("mention_id")
    try:
        res = webhook_module.send(url, embed,
                                  content=f"<@{mention_id}>" if mention_id else "",
                                  silent=bool(webhook_cfg.get("silent")))
    except Exception as exc:
        log(f"[Повтор] Уведомление не ушло: {exc}")
        return
    if not res["ok"]:
        log(f"[Повтор] Уведомление не ушло: {res['reason']}")


def send_webhook(webhook_cfg: dict, result: str, recording: str, duration: str,
                 loop_num: int, screenshot_path: str = None,
                 stats: dict = None, log=None) -> None:
    """Уведомление об исходе матча, отыгранного повтором.

    Карточка та же, что у автомата (те же поля, та же полоска серии, та же
    картинка status_card) — отличается только блок «Match»: вместо карты,
    этапа и сложности там имя записи и номер круга. Всё остальное человек
    читает одинаково в обоих режимах, и разводить два разных вида уведомления
    было бы ровно тем, за что их перестают читать.
    """
    log = log or (lambda m: None)
    url = (webhook_cfg or {}).get("url")
    if not url or not webhook_cfg.get("enabled"):
        return
    from core import webhook as webhook_module

    stats = stats or {}
    is_win = result == "win"
    sw, sl = stats.get("session_wins", 0), stats.get("session_losses", 0)
    aw, al = stats.get("all_time_wins", 0), stats.get("all_time_losses", 0)
    session_time = _format_elapsed(time.time() - stats["session_start"]) if stats.get("session_start") else "-"
    session_rate = f"{round(sw / (sw + sl) * 100)}%" if (sw + sl) else "-"
    all_time_rate = f"{round(aw / (aw + al) * 100)}%" if (aw + al) else "-"
    runs_per_hour = stats.get("runs_per_hour", "-")
    tuc = stats.get("time_until_challenge", "-")

    fields = [
        {"name": "⚔️ Match", "value": _tree_rows([
            ("Result", "Victory \U0001F3C6" if is_win else "Defeat \U0001F480"),
            ("Duration", duration or "-"),
            ("Запись", recording or "-"),
            ("Круг", loop_num or "-"),
        ]), "inline": True},
        {"name": "\U0001F4CA Session", "value": _tree_rows([
            ("Elapsed", session_time),
            ("Record", f"{sw}W · {sl}L"),
            ("Rate", session_rate),
            ("Runs/h", runs_per_hour),
            ("Challenge", tuc),
        ]), "inline": True},
        {"name": "\U0001F3C6 All Time", "value": _tree_rows([
            ("Record", f"{aw}W · {al}L"),
            ("Rate", all_time_rate),
        ]), "inline": False},
    ]

    result_word = "Victory" if is_win else "Defeat"
    description = f"{result_word} по записи **{recording}** — матч сессии **#{sw + sl}**."
    if sw + sl:
        filled = int(round(sw / (sw + sl) * 10))
        description += f"\n`{'▰' * filled}{'▱' * (10 - filled)}` **{session_rate}** за сессию"

    version = stats.get("version")
    main_embed = {
        "title": "Victory! \U0001F3C6" if is_win else "Defeat \U0001F480",
        "color": 0x3FBF6F if is_win else 0xE05A6D,
        "description": description,
        "fields": fields,
        "footer": {"text": "Anime Expeditions" + (f" · v{version}" if version else "")},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # Строка автора над заголовком — тем же местом, что у автомата занят
        # режим и сценарий, здесь подписан режим повтора и имя записи.
        "author": {"name": f"Повтор · {recording or '-'}"},
    }

    embeds = [main_embed]
    files = []
    try:
        import cv2
        from core import status_card
        card = status_card.render_status_card_bgr(
            is_win=is_win, action="Match Finished", last_run_duration=duration,
            last_run_win=is_win, time_until_challenge=tuc,
            session_wins=sw, session_losses=sl, all_time_wins=aw, all_time_losses=al,
            runs_per_hour=runs_per_hour, results=stats.get("results"))
        if card is not None:
            ok, buf = cv2.imencode(".png", card)
            if ok:
                files.append(("card.png", buf.tobytes()))
                main_embed["image"] = {"url": "attachment://card.png"}
    except Exception as exc:
        log(f"[Повтор] Не удалось нарисовать карточку: {exc}")

    if screenshot_path and os.path.isfile(screenshot_path):
        try:
            with open(screenshot_path, "rb") as f:
                files.append(("shot.png", f.read()))
            embeds.append({"color": main_embed["color"], "image": {"url": "attachment://shot.png"}})
        except OSError:
            pass

    mention_id = (webhook_cfg or {}).get("mention_id")
    try:
        res = webhook_module.send_rich(
            url, embeds=embeds, file_attachments=files,
            content=f"<@{mention_id}>" if mention_id else "",
            silent=bool(webhook_cfg.get("silent")))
    except Exception as exc:
        log(f"[Повтор] Уведомление не ушло: {exc}")
        return
    log("[Повтор] Уведомление отправлено." if res["ok"]
        else f"[Повтор] Уведомление не ушло: {res['reason']}")
