"""Анонимная фоновая телеметрия для мониторинга активности макроса.

ПОЧЕМУ ЭТО СДЕЛАНО ИМЕННО ТАК:
1. Полная анонимность (Privacy-First):
   - Никаких персональных данных, имён аккаунтов, путей или IP-адресов.
   - Идентификатор клиента — односторонний SHA-256 хэш MachineGUID с солью
     (или случайный UUID в settings.json). Восстановить реальное железо невозможно.
2. Безопасность базы данных:
   - В Supabase для публичного anon-ключа таблица закрыта на чтение (REVOKE ALL).
   - Клиент имеет право ТОЛЬКО вызывать RPC-функцию `report_heartbeat`.
   - Просматривать агрегированную статистику может только разработчик через защищённый ключ.
3. Полная неблокируемость:
   - Все запросы выполняются исключительно в фоновом демон-потоке с коротким таймаутом (4 сек).
   - Ошибки сети или отсутствие интернета перехватываются и подавляются тихо,
     не прерывая работу макроса и интерфейса.
"""
import hashlib
import os
import platform
import threading
import time
import uuid

import requests

from . import constants
from . import settings as cfg

# Публичный endpoint проекта Supabase (проект macroAE)
SUPABASE_URL = "https://ifpnicjcpyissiqhwotq.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmcG5pY2pjcHlpc3NpcWh3b3RxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAwODA3NjgsImV4cCI6MjEwNTY1Njc2OH0."
    "mX0YyBEoew5FmfjzYpnN7EWVL4NJG343lar6m_VycjI"
)

# Соль для хэширования MachineGuid, исключающая сопоставление по радужным таблицам
_SALT = "AE_MACRO_TELEMETRY_v2_2026"

_session_id = uuid.uuid4().hex[:12]
_session_start = time.time()
_is_active_farming = False
_thread = None
_stop_event = threading.Event()


def get_anonymous_client_id() -> str:
    """Возвращает стабильный анонимный 16-значный идентификатор клиента."""
    saved = cfg.load().get("telemetry_client_id")
    if saved and isinstance(saved, str) and len(saved) >= 8:
        return saved

    candidate = ""
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as k:
                guid, _ = winreg.QueryValueEx(k, "MachineGuid")
                if guid:
                    candidate = hashlib.sha256((str(guid) + _SALT).encode("utf-8")).hexdigest()[:16]
        except Exception:
            pass

    if not candidate:
        candidate = uuid.uuid4().hex[:16]

    cfg.update({"telemetry_client_id": candidate})
    return candidate


def set_farming_active(active: bool) -> None:
    """Отмечает, выполняет ли макрос забег в Roblox прямо сейчас."""
    global _is_active_farming
    _is_active_farming = bool(active)


def _get_os_name() -> str:
    if os.name == "nt":
        rel = platform.release()
        return f"Windows {rel}"
    elif platform.system() == "Darwin":
        return "macOS"
    return platform.system() or "Windows"


def send_heartbeat(api=None) -> bool:
    """Отправляет один анонимный пинг активности в Supabase."""
    try:
        from core import updater
        version = updater.get_current_version()
    except Exception:
        version = "2.0.1"

    client_id = get_anonymous_client_id()
    uptime_min = max(0, int((time.time() - _session_start) / 60))

    data = cfg.load()
    base_all_time = float(data.get("all_time_seconds", 0.0) or 0.0)
    current_total_hours = round((base_all_time + (time.time() - _session_start)) / 3600.0, 2)
    total_runs = len(data.get("run_history", []))

    payload = {
        "p_client_id": client_id,
        "p_version": str(version),
        "p_os": _get_os_name(),
        "p_session_id": _session_id,
        "p_uptime_minutes": uptime_min,
        "p_total_hours": current_total_hours,
        "p_total_runs": total_runs,
        "p_is_active": _is_active_farming,
    }

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "User-Agent": f"AnimeExpeditionsMacro/{version}",
    }

    url = f"{SUPABASE_URL}/rest/v1/rpc/report_heartbeat"
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=4.0)
        return resp.status_code in (200, 204)
    except Exception:
        return False


def _telemetry_worker(api=None):
    # Задержка перед первым пингом: даём интерфейсу и окну игры полностью подняться
    time.sleep(12)
    if _stop_event.is_set():
        return

    send_heartbeat(api)

    # Периодический пинг каждые 15 минут
    while not _stop_event.is_set():
        if _stop_event.wait(900):
            break
        send_heartbeat(api)


def start_telemetry(api=None) -> None:
    """Запускает фоновый демон-поток периодических пингов."""
    global _thread
    if _thread is not None and _thread.is_alive():
        return

    _stop_event.clear()
    _thread = threading.Thread(target=_telemetry_worker, args=(api,), daemon=True, name="TelemetryWorker")
    _thread.start()


def stop_telemetry(api=None) -> None:
    """Корректно завершает работу телеметрии и шлёт финальный пинг."""
    _stop_event.set()
    try:
        send_heartbeat(api)
    except Exception:
        pass
