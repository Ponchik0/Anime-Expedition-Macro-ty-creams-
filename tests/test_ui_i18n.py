"""Перевод интерфейса (`ui/i18n.js`) — через node, как и tests/test_ui_js.py.

Файл переводит интерфейс обходом DOM: английский текст в разметке, русский — из
словаря `RU`. Для строк с подставленными числами точного совпадения быть не
может, поэтому рядом со словарём живёт короткий список шаблонов `RU_PATTERNS`, и
обе ветки сходятся в одной функции `translate`.

До этого на i18n.js не было ни одного теста, а ошибка здесь тихая: строка просто
остаётся английской, и заметить это можно только глазами.
"""
import json
import os
import shutil
import subprocess
import textwrap

import pytest

I18N_JS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "i18n.js")

pytestmark = pytest.mark.skipif(shutil.which("node") is None,
                                reason="node is not installed; ui/i18n.js behaviour tests need it")

# i18n.js -- IIFE, поэтому целиком его не выполнить: он сразу полез бы в DOM.
# Вынимаем ровно то, что проверяем -- словарь, шаблоны и translate -- по
# балансу скобок, так же как tests/test_ui_js.py вынимает функции из app.js.
_EXTRACT = """
const fs = require('fs');
const src = fs.readFileSync(process.env.I18N_JS, 'utf8');

// Возвращает ТОЛЬКО литерал ({...} или [...]) после заданного начала.
// Присваиваем его в global явно: `eval('const X = ...')` объявляет X внутри
// самого eval и наружу его не отдаёт (в отличие от var), поэтому обёртка
// обязана быть выражением, а не объявлением.
function literal(startsWith, open, close) {
  const s = src.indexOf(startsWith);
  if (s === -1) throw new Error('not found: ' + startsWith);
  let d = 0, i = src.indexOf(open, s);
  const from = i;
  for (; i < src.length; i++) {
    if (src[i] === open) d++;
    else if (src[i] === close && --d === 0) return src.slice(from, i + 1);
  }
  throw new Error('unbalanced: ' + startsWith);
}
function fn(name) {
  const s = src.indexOf('function ' + name + '(');
  if (s === -1) throw new Error(name + ' not found in ui/i18n.js');
  let d = 0, i = src.indexOf('{', s);
  for (; i < src.length; i++) {
    if (src[i] === '{') d++;
    else if (src[i] === '}' && --d === 0) return src.slice(s, i + 1);
  }
  throw new Error('unbalanced braces in ' + name);
}
global.RU = eval('(' + literal('const RU = {', '{', '}') + ')');
global.RU_PATTERNS = eval('(' + literal('const RU_PATTERNS = [', '[', ']') + ')');
global.translate = eval('(' + fn('translate') + ')');
"""


def run_js(body, tmp_path):
    script = tmp_path / "t.js"
    script.write_text(_EXTRACT + textwrap.dedent(body), encoding="utf-8")
    env = {**os.environ, "I18N_JS": I18N_JS}
    proc = subprocess.run(["node", str(script)], capture_output=True, text=True,
                          encoding="utf-8", env=env, timeout=60)
    assert proc.returncode == 0, f"node failed:\n{proc.stdout}\n{proc.stderr}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


def _translate(tmp_path, *keys):
    body = """
    const keys = %s;
    console.log(JSON.stringify(keys.map(k => translate(k))));
    """ % json.dumps(list(keys))
    return run_js(body, tmp_path)


# ── Точное совпадение ─────────────────────────────────────────────────────

def test_a_known_string_is_translated(tmp_path):
    assert _translate(tmp_path, "Use Roblox Screen") == ["Снимок из игры"]


def test_an_unknown_string_stays_english(tmp_path):
    """null, а не пустая строка и не сам ключ: обход DOM по этому и решает,
    трогать узел или оставить как есть."""
    assert _translate(tmp_path, "Something Nobody Translated Yet") == [None]


def test_the_positions_default_snapshot_strings_are_translated(tmp_path):
    """Новые органы управления снимком по умолчанию. Интерфейс по умолчанию
    русский, так что пропущенный ключ здесь виден сразу."""
    out = _translate(tmp_path, "Mode", "Set as Default Snapshot",
                     "Save the frame on screen as this mode's default snapshot")
    assert all(out), out
    assert out[1] == "Сделать снимком по умолчанию"


# ── Шаблоны: строки с подставленными числами ──────────────────────────────

def test_download_progress_keeps_both_numbers(tmp_path):
    """Числа приходят из Python готовой строкой, словарём их не покрыть."""
    assert _translate(tmp_path, "Downloading update... 1.5 / 12.0 MB") == \
        ["Загружаю обновление... 1.5 / 12.0 МБ"]


def test_download_progress_without_a_total(tmp_path):
    assert _translate(tmp_path, "Downloading update... 3.2 MB") == \
        ["Загружаю обновление... 3.2 МБ"]


def test_patterns_are_anchored(tmp_path):
    """Шаблон обязан быть привязан к началу и концу строки -- иначе под него
    начнёт попадать что попало, и перевод сожрёт часть чужого текста."""
    out = _translate(tmp_path,
                     "Log: Downloading update... 3.2 MB (retry)",
                     "Downloading update... soon")
    assert out == [None, None]


def test_an_exact_hit_wins_over_the_patterns(tmp_path):
    """Порядок важен: сначала словарь, потом шаблоны."""
    body = """
    RU['Downloading update... 1.0 MB'] = 'ровно это';
    console.log(JSON.stringify([translate('Downloading update... 1.0 MB')]));
    """
    assert run_js(body, tmp_path) == ["ровно это"]


# ── Целостность словаря ───────────────────────────────────────────────────

def test_no_entry_translates_to_nothing(tmp_path):
    """Пустое значение стёрло бы подпись элемента интерфейса совсем -- это
    хуже, чем оставить её английской.

    Значение, РАВНОЕ ключу, здесь не считается ошибкой: часть слов в русском
    интерфейсе так и пишется (Webhook, Discord, Esc, Challenge), а часть ключей
    и так задана по-русски в разметке."""
    body = """
    const bad = Object.entries(RU).filter(([, v]) => !v).map(([k]) => k);
    console.log(JSON.stringify({ bad }));
    """
    assert run_js(body, tmp_path)["bad"] == []
