"""Расписание периодической сводки: когда она уходит и когда молчит.

Настройка обещает ровно две вещи — «раз в N часов» и «только пока идёт
прогон». Ошибка в любой из них замечается не сразу и стоит дорого в обе
стороны: либо канал получает сводку каждые полминуты, либо не получает её
никогда, а человек узнаёт об этом наутро.

Потоков и сна здесь нет: такт планировщика проигрывается вручную, часы
подаются снаружи. Тест про решение, а не про ожидание.
"""
import time
import types

import pytest

import main
from core import settings as cfg


@pytest.fixture
def api(tmp_path, monkeypatch):
    """Api с настройками во временном файле, без окон и без потоков."""
    monkeypatch.setattr(cfg, "SETTINGS_FILE", str(tmp_path / "settings.json"))
    a = main.Api.__new__(main.Api)                 # без __init__: он поднимает окно и потоки
    a._session_wins = 0
    a._session_losses = 0
    a._run_status = {"action": "Idle", "mode": "-", "macro": "-",
                     "current_task": "-", "current_repeat": "-", "map": "-"}
    a.push_log = lambda m: None
    a.session_start = time.time()
    a._all_time_base = 0.0
    a._status_accum = 0.0
    a._status_since = a.session_start
    a._player = None
    a.runner = types.SimpleNamespace(is_running=lambda: False)

    # Саму отправку подменяем: проверяется РЕШЕНИЕ слать, а не Discord.
    a.sent = []

    def fake_send(final=False, reset=True):
        a.sent.append({"final": final})
        if reset:
            a._reset_status_window()
        return {"ok": True, "reason": ""}

    a._send_status_report = fake_send
    return a


def _play(api, monkeypatch, ticks, step=None, tick=None, on_tick=None):
    """Проиграть `ticks` тактов планировщика с заданным ходом часов.

    Планировщик устроен как `while not stopping.wait(такт): ...`, поэтому и ход
    часов, и смена обстановки (прогон встал) навешиваются на wait: то самое
    место, где настоящий поток спит между тактами.

    `tick` — длина такта самого планировщика, `step` — насколько за этот такт
    ушли часы. Врозь, потому что расходятся они не всегда: спящий компьютер это
    ровно тот случай, когда такт двадцать секунд, а часов прошло восемь."""
    if tick is not None:
        monkeypatch.setattr(main, "STATUS_TICK_SECONDS", tick)
    step = main.STATUS_TICK_SECONDS if step is None else step
    clock = {"now": time.time()}
    left = {"n": ticks}
    monkeypatch.setattr(main.time, "time", lambda: clock["now"])

    def wait(_timeout):
        clock["now"] += step
        left["n"] -= 1
        if on_tick:
            on_tick(ticks - left["n"])            # номер такта, считая с единицы
        return left["n"] < 0

    api.stopping = types.SimpleNamespace(wait=wait)
    api._status_report_worker()


def _enable(hours=6.0, **over):
    settings = {"webhook_enabled": True, "webhook_url": "https://discord.com/api/webhooks/1/t",
                "webhook_status_enabled": True, "webhook_status_hours": hours}
    settings.update(over)
    cfg.update(settings)


def _running(flag=True):
    return types.SimpleNamespace(is_running=lambda: flag)


# ── Интервал ──────────────────────────────────────────────────────────────

def test_nothing_is_sent_before_the_interval_is_up(api, monkeypatch):
    _enable(hours=6.0, webhook_status_only_running=False)

    _play(api, monkeypatch, ticks=5)

    assert api.sent == []


def test_the_summary_goes_out_once_the_interval_is_up(api, monkeypatch):
    _enable(hours=1.0, webhook_status_only_running=False)

    # Такт длиной в час: два такта — два часа, то есть два отчёта.
    _play(api, monkeypatch, ticks=2, step=3600.0, tick=3600.0)

    assert len(api.sent) == 2


def test_a_disabled_status_stays_silent(api, monkeypatch):
    _enable(hours=1.0, webhook_status_enabled=False, webhook_status_only_running=False)

    _play(api, monkeypatch, ticks=3, step=3600.0, tick=3600.0)

    assert api.sent == []


