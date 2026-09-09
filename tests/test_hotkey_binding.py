"""Назначение горячих клавиш: то, из-за чего оно выглядело сломанным.

Жалоба была «нажал — ничего не изменилось». Причин у этого несколько, и все
они тихие: клавиша в момент назначения ПОПУТНО делала то, на что была
назначена раньше (F1 запускал макрос, F4 уводил с экрана настроек); одна
клавиша могла остаться сразу у двух действий; отвязать действие было нельзя
вовсе — пустая привязка молча подменялась исходной клавишей.
"""
import main


class _Api(main.Api):
    def __init__(self, registered_ok=True, reject=()):
        self.logs = []
        self._hotkey_capture = False
        self._hotkey_capture_timer = None
        self._registered = []
        self._reject = set(reject)
        self._on_hotkeys_changed = self._fake_register if registered_ok else None

    def push_log(self, message):
        self.logs.append(message)

    def _fake_register(self, keys_):
        """Заглушка вместо настоящей перерегистрации: запоминает, с чем её
        позвали, и возвращает действия, чьи клавиши «не приняты»."""
        self._registered.append(dict(keys_))
        return [a for a in self._reject if keys_.get(a)]


def _store(monkeypatch, initial=None):
    state = {"hotkeys": dict(initial or {})}
    monkeypatch.setattr(main.cfg, "load", lambda: state)
    monkeypatch.setattr(main.cfg, "update", lambda patch: state.update(patch))
    return state


# ── Пустая привязка означает «отвязано» ───────────────────────────────────

def test_unbound_action_stays_unbound():
    """Ровно этот `or` и делал сброс невозможным: действие с пустой клавишей
    получало обратно исходную F-клавишу при каждой регистрации."""
    assert main.hotkey_for({"macro_start": ""}, "macro_start") == ""


def test_a_missing_action_falls_back_to_its_default():
    """Настройки со старой версии, где действия ещё не было."""
    assert main.hotkey_for({}, "open_replay") == main.HOTKEY_DEFAULTS["open_replay"]


def test_browser_key_names_are_translated_for_the_hotkey_library():
    # Из браузера приходит 'printscreen', библиотека знает 'print screen'.
    assert main.normalize_hotkey("printscreen") == "print screen"
    assert main.normalize_hotkey("PageUp") == "page up"
    assert main.normalize_hotkey("F9") == "f9"


# ── Одна клавиша — одно действие ──────────────────────────────────────────

def test_taking_a_busy_key_frees_it_from_the_other_action(monkeypatch):
    _store(monkeypatch, {"macro_start": "f1", "macro_stop": "f2"})
    api = _Api()
    res = api.set_hotkey("macro_start", "f2")
    assert res["ok"] and res["cleared"] == ["macro_stop"]
    assert res["hotkeys"]["macro_start"] == "f2"
    assert res["hotkeys"]["macro_stop"] == ""
    assert any("unassigned" in line or "освобождено" in line for line in api.logs)


def test_rebinding_to_its_own_key_changes_nothing(monkeypatch):
    _store(monkeypatch, {"macro_start": "f1"})
    api = _Api()
    res = api.set_hotkey("macro_start", "f1")
    assert res["ok"] and res["cleared"] == []
    assert res["hotkeys"]["macro_start"] == "f1"


# ── Клавиша, которую библиотека не приняла ────────────────────────────────

def test_a_rejected_key_is_rolled_back_not_silently_kept(monkeypatch):
    state = _store(monkeypatch, {"macro_start": "f1"})
    api = _Api(reject={"macro_start"})
    res = api.set_hotkey("macro_start", "fn")
    assert res["ok"] is False and res["reason"] == "bad_key"
    # Главное: старая привязка на месте и в ответе, и в настройках.
    assert res["hotkeys"]["macro_start"] == "f1"
    assert state["hotkeys"]["macro_start"] == "f1"
    assert any("не подходит" in line or "not a valid" in line for line in api.logs)


def test_a_rejected_key_gives_back_the_key_it_took_from_someone_else(monkeypatch):
    _store(monkeypatch, {"macro_start": "f1", "macro_stop": "f2"})
    api = _Api(reject={"macro_start"})
    res = api.set_hotkey("macro_start", "f2")
    assert res["ok"] is False
    # Стоп не должен остаться без клавиши из-за неудачной попытки.
    assert res["hotkeys"]["macro_stop"] == "f2"
    assert res["hotkeys"]["macro_start"] == "f1"


# ── Ответ всегда содержит то, что реально сохранилось ─────────────────────

def test_the_answer_always_carries_the_full_current_map(monkeypatch):
    """Интерфейс рисует строки по этому словарю, а не по своим ожиданиям."""
    _store(monkeypatch)
    api = _Api()
    res = api.set_hotkey("open_replay", "f10")
    assert set(res["hotkeys"]) == set(main.HOTKEY_DEFAULTS)
    assert res["hotkeys"]["open_replay"] == "f10"


def test_an_unknown_action_is_refused_with_the_map_intact(monkeypatch):
    _store(monkeypatch)
    api = _Api()
    res = api.set_hotkey("нет такого действия", "f10")
    assert res["ok"] is False and res["reason"] == "unknown_action"
    assert res["hotkeys"]["macro_start"] == main.HOTKEY_DEFAULTS["macro_start"]


def test_esc_unbinds_and_that_is_what_gets_stored(monkeypatch):
    state = _store(monkeypatch, {"macro_pause": "f5"})
    api = _Api()
    res = api.set_hotkey("macro_pause", "")
    assert res["ok"] and res["hotkeys"]["macro_pause"] == ""
    assert state["hotkeys"]["macro_pause"] == ""
    assert main.hotkey_for(state["hotkeys"], "macro_pause") == ""


# ── Глушение на время захвата ─────────────────────────────────────────────

def test_capture_mode_is_a_plain_flag_with_a_watchdog():
    """Флаг снимает интерфейс, но он может и не дожить до этого — сторож
    обязателен, иначе хоткеи останутся немыми до перезапуска."""
    api = _Api()
    api.set_hotkey_capture(True)
    assert api._hotkey_capture is True
    assert api._hotkey_capture_timer is not None
    api.set_hotkey_capture(False)
    assert api._hotkey_capture is False
    assert api._hotkey_capture_timer is None


def test_starting_capture_twice_leaves_one_watchdog():
    api = _Api()
    api.set_hotkey_capture(True)
    first = api._hotkey_capture_timer
    api.set_hotkey_capture(True)
    assert api._hotkey_capture_timer is not first
    assert not first.is_alive() or first.finished.is_set()
    api.set_hotkey_capture(False)


# ── Сброс ─────────────────────────────────────────────────────────────────

def test_reset_returns_every_action_to_its_default(monkeypatch):
    state = _store(monkeypatch, {"macro_start": "z", "open_replay": ""})
    api = _Api()
    res = api.reset_hotkeys()
    assert res["hotkeys"] == main.HOTKEY_DEFAULTS
    assert state["hotkeys"] == main.HOTKEY_DEFAULTS
    assert api._registered[-1] == main.HOTKEY_DEFAULTS


def test_every_action_has_a_human_label():
    """Журнал читает человек: «Старт макроса → F9», а не «macro_start»."""
    assert set(main.HOTKEY_LABELS) == set(main.HOTKEY_DEFAULTS)
