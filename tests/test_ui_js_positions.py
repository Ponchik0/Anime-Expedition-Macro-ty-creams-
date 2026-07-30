"""Снимок по умолчанию для режима — сторона интерфейса (ui/app.js через node).

Стенд взят из tests/test_ui_js.py: каждая проверка вынимает НАСТОЯЩУЮ функцию
из ui/app.js по балансу скобок и запускает её. Ничего не переписано заново —
поменяется app.js, поменяется и то, что здесь проверяется.

Что вообще решается. Готовых карт в поставке нет: клик по чужому кадру
промахивается, ракурс камеры у каждого свой. Значит точный путь один —
«Снимок из игры», и раньше его приходилось повторять на КАЖДУЮ точку. Теперь
кадр сохраняется под режим и подставляется сам.

Откуда берётся режим: сценарий сам по себе к режиму НЕ привязан — в Macro
Manager у него только имя и блоки. Зато задачи ссылаются на сценарий по имени,
и режим есть у них, поэтому режим выводится из очереди задач. Неоднозначно или
сценарий ещё нигде не используется — берётся прошлый выбор, а его всегда можно
поменять селектором в окне.
"""
import json
import shutil

import pytest

from tests.test_ui_js import run_js

# Своя отметка, а не унаследованная: pytestmark из test_ui_js.py на этот файл
# не распространяется, и без неё без node тесты падали бы вместо пропуска.
pytestmark = pytest.mark.skipif(shutil.which("node") is None,
                                reason="node is not installed; ui/app.js behaviour tests need it")

# Общие заглушки: список режимов, разбор сценариев задачи и «память» о
# прошлом выборе (в приложении это localStorage).
_STAND = """
global.TASK_DATA = { story: {label:'Story'}, raid: {label:'Raid'},
                     expedition: {label:'Expedition'}, event: {label:'Event'} };
global.taskMacroNames = t => [t.macro, t.act4_macro].filter(Boolean);
let stored = null;
global.getRememberedPlaceUnitMode = () => stored || '';
global.rememberPlaceUnitMode = m => { stored = m; };
"""


def _resolve_mode(tmp_path, template_name, tasks, remembered=None):
    body = _STAND + """
    global.taskCards = %s;
    stored = %s;
    global.document = { getElementById: id =>
      id === 'template-name' ? { value: %s } : null };
    eval(extract('resolvePlaceUnitMode'));
    console.log(JSON.stringify({ mode: resolvePlaceUnitMode() }));
    """ % (json.dumps(tasks), json.dumps(remembered), json.dumps(template_name))
    return run_js(body, tmp_path)["mode"]


# ── Откуда берётся режим ──────────────────────────────────────────────────

def test_mode_comes_from_the_task_that_uses_this_template(tmp_path):
    tasks = [{"mode": "raid", "macro": "raid"}, {"mode": "story", "macro": "other"}]
    assert _resolve_mode(tmp_path, "raid", tasks) == "raid"


def test_mode_reads_the_act4_macro_too(tmp_path):
    """act4_macro -- второй сценарий той же задачи (авто-Act 4 по дропу
    реликвии), и он тоже привязывает сценарий к режиму задачи."""
    tasks = [{"mode": "event", "macro": "main", "act4_macro": "act4"}]
    assert _resolve_mode(tmp_path, "act4", tasks) == "event"


def test_an_ambiguous_template_falls_back_to_the_remembered_mode(tmp_path):
    """Один сценарий в двух режимах -- угадывать нельзя: подставился бы кадр
    не того режима, и точка уехала бы."""
    tasks = [{"mode": "raid", "macro": "shared"}, {"mode": "story", "macro": "shared"}]
    assert _resolve_mode(tmp_path, "shared", tasks, remembered="expedition") == "expedition"


def test_an_unused_template_falls_back_to_the_remembered_mode(tmp_path):
    assert _resolve_mode(tmp_path, "brand-new", [], remembered="raid") == "raid"


def test_with_nothing_to_go_on_the_mode_is_story(tmp_path):
    assert _resolve_mode(tmp_path, "", []) == "story"


def test_a_stale_remembered_mode_is_ignored(tmp_path):
    """В памяти мог остаться режим, которого больше нет -- он не должен
    доехать до пути на диске (там белый список, см. core/maps.py)."""
    assert _resolve_mode(tmp_path, "", [], remembered="nonsense") == "story"


# ── Селектор режима ───────────────────────────────────────────────────────

def test_mode_select_lists_every_task_mode_and_marks_the_current_one(tmp_path):
    body = _STAND + r"""
    global.puState = { mode: 'expedition' };
    const el = { innerHTML: '' };
    global.document = { getElementById: id => (id === 'pu-mode' ? el : null) };
    eval(extract('renderPlaceUnitModeSelect'));
    renderPlaceUnitModeSelect();
    console.log(JSON.stringify({
      html: el.innerHTML,
      selected: (el.innerHTML.match(/value="(\w+)" selected/) || [])[1],
      count: (el.innerHTML.match(/<option/g) || []).length,
    }));
    """
    out = run_js(body, tmp_path)
    assert out["count"] == 4, out["html"]
    assert out["selected"] == "expedition"


def test_switching_mode_remembers_it_and_refreshes_the_note(tmp_path):
    body = _STAND + """
    global.puState = { mode: 'story' };
    let refreshed = 0;
    global.refreshDefaultSnapshotNote = async () => { refreshed++; };
    eval(extract('onPlaceUnitModeChange'));
    onPlaceUnitModeChange('raid').then(() => {
      console.log(JSON.stringify({ mode: puState.mode, stored, refreshed }));
    });
    """
    out = run_js(body, tmp_path)
    assert out["mode"] == "raid"
    assert out["stored"] == "raid", "выбор режима не запомнился до следующего открытия"
    assert out["refreshed"] == 1