def test_a_disabled_webhook_stays_silent_even_with_the_status_on(api, monkeypatch):
    """Общий выключатель доставки главнее: выключил вебхук — выключил всё."""
    _enable(hours=1.0, webhook_enabled=False, webhook_status_only_running=False)

    _play(api, monkeypatch, ticks=3, step=3600.0, tick=3600.0)

    assert api.sent == []


# ── «Только во время прогона» ─────────────────────────────────────────────

def test_a_stopped_macro_does_not_accumulate_time(api, monkeypatch):
    """Остановил на ночь — утром не должно прийти пачки сводок."""
    _enable(hours=1.0, webhook_status_only_running=True)

    _play(api, monkeypatch, ticks=5, step=3600.0, tick=3600.0)

    assert api.sent == []
    assert api._status_accum == 0.0


def test_a_running_macro_does_accumulate(api, monkeypatch):
    _enable(hours=1.0, webhook_status_only_running=True)
    api.runner = _running()

    _play(api, monkeypatch, ticks=2, step=3600.0, tick=3600.0)

    assert len(api.sent) == 2


def test_a_replay_counts_as_a_run_too(api, monkeypatch):
    """Повтор об игре не знает ничего и сломанную запись крутит так же бодро,
    как рабочую, — сводка ему нужна даже больше, чем автомату."""
    _enable(hours=1.0, webhook_status_only_running=True)
    api._player = types.SimpleNamespace(running=True)

    _play(api, monkeypatch, ticks=1, step=3600.0, tick=3600.0)

    assert len(api.sent) == 1


def test_a_long_sleep_does_not_count_as_worked_time(api, monkeypatch):
    """Компьютер спал восемь часов — проснувшись, поток не должен выдать сводку
    «за 8 ч», в которую макрос не отработал ни минуты."""
    _enable(hours=1.0, webhook_status_only_running=False)

    _play(api, monkeypatch, ticks=1, step=8 * 3600.0)

    assert api.sent == []
    assert api._status_accum <= main.STATUS_TICK_SECONDS * 3


def test_the_window_start_follows_a_stopped_macro(api, monkeypatch):
    """Пока прогона нет, окно ещё не началось — иначе в первую же сводку
    попали бы вчерашние матчи."""
    _enable(hours=99.0, webhook_status_only_running=True)
    started_at = api._status_since

    _play(api, monkeypatch, ticks=3, step=3600.0, tick=3600.0)

    assert api._status_since > started_at


# ── Итог при остановке ────────────────────────────────────────────────────

def test_the_end_of_a_run_sends_a_final_summary(api, monkeypatch):
    """Ловим переходом «шёл → не идёт», а не хуком в кнопку «Стоп»: прогон
    кончается и сам, отыграв все круги, и такой конец не менее интересен."""
    _enable(hours=99.0, webhook_status_only_running=True)
    live = {"on": True}
    api.runner = types.SimpleNamespace(is_running=lambda: live["on"])

    _play(api, monkeypatch, ticks=2, step=3600.0, tick=3600.0,
          on_tick=lambda n: live.__setitem__("on", n < 2))

    assert [s["final"] for s in api.sent] == [True]


def test_the_final_summary_can_be_turned_off(api, monkeypatch):
    _enable(hours=99.0, webhook_status_only_running=True, webhook_status_on_stop=False)
    live = {"on": True}
    api.runner = types.SimpleNamespace(is_running=lambda: live["on"])

    _play(api, monkeypatch, ticks=2, step=3600.0, tick=3600.0,
          on_tick=lambda n: live.__setitem__("on", n < 2))

    assert api.sent == []


def test_a_run_that_barely_started_gets_no_summary(api):
    """Нажал «Старт», через десять секунд передумал — итог «за 10 с, матчей 0»
    это чистый шум."""
    api._status_accum = 10.0
    api._status_since = time.time()

    assert api._status_worth_a_summary() is False


def test_a_minute_of_work_is_already_worth_a_summary(api):
    api._status_accum = 120.0

    assert api._status_worth_a_summary() is True


def test_even_a_short_run_is_worth_it_if_a_match_landed(api):
    """Матч отыгран — значит прогон был настоящий, сколько бы он ни длился."""
    api._status_accum = 5.0
    api._status_since = time.time() - 60
    cfg.update({"run_history": [{"result": "win", "map": "-", "duration": "1m",
                                  "at": time.time()}]})

    assert api._status_worth_a_summary() is True


# ── Интервал из настроек ──────────────────────────────────────────────────

