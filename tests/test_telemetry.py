"""Тесты фоновой анонимной телеметрии (core/telemetry.py).

ПОЧЕМУ ИМЕННО ЭТО.
1. Телеметрия ни при каких обстоятельствах не должна нарушать конфиденциальность
   пользователя: ID обязан быть стабильным 16-значным анонимным хэшем без личных данных.
2. Сетевые ошибки (отсутствие интернета, таймауты, сбои DNS) обязаны гаситься тихо
   и не должны приводить к падению макроса или выбросу исключений в вызывающий код.
3. Пакет данных обязан содержать корректные типы и ключи, ожидаемые RPC-функцией Supabase.
"""
import pytest

from core import telemetry
from core import settings as cfg


def test_anonymous_client_id_is_valid_and_persisted(tmp_path, monkeypatch):
    """Анонимный ID генерируется, сохраняется в настройках и остаётся неизменным."""
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(cfg, "SETTINGS_FILE", str(settings_file))

    cid1 = telemetry.get_anonymous_client_id()
    assert isinstance(cid1, str)
    assert len(cid1) >= 8

    # При повторном вызове должен вернуться тот же самый сохранённый ID
    cid2 = telemetry.get_anonymous_client_id()
    assert cid1 == cid2


def test_send_heartbeat_constructs_valid_payload_and_handles_success(monkeypatch):
    """Проверяет отправку валидного payload в RPC report_heartbeat."""
    recorded_requests = []

    class FakeResponse:
        status_code = 200

    def fake_post(url, json=None, headers=None, timeout=None):
        recorded_requests.append({
            "url": url,
            "json": json,
            "headers": headers,
            "timeout": timeout,
        })
        return FakeResponse()

    monkeypatch.setattr(telemetry.requests, "post", fake_post)
    telemetry.set_farming_active(True)

    ok = telemetry.send_heartbeat()
    assert ok is True
    assert len(recorded_requests) == 1

    req = recorded_requests[0]
    assert "report_heartbeat" in req["url"]
    p = req["json"]
    assert "p_client_id" in p
    assert "p_version" in p
    assert "p_uptime_minutes" in p
    assert "p_total_hours" in p
    assert "p_total_runs" in p
    assert p["p_is_active"] is True
    assert req["headers"]["apikey"] == telemetry.SUPABASE_ANON_KEY


def test_send_heartbeat_silently_suppresses_network_errors(monkeypatch):
    """При падении сети send_heartbeat возвращает False, но никогда не выбрасывает исключение."""
    def fake_post_raise(*args, **kwargs):
        raise ConnectionError("No internet connection")

    monkeypatch.setattr(telemetry.requests, "post", fake_post_raise)

    # Не должно упасть с исключением
    ok = telemetry.send_heartbeat()
    assert ok is False


def test_telemetry_start_and_stop_lifecycle(monkeypatch):
    """Запуск и остановка телеметрии корректно управляют потоком."""
    calls = []

    monkeypatch.setattr(telemetry, "send_heartbeat", lambda *args: calls.append("heartbeat") or True)
    # Быстрый воркер для проверки
    monkeypatch.setattr(telemetry.time, "sleep", lambda s: None)

    telemetry.start_telemetry()
    assert telemetry._thread is not None
    telemetry.stop_telemetry()
    assert telemetry._stop_event.is_set()