# ── Подстановка снимка ────────────────────────────────────────────────────

def test_loading_the_default_snapshot_respects_the_stale_request_guard(tmp_path):
    """Окно могли закрыть и открыть заново, пока ответ шёл -- тогда кадр
    рисовать нельзя, иначе он ляжет поверх нового выбора (см. puRequestId)."""
    body = """
    global.puState = { mode: 'raid' };
    let drawn = 0;
    global.loadPlaceUnitImage = () => { drawn++; };
    global.pywebview = { api: { get_mode_map_snapshot: async () => ({ ok: true, data_uri: 'data:x' }) } };
    global.puRequestId = 7;
    eval(extract('loadDefaultModeSnapshot'));
    loadDefaultModeSnapshot(3).then(stale =>            // запрос устарел
      loadDefaultModeSnapshot(7).then(fresh =>          // запрос свежий
        console.log(JSON.stringify({ stale, fresh, drawn }))));
    """
    out = run_js(body, tmp_path)
    assert out["stale"] is False
    assert out["fresh"] is True
    assert out["drawn"] == 1, "устаревший ответ всё-таки нарисовали"


def test_a_missing_default_snapshot_is_not_an_error(tmp_path):
    """Снимка ещё нет -- окно просто открывается как раньше, сеткой карт."""
    body = """
    global.puState = { mode: 'raid' };
    global.loadPlaceUnitImage = () => { throw new Error('нечего рисовать'); };
    global.pywebview = { api: { get_mode_map_snapshot: async () => ({ ok: false, reason: 'not_found' }) } };
    global.puRequestId = 1;
    eval(extract('loadDefaultModeSnapshot'));
    loadDefaultModeSnapshot(1).then(ok => console.log(JSON.stringify({ ok })));
    """
    assert run_js(body, tmp_path)["ok"] is False


def test_a_backend_failure_does_not_break_opening_the_picker(tmp_path):
    """Мост в Python может отвалиться -- окно всё равно обязано открыться."""
    body = """
    global.puState = { mode: 'raid' };
    global.loadPlaceUnitImage = () => {};
    global.pywebview = { api: { get_mode_map_snapshot: async () => { throw new Error('boom'); } } };
    global.puRequestId = 1;
    eval(extract('loadDefaultModeSnapshot'));
    loadDefaultModeSnapshot(1).then(ok => console.log(JSON.stringify({ ok })));
    """
    assert run_js(body, tmp_path)["ok"] is False


# ── Сохранение ────────────────────────────────────────────────────────────

def test_saving_without_a_capture_says_so_instead_of_failing_silently(tmp_path):
    body = """
    global.puState = { mode: 'raid', categories: [] };
    const logs = [];
    global.addLog = m => logs.push(m);
    global.renderPlaceUnitCategoryTabs = () => {};
    global.refreshDefaultSnapshotNote = async () => {};
    global.pywebview = { api: { save_mode_map_snapshot: async () => ({ ok: false, reason: 'no_capture' }) } };
    eval(extract('saveDefaultModeSnapshot'));
    saveDefaultModeSnapshot().then(() => console.log(JSON.stringify({ logs })));
    """
    logs = run_js(body, tmp_path)["logs"]
    assert len(logs) == 1
    assert "no_capture" not in logs[0], "показали код ошибки вместо того, что делать"
    assert "Снимок из игры" in logs[0]


def test_saving_refreshes_the_category_tabs(tmp_path):
    """Снимок ложится в каталог карт обычной картинкой, поэтому вкладка режима
    могла появиться только что -- без перечитывания её не видно до
    переоткрытия окна."""
    body = """
    global.puState = { mode: 'raid', categories: [] };
    global.addLog = () => {};
    let tabsRendered = 0, noteRefreshed = 0;
    global.renderPlaceUnitCategoryTabs = () => { tabsRendered++; };
    global.refreshDefaultSnapshotNote = async () => { noteRefreshed++; };
    global.pywebview = { api: {
      save_mode_map_snapshot: async () => ({ ok: true, category: 'Raid', name: 'Snapshot' }),
      list_map_categories: async () => ['Raid'],
    } };
    eval(extract('saveDefaultModeSnapshot'));
    saveDefaultModeSnapshot().then(() => console.log(JSON.stringify({
      categories: puState.categories, tabsRendered, noteRefreshed })));
    """
    out = run_js(body, tmp_path)
    assert out["categories"] == ["Raid"]
    assert out["tabsRendered"] == 1
    assert out["noteRefreshed"] == 1


# ── Выбор координат из Настроек использует то же окно ─────────────────────

def test_the_default_snapshot_controls_hide_for_a_coordinate_pick(tmp_path):
    """Настройки > Отладка > Macro Coordinates открывают ЭТО ЖЕ окно, но там
    режима нет: иначе кнопка предлагала бы сохранить кадр «для режима Story»,
    когда речь про координату кнопки в интерфейсе."""
    body = """
    const els = {};
    for (const id of ['pu-default-controls', 'pu-save-default', 'pu-default-note']) els[id] = { style: {} };
    global.document = { getElementById: id => els[id] || null };
    eval(extract('setPlaceUnitDefaultControlsVisible'));
    setPlaceUnitDefaultControlsVisible(false);
    const hidden = Object.values(els).map(e => e.style.display);
    setPlaceUnitDefaultControlsVisible(true);
    console.log(JSON.stringify({ hidden, shown: Object.values(els).map(e => e.style.display) }));
    """
    out = run_js(body, tmp_path)
    assert out["hidden"] == ["none", "none", "none"]
    assert out["shown"] == ["", "", ""]
