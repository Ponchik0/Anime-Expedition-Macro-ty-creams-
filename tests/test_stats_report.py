"""Сводка по журналу забегов: что она считает и чего не считает.

Цифры отсюда уходят в Discord и живут там вечно — их никто не перепроверит.
Поэтому тут проверяется не «функция вернула словарь», а ровно те случаи, на
которых сводка могла бы соврать: слепой промежуток вместо длины матча, серия
через границу, «сегодня» на стыке суток, единственный источник забегов.
"""
import time
from datetime import datetime, timedelta

import pytest

from core import stats_report


def _row(result="win", duration="5m 0s", at=None, source="auto"):
    return {"result": result, "map": "-", "duration": duration,
            "at": time.time() if at is None else at, "source": source}


# ── Длительность: строка обратно в секунды ────────────────────────────────

@pytest.mark.parametrize("text,seconds", [
    ("47s", 47),
    ("3m 12s", 192),
    ("1h 4m 9s", 3849),
    ("1m", 60),
])
def test_a_duration_reads_back_as_seconds(text, seconds):
    assert stats_report.parse_duration(text) == seconds


def test_a_blind_stretch_is_not_a_match_length():
    """«1h 44m 23s (с начала повтора)» — это НЕ длина матча, а время с начала
    повтора: предыдущий исход распознан не был. Один такой слепой час завысил
    бы средний матч на порядок."""
    assert stats_report.parse_duration("1h 44m 23s (с начала повтора)") is None


@pytest.mark.parametrize("text", ["", None, "-", "невесть что"])
def test_nonsense_gives_nothing_rather_than_zero(text):
    """Ноль и «данных нет» — разные вещи: ноль попал бы в среднее и утянул его."""
    assert stats_report.parse_duration(text) is None


# ── Серии ─────────────────────────────────────────────────────────────────

def test_the_current_streak_counts_from_the_fresh_end():
    """Журнал хранится новыми записями вперёд — серия считается оттуда же."""
    history = [_row("win"), _row("win"), _row("win"), _row("loss"), _row("win")]

    derived = stats_report.derive(history)

    assert derived["streak_kind"] == "win"
    assert derived["streak_len"] == 3


def test_a_loss_streak_is_reported_as_such():
    """Серия поражений — это ровно тот случай, ради которого на неё и смотрят."""
    derived = stats_report.derive([_row("loss"), _row("loss"), _row("win")])

    assert derived["streak_kind"] == "loss"
    assert derived["streak_len"] == 2


def test_the_best_streak_is_the_longest_win_run_in_the_journal():
    history = [_row("win"), _row("loss")] + [_row("win")] * 5 + [_row("loss")]

    assert stats_report.derive(history)["best_streak"] == 5


# ── «Сегодня» ─────────────────────────────────────────────────────────────

def test_today_is_the_local_calendar_day_not_the_last_24_hours():
    """Человек спрашивает «сколько сегодня наиграл», имея в виду свой день.
    Сдвижное суточное окно отвечало бы на другой вопрос."""
    now = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    yesterday_evening = (now - timedelta(hours=20)).timestamp()  # вчера, но меньше суток назад

    derived = stats_report.derive(
        [_row("win", at=now.timestamp()), _row("win", at=yesterday_evening)],
        now=now.timestamp())

    assert (derived["today_wins"], derived["today_losses"]) == (1, 0)


# ── Длина матча ───────────────────────────────────────────────────────────

def test_the_best_match_is_the_fastest_win():
    """Быстрое поражение — это слив на первой волне, а не рекорд."""
    history = [_row("loss", "1m 0s"), _row("win", "4m 0s"), _row("win", "9m 0s")]

    assert stats_report.derive(history)["best_seconds"] == 240


def test_the_average_ignores_the_blind_stretches():
    """Иначе один слепой час перевесил бы десяток честных матчей."""
    history = [_row("win", "4m 0s"), _row("win", "6m 0s"),
               _row("win", "1h 44m 23s (с начала повтора)")]

    assert stats_report.derive(history)["avg_seconds"] == 300


def test_no_readable_durations_gives_no_average_rather_than_zero():
    history = [_row("win", "-"), _row("loss", "")]

    derived = stats_report.derive(history)
    assert derived["avg_seconds"] is None and derived["best_seconds"] is None


# ── Откуда забеги ─────────────────────────────────────────────────────────

def test_runs_are_split_by_who_played_them():
    history = [_row("win", source="replay"), _row("loss", source="replay"),
               _row("win", source="auto")]

    by_source = stats_report.derive(history)["by_source"]

    assert by_source["replay"] == {"wins": 1, "losses": 1}
    assert by_source["auto"] == {"wins": 1, "losses": 0}


def test_a_journal_row_without_a_source_reads_as_the_automat():
    """Записи, сделанные до появления поля: режима повтора тогда не было."""
    history = [{"result": "win", "map": "-", "duration": "1m", "at": time.time()}]

    assert stats_report.derive(history)["by_source"] == {"auto": {"wins": 1, "losses": 0}}


# ── Пустой журнал ─────────────────────────────────────────────────────────

def test_an_empty_journal_derives_nothing_at_all():
    """Пустой словарь, а не словарь нулей: по нему поля понимают, что
    показывать нечего, и не рисуют «Серия: 0» там, где сказать нечего."""
    assert stats_report.derive([]) == {}
    assert stats_report.derive(None) == {}


