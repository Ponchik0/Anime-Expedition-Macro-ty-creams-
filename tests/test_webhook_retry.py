"""Повторы отправки webhook: что повторяем, что нет, сколько ждём.

Раньше повтор был ровно один -- на 429 («слишком часто»). Всё остальное
отбрасывало уведомление с первой осечки: обрыв связи, таймаут, 502/503/504 от
Cloudflare перед Discord'ом. Ровно это и случается чаще всего на домашнем
интернете, то есть уведомления терялись именно тогда, когда за ними следят.

Правило повтора живёт в двух функциях (_retry_wait_for_status /
_retry_wait_for_exception) и одинаково для всех трёх отправок -- до этого оно
было переписано в каждой отдельно, двенадцатью местами, которые обязаны
совпадать.
"""
import urllib.error

import pytest

from core import webhook

URL = "https://discord.com/api/webhooks/123456789/tok"


@pytest.fixture(autouse=True)
def no_sleeping(monkeypatch):
    """Паузы записываем, но не спим -- иначе набор тестов идёт минуты."""
    slept = []
    monkeypatch.setattr(webhook.time, "sleep", slept.append)
    return slept


# ── Правило повтора ───────────────────────────────────────────────────────

@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_server_errors_are_retried(status):
    assert webhook._retry_wait_for_status(None, status, attempt=0) is not None


@pytest.mark.parametrize("status", [400, 401, 403, 404, 405, 413])
def test_client_errors_are_never_retried(status):
    """Вебхук удалён, токен не тот, ссылка не та -- повтором это не лечится:
    сколько попыток, столько же ошибок, только с задержкой."""
    assert webhook._retry_wait_for_status(None, status, attempt=0) is None


def test_rate_limit_waits_exactly_what_discord_asked():
    class _Resp:
        headers = {}

        @staticmethod
        def json():
            return {"retry_after": 2.0}

    wait = webhook._retry_wait_for_status(_Resp(), 429, attempt=0)
    assert wait == pytest.approx(2.25)  # +0.25 буфер, см. _retry_after


def test_rate_limit_wait_is_capped():
    """Испорченное или огромное значение не должно вешать отправку."""
    class _Resp:
        headers = {}

        @staticmethod
        def json():
            return {"retry_after": 9999.0}

    assert webhook._retry_wait_for_status(_Resp(), 429, attempt=0) == webhook._RETRY_WAIT_CAP


def test_retries_run_out():
    assert webhook._retry_wait_for_status(None, 503, attempt=webhook._RETRY_MAX) is None
    assert webhook._retry_wait_for_exception(attempt=webhook._RETRY_MAX) is None


def test_the_pause_grows():
    """Растущая пауза, а не одинаковая: короткий сбой проходит со второй
    попытки, длинному нужно дать больше времени."""
    waits = [webhook._retry_wait_for_exception(a) for a in range(webhook._RETRY_MAX)]
    assert waits == sorted(waits) and waits[0] < waits[-1]


# ── send(): сбой сети ──────────────────────────────────────────────────────

def test_send_retries_a_dropped_connection_and_succeeds(monkeypatch, no_sleeping):
    calls = []

    class _Ok:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def urlopen(req, timeout=None):
        calls.append(1)
        if len(calls) < 3:
            raise urllib.error.URLError("connection reset")
        return _Ok()

    monkeypatch.setattr(webhook.urllib.request, "urlopen", urlopen)

    result = webhook.send(URL, {"title": "x"})

    assert result["ok"] is True, result["reason"]
    assert len(calls) == 3, "не дожал до успеха"
    assert len(no_sleeping) == 2


def test_send_gives_up_after_the_cap(monkeypatch, no_sleeping):
    calls = []

    def urlopen(req, timeout=None):
        calls.append(1)
        raise urllib.error.URLError("no route to host")

    monkeypatch.setattr(webhook.urllib.request, "urlopen", urlopen)

    result = webhook.send(URL, {"title": "x"})

    assert result["ok"] is False
    assert "no route to host" in result["reason"], "потеряли настоящую причину"
    assert len(calls) == webhook._RETRY_MAX + 1, "число попыток вышло за предел"


# ── send(): коды ответа ────────────────────────────────────────────────────

def _http_error(code, body=b"{}"):
    return urllib.error.HTTPError(URL, code, "err", {}, None if body is None else _Body(body))


class _Body:
    """Тело ответа для HTTPError. `close` обязателен: HTTPError оборачивает
    переданный поток во временный файл и закрывает его при сборке мусора --
    без метода это всплывает как PytestUnraisableExceptionWarning."""

    def __init__(self, data):
        self._data = data

    def read(self):
        return self._data

    def close(self):
        pass


def test_send_retries_a_bad_gateway(monkeypatch, no_sleeping):
    calls = []

    class _Ok:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def urlopen(req, timeout=None):
        calls.append(1)
        if len(calls) == 1:
            raise _http_error(502)
        return _Ok()

    monkeypatch.setattr(webhook.urllib.request, "urlopen", urlopen)

    assert webhook.send(URL, {"title": "x"})["ok"] is True
    assert len(calls) == 2


def test_send_does_not_retry_a_deleted_webhook(monkeypatch, no_sleeping):
    """404 = вебхук удалён. Повторять бессмысленно, и ошибка обязана дойти до
    журнала как есть -- по ней человек и поймёт, что надо заменить ссылку."""
    calls = []

    def urlopen(req, timeout=None):
        calls.append(1)
        raise _http_error(404, b'{"message": "Unknown Webhook"}')

    monkeypatch.setattr(webhook.urllib.request, "urlopen", urlopen)

    result = webhook.send(URL, {"title": "x"})

    assert result["ok"] is False
    assert len(calls) == 1, "повторяли то, что повторять нельзя"
    assert "404" in result["reason"] and "Unknown Webhook" in result["reason"]


# ── send_rich(): тот же набор правил, другая библиотека ───────────────────

def test_send_rich_retries_then_succeeds(monkeypatch, no_sleeping):
    calls = []

    class _Resp:
        def __init__(self, code):
            self.status_code = code
            self.text = ""
            self.headers = {}

        def json(self):
            return {}

    def post(url, **kw):
        calls.append(kw)
        if len(calls) == 1:
            raise webhook.requests.RequestException("timed out")
        if len(calls) == 2:
            return _Resp(503)
        return _Resp(204)

    monkeypatch.setattr(webhook.requests, "post", post)

    result = webhook.send_rich(URL, embeds=[{"title": "x"}])

    assert result["ok"] is True, result["reason"]
    assert len(calls) == 3


def test_send_rich_does_not_retry_a_forbidden(monkeypatch, no_sleeping):
    calls = []

    class _Resp:
        status_code = 403
        text = "forbidden"
        headers = {}

        def json(self):
            return {}

    monkeypatch.setattr(webhook.requests, "post", lambda url, **kw: calls.append(1) or _Resp())

    result = webhook.send_rich(URL, embeds=[{"title": "x"}])

    assert result["ok"] is False
    assert len(calls) == 1
    assert "403" in result["reason"]


def test_send_file_falls_back_to_a_plain_send_without_the_file(monkeypatch, no_sleeping):
    """Обещание докстринга send_file: недоступный скриншот не должен стоить
    целого уведомления."""
    sent = []
    monkeypatch.setattr(webhook, "send", lambda url, embed, content="", silent=False:
                        sent.append(embed) or {"ok": True, "reason": ""})

    result = webhook.send_file(URL, {"title": "x"}, "no/such/file.png")

    assert result["ok"] is True
    assert len(sent) == 1
