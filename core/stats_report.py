"""Сводка по забегам: что показать в карточке матча и что послать по часам.

ЗАЧЕМ ОТДЕЛЬНЫЙ МОДУЛЬ. Карточку результата собирают ДВА места — автомат
(core/runner.py::_send_result_webhook) и повтор (core/replay_result.py::
send_webhook), — и до сих пор каждое перечисляло поля само. Пока полей было
три, это ещё держалось; стоит добавить четвёртое, и уведомления двух режимов
разъезжаются: одно и то же событие человек читает по-разному в зависимости от
того, каким способом отыгран забег. Поэтому поля собираются здесь, один раз, а
каждый режим отдаёт только своё — верхний блок («Match» у одного, «Сейчас» у
периодического статуса).

ЧТО СЧИТАЕТСЯ ЗДЕСЬ, А ЧТО ПРИХОДИТ ГОТОВЫМ. Готовыми приходят счётчики,
которые макрос ведёт сам: победы сессии, победы за всё время, время старта
сессии, аптайм (см. Api._run_stats_snapshot). Здесь из ЖУРНАЛА ЗАБЕГОВ
(run_history) достаётся то, чего в счётчиках нет и никогда не было: серии,
счёт за сегодня, длина матча, разбивка «автомат / повтор».

ГРАНИЦА ТОЧНОСТИ, и её надо знать заранее. Журнал кольцевой: в нём последние
RUN_HISTORY_LIMIT забегов (50 на сегодня, см. main.py). Значит «лучшая серия»,
«средний матч» и разбивка по режимам считаются ПО ЭТОМУ ХВОСТУ, а не за всё
время. Держать вечный журнал ради трёх цифр — плохая сделка: файл настроек
растёт, а вопрос «как идут дела» всё равно про недавнее. Всевременные же
победы/поражения — отдельные счётчики, они полные.
"""
from __future__ import annotations

import re
import time
from datetime import datetime

# Длину матча журнал хранит СТРОКОЙ («4m 36s») — в том же виде, в каком её
# читает человек в интерфейсе и в уведомлении. Чтобы посчитать среднее, её надо
# разобрать обратно. Разбираем по кусочкам «число + буква», а не одним
# выражением со всеми необязательными группами: такое выражение совпадает и с
# пустой строкой, то есть молча возвращает ноль там, где данных нет вовсе.
_PART_RE = re.compile(r"(\d+)\s*([hms])")
_UNIT_SECONDS = {"h": 3600, "m": 60, "s": 1}


def parse_duration(text) -> float:
    """Строка длительности обратно в секунды. None, если считать нечего."""
    if not text:
        return None
    text = str(text)
    # «1h 44m 23s (с начала повтора)» — это НЕ длина матча, а время с начала
    # повтора: предыдущий исход распознан не был (см. core/replay_result.py,
    # подпись «с начала повтора»). Такую строку в среднее пускать нельзя — один
    # слепой час завысит средний матч на порядок и сделает цифру бесполезной.
    # Скобка в этом поле бывает только там, поэтому её и хватает как приметы.
    if "(" in text:
        return None
    total, found = 0.0, False
    for value, unit in _PART_RE.findall(text):
        found = True
        total += int(value) * _UNIT_SECONDS[unit]
    return total if found else None


def format_duration(seconds: float) -> str:
    """«3m 12s» / «47s» / «1h 4m 9s» — длина ОДНОГО матча.

    Часы отдельной единицей: без них десятичасовой промежуток печатался как
    «620m 18s» — формально верно, читается как опечатка."""
    seconds = max(0, int(seconds or 0))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s" if m else f"{s}s"


def format_elapsed(seconds: float) -> str:
    """«11h 27m» / «27m 4s» / «45s» — промежуток ДЛИННЕЕ матча (сессия,
    аптайм, окно отчёта), поэтому ведёт часами и не тратит место на секунды,
    когда их всё равно никто не читает."""
    seconds = max(0, int(seconds or 0))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        # Ровные часы без «0m»: этой строкой подписан заголовок сводки, и
        # «Статус за 6h 0m» читается как недоделанный, а не как ровно шесть.
        return f"{h}h {m}m" if m else f"{h}h"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def rate(wins: int, losses: int) -> str:
    """«78%» или прочерк. Прочерк, а не «0%», когда матчей не было вовсе:
    ноль процентов читается как «всё проиграно»."""
    total = (wins or 0) + (losses or 0)
    return f"{round(wins * 100 / total)}%" if total else "-"


