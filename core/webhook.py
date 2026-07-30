import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import requests

# Any Discord client build (stable/canary/PTB) and both the current and
# legacy API host resolve webhooks identically -- matched by suffix instead
# of an exact host list so this doesn't need updating for every variant.
DISCORD_HOST_SUFFIXES = ("discord.com", "discordapp.com")

SUPPRESS_NOTIFICATIONS_FLAG = 4096  # Discord webhook message flag for "silent" sends

# Discord sits behind Cloudflare, which blocks urllib's default User-Agent
# ("Python-urllib/3.x") outright -- every send was failing with a 403
# ("error code: 1010", Cloudflare's own bot-block page, not a Discord API
# error) with nothing logged about it, since send() swallowed the exception
# and just returned False. Same fix as tools/fetch_item_icons.py's wiki
# requests needed for the same reason: a normal browser User-Agent clears it.
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Discord rate-limits webhooks (HTTP 429) and tells you how long to wait in
# the response -- send()/send_file() honour that and retry rather than
# dropping the notification. Kept SYNCHRONOUS on purpose: the caller relies
# on the real {ok, reason} result (the Settings "Send Test" button reports
# whether the webhook actually works, and result/event sends log the failure
# reason), so a fire-and-forget queue that always returns "ok" would break
# both. The frequent send -- match results -- already runs on a background
# thread (see runner._finish_match_result_background), so the brief wait
# here doesn't stall the macro loop.
_RETRY_MAX = 3          # attempts after the first (429, 5xx, обрыв связи -- см. ниже)
_RETRY_WAIT_CAP = 5.0   # never sleep longer than this per retry, whatever Discord asks

# ПОВТОРЯЕМ НЕ ТОЛЬКО 429. Раньше повтор был ровно один -- на «слишком
# часто». Всё остальное отбрасывало уведомление с первой же осечки: разрыв
# соединения, таймаут, 502/503/504 от Cloudflare перед Discord'ом. Ровно эти
# три вещи и случаются чаще всего на домашнем интернете и при коротких
# сбоях Discord, то есть уведомления терялись именно тогда, когда за ними
# следят. Теперь такие ответы -- тоже повтор, с растущей паузой.
_RETRY_STATUS = (500, 502, 503, 504)
_RETRY_BACKOFF = (0.5, 1.5, 3.0)  # пауза перед 1-й, 2-й и 3-й повторной попыткой


def _backoff_wait(attempt: int) -> float:
    """Пауза перед повторной попыткой номер `attempt` (с нуля)."""
    return _RETRY_BACKOFF[min(attempt, len(_RETRY_BACKOFF) - 1)]


# ── Одно правило повтора на все три отправки ──────────────────────────────
# Отправок здесь три (send / send_file / send_rich), и решение «повторять или
# сдаться» раньше было переписано в каждой отдельно -- четыре ветки на три
# функции, двенадцать мест, которые обязаны совпадать. Такое расходится:
# именно так 5xx долго повторялся в одной отправке и не повторялся в двух
# других. Теперь правило одно, и обе функции ниже возвращают одно и то же:
# СКОЛЬКО СПАТЬ перед повтором, либо None -- «повторять нельзя, отдавай ошибку».


def _retry_wait_for_status(source, status: int, attempt: int):
    """Пауза перед повтором для КОДА ОТВЕТА, или None если повторять нельзя.

    429 -- ждём столько, сколько попросил Discord (он присылает точное число).
    5xx -- растущая пауза: это Cloudflare/Discord прилёг на секунды.
    Всё остальное (401/403/404 -- вебхук удалён, токен не тот, ссылка не та)
    повтором не лечится: столько же попыток, столько же ошибок."""
    if attempt >= _RETRY_MAX:
        return None
    if status == 429:
        return _retry_after(source)
    if status in _RETRY_STATUS:
        return _backoff_wait(attempt)
    return None


def _retry_wait_for_exception(attempt: int):
    """Пауза перед повтором для СБОЯ СЕТИ (обрыв, таймаут), или None если
    попытки кончились. Домашний интернет отваливается на секунду-две, и без
    повтора уведомление терялось с первой же осечки."""
    if attempt >= _RETRY_MAX:
        return None
    return _backoff_wait(attempt)