@pytest.mark.parametrize("stored,expected", [
    (6, 6.0), ("3", 3.0), (0, main.STATUS_HOURS_MIN), (-5, main.STATUS_HOURS_MIN),
    (999, main.STATUS_HOURS_MAX), ("ерунда", main.STATUS_HOURS_DEFAULT),
    (None, main.STATUS_HOURS_DEFAULT), (float("nan"), main.STATUS_HOURS_DEFAULT),
])
def test_the_interval_is_clamped_to_something_sane(stored, expected):
    """Ноль опаснее всего: без зажима он превратил бы планировщик в рассылку
    по сообщению за такт."""
    assert main._status_hours({"webhook_status_hours": stored}) == expected


def test_the_interval_survives_a_missing_setting():
    assert main._status_hours({}) == main.STATUS_HOURS_DEFAULT


# ── Настройки туда и обратно ──────────────────────────────────────────────

def test_the_status_settings_round_trip(api):
    api.save_webhook_settings("https://discord.com/api/webhooks/1/t", True, False, "42",
                               status_enabled=True, status_hours=3,
                               status_only_running=False, status_on_stop=False)

    wh = api.get_webhook_settings()
    assert wh["status_enabled"] is True
    assert wh["status_hours"] == 3.0
    assert wh["status_only_running"] is False
    assert wh["status_on_stop"] is False


def test_an_old_four_argument_save_does_not_wipe_the_status_settings(api):
    """Страница могла остаться в кэше вебвью со старым вызовом — он обязан
    сохранить ссылку и не тронуть чужие настройки."""
    api.save_webhook_settings("https://discord.com/api/webhooks/1/t", True, False, "42",
                               status_enabled=True, status_hours=12)

    api.save_webhook_settings("https://discord.com/api/webhooks/2/t", True, False, "42")

    wh = api.get_webhook_settings()
    assert wh["status_enabled"] is True and wh["status_hours"] == 12.0


def test_the_status_is_off_by_default(api):
    """Канал, в который сами собой начали падать сообщения, никто не просил."""
    wh = api.get_webhook_settings()

    assert wh["status_enabled"] is False
    assert wh["status_hours"] == main.STATUS_HOURS_DEFAULT
    assert wh["status_only_running"] is True
    assert wh["status_on_stop"] is True


# ── Отправка целиком ──────────────────────────────────────────────────────

def test_a_manual_send_does_not_move_the_schedule(api, monkeypatch):
    """Посмотреть сводку сейчас — это не то же самое, что сдвинуть расписание:
    нажатие кнопки не должно отменять очередной плановый отчёт."""
    _enable(hours=6.0)
    api._status_accum = 5 * 3600.0
    sent = []
    monkeypatch.setattr(main.webhook, "send",
                        lambda url, embed, content="", silent=False: (
                            sent.append(embed), {"ok": True, "reason": ""})[1])
    del api._send_status_report                    # снимаем подмену из фикстуры

    api.send_status_report_now()

    assert len(sent) == 1
    assert api._status_accum == 5 * 3600.0


def test_the_report_is_not_sent_without_a_webhook(api, monkeypatch):
    cfg.update({"webhook_enabled": False})
    sent = []
    monkeypatch.setattr(main.webhook, "send",
                        lambda *a, **kw: (sent.append(a), {"ok": True})[1])
    del api._send_status_report

    res = api.send_status_report_now()

    assert sent == [] and res["ok"] is False


def test_the_report_carries_the_matches_of_its_own_window(api, monkeypatch):
    """Сводка «за шесть часов» обязана считать матчи ровно за эти шесть часов,
    а не за всю историю: иначе каждая следующая повторяла бы предыдущую."""
    _enable(hours=6.0)
    now = time.time()
    api._status_since = now - 3600
    api._status_accum = 3600.0
    cfg.update({"run_history": [
        {"result": "win", "map": "-", "duration": "5m", "at": now - 100},
        {"result": "loss", "map": "-", "duration": "5m", "at": now - 200},
        {"result": "win", "map": "-", "duration": "5m", "at": now - 100_000},
    ]})
    sent = []
    monkeypatch.setattr(main.webhook, "send",
                        lambda url, embed, content="", silent=False: (
                            sent.append(embed), {"ok": True, "reason": ""})[1])
    del api._send_status_report

    api.send_status_report_now()

    assert "1W · 1L" in sent[0]["description"]