def session_bar(wins: int, losses: int) -> str:
    """Полоска винрейта на десять делений — как идёт дело, видно без чтения
    процентов. Пустая строка, когда матчей ещё нет: рисовать шкалу ни для чего
    незачем."""
    total = (wins or 0) + (losses or 0)
    if not total:
        return ""
    filled = int(round(wins * 10 / total))
    return f"`{'▰' * filled}{'▱' * (10 - filled)}` **{rate(wins, losses)}**"


def tree_rows(rows) -> str:
    """Строки-ветки одного поля эмбеда: «├ **Ключ:** `значение`», последняя на
    уголке «└». Вид общий для всех уведомлений макроса — иначе они читаются как
    сообщения от разных программ."""
    rows = [r for r in rows if r is not None]
    return "\n".join(
        f'{"└" if i == len(rows) - 1 else "├"} **{label}:** `{value}`'
        for i, (label, value) in enumerate(rows))


# ─────────────────────────────────────────── ЧТО ДОСТАЁТСЯ ИЗ ЖУРНАЛА ──────
def slice_since(history, since: float):
    """Забеги журнала, случившиеся ПОСЛЕ момента `since`.

    Отдельной функцией, потому что этим меряется окно периодического отчёта:
    «за шесть часов записано 27 матчей» — это ровно длина такого среза."""
    if not since:
        return [h for h in (history or []) if isinstance(h, dict)]
    return [h for h in (history or [])
            if isinstance(h, dict) and isinstance(h.get("at"), (int, float))
            and h["at"] >= since]


def count(rows) -> tuple:
    """(побед, поражений) в списке строк журнала."""
    wins = sum(1 for r in rows if isinstance(r, dict) and r.get("result") == "win")
    losses = sum(1 for r in rows if isinstance(r, dict) and r.get("result") == "loss")
    return wins, losses


def derive(history, now: float = None) -> dict:
    """Всё, что видно ТОЛЬКО из журнала: серии, «сегодня», длина матча, откуда
    забеги. Счётчики побед сюда не входят — они и так есть у макроса.

    Пустой журнал даёт пустой словарь, а не словарь нулей: по нему поля
    сводки понимают, что показывать нечего, и не рисуют «Серия: 0» первому же
    забегу, о котором ещё нечего сказать."""
    now = time.time() if now is None else now
    rows = [h for h in (history or []) if isinstance(h, dict)]
    if not rows:
        return {}

    # СЕРИЯ — со свежего конца: журнал хранится новыми записями вперёд
    # (см. _record_match_result в main.py).
    streak_kind, streak_len = "", 0
    for r in rows:
        res = r.get("result")
        if res not in ("win", "loss"):
            break
        if not streak_kind:
            streak_kind = res
        elif res != streak_kind:
            break
        streak_len += 1

    best_streak = run = 0
    for r in rows:
        if r.get("result") == "win":
            run += 1
            best_streak = max(best_streak, run)
        else:
            run = 0

    # «СЕГОДНЯ» — по МЕСТНОМУ календарю, а не по «минус 24 часа»: человек
    # спрашивает «сколько сегодня наиграл», имея в виду свой день, и сдвижное
    # суточное окно на этот вопрос отвечает мимо.
    today = datetime.fromtimestamp(now).date()
    today_wins = today_losses = 0
    for r in rows:
        at = r.get("at")
        if not isinstance(at, (int, float)) or datetime.fromtimestamp(at).date() != today:
            continue
        if r.get("result") == "win":
            today_wins += 1
        elif r.get("result") == "loss":
            today_losses += 1

    lengths = [d for d in (parse_duration(r.get("duration")) for r in rows) if d]
    win_lengths = [d for d in (parse_duration(r.get("duration"))
                                for r in rows if r.get("result") == "win") if d]

    # ОТКУДА ЗАБЕГ. `source` — «кто играл»: автомат по очереди задач или повтор
    # записи. Разбирая просадку винрейта, это первое, что нужно знать, а по
    # названию карты не отличишь. Строки, записанные до появления поля, — это
    # автомат: режима повтора тогда просто не было.
    by_source = {}
    for r in rows:
        slot = by_source.setdefault(r.get("source") or "auto", {"wins": 0, "losses": 0})
        if r.get("result") == "win":
            slot["wins"] += 1
        elif r.get("result") == "loss":
            slot["losses"] += 1

    return {
        "streak_kind": streak_kind,
        "streak_len": streak_len,
        "best_streak": best_streak,
        "today_wins": today_wins,
        "today_losses": today_losses,
        # Средняя длина — по всему хвосту журнала, лучшая — только по победам:
        # быстрое поражение это не достижение, а слив на первой волне, и
        # смешивать его с рекордом значит рекорд обесценить.
        "avg_seconds": (sum(lengths) / len(lengths)) if lengths else None,
        "best_seconds": min(win_lengths) if win_lengths else None,
        "by_source": by_source,
        "history_len": len(rows),
    }