def _retry_after(source) -> float:
    """Seconds to wait before retrying a 429, from Discord's JSON
    `retry_after` (webhook API gives it in seconds) or the Retry-After
    header as a fallback. A small buffer is added and the total is capped so
    a malformed/huge value can't hang the send. `source` is a requests
    Response or a urllib HTTPError -- both expose .headers, and JSON is read
    via the matching call."""
    delay = None
    try:
        body = source.json() if hasattr(source, "json") else json.loads(
            source.read().decode("utf-8", errors="replace"))
        delay = float(body.get("retry_after"))
    except Exception:
        try:
            hdr = source.headers.get("Retry-After") if source.headers else None
            delay = float(hdr) if hdr is not None else None
        except (TypeError, ValueError):
            delay = None
    if delay is None:
        delay = 1.0
    return max(0.0, min(delay + 0.25, _RETRY_WAIT_CAP))


def validate(url: str) -> dict:
    url = (url or "").strip()
    if not url:
        return {"valid": False, "reason": "empty"}
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return {"valid": False, "reason": "bad_format"}
    if parsed.scheme != "https":
        return {"valid": False, "reason": "not_https"}

    host = parsed.netloc.lower()
    if not any(host == suffix or host.endswith("." + suffix) for suffix in DISCORD_HOST_SUFFIXES):
        return {"valid": False, "reason": "not_discord"}

    # .../api/webhooks/<id>/<token>, checked from the end so a trailing slash
    # or a `?wait=true`-style query string don't matter.
    #
    # Anchored on "webhooks", not on "api" being exactly four from the end:
    # Discord also serves the versioned form, .../api/v10/webhooks/<id>/<tok>,
    # which is what its own docs show and what the developer portal copies for
    # some flows. That has "api" at parts[-5], so the old check rejected it as
    # bad_format -- despite the comment right here claiming a version segment
    # was already handled.
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 3 or parts[-3] != "webhooks":
        return {"valid": False, "reason": "bad_format"}
    # Whatever precedes "webhooks" must still be the API path, optionally with
    # one version segment -- so a lookalike like /foo/webhooks/1/t is refused.
    before = parts[:-3]
    if not before or before[-1] != "api":
        if len(before) < 2 or before[-2] != "api" or not re.fullmatch(r"v\d+", before[-1]):
            return {"valid": False, "reason": "bad_format"}
    webhook_id, token = parts[-2], parts[-1]
    if not webhook_id.isdigit() or not token:
        return {"valid": False, "reason": "bad_format"}
    return {"valid": True, "reason": "ok"}


def validate_webhook_url(url: str) -> bool:
    """Validates whether the webhook URL is HTTPS and belongs to allowed Discord domains."""
    return validate(url).get("valid", False)



def send(url: str, embed: dict, content: str = "", silent: bool = False) -> dict:
    """Returns {"ok": bool, "reason": str} instead of a bare bool -- a
    failed send used to disappear silently (the caller never even logged
    it), which is exactly how the Cloudflare User-Agent block above went
    unnoticed. "ok" is False for a genuine failure; "reason" is empty on
    success."""
    if not url:
        return {"ok": False, "reason": "no webhook URL configured"}
    if not validate_webhook_url(url):
        return {"ok": False, "reason": "invalid webhook URL format or non-Discord target"}
    payload = {"embeds": [embed]}
    if content:
        payload["content"] = content
    if silent:
        payload["flags"] = SUPPRESS_NOTIFICATIONS_FLAG
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    for attempt in range(_RETRY_MAX + 1):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if 200 <= resp.status < 300:
                    return {"ok": True, "reason": ""}
                return {"ok": False, "reason": f"HTTP {resp.status}"}
        except urllib.error.HTTPError as exc:
            # _retry_after читает тело ответа, поэтому вызывается ДО того, как
            # тело прочитают для сообщения об ошибке -- иначе на 429 он получил
            # бы пустой поток и вернул паузу по умолчанию.
            wait = _retry_wait_for_status(exc, exc.code, attempt)
            if wait is not None:
                time.sleep(wait)
                continue
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")[:200]
            except Exception:
                pass
            return {"ok": False, "reason": f"HTTP {exc.code}: {body}" if body else f"HTTP {exc.code}"}
        except (urllib.error.URLError, OSError) as exc:
            wait = _retry_wait_for_exception(attempt)
            if wait is None:
                return {"ok": False, "reason": str(exc)}
            time.sleep(wait)
            continue
    return {"ok": False, "reason": "gave up after retries"}


