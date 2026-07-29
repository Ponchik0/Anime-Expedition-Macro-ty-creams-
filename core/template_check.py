"""Проверка эталонов: что из картинок макрос сейчас видит на экране.

ЗАЧЕМ. Движок ищет кнопки по эталонным картинкам из Assets/ui. Если у тебя
игра рисуется хоть немного иначе, чем у того, кто эталон снимал, поиск
промахивается — и макрос встаёт. Уже дважды так и было: exp_enter_matchmaking
(счёт 0.756 при пороге 0.90) и repeat_stage.

Беда в том, что узнаёшь об этом ночью и постфактум. Здесь можно узнать
заранее: открыл нужный экран игры, нажал кнопку — и видишь список, что
находится уверенно, что на грани, а чего нет вообще.

БЕЗОПАСНОСТЬ. Модуль ТОЛЬКО ЧИТАЕТ: один снимок окна и сравнение картинок
в памяти. Ни одного клика, ни одного нажатия, ничего не пишется в
настройки. Запускать можно прямо во время работы макроса — он этого даже
не заметит.

ЧТО ЗНАЧАТ ЦИФРЫ. Счёт — совпадение от 0 до 1. Порог движка 0.90.
    >= 0.90  найдено   — макрос эту кнопку увидит
    0.75..0.90 на грани — сегодня повезло, завтра нет. Это и есть мины:
                          картинка почти совпадает, но порога не берёт
    < 0.75   нет        — либо кнопки сейчас нет на экране (нормально:
                          на одном экране видна лишь часть), либо эталон
                          не подходит совсем
"""
from __future__ import annotations

import os

from core import vision

# Ниже этого даже не упоминаем: кнопки просто нет на текущем экране, и
# перечислять полсотни таких строк — только мешать читать.
QUIET_BELOW = 0.55
# Полоса «почти совпало, но порога не берёт» — ровно те случаи, ради
# которых всё и затевалось.
RISK_LOW = 0.75


def list_names(template_dir: str = None) -> list:
    """Все имена, по которым движок умеет искать (папка на имя)."""
    root = template_dir or vision.UI_ASSETS_DIR
    if not os.path.isdir(root):
        return []
    out = []
    for entry in sorted(os.listdir(root)):
        full = os.path.join(root, entry)
        if os.path.isdir(full):
            if any(f.lower().endswith(".png") for f in os.listdir(full)):
                out.append(entry)
        elif entry.lower().endswith(".png"):
            out.append(os.path.splitext(entry)[0])
    return out


def check(hwnd: int, template_dir: str = None) -> dict:
    """Один снимок окна и прогон по нему всех эталонов.

    Снимок делается РОВНО ОДИН и переиспользуется для всех имён: иначе
    полсотни отдельных захватов заняли бы секунды и картинка успела бы
    измениться между ними — половина результатов относилась бы к разным
    кадрам.
    """
    if not hwnd:
        return {"ok": False, "reason": "no_window"}
    try:
        shot = vision.capture_game_gray(hwnd)
    except Exception as exc:
        return {"ok": False, "reason": f"capture_failed: {exc}"}
    if shot is None or getattr(shot, "size", 0) == 0:
        return {"ok": False, "reason": "empty_capture"}

    found, risky, missing = [], [], []
    for name in list_names(template_dir):
        score = 0.0
        try:
            # Порог 0 — нам нужен САМ счёт, а не ответ «да/нет»: значение
            # 0.86 при пороге 0.90 и есть та мина, которую мы ищем.
            hit = vision.find_in_gray_multiscale(
                shot, name, template_dir or vision.UI_ASSETS_DIR, threshold=0.0)
            if hit:
                score = float(hit.get("score") or 0.0)
        except vision.TemplateNotFound:
            continue
        except Exception:
            continue

        row = {"name": name, "score": round(score, 3)}
        if score >= vision.DEFAULT_THRESHOLD:
            found.append(row)
        elif score >= RISK_LOW:
            risky.append(row)
        elif score >= QUIET_BELOW:
            missing.append(row)

    found.sort(key=lambda r: -r["score"])
    risky.sort(key=lambda r: -r["score"])
    missing.sort(key=lambda r: -r["score"])
    return {
        "ok": True,
        "threshold": vision.DEFAULT_THRESHOLD,
        "found": found,
        "risky": risky,
        "missing": missing,
        "total": len(list_names(template_dir)),
    }


def summary(res: dict) -> str:
    """Короткий человеческий отчёт для журнала."""
    if not res.get("ok"):
        return {
            "no_window": "Окно Roblox не найдено.",
            "empty_capture": "Не удалось снять кадр окна.",
        }.get(res.get("reason"), f"Проверка не удалась: {res.get('reason')}")

    lines = [f"Проверка эталонов: найдено {len(res['found'])}, "
             f"на грани {len(res['risky'])}, всего имён {res['total']}."]
    if res["risky"]:
        lines.append("НА ГРАНИ — эти подведут в любой момент "
                     f"(порог {res['threshold']}):")
        for r in res["risky"]:
            lines.append(f"    {r['name']} — {r['score']}  ← пересними через F6")
    else:
        lines.append("На грани ничего нет — с этого экрана всё чисто.")
    if res["found"]:
        names = ", ".join(r["name"] for r in res["found"][:8])
        lines.append(f"Уверенно видно: {names}"
                     + (" и другие" if len(res["found"]) > 8 else ""))
    return "\n".join(lines)