# ───────────────────────────────────────────────── ПОЛЯ УВЕДОМЛЕНИЯ ────────
SOURCE_NAMES = {"auto": "Автомат", "replay": "Повтор"}


def _streak_line(derived: dict) -> str:
    kind, length = derived.get("streak_kind"), derived.get("streak_len") or 0
    if not kind or not length:
        return "-"
    word = "побед" if kind == "win" else "поражений"
    if length == 1:
        word = "победа" if kind == "win" else "поражение"
        return f"1 {word}"
    return f"{length} {word} подряд"


def extra_fields(stats: dict) -> list:
    """Блоки, которых в карточке раньше не было: серия, длина матча, откуда
    забеги, активные сервисы автоматизации."""
    stats = stats or {}
    derived = stats.get("derived") or {}
    fields = []

    if derived.get("history_len"):
        fields.append({
            "name": "Серия", "inline": True, "value": tree_rows([
                ("Сейчас", _streak_line(derived)),
                ("Лучшая", derived.get("best_streak") or 0),
                ("Сегодня", f'{derived.get("today_wins", 0)}W · {derived.get("today_losses", 0)}L'),
            ])})

    avg, best = derived.get("avg_seconds"), derived.get("best_seconds")
    if avg or best:
        fields.append({
            "name": "Матчи", "inline": True, "value": tree_rows([
                ("Средний", format_duration(avg) if avg else "-"),
                ("Лучший", format_duration(best) if best else "-"),
                ("В журнале", derived.get("history_len", 0)),
            ])})

    # РАЗБИВКА ПО РЕЖИМАМ — только когда режимов в журнале правда несколько.
    # С одним источником это поле повторяло бы соседнее слово в слово, а
    # уведомление не должно обрастать строками, которые всегда одинаковые (тем
    # же правилом живёт блок «Расстановка» в core/runner.py).
    by_source = derived.get("by_source") or {}
    if len(by_source) > 1:
        rows = [(SOURCE_NAMES.get(name, name), f'{slot["wins"]}W · {slot["losses"]}L')
                for name, slot in sorted(by_source.items())]
        fields.append({"name": "Откуда", "inline": True, "value": tree_rows(rows)})

    # АКТИВНЫЕ АВТОМАТИЗАЦИИ — отображаются отдельным компактным блоком,
    # если в настройках включены фоновые сервисы (магазин, баунти, крафт, топливо).
    automations = (stats or {}).get("automations") or {}
    if automations:
        rows = [(name, val) for name, val in automations.items() if val]
        if rows:
            fields.append({"name": "Automations", "inline": True, "value": tree_rows(rows)})

    return fields


def report_fields(head_name: str, head_rows, stats: dict) -> list:
    """Полный набор полей эмбеда: свой верхний блок + Session + All Time +
    сводка из журнала.

    `head_name`/`head_rows` — то, чем отличаются уведомления: у автомата и
    повтора это «Match» с исходом матча, у периодического статуса —
    «Сейчас» с тем, что макрос делает прямо в эту минуту. Всё остальное
    одинаково всюду по построению, а не по договорённости."""
    stats = stats or {}
    sw, sl = stats.get("session_wins", 0), stats.get("session_losses", 0)
    aw, al = stats.get("all_time_wins", 0), stats.get("all_time_losses", 0)
    session_time = (format_elapsed(time.time() - stats["session_start"])
                    if stats.get("session_start") else "-")
    uptime = stats.get("all_time_seconds")

    fields = []
    if head_rows:
        fields.append({"name": head_name, "value": tree_rows(head_rows), "inline": True})
    # «Не распознано» появляется, только когда такие матчи были. Строка,
    # которая всегда показывает ноль, читается как «всё в порядке» и потому
    # перестаёт читаться вовсе — а нужна она ровно в тот единственный раз,
    # когда цифра не ноль.
    unknown = stats.get("session_unknown") or 0
    fields.append({"name": "Session", "inline": True, "value": tree_rows([
        ("Elapsed", session_time),
        ("Record", f"{sw}W · {sl}L"),
        ("Rate", rate(sw, sl)),
        ("Не распознано", unknown) if unknown else None,
        ("Runs/h", stats.get("runs_per_hour", "-")),
        ("Challenge", stats.get("time_until_challenge", "-")),
    ])})
    # All Time стал inline: с шестью полями Discord раскладывает их в две
    # ровные строки по три, а полноширинное поле посреди разрывало бы обе.
    all_unknown = stats.get("all_time_unknown") or 0
    fields.append({"name": "All Time", "inline": True, "value": tree_rows([
        ("Record", f"{aw}W · {al}L"),
        ("Rate", rate(aw, al)),
        ("Матчей", aw + al),
        ("Не распознано", all_unknown) if all_unknown else None,
        ("Аптайм", format_elapsed(uptime) if uptime else "-"),
    ])})
    return fields + extra_fields(stats)


