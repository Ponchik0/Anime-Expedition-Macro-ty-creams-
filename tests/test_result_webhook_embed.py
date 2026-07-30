"""Уведомление о результате матча: что в нём есть и чего в нём больше нет.

Блок «Links» (Discord • YouTube • GitHub) висел на КАЖДОМ результате, то есть по
многу раз в час, и занимал целое поле во весь размах эмбеда — вытесняя то, за
чем на уведомление вообще смотрят. Он убран, а освободившееся место отдано
тому, что реально решает исход забега: непоставленным юнитам.
"""
import pytest

from core import runner as runner_module
from core import webhook as webhook_module
from core.runner import MacroRunner
from core.runner_constants import RESULT_ROUND_ENDED


def _runner(monkeypatch, sent):
    runner = MacroRunner.__new__(MacroRunner)
    runner.logs = []
    runner._log = runner.logs.append
    runner._get_run_stats = lambda: {
        "session_wins": 3, "session_losses": 1,
        "all_time_wins": 10, "all_time_losses": 4,
        "session_start": None, "runs_per_hour": "6", "time_until_challenge": "1h",
        "version": "1.0.1", "results": [],
    }

    def send_rich(url, embeds=None, file_attachments=None, content="", silent=False):
        sent.append({"embeds": embeds, "content": content})
        return {"ok": True, "reason": ""}

    # Подменяется САМА ФУНКЦИЯ в настоящем модуле, а не модуль в sys.modules:
    # `from . import webhook` внутри _send_result_webhook берёт уже
    # импортированный атрибут пакета, поэтому подмена в sys.modules работала бы
    # только пока никто другой не импортировал core.webhook раньше -- то есть
    # в одиночном прогоне да, в общем нет.
    monkeypatch.setattr(webhook_module, "send_rich", send_rich)
    return runner


def _send(monkeypatch, placement=None, result="loss", mention=None):
    sent = []
    runner = _runner(monkeypatch, sent)
    # status_card рисует картинку и здесь не нужен -- проверяем текст эмбеда.
    monkeypatch.setattr(runner_module, "cv2", None, raising=False)
    webhook = {"url": "https://discord.com/api/webhooks/1/t", "enabled": True}
    if mention:
        webhook["mention_id"] = mention
    task = {"mode": "expedition", "map": "School Grounds", "stage": "-", "macro": "exp"}
    runner._send_result_webhook(webhook, result, task, "4m 36s", None, placement)
    assert sent, "уведомление не ушло вообще"
    return sent[0]


def _field_names(message):
    return [f["name"] for f in message["embeds"][0]["fields"]]


def _field(message, needle):
    for f in message["embeds"][0]["fields"]:
        if needle in f["name"]:
            return f
    return None


# ── Блока ссылок больше нет ───────────────────────────────────────────────

def test_the_links_field_is_gone(monkeypatch):
    message = _send(monkeypatch)

    assert not any("Links" in n for n in _field_names(message)), _field_names(message)
    body = str(message["embeds"][0])
    for url in ("discord.gg", "youtube.com", "github.com"):
        assert url not in body, f"{url} снова уехал в уведомление"


def test_the_useful_fields_are_still_there(monkeypatch):
    names = _field_names(_send(monkeypatch))

    assert any("Match" in n for n in names)
    assert any("Session" in n for n in names)
    assert any("All Time" in n for n in names)


# ── Расстановка: поле появляется только когда с ней что-то не так ─────────

def test_a_clean_placement_adds_no_field(monkeypatch):
    """Уведомление не должно обрастать строками, которые всегда одинаковые."""
    clean = {"ok": 6, "failed": 0, "failed_names": [], "skipped": 0, "skipped_names": []}

    assert _field(_send(monkeypatch, clean), "Расстановка") is None


def test_a_missing_tally_adds_no_field(monkeypatch):
    """Итога может не быть вовсе (например, забег прервали) -- это не повод
    падать или печатать пустое поле."""
    assert _field(_send(monkeypatch, None), "Расстановка") is None


def test_units_that_did_not_land_are_reported(monkeypatch):
    """Ровно тот случай из журнала: пять юнитов встали, шестой нет."""
    tally = {"ok": 5, "failed": 1, "failed_names": ["dps"], "skipped": 0, "skipped_names": []}

    field = _field(_send(monkeypatch, tally), "Расстановка")

    assert field is not None, "про непоставленного юнита в уведомлении ни слова"
    assert "dps" in field["value"]
    assert "Не встало" in field["value"]
    assert "Встало" in field["value"]


def test_skipped_blocks_are_reported_too(monkeypatch):
    """Шесть блоков без хоткея -- то же пустое поле, что и шесть
    непоставленных юнитов, и об этом надо говорить так же громко."""
    tally = {"ok": 0, "failed": 0, "failed_names": [],
             "skipped": 6, "skipped_names": ["dps", "farm"]}

    field = _field(_send(monkeypatch, tally), "Расстановка")

    assert field is not None
    assert "Пропущено" in field["value"]
    assert "dps" in field["value"] and "farm" in field["value"]