def send_file(url: str, embed: dict, screenshot_path: str, content: str = "", silent: bool = False) -> dict:
    """Like send(), but attaches a screenshot -- for events worth SEEING,
    not just reading about (a stuck Start Game click, a disconnect, a task
    finally giving up). Discord's webhook endpoint only accepts a file
    alongside JSON as multipart/form-data (the payload as a "payload_json"
    field, not the request body directly), which needs actual multipart
    encoding -- urllib has no built-in support for that, hence `requests`
    here instead of send()'s plain urllib request.

    Falls back to a screenshot-less send() if the file itself can't be
    read, rather than losing the notification entirely over a missing/
    unreadable debug screenshot."""
    if not url:
        return {"ok": False, "reason": "no webhook URL configured"}
    if not validate_webhook_url(url):
        return {"ok": False, "reason": "invalid webhook URL format or non-Discord target"}
    if not screenshot_path or not os.path.isfile(screenshot_path):
        return send(url, embed, content=content, silent=silent)

    filename = os.path.basename(screenshot_path)
    payload = {"embeds": [embed]}
    if content:
        payload["content"] = content
    if silent:
        payload["flags"] = SUPPRESS_NOTIFICATIONS_FLAG
    embed["image"] = {"url": f"attachment://{filename}"}

    # Read the bytes up front (not streamed from the open handle inside the
    # request): the same bytes are reused across 429 retries, and a debug
    # screenshot getting deleted between here and the send can't race the
    # upload. If it can't be read, fall back to a text-only send rather than
    # lose the whole notification over an unreadable screenshot -- what this
    # function's docstring has always promised.
    try:
        with open(screenshot_path, "rb") as f:
            file_bytes = f.read()
    except OSError:
        return send(url, embed, content=content, silent=silent)

    data = {"payload_json": json.dumps(payload)}
    for attempt in range(_RETRY_MAX + 1):
        try:
            resp = requests.post(
                url, data=data, files={"file": (filename, file_bytes, "image/png")},
                headers={"User-Agent": USER_AGENT}, timeout=15)
        except requests.RequestException as exc:
            wait = _retry_wait_for_exception(attempt)
            if wait is None:
                return {"ok": False, "reason": str(exc)}
            time.sleep(wait)
            continue
        if 200 <= resp.status_code < 300:
            return {"ok": True, "reason": ""}
        wait = _retry_wait_for_status(resp, resp.status_code, attempt)
        if wait is not None:
            time.sleep(wait)
            continue
        return {"ok": False, "reason": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    return {"ok": False, "reason": "gave up after retries"}


def send_rich(url: str, embeds: list = None, file_attachments: list = None,
              components: list = None, content: str = "", silent: bool = False) -> dict:
    """A fuller send than send()/send_file(): MULTIPLE embeds, MULTIPLE image
    attachments, and message components (a link-button action row) in one
    message -- what the match-result webhook needs to show the status card
    and the game screenshot as two separate images in one notification.
    (`components` больше не используется отправкой результата: блок ссылок
    из уведомления убран, но параметр оставлен -- он не про ссылки, а про
    компоненты в целом.)

    `file_attachments` is a list of (filename, bytes); an embed references
    one via {"image": {"url": "attachment://<filename>"}}. `components` is a
    raw Discord components array (already shaped by the caller). Returns the
    same {"ok", "reason"} contract as the others, and honours 429 retries.

    Plain incoming webhooks DO accept link-style buttons (verified live) --
    unlike the interactive component types, which need a bot; if Discord ever
    rejects the components, the whole send fails with that HTTP reason rather
    than silently dropping them, so it surfaces instead of hiding.
    """
    if not url:
        return {"ok": False, "reason": "no webhook URL configured"}
    if not validate_webhook_url(url):
        return {"ok": False, "reason": "invalid webhook URL format or non-Discord target"}
    payload = {}
    if embeds:
        payload["embeds"] = embeds
    if content:
        payload["content"] = content
    if components:
        payload["components"] = components
    if silent:
        payload["flags"] = SUPPRESS_NOTIFICATIONS_FLAG

    files = {}
    for i, (name, data) in enumerate(file_attachments or []):
        files[f"files[{i}]"] = (name, data, "image/png")

    for attempt in range(_RETRY_MAX + 1):
        try:
            if files:
                resp = requests.post(
                    url, data={"payload_json": json.dumps(payload)}, files=files,
                    headers={"User-Agent": USER_AGENT}, timeout=15)
            else:
                resp = requests.post(
                    url, json=payload, headers={"User-Agent": USER_AGENT}, timeout=15)
        except requests.RequestException as exc:
            wait = _retry_wait_for_exception(attempt)
            if wait is None:
                return {"ok": False, "reason": str(exc)}
            time.sleep(wait)
            continue
        if 200 <= resp.status_code < 300:
            return {"ok": True, "reason": ""}
        wait = _retry_wait_for_status(resp, resp.status_code, attempt)
        if wait is not None:
            time.sleep(wait)
            continue
        return {"ok": False, "reason": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    return {"ok": False, "reason": "gave up after retries"}