# ──────────────────────────────────────── ПЕРИОДИЧЕСКИЙ ОТЧЁТ «СТАТУС» ─────
# Цвета отличают отчёт от результата матча с одного взгляда: зелёный и красный
# заняты победой и поражением, и красить ими сводку значило бы подсовывать
# исход там, где его нет.
STATUS_COLOR = 0x5B8DEF          # плановая сводка
FINAL_COLOR = 0x8E7CC3           # итог остановленного прогона


def status_embed(stats: dict, *, window_seconds: float, window_wins: int,
                 window_losses: int, window_unknown: int = 0, now_rows=None,
                 final: bool = False, timestamp: str = "") -> dict:
    """Эмбед периодического статуса: сколько наиграно за окно и как дела в целом.

    Отдельно от карточки матча, потому что отвечает на другой вопрос. Карточка
    отвечает «чем кончился вот этот матч», статус — «что вообще происходит,
    пока я на это не смотрю». Второе и есть то, ради чего макрос оставляют на
    ночь, и до сих пор об этом можно было узнать только из результата
    очередного матча — то есть ровно тогда, когда всё и так хорошо. Когда
    плохо, матчей нет, и молчали обе стороны."""
    stats = stats or {}
    played = (window_wins or 0) + (window_losses or 0)
    span = format_elapsed(window_seconds)

    if final:
        title = "Прогон закончен · итог"
    else:
        title = f"Статус за {span}"

    unknown = max(0, window_unknown or 0)
    if played:
        description = (f"За **{span}** записано **{played}** "
                       f"{_matches_word(played)}: **{window_wins}W · {window_losses}L** "
                       f"({rate(window_wins, window_losses)}).")
        bar = session_bar(window_wins, window_losses)
        if bar:
            description += f"\n{bar} за этот промежуток"
    elif unknown:
        # Матчи ИДУТ, а в статистику не попадает ни один. Раньше эти два факта
        # жили порознь: сводка говорила «матчей нет», журнал приложения —
        # «баннер не распознан», и связать их было некому. Теперь это одна
        # фраза, и она сразу называет виновного.
        description = f"За **{span}** не записано ни одного матча."
    else:
        # НОЛЬ МАТЧЕЙ — это и есть главная новость такого отчёта, а не пустая
        # строчка в нём. Именно так выглядит ночь, в которую что-то сломалось:
        # макрос бодро крутится, а исходов нет вовсе.
        description = (f"За **{span}** не записано ни одного матча.\n"
                       f"Если прогон всё это время шёл — значит исход матча не "
                       f"распознаётся: Настройки → Общие → Менеджер картинок.")

    if unknown:
        # СКОЛЬКО МАТЧЕЙ ПРОШЛО МИМО СЧЁТЧИКОВ. Ровно эта цифра отличает
        # «сегодня не везёт» от «распознавание сломано»: матч кончился, экран
        # результата был, а баннер с эталоном не совпал.
        share = f" — это {round(unknown * 100 / (played + unknown))}% всех матчей" if played else ""
        description += (f"\nЕщё **{unknown}** "
                        f"{_matches_word(unknown)} кончилось без распознанного исхода"
                        f"{share}. В счёт они не пошли.\n"
                        f"Пересними баннеры «victory» и «defeat» своей вырезкой: "
                        f"Настройки → Общие → Менеджер картинок.")

    version = stats.get("version")
    return {
        "title": title,
        "color": FINAL_COLOR if final else STATUS_COLOR,
        "description": description,
        "fields": report_fields("Сейчас", now_rows or [], stats),
        "footer": {"text": "Anime Expeditions" + (f" · v{version}" if version else "")},
        "timestamp": timestamp,
    }


def _matches_word(n: int) -> str:
    """«матч» / «матча» / «матчей» — сводку читают каждые несколько часов, и
    «записано 27 матч» в ней мозолит глаза быстрее, чем кажется."""
    if 11 <= (n % 100) <= 14:
        return "матчей"
    last = n % 10
    if last == 1:
        return "матч"
    if 2 <= last <= 4:
        return "матча"
    return "матчей"