# ── Поля уведомления ──────────────────────────────────────────────────────

def _stats(history=None, **over):
    history = [_row("win"), _row("loss"), _row("win")] if history is None else history
    stats = {
        "session_wins": 2, "session_losses": 1,
        "all_time_wins": 41, "all_time_losses": 9,
        "session_start": time.time() - 3600, "runs_per_hour": "4.8",
        "time_until_challenge": "Disabled", "version": "1.0.1",
        "all_time_seconds": 60150.0,
        "derived": stats_report.derive(history),
    }
    stats.update(over)
    return stats


def _names(fields):
    return [f["name"] for f in fields]


def _field(fields, needle):
    for f in fields:
        if needle in f["name"]:
            return f
    return None


def test_the_card_still_carries_the_fields_it_always_had():
    fields = stats_report.report_fields("⚔️ Match", [("Result", "Victory")], _stats())

    names = _names(fields)
    assert any("Match" in n for n in names)
    assert any("Session" in n for n in names)
    assert any("All Time" in n for n in names)


def test_the_card_now_carries_the_streak_and_the_match_lengths():
    """Ровно то, о чём просили: победа показывает не только себя."""
    fields = stats_report.report_fields("⚔️ Match", [("Result", "Victory")], _stats())

    assert _field(fields, "Серия") is not None
    assert _field(fields, "Матчи") is not None


def test_all_time_shows_the_total_and_the_uptime():
    fields = stats_report.report_fields("⚔️ Match", [], _stats())

    value = _field(fields, "All Time")["value"]
    assert "50" in value          # 41 победа + 9 поражений
    assert "16h" in value         # 60150 секунд аптайма


def test_the_breakdown_by_mode_appears_only_when_there_is_something_to_split():
    """С одним источником это поле слово в слово повторяло бы соседнее."""
    one_source = _stats([_row("win"), _row("loss")])
    two_sources = _stats([_row("win"), _row("loss", source="replay")])

    assert _field(stats_report.report_fields("⚔️ Match", [], one_source), "Откуда") is None
    assert _field(stats_report.report_fields("⚔️ Match", [], two_sources), "Откуда") is not None


def test_an_empty_journal_adds_no_empty_fields():
    """Первый забег ещё ничего не знает о сериях — и молчит об этом."""
    fields = stats_report.report_fields("⚔️ Match", [("Result", "Victory")], _stats([]))

    assert _field(fields, "Серия") is None
    assert _field(fields, "Матчи") is None


def test_missing_stats_do_not_break_the_card():
    """Снимок статистики может не собраться — уведомление обязано уйти."""
    fields = stats_report.report_fields("⚔️ Match", [("Result", "Victory")], {})

    assert _names(fields)  # хоть что-то, а не исключение


# ── Периодическая сводка ──────────────────────────────────────────────────

def test_the_status_report_says_how_much_was_played_in_the_window():
    embed = stats_report.status_embed(_stats(), window_seconds=6 * 3600,
                                       window_wins=21, window_losses=6)

    assert "6h" in embed["title"]
    assert "21W · 6L" in embed["description"]


def test_an_empty_window_is_the_news_not_a_blank_line():
    """Именно так выглядит ночь, в которую что-то сломалось: макрос бодро
    крутится, а исходов нет вовсе."""
    embed = stats_report.status_embed(_stats(), window_seconds=6 * 3600,
                                       window_wins=0, window_losses=0)

    assert "ни одного матча" in embed["description"]
    assert "Менеджер картинок" in embed["description"]


def test_the_status_report_carries_what_the_macro_is_doing_now():
    embed = stats_report.status_embed(
        _stats(), window_seconds=600, window_wins=1, window_losses=0,
        now_rows=[("Состояние", "идёт прогон"), ("Режим", "Повтор")])

    assert _field(embed["fields"], "Сейчас") is not None
    assert "Повтор" in _field(embed["fields"], "Сейчас")["value"]


def test_the_final_summary_is_titled_and_coloured_differently():
    """Итог прогона и плановая сводка не должны сливаться в ленте."""
    planned = stats_report.status_embed(_stats(), window_seconds=600,
                                         window_wins=1, window_losses=0)
    final = stats_report.status_embed(_stats(), window_seconds=600, window_wins=1,
                                       window_losses=0, final=True)

    assert planned["title"] != final["title"]
    assert planned["color"] != final["color"]


@pytest.mark.parametrize("n,word", [(1, "матч"), (2, "матча"), (5, "матчей"),
                                     (11, "матчей"), (21, "матч"), (24, "матча")])
def test_the_match_count_is_spelled_properly(n, word):
    """Сводку читают каждые несколько часов — «записано 27 матч» мозолит глаза
    быстрее, чем кажется."""
    assert stats_report._matches_word(n) == word


# ── Окно отчёта ───────────────────────────────────────────────────────────

def test_the_window_only_holds_what_happened_after_it_started():
    now = time.time()
    history = [_row(at=now), _row(at=now - 100), _row(at=now - 100_000)]

    rows = stats_report.slice_since(history, now - 3600)

    assert len(rows) == 2


def test_counting_a_window_ignores_rows_without_a_verdict():
    rows = [_row("win"), _row("loss"), {"result": "unknown", "at": time.time()}]

    assert stats_report.count(rows) == (1, 1)