def test_names_may_be_absent_without_breaking_the_send(monkeypatch):
    """Числа есть, списка имён нет -- уведомление обязано уйти, а не упасть на
    отправке результата."""
    tally = {"ok": 1, "failed": 2}

    field = _field(_send(monkeypatch, tally), "Расстановка")

    assert field is not None
    assert "2" in field["value"]


# ── Остальное содержимое ──────────────────────────────────────────────────

def test_the_session_bar_is_drawn(monkeypatch):
    """Полоска винрейта вместо ссылок: как идёт сессия, видно с одного взгляда."""
    description = _send(monkeypatch)["embeds"][0]["description"]

    assert "▰" in description or "▱" in description


def test_the_author_line_says_the_mode_and_the_macro(monkeypatch):
    """В очереди несколько задач, уведомления идут подряд -- надо понимать, о
    какой именно речь."""
    author = _send(monkeypatch)["embeds"][0]["author"]["name"]

    assert "Expedition" in author and "exp" in author


@pytest.mark.parametrize("result,word", [("win", "Victory"), ("loss", "Defeat")])
def test_the_title_matches_the_result(monkeypatch, result, word):
    assert word in _send(monkeypatch, result=result)["embeds"][0]["title"]


def test_the_mention_is_passed_as_content(monkeypatch):
    assert _send(monkeypatch, mention="42")["content"] == "<@42>"


def test_a_disabled_webhook_sends_nothing(monkeypatch):
    sent = []
    runner = _runner(monkeypatch, sent)

    runner._send_result_webhook({"url": "https://discord.com/api/webhooks/1/t", "enabled": False},
                                 "loss", {"mode": "raid"}, "1m", None, None)

    assert sent == []


# ── Raid: раунд кончился, а экрана результата не было ─────────────────────
# Карточку результата отправляет _handle_match_result, а при таком исходе он не
# вызывается вовсе -- поэтому после raid не приходило НИЧЕГО, хотя после
# expedition приходила полная карточка. Теперь карточка та же, только вердикт
# в ней честный.

def _round_ended(monkeypatch, placement=None):
    return _send(monkeypatch, placement, result=RESULT_ROUND_ENDED)


def test_a_finished_round_still_sends_the_card(monkeypatch):
    """Главное: уведомление вообще уходит."""
    message = _round_ended(monkeypatch)

    assert message["embeds"], "после raid снова не пришло ничего"


def test_a_finished_round_does_not_claim_a_verdict(monkeypatch):
    """Написать «Victory» или «Defeat» тут значило бы соврать."""
    embed = _round_ended(monkeypatch)["embeds"][0]

    assert "Victory" not in embed["title"] and "Defeat" not in embed["title"]
    assert "не распознан" in _field(_round_ended(monkeypatch), "Match")["value"]


def test_a_finished_round_says_how_to_fix_it(monkeypatch):
    """Без этой строки человек не поймёт, почему вердикта нет."""
    description = _round_ended(monkeypatch)["embeds"][0]["description"]

    assert "Менеджер картинок" in description


def test_a_finished_round_keeps_the_session_and_all_time_fields(monkeypatch):
    """Ровно то, о чём просили: «такая же инфа, как в expeditions»."""
    names = _field_names(_round_ended(monkeypatch))

    assert any("Session" in n for n in names)
    assert any("All Time" in n for n in names)


def test_a_finished_round_does_not_pretend_to_be_match_number_n(monkeypatch):
    """В счётчики раунд не попал, значит и «матч #N» писать нельзя."""
    assert "session match" not in _round_ended(monkeypatch)["embeds"][0]["description"]


def test_a_finished_round_still_reports_placement_trouble(monkeypatch):
    """Непоставленный юнит одинаково важен при любом исходе."""
    tally = {"ok": 5, "failed": 1, "failed_names": ["dps"], "skipped": 0, "skipped_names": []}

    field = _field(_round_ended(monkeypatch, tally), "Расстановка")

    assert field is not None and "dps" in field["value"]


def test_a_finished_round_is_kept_out_of_the_stats(monkeypatch):
    """record=False: записать наугад значит испортить и винрейт, и
    предохранитель серии поражений."""
    recorded = []
    runner = _runner(monkeypatch, [])
    runner._record_result = lambda *a: recorded.append(a)

    runner._finish_match_result_background(
        RESULT_ROUND_ENDED, "Spirit City", "5m", {"mode": "raid"}, None, None, None, record=False)

    assert recorded == []


@pytest.mark.parametrize("result", ["win", "loss"])
def test_a_known_outcome_is_still_recorded(monkeypatch, result):
    recorded = []
    runner = _runner(monkeypatch, [])
    runner._record_result = lambda *a: recorded.append(a)

    runner._finish_match_result_background(
        result, "Spirit City", "5m", {"mode": "raid"}, None, None, None)

    assert len(recorded) == 1
