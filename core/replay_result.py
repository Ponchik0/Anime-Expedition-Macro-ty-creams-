"""Исход матча в режиме «Повтор»: победа/поражение, статистика, уведомление.

ЗАЧЕМ ОТДЕЛЬНЫЙ МОДУЛЬ, если всё это уже умеет автомат. Автомат знает исход
потому, что сам довёл забег до экрана результата: он щёлкал по меню, ждал
телепорт, следил за боем — и в нужный момент посмотрел на баннер. Повтор об
игре не знает НИЧЕГО, он просто крутит записанные нажатия. Поэтому и смотреть
за экраном ему надо иначе: не «в конце матча», а всё время, пока крутится
запись, и не мешая расписанию.

Что делает наблюдатель:
    • раз в полсекунды снимает ОДИН кадр и считает по нему, насколько похожи
      «victory»/«defeat» — теми же эталонами, что и автомат (Assets/ui), своих
      картинок не заводит, чтобы Менеджер картинок правил оба режима сразу;
    • решает по СЧЁТУ, а не по «да/нет» (см. STRONG_THRESHOLD/WEAK_THRESHOLD);
    • поймал исход — отдаёт его наружу (там он идёт в историю забегов, в
      счётчики сессии и в уведомление) и ЗАПИРАЕТСЯ до тех пор, пока баннер не
      уйдёт с экрана. Без этого запора один матч посчитался бы столько раз,
      сколько опросов успело пройти, пока висит экран результата, — то есть
      десяток побед за один забег;
    • длину матча считает от предыдущего исхода, а не от начала повтора: круг
      второй и дальше должны показывать своё время, а не сумму с начала.

ПОЧЕМУ ПО СЧЁТУ, А НЕ ПО «ДА/НЕТ». Живой случай: за десять часов повтора
засчитан ОДИН матч из примерно сотни. Разбор — автомат в том же журнале ловит
баннер со счётом 0.90 и 0.91 при пороге 0.90, то есть берёт порог с запасом в
одну сотую. На таком зазоре совпадение мерцает от кадра к кадру: попал,
промахнулся, попал. Автомату это безразлично — он засчитывает ПЕРВОЕ попадание
(см. _wait_for_result в core/runner.py). А здесь стояло подтверждение по двум
кадрам ПОДРЯД, и любой единичный промах сбрасывал счётчик в ноль. Два подряд на
таком зазоре почти не выпадают — отсюда и один матч за ночь.

Поэтому теперь так:
    • счёт взял STRONG_THRESHOLD — засчитываем сразу, как автомат. Мерцать
      нечему;
    • счёт в полосе WEAK..STRONG — «почти»: ждём подтверждения, но НЕ подряд, а
      в пределах CONFIRM_WINDOW и НА ТОМ ЖЕ МЕСТЕ экрана. Место и отличает
      настоящий баннер от случайного пятна похожей яркости посреди боя: баннер
      стоит, пятно ползёт;
    • баннера нет вовсе, но видно кнопку «Repeat Stage» — матч всё равно
      кончился (RESULT_UNKNOWN, ровно как у автомата). В статистику такой не
      идёт, но и тишиной больше не притворяется.

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
from core import stats_report
from core import vision
from core.runner_constants import (MATCH_END_BUTTON_NAME, MATCH_RESULT_RELAXED_THRESHOLD,
                                    RESULT_UNKNOWN)

# Вид длительности — общий на весь макрос (core/stats_report.py). Своя копия
# этой функции жила здесь ровно до тех пор, пока не понадобилась третьему
# месту: три копии одного форматирования расходятся молча, и уведомления
# начинают выглядеть как сообщения от разных программ.
format_duration = stats_report.format_duration

# Опрос экрана. Полсекунды — вдвое чаще, чем у автомата (1.0 с), и вот почему.
#
# У автомата экран результата ВИСИТ: он сам его и закрывает, когда сочтёт
# нужным, поэтому там можно опрашивать неспешно и засчитывать с первого
# совпадения. В повторе экран закрывает ЗАПИСЬ — то есть ты сам, и при записи
# «Leave Stage» жмут сразу, через секунду-другую. Прежние 1.5 секунды на такт
# при подтверждении по двум кадрам (см. CONFIRM_SIGHTINGS) требовали, чтобы
# баннер провисел от полутора до трёх секунд. Он столько не висит, и наблюдатель
# честно молчал по пятнадцать минут подряд.
#
# Полсекунды сокращают нужную выдержку до 0.5-1.0 с — короче, чем у автомата,
# при том что подтверждение по двум кадрам остаётся.
POLL_INTERVAL = 0.5

# Баннеры исхода. Имена — те же, что ищет автомат.
BANNERS = (("victory", "win"), ("defeat", "loss"))

# УВЕРЕННОЕ СОВПАДЕНИЕ — засчитываем сразу, без подтверждения, ровно как
# автомат. Порог тот же самый: разводить два разных понятия «нашлось» для
# одного и того же экрана нельзя, они разойдутся.
STRONG_THRESHOLD = vision.DEFAULT_THRESHOLD
# ПОЛОСА «ПОЧТИ». Ниже уверенного порога, но выше этого — совпадение,
# которому нужно подтверждение. Значение то же, каким автомат перепроверяет
# баннер на экране результата.
WEAK_THRESHOLD = MATCH_RESULT_RELAXED_THRESHOLD

# ПОДТВЕРЖДЕНИЕ СЛАБОГО СОВПАДЕНИЯ. Один кадр «почти» — этого мало: захват
# ловит и промежуточные кадры анимации, и полупрозрачные наложения. Ложное
# срабатывание тут стоит дорого — оно пишет в статистику победу, которой не
# было, и портит винрейт навсегда.
CONFIRM_SIGHTINGS = 2
# ...но НЕ подряд. Требование «два опроса подряд» и сожгло живую ночь: на
# пограничном счёте кадры мерцают, и любой единичный промах обнулял счётчик.
# Считаем совпадения в пределах окна — промах внутри него ничего не рушит.
CONFIRM_WINDOW = 4.0
# И на том же месте экрана: настоящий баннер стоит, а случайное пятно похожей
# яркости посреди боя ползёт вместе с картинкой. Допуск в пикселях кадра.
CONFIRM_SAME_SPOT = 16

# СКОЛЬКО ПУСТЫХ ОПРОСОВ = «БАННЕР УШЁЛ». Именно этим один матч отделяется от
# следующего. Один пустой кадр таким признаком быть не может по той же
# причине, по которой одного совпадения мало для победы: экран моргает.
REARM_MISSES = 3

# Сторож тишины: столько кругов подряд без единого распознанного исхода — и
# что-то не так (игра обновилась, кнопка съехала, запись больше не подходит).
# Не останавливаем — просто говорим вслух, потому что длинная запись с одним
# матчем на три круга это законный случай.
SILENCE_CYCLES = 3
# Но не раньше этого времени: у короткой записи три круга — это минута, и
# ругаться через минуту после старта было бы просто шумом.
SILENCE_MIN_SECONDS = 15 * 60
# И НЕ ОДИН РАЗ. Прежний сторож ругался ровно однажды за затишье, а сбрасывался
# только распознанным исходом — то есть в единственном случае, ради которого он
# и написан (сломалось и молчит всю ночь), человек получал одно сообщение на
# пятнадцатой минуте и больше ничего десять часов. Дальше повторяем, удваивая
# паузу: настойчиво в начале, когда это ещё можно застать, и редко потом, чтобы
# к утру не набить канал сотней одинаковых строк.
SILENCE_REPEAT_MAX = 60 * 60


class ResultWatcher:
    """Фоновый наблюдатель за экраном во время повтора.

    on_result(result, duration_str, screenshot_path) вызывается из ЭТОГО
    потока: он ничего не блокирует у повтора, но и держать его долго не стоит —
    отправка уведомления внутри обработчика это уже делает сама, на своём
    потоке.
    """

    def __init__(self, get_hwnd, on_result, log=None, while_running=None, on_silence=None,
                 on_unknown=None):
        self._get_hwnd = get_hwnd
        self._on_result = on_result
        self._log = log or (lambda m: None)
        # Матч кончился, а какой именно — не разобрали. Отдаём наружу тем же
        # порядком, что и распознанный исход: сама по себе эта цифра и есть
        # диагноз («матчи идут, распознавание сломано»), и держать её только
        # внутри наблюдателя значит прятать ответ на главный вопрос.
        self._on_unknown = on_unknown or (lambda: None)
        # Сторож тишины зовёт это, когда исходов долго нет. Отдельным
        # обработчиком, а не отправкой прямо отсюда: наблюдатель не должен
        # знать ни про настройки вебхука, ни про то, что там за адрес.
        self._on_silence = on_silence or (lambda shot=None, detail="": None)
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
        # Сколько раз матч кончился, а какой именно — не разобрали (панель
        # результата на экране, баннер не читается). В статистику такие не
        # идут, но молчать о них тоже нельзя: сотня таких за ночь и есть
        # диагноз, см. RESULT_UNKNOWN.
        self.unknown = 0

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _silence_limit(self) -> float:
        """Сколько тишины считать подозрительной.

        Порог считается от ДЛИНЫ КРУГА, а не фиксированным числом минут: у
        записи на три минуты и у записи на сорок «давно ничего не было» —
        это очень разное время. Нижняя граница нужна, чтобы короткая запись не
        начала ругаться через минуту после старта."""
        return max(SILENCE_MIN_SECONDS, self._cycle_seconds * SILENCE_CYCLES)

    def _silent_too_long(self, since: float) -> bool:
        """Пора ли ругаться на затянувшуюся тишину (первый раз за затишье)."""
        return (time.perf_counter() - since) >= self._silence_limit()

    def start(self, name: str = "", cycle_seconds: float = 0.0) -> bool:
        # ПРЕДЫДУЩИЙ НАБЛЮДАТЕЛЬ МОГ ЕЩЁ НЕ УСПЕТЬ УЙТИ.
        #
        # Он уходит сам, увидев через while_running, что плеер встал, — но
        # проверяет это раз в такт (POLL_INTERVAL, полторы секунды). Остановил
        # повтор и тут же запустил снова — старый поток ещё жив, и прежний
        # `if self.running: return False` молча отказывал в запуске. Снаружи
        # это выглядело как «история по записям не работает»: повтор крутится,
        # а победы и поражения в неё не попадают вовсе.
        #
        # Останавливаем явно. Это быстро: _stop.wait просыпается мгновенно.
        if self.running:
            self.stop()
        self.name = name
        try:
            self._cycle_seconds = max(0.0, float(cycle_seconds or 0.0))
        except (TypeError, ValueError):
            self._cycle_seconds = 0.0
        self.matches = 0
        self.unknown = 0
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

    def _score(self, shot, image_name: str, missing: set):
        """Насколько похож эталон на этот кадр: (счёт, (x, y)).

        `missing` копит имена эталонов, которых нет на диске: ругаться о них
        надо один раз, а не каждые полсекунды все полчаса забега."""
        try:
            hit = vision.best_match_in_gray_multiscale(shot, image_name, stop_at=STRONG_THRESHOLD)
        except vision.TemplateNotFound:
            if image_name not in missing:
                missing.add(image_name)
                self._log(f'[Replay] Missing template "{image_name}" -- match outcome '
                          f'распознаваться не будет. Добавь свою вырезку: '
                          f'Настройки → Общие → Менеджер картинок.')
            return 0.0, None
        except Exception:
            return 0.0, None              # разовый сбой поиска — не повод падать
        if hit is None:
            return 0.0, None
        return float(hit.get("score") or 0.0), (hit.get("x", 0), hit.get("y", 0))

    def _find(self, hwnd: int, missing: set, best_seen: dict = None):
        """Что на экране прямо сейчас: (исход, уверенно ли, место, счёт).

        Исход — "win"/"loss"/RESULT_UNKNOWN/None. ОДИН кадр на весь опрос:
        прежде каждый поиск делал свой захват (см. find_image), то есть три
        снимка за такт, и три снимка РАЗНЫХ моментов — баннер мог быть на
        первом и уйти ко второму.

        ВТОРАЯ ПРИМЕТА КОНЦА МАТЧА. Баннеры «Victory»/«Defeat» нарезаны на
        настройках автора движка и совпадают не у всех: другое качество
        графики, другое разрешение — и порог не дотягивается. Но экран
        результата при этом на месте, и на нём есть кнопка «Repeat Stage»,
        которой в бою не бывает (там на её месте живой «Leave Stage» — это
        другое имя поиска). Нет баннера, но есть кнопка — матч всё равно
        кончился, просто исход неизвестен. Автомат отвечает на это
        RESULT_UNKNOWN (см. _match_ended_without_a_banner в core/runner.py), и
        разводить две разные логики для одного экрана нельзя — разойдутся.

        Кнопку ищем только когда баннера нет даже слабого: на экране
        результата она висит рядом с баннером, и платить за её перебор, когда
        исход уже прочитан, незачем."""
        try:
            shot = vision.capture_game_gray(hwnd)
        except Exception:
            return None, False, None, 0.0
        if shot is None or getattr(shot, "size", 0) == 0:
            return None, False, None, 0.0

        best_result, best_score, best_spot = None, 0.0, None
        for image_name, result in BANNERS:
            score, spot = self._score(shot, image_name, missing)
            if best_seen is not None:
                best_seen[image_name] = max(best_seen.get(image_name, 0.0), score)
            if score > best_score:
                best_result, best_score, best_spot = result, score, spot
        if best_score >= WEAK_THRESHOLD:
            return best_result, best_score >= STRONG_THRESHOLD, best_spot, best_score

        panel, _ = self._score(shot, MATCH_END_BUTTON_NAME, missing)
        if best_seen is not None:
            best_seen[MATCH_END_BUTTON_NAME] = max(
                best_seen.get(MATCH_END_BUTTON_NAME, 0.0), panel)
        if panel >= STRONG_THRESHOLD:
            return RESULT_UNKNOWN, True, None, panel
        return None, False, None, best_score

    def _loop(self):
        missing = set()
        armed = True                      # готов засчитать следующий исход
        since = time.perf_counter()       # начало текущего матча
        # Отсчёт длины матча начат исходом или просто стартом повтора? От
        # этого зависит, можно ли называть посчитанное «длиной матча»: первый
        # же исход после слепого часа мерил бы этот слепой час.
        since_is_outcome = False
        pending = None                    # слабый исход, ждущий подтверждения
        pending_spot = None               # и место, на котором его видели
        pending_since = 0.0               # когда увидели впервые
        pending_hits = 0                  # сколько раз увидели
        misses = 0                        # пустых опросов подряд
        # Лучшие счета эталонов за нынешнее затишье — сторож показывает их
        # вместо гаданий о причине.
        best_seen = {}
        last_signal = time.perf_counter()  # последний РАСПОЗНАННЫЙ исход
        silence_gap = self._silence_limit()
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

            found, strong, spot, _score = self._find(hwnd, missing, best_seen)
            now = time.perf_counter()
            counted = None

            if found is None:
                misses += 1
                # Баннер ушёл — снова готовы ловить. Именно так и отделяется
                # один матч от следующего. Не с первого пустого кадра: экран
                # моргает ровно по тем же причинам, по которым одного
                # совпадения мало для победы.
                if misses >= REARM_MISSES:
                    armed = True
                    pending, pending_hits, pending_spot = None, 0, None
            else:
                misses = 0
                if not armed:
                    pass                  # матч уже засчитан, ждём, когда экран уйдёт
                elif strong:
                    # Уверенное совпадение — засчитываем сразу, как автомат
                    # (_wait_for_result в core/runner.py). Ждать подтверждения
                    # тому, что и так выше порога, нечего: именно это ожидание
                    # и съело живую ночь.
                    counted = found
                elif pending != found or (now - pending_since) > CONFIRM_WINDOW or (
                        pending_spot and spot and
                        (abs(spot[0] - pending_spot[0]) > CONFIRM_SAME_SPOT or
                         abs(spot[1] - pending_spot[1]) > CONFIRM_SAME_SPOT)):
                    # Первое «почти». Само по себе оно ничего не значит: захват
                    # ловит и кадры анимации, и полупрозрачные наложения.
                    pending, pending_hits, pending_spot, pending_since = found, 1, spot, now
                else:
                    pending_hits += 1
                    if pending_hits >= CONFIRM_SIGHTINGS:
                        counted = found

            if counted is not None:
                armed = False
                pending, pending_hits, pending_spot = None, 0, None
                elapsed, blind = now - since, not since_is_outcome
                since, since_is_outcome = now, True
                if counted == RESULT_UNKNOWN:
                    # Матч кончился, а какой — не разобрали. В статистику не
                    # пишем (соврать про победу хуже, чем промолчать), но и
                    # тишиной это больше не притворяется: счётчик уходит в
                    # сообщение сторожа. Отдельного уведомления на каждый
                    # такой матч нет намеренно — за ночь их бывает сотня.
                    self.unknown += 1
                    self._log(f"[Replay] Match finished (repeat button detected), but outcome "
                              f"именно баннер — не распознал: {self.unknown}-й раз за "
                              f"прогон. В статистику не пишу. Пересними «victory» и "
                              f"«defeat»: Настройки → Общие → Менеджер картинок.")
                    try:
                        self._on_unknown()
                    except Exception as exc:
                        self._log(f"[Replay] Failed to record unrecognized outcome: {exc}")
                else:
                    last_signal = now     # исход есть — затишье кончилось
                    silence_gap = self._silence_limit()
                    best_seen = {}
                    self.matches += 1
                    duration = format_duration(elapsed)
                    if blind and elapsed >= self._silence_limit():
                        # Честная подпись: это не длина матча, а время с начала
                        # повтора — прошлый исход распознан не был. Ставится
                        # только на подозрительно долгом промежутке: у первого
                        # матча обычного прогона «от старта» и есть его длина.
                        duration += " (с начала повтора)"
                    shot = self._capture(hwnd)
                    self._log(f'[Replay] {"Victory" if counted == "win" else "Defeat"} '
                              f'— матч {self.matches} за прогон, {duration}.')
                    try:
                        self._on_result(counted, duration, shot)
                    except Exception as exc:
                        self._log(f"[Replay] Failed to record match outcome: {exc}")
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
            #
            # И повторяем, удваивая паузу. Прежний сторож говорил ровно один раз
            # за затишье — то есть в единственном случае, ради которого написан,
            # выдавал одно сообщение на пятнадцатой минуте и молчал следующие
            # десять часов.
            if (time.perf_counter() - last_signal) >= silence_gap:
                quiet = format_duration(time.perf_counter() - last_signal)
                silence_gap = min(silence_gap * 2, SILENCE_REPEAT_MAX)
                last_signal = time.perf_counter()
                detail = self._silence_detail(best_seen)
                # Счета копим ЗА ОКНО между сообщениями: иначе второе и третье
                # показывали бы лучший кадр давно прошедшего часа.
                best_seen = {}
                self._log(f"[Replay] No recognized outcome during {quiet}. {detail}")
                # СО СНИМКОМ ЭКРАНА. Без него о причине можно только гадать, а
                # с кадром видно, что было на экране, и из него же режется
                # недостающая вырезка баннера.
                self._on_silence(self._capture(hwnd), detail)

            self._stop.wait(POLL_INTERVAL)

    def _silence_detail(self, best_seen: dict) -> str:
        """Чем именно кончилось это затишье — фактом, а не догадкой.

        Прежний текст перечислял версии («запись закрывает экран быстрее»,
        «эталоны перестали совпадать») и в живом случае промахнулся мимо обеих:
        эталоны совпадали, просто на волосок ниже порога. Счёт это показывает
        сразу — 0.89 при пороге 0.90 читается однозначно."""
        parts = []
        for image_name in [name for name, _ in BANNERS] + [MATCH_END_BUTTON_NAME]:
            if image_name in best_seen:
                parts.append(f"{image_name} {best_seen[image_name]:.2f}")
        if self.unknown:
            parts.append(f"матчей без распознанного исхода: {self.unknown}")
        if not parts:
            return ("Экран ни разу не удалось прочитать — похоже, захват окна "
                    "возвращает пустой кадр.")
        return (f"Лучшее совпадение за это время: {' · '.join(parts)} "
                f"(порог {STRONG_THRESHOLD:.2f}).")

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
def send_notice(webhook_cfg: dict, title: str, text: str, warning: bool = True,
                log=None, screenshot_path: str = None) -> None:
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
    content = f"<@{mention_id}>" if mention_id else ""
    silent = bool(webhook_cfg.get("silent"))
    try:
        # Со снимком, когда он есть: «эталоны не совпадают» без кадра — это
        # догадка, которую нечем проверить, а с кадром видно, что было на
        # экране, и из него же режется недостающая вырезка.
        if screenshot_path and os.path.isfile(screenshot_path):
            res = webhook_module.send_file(url, embed, screenshot_path,
                                           content=content, silent=silent)
        else:
            res = webhook_module.send(url, embed, content=content, silent=silent)
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
    tuc = stats.get("time_until_challenge", "-")
    runs_per_hour = stats.get("runs_per_hour", "-")

    # Поля собирает core/stats_report.py — там же, где их собирает автомат.
    # Своё здесь только то, чем повтор от автомата отличается: вместо карты,
    # этапа и сложности — имя записи и номер круга.
    fields = stats_report.report_fields("⚔️ Match", [
        ("Result", "Victory \U0001F3C6" if is_win else "Defeat \U0001F480"),
        ("Duration", duration or "-"),
        ("Запись", recording or "-"),
        ("Круг", loop_num or "-"),
    ], stats)

    result_word = "Victory" if is_win else "Defeat"
    description = f"{result_word} по записи **{recording}** — матч сессии **#{sw + sl}**."
    bar = stats_report.session_bar(sw, sl)
    if bar:
        description += f"\n{bar} за сессию"

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
