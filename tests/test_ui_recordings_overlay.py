"""Накладка «Записи» (F9) — порядок действий на кнопке «Начать запись».

Порядок здесь не косметика, а условие работоспособности. Запись идёт только
пока окно Roblox видно и оно в фокусе (core/replay.py, game_active). Если
включить рекордер, оставив список на экране, запись честно встанет в
ожидание — и человек получит пустой файл, нажав всё правильно. Поэтому
сначала накладка уходит и экран возвращается к игре, и только потом
включается запись.

Проверяется настоящий код из ui/app.js — функция вынимается из файла по
балансу скобок, как в tests/test_ui_js.py.
"""
import json
import os
import shutil
import subprocess
import textwrap

import pytest

APP_JS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "app.js")

pytestmark = pytest.mark.skipif(shutil.which("node") is None,
                                reason="node is not installed; ui/app.js behaviour tests need it")

_EXTRACT = """
const fs = require('fs');
const src = fs.readFileSync(process.env.APP_JS, 'utf8');
function extract(name) {
  const plain = src.indexOf('function ' + name + '(');
  const asy = src.indexOf('async function ' + name + '(');
  const s = asy !== -1 && (plain === -1 || asy < plain) ? asy : plain;
  if (s === -1) throw new Error(name + ' not found in ui/app.js');
  let d = 0, i = src.indexOf('{', s);
  for (; i < src.length; i++) {
    if (src[i] === '{') d++;
    else if (src[i] === '}' && --d === 0) return src.slice(s, i + 1);
  }
  throw new Error('unbalanced braces in ' + name);
}
"""


def run_js(body, tmp_path):
    script = tmp_path / "t.js"
    script.write_text(_EXTRACT + textwrap.dedent(body), encoding="utf-8")
    env = {**os.environ, "APP_JS": APP_JS}
    proc = subprocess.run(["node", str(script)], capture_output=True, text=True,
                          encoding="utf-8", env=env, timeout=60)
    assert proc.returncode == 0, f"node failed:\n{proc.stdout}\n{proc.stderr}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


# Общая обвязка: журнал вызовов в порядке их совершения. Всё, до чего
# функция дотягивается наружу, здесь подменено заглушкой, которая только
# отмечается в этом журнале.
_WORLD = """
const trace = [];
let recOverlayOpen = true;
let recOverlayStartedRecording = false;
const nameField = { value: NAME, style: {} };
function getEl(id) { return id === 'rec-ov-name' ? nameField : null; }
global.document = { getElementById: getEl };
function closeRecordingsOverlay() { trace.push('close'); recOverlayOpen = false; }
async function openRecordingsOverlay() { trace.push('reopen'); recOverlayOpen = true; }
function switchScreen(name) { trace.push('screen:' + name); }
function addLog(m) { trace.push('log'); }
async function refreshRecOverlay() { trace.push('refresh'); }
const pywebview = { api: {
  replay_recording_status: async () => { trace.push('status'); return STATUS; },
  replay_start_recording: async (name) => {
    trace.push('start:' + JSON.stringify(name));
    return START;
  },
  replay_stop_recording: async (name) => { trace.push('stop'); return { ok: true }; },
} };
"""


def _run(tmp_path, name="'Забег на боссе'", status="{ recording: false }", start="{ ok: true }"):
    return run_js(_WORLD.replace("NAME", name).replace("STATUS", status).replace("START", start) + """
        eval(extract('recOverlayToggleRecording'));
        (async () => {
          await recOverlayToggleRecording();
          console.log(JSON.stringify({
            trace, started: recOverlayStartedRecording,
            open: recOverlayOpen, field: nameField.value,
          }));
        })();
    """, tmp_path)


def test_the_list_steps_aside_before_the_recorder_starts(tmp_path):
    out = _run(tmp_path)
    assert out["trace"] == ["status", "close", "screen:dashboard", "start:\"Забег на боссе\""], \
        "накладка обязана уйти и экран вернуться к игре ДО включения записи"
    assert out["open"] is False
    assert out["started"] is True


def test_the_typed_name_travels_with_the_start(tmp_path):
    """Имя спрашивают до старта, потому что останавливают запись клавишей,
    сидя в игре, — тогда спросить будет уже негде (см. _pending_rec_name)."""
    out = _run(tmp_path, name="'  Рейд  '")
    assert 'start:"Рейд"' in out["trace"]
    assert out["field"] == "", "поле должно очиститься, а не подставить то же имя в следующий раз"


def test_an_unnamed_recording_starts_all_the_same(tmp_path):
    out = _run(tmp_path, name="''")
    assert 'start:""' in out["trace"]


def test_a_refused_start_brings_the_list_back(tmp_path):
    """Иначе отказ остался бы одной строкой в журнале при уехавшей панели —
    со стороны это «нажал запись, и ничего не произошло»."""
    out = _run(tmp_path, start="{ ok: false, reason: 'macro_running' }")
    assert out["trace"][-2:] == ["log", "reopen"]
    assert out["open"] is True
    assert out["started"] is False, "записи нет — и показывать список по её окончании нечего"


def test_while_recording_the_same_button_stops_it(tmp_path):
    out = _run(tmp_path, status="{ recording: true }")
    assert out["trace"] == ["status", "stop", "refresh"]
    assert out["open"] is True, "остановка не должна уводить накладку с экрана"
