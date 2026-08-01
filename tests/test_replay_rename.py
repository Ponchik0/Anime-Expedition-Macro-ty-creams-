"""Переименование сохранённых записей.

Само переименование — это os.rename, интересного в нём ничего. Интересны
отказы: имя может быть пустым, занятым или содержать символы, запрещённые в
имени файла. Каждый такой случай обязан вернуться СЛОВОМ, а не общим «не
вышло»: интерфейс по нему пишет человеку, что именно не так.

Плюс подводный камень: настройка «какую запись играть» указывает на запись по
имени, и без её обновления переименование тихо ломало бы режим повтора.
"""
import main
import pytest

from core import replay


class _Api(main.Api):
    def __init__(self):
        self.logs = []

    def push_log(self, message):
        self.logs.append(message)


@pytest.fixture
def store(monkeypatch, tmp_path):
    monkeypatch.setattr(replay, "RECORDINGS_DIR", str(tmp_path))
    state = {}
    monkeypatch.setattr(main.cfg, "load", lambda: state)
    monkeypatch.setattr(main.cfg, "update", lambda patch: state.update(patch))
    return state


def _make(name, actions=1):
    events = [{"t": 100.0 * i, "kind": "down", "code": "W", "x": 1, "y": 2}
              for i in range(1, actions + 1)]
    return replay.save(name, events, 1152, 756)


# ── Удачные случаи ────────────────────────────────────────────────────────

def test_renaming_moves_the_recording(store):
    _make("Забег")
    api = _Api()
    res = api.replay_rename("Забег", "Босс")
    assert res["ok"] and res["name"] == "Босс"
    assert replay.exists("Босс") and not replay.exists("Забег")
    assert [r["name"] for r in replay.listing()] == ["Босс"]


def test_the_selected_recording_follows_its_new_name(store):
    _make("Забег")
    store["replay_file"] = "Забег"
    api = _Api()
    assert api.replay_rename("Забег", "Босс")["ok"]
    assert store["replay_file"] == "Босс"


def test_another_recording_selection_is_left_alone(store):
    _make("Забег")
    _make("Другая")
    store["replay_file"] = "Другая"
    api = _Api()
    assert api.replay_rename("Забег", "Босс")["ok"]
    assert store["replay_file"] == "Другая"


def test_renaming_to_the_same_name_is_not_an_error(store):
    _make("Забег")
    api = _Api()
    res = api.replay_rename("Забег", "  Забег  ")
    assert res["ok"] and res.get("unchanged")
    assert replay.exists("Забег")


def test_changing_only_the_letter_case_is_allowed(store):
    """На Windows регистр в именах файлов не различается, и проверка
    занятости имени говорила бы «уже есть» про сам переименовываемый файл."""
    _make("забег")
    api = _Api()
    res = api.replay_rename("забег", "Забег")
    assert res["ok"], res
    assert [r["name"] for r in replay.listing()] == ["Забег"]


def test_forbidden_characters_are_stripped_and_reported(store):
    """safe_name вычищает то, что нельзя в имени файла. Сохранённое имя тогда
    отличается от набранного, и молчать об этом нельзя."""
    _make("Забег")
    api = _Api()
    res = api.replay_rename("Забег", 'Босс: часть 2 <финал>')
    assert res["ok"] and res["sanitized"] is True
    assert res["name"] == "Босс_ часть 2 _финал_"
    assert replay.exists(res["name"])


# ── Отказы ────────────────────────────────────────────────────────────────

def test_an_empty_name_is_refused(store):
    _make("Забег")
    api = _Api()
    res = api.replay_rename("Забег", "   ")
    assert res == {"ok": False, "reason": "empty"}
    assert replay.exists("Забег"), "запись не должна пострадать от отказа"


def test_a_taken_name_is_refused_and_neither_file_is_touched(store):
    _make("Забег", actions=1)
    _make("Босс", actions=3)
    api = _Api()
    res = api.replay_rename("Забег", "Босс")
    assert res == {"ok": False, "reason": "exists"}
    # Главное: чужую запись не затёрли.
    assert replay.stats(replay.load("Босс"))["actions"] == 3
    assert replay.exists("Забег")


def test_renaming_something_that_is_gone_says_so(store):
    api = _Api()
    res = api.replay_rename("Призрак", "Босс")
    assert res == {"ok": False, "reason": "missing"}


# ── Вспомогательное ───────────────────────────────────────────────────────

def test_exists_does_not_read_the_whole_file(store, monkeypatch):
    """Проверка занятости имени должна быть дешёвой: в записи бывают сотни
    тысяч событий, и читать их ради ответа «да/нет» незачем."""
    _make("Забег", actions=5)

    def _boom(_name):
        raise AssertionError("exists() не должен читать файл")

    monkeypatch.setattr(replay, "load", _boom)
    assert replay.exists("Забег") is True
    assert replay.exists("Нет такой") is False
