/* AE Macro · Glass concept: интерактивный статический прототип.
   Никакого бэкенда: все данные моковые, поведение имитирует
   реальный Api (start_macro, replay_*, set_setting) из main.py. */

"use strict";

const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
const scrollBehavior = reduceMotion ? "auto" : "smooth";

/* --------------------------------------------------------------- язык */
/* Переключение флагами US/RU. Журнал не переводится никогда: это вывод
   макроса (правило сборки). Не помеченные data-i18n экраны в демо
   остаются английскими, в приложении их переводит ui/i18n.js. */
let LANG = "ru";
try {
  const savedLang = localStorage.getItem("ui_lang") || localStorage.getItem("ae_lang");
  if (savedLang === "en" || savedLang === "ru") LANG = savedLang;
} catch (_) {}

const STR = {
  en: {
    nav_home: "Home", nav_tasks: "Tasks", nav_scenarios: "Scenarios",
    nav_recordings: "Recordings", nav_settings: "Settings",
    nav_resources: "Resources", nav_help: "Help",
    res_enable: "Enable between tasks",
    run_idle: "Idle", run_running: "Running", run_paused: "Paused",
    sub_idle: "Task queue is idle. Press Start to begin.",
    sub_running: "Summer Fishing · repeat 6 of 9999 · wave 12/30",
    sub_paused: "Macro paused. Resume or stop the queue.",
    btn_start: "Start", btn_pause: "Pause", btn_resume: "Resume", btn_stop: "Stop",
    hint_start: "start", hint_stop: "stop", hint_pause: "pause",
    runmode: "Run mode", mode_auto: "Auto",
    game_title: "Roblox docks here",
    game_sub: "Embedded game window · {res}",
    attach: "Attach window",
    foot_idle: "Queue idle", foot_play: "Playing: Summer Fishing", foot_hold: "Holding position",
    uptime: "uptime", toggle_game: "toggle game",
    live_idle: "Idle", live_live: "Live", live_paused: "Paused",
    sec_session: "Session", st_runs: "Runs", st_wins: "Wins", st_losses: "Losses", st_time: "Time",
    all_time: "All time", rate: "Rate",
    sec_log: "Process Log", sec_hist: "Run History", now: "now", no_runs_yet: "No runs yet",
    lang_note: "English UI. Other screens switch through ui/i18n.js in the real app",
    upd_checking: "Checking GitHub Releases",
    upd_latest: "v2.0.0 is the latest release",
    upd_title: "Update 2.0.0 available",
    upd_text: "Improvements and fixes · installs in background",
    upd_download: "Download", upd_downloading: "Downloading…", upd_done: "Installed · restart to apply",
    upd_done_short: "Installed · restart to apply",
    upd_installed: "Update installed",
    upd_restart: "restart to apply",
    bell_title: "System warnings", bell_empty: "No notifications. All clear.",
    dash_custom_title: "Customize Dashboard",
    dash_custom_tag: "Customize",
    dash_customize: "Customize",
    dash_custom_desc: "Drag cards to swap · Drag dividers to resize · Toggle cards below",
    chip_controls: "Controls",
    chip_stats: "Stats",
    chip_log: "Log",
    chip_history: "History",
    resizer_hint_height: "↕ Height",
    resizer_hint_width: "↔ Width",
    customize_layout: "Customize",
    drag_swap: "Drag to swap",
    card_hide: "Hide",
    card_restore: "Restore",
    btn_reset: "Reset",
    btn_done: "Done",
    card_game: "Roblox Game",
    card_controls: "Queue Controls",
    card_stats: "Session Stats",
    card_log: "Process Log",
    card_history: "Run History",
    hidden_cards_label: "Hidden:",
    btn_restore_all: "Restore all",
    dash_layout_sec: "Dashboard Layout",
    dash_layout_hint: "Drag cards to swap cells or hide them directly on the main screen",
    dash_open_custom: "Interactive Customizer",
    dash_reset_done: "Dashboard layout reset to default",
    dash_swap_done: "Swapped {a} and {b}",
    dash_card_hidden: "{name} hidden",
    dash_card_shown: "{name} restored",
    preview_swap_here: "Swap with: {name}",
    preview_swap_yield: "Moves to: {name}",
    btn_restore_stats: "Reset stats",
    stat_add_tile_title: "Add to Session",
    stat_tile_restored: "{name} restored",
    stat_all_active: "All stats active",
    stat_tile_hidden: "Stat tile hidden",
    stat_tiles_restored: "Stat tiles restored",
    stat_all_hidden: "All stats hidden · Click + or Reset stats",
    log_copied: "Process log copied to clipboard",
    log_cleared: "Process log cleared",
    hist_cleared: "Run history cleared",
    help_authors_title: "Authors & Community Links",
    author_fork_title: "Anime Expeditions Macro — Enhanced Edition",
    author_fork_desc: "Enhanced edition · Ponchik0 fork · Concept Glass UI, Replay mode, adaptive lobby and Discord webhooks",
    author_fork_btn: "GitHub Fork",
    author_creams_title: "Cweamy (Creams) — Original Macro Engine",
    author_creams_desc: "Lead developer of original macro for Anime Expeditions · Official Creams repository",
    author_creams_btn: "Creams Repo",
    author_guide_title: "YouTube Video Guide by Cweamy",
    author_guide_desc: "Official video guide for configuring and farming Anime Expeditions",
    author_guide_btn: "Watch Video",
    author_report_title: "Export Failure Report",
    author_report_desc: "Packages screenshots, log, and config into a .zip archive on Desktop for fast technical support",
    author_report_btn: "Export .zip",
    help_tab_faq: "FAQ & Troubleshooting",
    help_tab_authors: "Authors & Community",
    help_faq_title: "Help & Troubleshooting FAQ",
    tab_window: "Game Window",
    tab_automation: "Automation",
    tab_hotkeys: "Hotkeys",
    tab_appearance: "Appearance",
    tab_discord: "Discord",
    tab_updates: "Updates",
    tab_debug: "Debug",
    set_loss_streak_title: "Loss streak safety stop",
    set_loss_streak_desc: "Automatically stop macro after consecutive defeats to protect stats",
    set_focus_guard_title: "Focus guard",
    set_focus_guard_desc: "Pause replay/actions when Roblox window is not active or hidden",
    set_sound_alerts_title: "Sound notifications",
    set_sound_alerts_desc: "Play audio tone on match victory, defeat, or critical error",
    test_sound: "Test",
    set_auto_screenshot_title: "Auto-screenshot on failure",
    set_auto_screenshot_desc: "Automatically capture a debug screenshot when a run fails or desyncs",
    set_humanizer_title: "Input humanizer (Anti-cheat jitter)",
    set_humanizer_desc: "Add micro-delays between mouse clicks to simulate natural player timing",
    set_vip_reconnect_title: "Private server VIP link",
    set_vip_reconnect_desc: "Used to automatically rejoin your private server upon disconnect",
    set_font_scale_title: "Font scale",
    set_font_scale_desc: "Adjust text scale across the interface",
    set_glass_blur_title: "Glass blur level",
    set_glass_blur_desc: "Background backdrop filter intensity",
    font_compact: "Compact",
    font_standard: "Standard",
    font_large: "Large",
    blur_ultra: "Ultra (28px)",
    blur_soft: "Soft (14px)",
    blur_off: "Off",
    modal_crafting_sprites_title: "Choose Sprites to Craft",
    modal_fuel_paths_title: "Expedition Hub Walking Paths",
    modal_challenge_maps_title: "Story Map Macro Setup",
    craft_priority_item: "Priority crafting target",
    craft_saved: "Crafting sprites priority saved",
    custom_presets_title: "Layout Presets",
    custom_sizes_title: "Card Dimensions & Heights",
    custom_slots_title: "Card Placement & Visibility",
    preset_balanced: "Balanced (Default)",
    preset_balanced_desc: "Standard balanced view for 1080p+",
    preset_log_focus: "Log Focus",
    preset_log_focus_desc: "Expanded log width & height to monitor actions",
    preset_compact: "Compact",
    preset_compact_desc: "Tight card paddings & balanced heights",
    preset_fullscreen: "Fullscreen Pro",
    preset_fullscreen_desc: "Optimal space utilization on 2K / 4K monitors",
    lower_tier_height: "Bottom Tier Height (Logs & History)",
    lower_split_ratio: "Log vs History Width Split",
    stats_card_height: "Session Stats Height",
    card_density_title: "Card Density & Padding",
    card_density_desc: "Prevents cards from looking huge in fullscreen",
    roblox_static_note: "Roblox window is docked at 1152×756 to guarantee pixel-accurate macro recognition.",
    live_drag_mode: "Live Drag on Screen",
    slot_side_top: "Side Top",
    slot_side_bottom: "Side Bottom",
    slot_lower_left: "Bottom Left",
    slot_lower_right: "Bottom Right",
    card_expanded: "{name} expanded to full width",
    card_restored_width: "{name} width restored",
    // --- Scenarios screen ---
    btn_save: "Save", btn_new: "New", btn_test_run: "Test run",
    scen_prestart: "Pre Start", scen_prestart_sub: "setup",
    scen_battle: "Battle", scen_battle_sub: "combat",
    scen_loop_a: "Loop A", scen_loop_b: "Loop B", scen_loop_sub: "repeats",
    scen_guide_title: "How Scenarios Work (Execution Phases)",
    scen_guide_hide: "Hide",
    scen_guide_show: "Show Guide",
    scen_g1_title: "Pre Start (Initial Setup)",
    scen_g1_desc: "Runs ONCE when match starts before waves appear. Use for: walk path, hotbar selection, first fishing rod cast, or starter unit placements.",
    scen_g2_title: "Battle (Combat Flow)",
    scen_g2_desc: "Runs DURING the match. Use for: wave-triggered placements, unit upgrades, selling units, and detecting victory/defeat outcome screens.",
    scen_g3_title: "Loop A & B (Continuous Loops)",
    scen_g3_desc: "Runs REPEATEDLY alongside Battle throughout the entire game. Perfect for fishing (Loop A: cast + reel in), continuous clicking, or collecting orbs.",
    scen_prestart_hint: "Before round: walk, equip, initial actions",
    scen_battle_hint: "During battle: wave placements, upgrades, results",
    scen_loop_a_hint: "Main loop: continuous casting, clicks, catches",
    scen_loop_b_hint: "Secondary loop: parallel orb collection or skill spam",
    scen_step_comment: "Step Note / Comment",
    scen_step_comment_placeholder: "e.g.: Equip rod, place unit at wave 5, pull fish...",
    scen_palette: "Palette",
    scen_palette_hint: "Click to add to active phase, or drag directly into any column",
    scen_place_unit: "Place Unit", scen_upgrade_unit: "Upgrade Unit",
    scen_auto_upgrade: "Auto Upgrade", scen_sell_unit: "Sell Unit",
    scen_target_priority: "Target Priority", scen_walk_path: "Walk Path",
    scen_walk: "Walk", scen_wait_ms: "Wait (ms)", scen_wait_wave: "Wait Wave",
    scen_leave_minute: "Leave Minute", scen_click: "Click", scen_drag: "Drag",
    scen_send_key: "Send Key", scen_record: "Record", scen_detect: "Detect",
    // --- Resources tabs ---
    res_tab_crafting: "Auto Crafting", res_tab_fuel: "Auto Fuel",
    res_tab_shop: "Auto Shop", res_tab_challenge: "Auto Challenge",
    // --- Recordings ---
    rec_library: "Library",
    // --- Resolution dropdown ---
    res_menu_title: "Game Resolution",
    res_std: "Standard",
    res_min: "Min (4:3)",
    res_laptop: "Laptop",
    res_max: "Max FHD",
    res_compact: "Compact",
    res_small: "Small",
    res_apply: "Apply",
    res_changed: "Game resolution set to {res}",
    res_range_hint: "1024×768 min · 1920×1080 max",
    res_clamped_hint: "Resolution adjusted to supported range (1024×768 — 1920×1080)",
    // --- Tasks queue ---
    task_reordered: "Task queue reordered",
    task_added: "New task added to queue",
    // --- Run kinds ---
    "Summer Fishing": "Summer Fishing",
    "Event Infinite": "Event Infinite",
    "Story Infinite": "Story Infinite",
    "Portals": "Portals",
    // --- Live metadata & Window settings ---
    game_resolution: "Game Resolution",
    lbl_task: "Task",
    lbl_action: "Action",
    lbl_repeat: "Repeat",
    lbl_map: "Map",
    lbl_mode: "Mode",
    lbl_stage: "Stage",
    lbl_difficulty: "Difficulty",
    lbl_last_run: "Last Run",
    set_roblox_win_title: "Select Roblox Window",
    set_roblox_win_desc: "Target process to dock and control",
    set_attach_title: "Window Attachment",
    set_attach_desc: "Dock or detach the live Roblox window",
    set_force_rejoin_title: "Force Rejoin Lobby",
    set_force_rejoin_desc: "Relaunch Roblox straight back into the lobby via deep-link",
    rejoin_now: "Rejoin Now",
    set_flicker_free_title: "Flicker-Free Capture",
    set_flicker_free_desc: "Read game window directly to prevent display white flashing",
    set_wgc_title: "Hardware Capture Fix (WGC)",
    set_wgc_desc: "Windows.Graphics.Capture for setups where game captures black",
    detach: "Detach",
    streak_wins: "Wins Streak",
    streak_best: "Best:",
    hud_streak: "Streak",
    hud_record: "Record",
    hud_challenge: "Challenge",
    task_queue_title: "Task Queue",
    task_queue_ready: "Task queue ready · Press Start (F1)",
    card_macro_engine: "Macro Engine",
    auto_restart_loop: "Auto-Restart",
    vip_rejoin: "VIP Rejoin",
    skip_task: "Skip",
    lbl_queue_preview: "Upcoming Queue",
    manage_tasks: "Manage",
    queue_empty_presets: "Queue empty · Quick presets:",
    hk_auto_restart: "Auto-Restart Loop",
    hk_vip_rejoin: "VIP Lobby Rejoin",
    auto_restart_enabled: "Auto-Restart Loop enabled",
    auto_restart_disabled: "Auto-Restart Loop disabled",
    vip_rejoin_triggered: "Triggering VIP Lobby Rejoin...",
    sec_automations: "Active Automations",
    auto_shop: "Auto-Shop",
    bounty: "Bounty",
    crafting: "Crafting",
    fuel: "Fuel",
    // --- Additional elements & toolbar ---
    sub_streak: "Streak",
    sub_meta: "Task Details",
    sub_queue: "Upcoming Queue",
    sub_automations: "Automations",
    task_queue: "Task Queue",
    import: "Import",
    export: "Export",
    clear: "Clear",
    btn_add_task: "+ Add Task",
    task_builder: "Task Builder",
    reset: "Reset",
    btn_cancel: "Cancel",
    btn_close: "Close",
    drawer_recordings_title: "Recordings",
    drawer_recordings_sub: "Select or play recorded routes · F10",
    ph_search_recordings: "Search recordings...",
    lbl_macro_start_mode: "Start button mode",
    desc_start_mode_replay: "Start replays selected recording",
    desc_start_mode_auto: "Start runs automated task queue",
    hint_drawer_esc: "Esc or F10 to close",
    btn_select: "Select",
    btn_selected: "Active",
    btn_record: "Record",
    tt_start_rec: "Start Recording (F8)",
    tt_task_presets: "Saved task presets on this machine",
    opt_no_presets: "No saved presets",
    btn_load: "Load",
    tt_load_preset: "Load selected preset",
    ph_preset_name: "Preset name",
    tt_preset_name: "Preset name",
    tt_save_preset: "Save current queue as preset",
    tt_del_preset: "Delete preset",
    tt_folder_presets: "Open presets folder in Explorer",
    tt_import_tasks: "Import tasks from JSON",
    tt_export_tasks: "Export tasks to JSON",
    tt_clear_tasks: "Clear all tasks",
    sub_select_task: "Select a task on the left to edit",
    btn_clone: "Clone",
    tt_clone_task: "Clone this task",
    btn_delete: "Delete",
    tt_del_task: "Delete this task",
    empty_task_builder_desc: "Select a task on the left to configure it, or click \"+ Add Task\" to create one.",
    ph_scen_name: "Scenario name",
    tt_scen_name: "Scenario name",
    tt_select_scen: "Select scenario",
    tt_save_scen: "Save scenario",
    tt_new_scen: "New scenario",
    tt_del_scen: "Delete loaded scenario",
    tt_folder_scen: "Open templates folder in Explorer",
    tt_validate_scen: "Validate all blocks in scenario",
    tt_toggle_guide: "Collapse / expand scenario guide",
    modal_edit_block: "Edit Block",
    modal_insert_action: "Insert Action",
    modal_insert_sub: "Choose an action to insert at this step",
    modal_save_path_title: "Save Recorded Walk Path",
    lbl_save_path_name: "Name for this WASD route:",
    ph_save_path: "e.g. My Spot or East Town",
    btn_discard: "Discard",
    btn_save_path: "Save Path",
    rec_popout_title: "WASD Recording",
    rec_popout_text: "Move in game · 1.8s idle saves path",
    app_closed_title: "Panel closed",
    app_closed_text: "Macro stopped. Click below to reopen.",
    btn_reopen: "Reopen panel",
    restore_pill: "AE Macro · minimized",
    res_crafting_title: "Auto Crafting",
    res_crafting_enable: "Enable Auto Crafting",
    res_crafting_enable_desc: "After every N qualifying wins, leaves to the Crafting area, crafts chosen sprites, then resumes farming",
    res_craft_every: "Craft every",
    res_craft_every_desc: "Wins that count: Mastery (Story) and Challenge victories",
    res_sprites_craft: "Sprites to Craft",
    res_sprites_desc: "Priority list: Trait Crystal ×5, Mana Flask ×10, Cursed Boba ×2",
    btn_choose_sprites: "Choose sprites",
    res_reset_progress: "Reset Progress",
    res_reset_progress_desc: "Set the win counter back to 0",
    btn_reset_counter: "Reset counter",
    res_fuel_title: "Auto Fuel",
    res_fuel_enable: "Enable Auto Fuel",
    res_fuel_enable_desc: "Refills fuel at safe Task Queue boundaries",
    res_refill_interval: "Refill interval",
    res_refill_desc: "Auto refills after 8 hours or numeric fuel duration",
    btn_auto_8h: "Auto (8h)",
    res_resource_drill: "Resource Drill",
    res_gold_mine: "Gold Mine",
    res_walking_paths: "Walking Paths",
    res_paths_desc: "Record and assign the three routes used inside Expedition Hub",
    btn_configure_paths: "Configure paths",
    res_reset_fuel_timer: "Reset Fuel Timer",
    res_reset_fuel_desc: "Makes every enabled resource ready for an immediate refill",
    btn_reset_timer: "Reset timer",
    res_shop_title: "Auto Shop",
    res_shop_enable: "Enable Auto Shop",
    res_shop_enable_desc: "Runs enabled shops at safe task boundaries, daily UTC reset",
    res_gold_shop_order: "Gold Shop purchase order",
    res_gold_shop_desc: "Items are bought in priority order until sold out",
    res_challenge_title: "Auto Challenge",
    res_daily_challenge: "Enable Daily Challenge",
    res_regular_challenge: "Enable Regular Challenge",
    res_challenge_mode: "Challenge Play Mode",
    res_story_map_setup: "Story Map Setup",
    res_stages_progress: "Stages 1-3 progress",
    res_reset_challenge_status: "Reset Challenge Status",
    btn_reset_counters: "Reset counters",
    btn_story_maps: "Story maps",
    set_discord_connected: "Webhook connected",
    set_discord_url: "Webhook URL",
    set_mention_id: "Mention ID",
    set_notifications: "Result notifications",
    set_pings: "Progress pings",
    set_reports: "Status reports",
    btn_send_status_now: "Send status now",
    btn_test_hook: "Send test",
    set_theme: "Theme",
    set_density: "Density",
    set_corners: "Corners",
    set_ambient_motion: "Ambient motion",
    opt_default: "Default",
    opt_soft: "Soft",
    opt_full: "Full",
    opt_calm: "Calm",
    opt_off: "Off",
    set_diag_screenshot: "Save screenshot",
    set_diag_screenshot_desc: "Full window capture into the debug folder",
    set_diag_system: "System Diagnostics",
    set_diag_system_desc: "Run comprehensive subsystem health check",
    btn_health_check: "Run Health Check",
    set_diag_templates: "Check Templates",
    set_diag_templates_desc: "Verify vision reference templates and coordinates",
    btn_check_templates: "Check Templates",
    set_diag_assets: "Assets folder",
    set_diag_assets_desc: "Reference images used by vision search",
    btn_open: "Open",
    set_diag_report: "Export failure report",
    set_diag_report_desc: "Bundle logs and screenshots for bug report",
    btn_export_zip: "Export ZIP",
    rec_req_focus: "Require game in focus",
    rec_req_focus_desc: "Stops playback immediately when Roblox loses window focus",
    rec_start_delay: "Start delay",
    rec_start_delay_desc: "Pause after starting before executing recorded keys/clicks",
    rec_loops: "Loops",
    rec_loops_desc: "How many times to loop this sequence (0 = infinite)",
    rec_empty_note: "A recording replays tick for tick. The macro needs no setup: no templates, no coordinates.",
    tt_export_bundle: "Export bundle",
    tt_import_bundle: "Import bundle",
    tt_open_folder: "Open folder",
    ph_search_help: "Search questions (e.g., Act 3, virus, camera, OCR, updater)...",
    tt_clear_search: "Clear search",
    // --- Newly localized keys ---
    hk_macro_start: "Macro start",
    hk_macro_stop: "Macro stop",
    hk_macro_pause: "Macro pause",
    hk_debug_screenshot: "Debug screenshot",
    hk_toggle_game: "Toggle game",
    hk_toggle_record: "Toggle record",
    hk_open_replay: "Open replay",
    hk_toggle_walk_record: "WASD Walk Recording",
    hk_note: "Click a key, then press the new combination. <kbd>Esc</kbd> cancels.",
    hk_reset_default: "Reset hotkeys to default",
    set_theme_desc: "Glass atmosphere of the panel",
    set_density_desc: "Row spacing across the panel",
    set_corners_desc: "Card and control rounding",
    set_ambient_motion_desc: "Background drift and live indicators",
    set_auto_update: "Install automatically",
    set_auto_update_desc: "Download and apply releases in background",
    btn_check_upd: "Check",
    lbl_version: "Version",
    upd_state_ok: "Up to date",
    rec_status_not_rec: "Not recording",
    rec_hint_hotkey: "Recording runs entirely from the hotkey. Play one match by hand.",
    rec_settings_title: "Recorder Settings",
    rec_note_f8: "Press <kbd>F8</kbd> anywhere to start or stop recording. The macro records clicks, keys, and hold timings tick-for-tick with zero game injection.",
    res_daily_challenge_desc: "Runs the once-per-game-day Daily Challenge first (resets 00:00 UTC)",
    res_regular_challenge_desc: "Runs every ready stage once before the Task Queue on Start",
    res_challenge_mode_desc: "Solo or Matchmaking for Daily and Regular stages",
    res_story_map_desc: "Assign a Macro Operation to each Story map the challenge can land on",
    res_stages_progress_desc: "Per-stage limits, cooldowns, and completed counts",
    res_reset_challenge_desc: "Clears Daily completion, counts, and cooldowns",
  },
  ru: {
    nav_home: "Панель", nav_tasks: "Задачи", nav_scenarios: "Сценарии",
    nav_recordings: "Запись", nav_settings: "Настройки",
    nav_resources: "Ресурсы", nav_help: "Справка",
    res_enable: "Включать между задачами",
    run_idle: "Ожидание", run_running: "Работает", run_paused: "Пауза",
    sub_idle: "Очередь задач простаивает. Нажмите Старт.",
    sub_running: "Summer Fishing · повтор 6 из 9999 · волна 12/30",
    sub_paused: "Макрос на паузе. Продолжите или остановите очередь.",
    btn_start: "Старт", btn_pause: "Пауза", btn_resume: "Продолжить", btn_stop: "Стоп",
    hint_start: "старт", hint_stop: "стоп", hint_pause: "пауза",
    runmode: "Режим запуска", mode_auto: "Авто",
    game_title: "Здесь встраивается Roblox",
    game_sub: "Встроенное окно игры · {res}",
    attach: "Прикрепить окно",
    foot_idle: "Очередь простаивает", foot_play: "Играет: Summer Fishing", foot_hold: "Удержание позиции",
    uptime: "время", toggle_game: "показать игру",
    live_idle: "Ожидание", live_live: "В эфире", live_paused: "Пауза",
    sec_session: "Сессия", st_runs: "Забеги", st_wins: "Победы", st_losses: "Поражения", st_time: "Время",
    all_time: "За всё время", rate: "Темп",
    sec_log: "Журнал", sec_hist: "История забегов", now: "только что", no_runs_yet: "Забегов пока нет",
    lang_note: "Английский интерфейс. Остальные экраны переключает ui/i18n.js в приложении",
    upd_checking: "Проверяю GitHub Releases",
    upd_latest: "v2.0.0 — последняя версия",
    upd_title: "Доступно обновление 2.0.0",
    upd_text: "Улучшения и исправления · ставится в фоне",
    upd_download: "Скачать", upd_downloading: "Скачиваю…", upd_done: "Установлено · перезапустите",
    upd_done_short: "Установлено · перезапустите",
    upd_installed: "Обновление установлено",
    upd_restart: "перезапустите, чтобы применить",
    bell_title: "Системные предупреждения", bell_empty: "Уведомлений нет. Всё чисто.",
    dash_custom_title: "Настройка дашборда",
    dash_custom_tag: "Кастомизация",
    dash_customize: "Кастомизация",
    dash_custom_desc: "Перетаскивайте карточки для обмена · Тяните границы для изменения размера",
    chip_controls: "Очередь",
    chip_stats: "Статистика",
    chip_log: "Журнал",
    chip_history: "История",
    resizer_hint_height: "↕ Высота",
    resizer_hint_width: "↔ Ширина",
    customize_layout: "Настроить",
    drag_swap: "Перетащить",
    card_hide: "Скрыть",
    card_restore: "Вернуть",
    btn_reset: "Сбросить",
    btn_done: "Готово",
    card_game: "Окно игры Roblox",
    card_controls: "Управление очередью",
    card_stats: "Статистика сессии",
    card_log: "Журнал процесса",
    card_history: "История забегов",
    hidden_cards_label: "Скрыто:",
    btn_restore_all: "Вернуть все",
    dash_layout_sec: "Раскладка дашборда",
    dash_layout_hint: "Перетаскивайте карточки для обмена или скрывайте их прямо на главном экране",
    dash_open_custom: "Интерактивная настройка",
    dash_reset_done: "Раскладка сброшена по умолчанию",
    dash_swap_done: "Карточки «{a}» и «{b}» поменялись местами",
    dash_card_hidden: "Карточка «{name}» скрыта",
    dash_card_shown: "Карточка «{name}» восстановлена",
    preview_swap_here: "Сюда встанет: {name}",
    preview_swap_yield: "Сюда перейдёт: {name}",
    btn_restore_stats: "Сбросить статистику",
    stat_add_tile_title: "Добавить в Session",
    stat_tile_restored: "Показатель «{name}» возвращён",
    stat_all_active: "Все показатели включены",
    stat_tile_hidden: "Показатель скрыт",
    stat_tiles_restored: "Показатели статистики восстановлены",
    stat_all_hidden: "Все показатели скрыты · Нажмите «+» или «Сбросить»",
    log_copied: "Журнал процесса скопирован в буфер",
    log_cleared: "Журнал процесса очищен",
    hist_cleared: "История забегов очищена",
    help_authors_title: "Авторы и сообщество",
    author_fork_title: "Anime Expeditions Macro — Расширенное издание",
    author_fork_desc: "Моё усовершенствование макроса · Форк Ponchik0 · Стеклянный интерфейс Glass UI, режим Повтора, адаптивное лобби и Discord вебхуки",
    author_fork_btn: "GitHub форк",
    author_creams_title: "Cweamy (Creams) — Создатель оригинального макроса",
    author_creams_desc: "Главный разработчик оригинального движка макроса для Anime Expeditions · Официальный репозиторий Creams",
    author_creams_btn: "Репозиторий Creams",
    author_guide_title: "Видео-руководство на YouTube от Cweamy",
    author_guide_desc: "Официальное обучающее видео по настройке и автофарму Anime Expeditions",
    author_guide_btn: "Смотреть видео",
    author_report_title: "Экспорт отчёта об ошибках",
    author_report_desc: "Сохраняет скриншоты, лог и конфиг в .zip архив на Рабочий стол для быстрой техподдержки",
    author_report_btn: "Экспорт .zip",
    help_tab_faq: "Частые вопросы и гайды",
    help_tab_authors: "Авторы и сообщество",
    help_faq_title: "Частые вопросы и решение проблем",
    tab_window: "Окно игры",
    tab_automation: "Автоматизация",
    tab_hotkeys: "Горячие клавиши",
    tab_appearance: "Внешний вид",
    tab_discord: "Дискорд",
    tab_updates: "Обновления",
    tab_debug: "Отладка",
    set_loss_streak_title: "Остановка при череде поражений",
    set_loss_streak_desc: "Автоматически останавливать макрос после нескольких поражений подряд для защиты статистики",
    set_focus_guard_title: "Контроль фокуса окна",
    set_focus_guard_desc: "Приостанавливать действия, когда окно Roblox свернуто или не в фокусе",
    set_sound_alerts_title: "Звуковые оповещения",
    set_sound_alerts_desc: "Воспроизводить звуковой сигнал при победе, поражении или ошибке",
    test_sound: "Тест",
    set_auto_screenshot_title: "Авто-скриншот при сбое",
    set_auto_screenshot_desc: "Автоматически сохранять скриншот окна при ошибке или поражении",
    set_humanizer_title: "Хуманизатор кликов (Анти-детект)",
    set_humanizer_desc: "Случайные микро-задержки между кликами для имитации движений человека",
    set_vip_reconnect_title: "Ссылка на VIP сервер",
    set_vip_reconnect_desc: "Используется для автоматического переподключения к приватному серверу",
    set_font_scale_title: "Масштаб шрифта",
    set_font_scale_desc: "Размер текста по всему интерфейсу",
    set_glass_blur_title: "Сила размытия стекла",
    set_glass_blur_desc: "Интенсивность блюра стеклянных панелей",
    font_compact: "Компактный",
    font_standard: "Стандартный",
    font_large: "Крупный",
    blur_ultra: "Ультра (28px)",
    blur_soft: "Мягкий (14px)",
    blur_off: "Отключен",
    modal_crafting_sprites_title: "Выбор спрайтов для авто-крафта",
    modal_fuel_paths_title: "Маршруты топлива в Хабе (Expedition Hub)",
    modal_challenge_maps_title: "Привязка макросов к картам испытаний",
    craft_priority_item: "Приоритетный предмет крафта",
    craft_saved: "Приоритеты авто-крафта сохранены",
    custom_presets_title: "Пресеты компоновки",
    custom_sizes_title: "Размеры и высота карточек",
    custom_slots_title: "Размещение и видимость карточек",
    preset_balanced: "Сбалансированный",
    preset_balanced_desc: "Стандартный вид для большинства экранов",
    preset_log_focus: "Фокус на логах",
    preset_log_focus_desc: "Увеличенный лог по ширине и высоте",
    preset_compact: "Компактный",
    preset_compact_desc: "Уменьшенные отступы, не растягивается",
    preset_fullscreen: "Полноэкранный Pro",
    preset_fullscreen_desc: "Оптимально для больших мониторов",
    lower_tier_height: "Высота нижнего яруса (Лог и История)",
    lower_split_ratio: "Ширина лога и истории (Разделение)",
    stats_card_height: "Высота статистики сессии",
    card_density_title: "Плотность карточек (Отступы)",
    card_density_desc: "Предотвращает раздувание карточек на весь экран",
    roblox_static_note: "Окно Roblox зафиксировано в размере 1152×756 для точного распознавания пикселей макросом.",
    live_drag_mode: "Перетащить на экране",
    slot_side_top: "Боковой верх",
    slot_side_bottom: "Боковой низ",
    slot_lower_left: "Нижний левый",
    slot_lower_right: "Нижний правый",
    card_expanded: "Карточка «{name}» развернута на всю ширину",
    card_restored_width: "Ширина карточки «{name}» восстановлена",
    // --- Экран Сценариев ---
    btn_save: "Сохранить", btn_new: "Новый", btn_test_run: "Тест-прогон",
    scen_prestart: "Pre Start", scen_prestart_sub: "подготовка",
    scen_battle: "Бой", scen_battle_sub: "сражение",
    scen_loop_a: "Цикл A", scen_loop_b: "Цикл B", scen_loop_sub: "повторы",
    scen_guide_title: "Как работают сценарии (фазы выполнения)",
    scen_guide_hide: "Скрыть",
    scen_guide_show: "Справка",
    scen_g1_title: "Pre Start (Подготовка)",
    scen_g1_desc: "Выполняется 1 раз при входе на карту до старта волн. Сюда ставят: маршрут ходьбы, выбор слота хотбара, первый заброс удочки или расстановку стартовых юнитов.",
    scen_g2_title: "Battle (Ход боя)",
    scen_g2_desc: "Выполняется по ходу матча. Сюда ставят: расстановку юнитов на определенных волнах, прокачку, продажу и проверку победы/поражения (Detect Game_results).",
    scen_g3_title: "Loop A & B (Параллельные циклы)",
    scen_g3_desc: "Крутятся по кругу непрерывно на протяжении всего матча. Идеально для рыбалки (Loop A: клик в воду + клик подсечь), автокликов или сбора сфер/скиллов.",
    scen_prestart_hint: "До старта: ходьба, экипировка, стартовые клики",
    scen_battle_hint: "Во время боя: волны, прокачка, исход матча",
    scen_loop_a_hint: "Главный цикл: заброс удочки, автоклики, сбор",
    scen_loop_b_hint: "Второй цикл: параллельный сбор или спам навыков",
    scen_step_comment: "Заметка к действию (для чего этот шаг)",
    scen_step_comment_placeholder: "например: Достать удочку, поставить Наруто на волне 5...",
    scen_palette: "Палитра",
    scen_palette_hint: "Нажми, чтобы добавить в активную фазу, или перетащи в любую колонку",
    scen_place_unit: "Поставить юнита", scen_upgrade_unit: "Прокачать юнита",
    scen_auto_upgrade: "Авто-прокачка", scen_sell_unit: "Продать юнита",
    scen_target_priority: "Приоритет цели", scen_walk_path: "Путь ходьбы",
    scen_walk: "Ходьба", scen_wait_ms: "Ждать (мс)", scen_wait_wave: "Ждать волну",
    scen_leave_minute: "Уйти в минуту", scen_click: "Клик", scen_drag: "Перетащить",
    scen_send_key: "Нажать клавишу", scen_record: "Запись", scen_detect: "Обнаружить",
    // --- Вкладки Ресурсов ---
    res_tab_crafting: "Авто-крафт", res_tab_fuel: "Авто-топливо",
    res_tab_shop: "Авто-магазин", res_tab_challenge: "Авто-Challenge",
    // --- Записи ---
    rec_library: "Библиотека",
    // --- Меню разрешения ---
    res_menu_title: "Разрешение игры",
    res_std: "Стандартное",
    res_min: "Мин. (4:3)",
    res_laptop: "Ноутбук",
    res_max: "Макс. FHD",
    res_compact: "Компактное",
    res_small: "Маленькое",
    res_apply: "Применить",
    res_changed: "Разрешение игры: {res}",
    res_range_hint: "1024×768 мин · 1920×1080 макс",
    res_clamped_hint: "Разрешение скорректировано под допустимый диапазон (1024×768 — 1920×1080)",
    // --- Очередь задач ---
    task_reordered: "Порядок задач обновлён",
    task_added: "Новая задача добавлена в очередь",
    // --- Run kinds ---
    "Summer Fishing": "Рыбалка",
    "Event Infinite": "Event Infinite",
    "Story Infinite": "Story Infinite",
    "Portals": "Порталы",
    // --- Live metadata & Window settings ---
    game_resolution: "Разрешение игры",
    lbl_task: "Задача",
    lbl_action: "Действие",
    lbl_repeat: "Повтор",
    lbl_map: "Карта",
    lbl_mode: "Режим",
    lbl_stage: "Этап",
    lbl_difficulty: "Сложность",
    lbl_last_run: "Последний забег",
    set_roblox_win_title: "Выбор окна Roblox",
    set_roblox_win_desc: "Целевой процесс игры для захвата",
    set_attach_title: "Встраивание окна",
    set_attach_desc: "Привязать или отвязать активное окно Roblox",
    set_force_rejoin_title: "Принудительный перезаход",
    set_force_rejoin_desc: "Перезапуск Roblox с мгновенным заходом в лобби",
    rejoin_now: "Перезайти сейчас",
    set_flicker_free_title: "Захват без мерцания",
    set_flicker_free_desc: "Чтение окна напрямую через PrintWindow без белых вспышек",
    set_wgc_title: "Аппаратный захват (WGC)",
    set_wgc_desc: "Windows Graphics Capture для систем с чёрным экраном",
    detach: "Отвязать",
    streak_wins: "Серия побед",
    streak_best: "Рекорд:",
    hud_streak: "Серия",
    hud_record: "Рекорд",
    hud_challenge: "Челлендж",
    task_queue_title: "Очередь задач",
    task_queue_ready: "Очередь задач готова · Нажмите Старт (F1)",
    card_macro_engine: "Движок макроса",
    auto_restart_loop: "Авто-рестарт",
    vip_rejoin: "VIP Реджоин",
    skip_task: "Пропустить",
    lbl_queue_preview: "Очередь задач",
    manage_tasks: "Настроить",
    queue_empty_presets: "Очередь пуста · Быстрые шаблоны:",
    hk_auto_restart: "Авто-рестарт цикла",
    hk_vip_rejoin: "Перезаход в VIP лобби",
    auto_restart_enabled: "Авто-рестарт включен",
    auto_restart_disabled: "Авто-рестарт выключен",
    vip_rejoin_triggered: "Выполняется перезаход в VIP лобби...",
    sec_automations: "Фоновые сервисы",
    auto_shop: "Торговец",
    bounty: "Баунти",
    crafting: "Крафт",
    fuel: "Топливо",
    // --- Дополнительные элементы и панель инструментов ---
    sub_streak: "Серия побед",
    sub_meta: "Параметры задачи",
    sub_queue: "Очередь задач",
    sub_automations: "Фоновые сервисы",
    task_queue: "Очередь задач",
    import: "Импорт",
    export: "Экспорт",
    clear: "Очистить",
    btn_add_task: "+ Добавить задачу",
    task_builder: "Конструктор задачи",
    reset: "Сбросить",
    btn_cancel: "Отмена",
    btn_close: "Закрыть",
    drawer_recordings_title: "Записи",
    drawer_recordings_sub: "Выбор и воспроизведение записей · F10",
    ph_search_recordings: "Поиск записей...",
    lbl_macro_start_mode: "Режим кнопки «Старт»",
    desc_start_mode_replay: "Старт запускает выбранную запись",
    desc_start_mode_auto: "Старт выполняет очередь задач",
    hint_drawer_esc: "Esc или F10 для закрытия",
    btn_select: "Выбрать",
    btn_selected: "Выбрано",
    btn_record: "Запись",
    tt_start_rec: "Начать запись (F8)",
    tt_task_presets: "Сохранённые шаблоны очереди на этом ПК",
    opt_no_presets: "Нет сохранённых шаблонов",
    btn_load: "Загрузить",
    tt_load_preset: "Загрузить выбранный шаблон",
    ph_preset_name: "Имя шаблона",
    tt_preset_name: "Имя шаблона",
    tt_save_preset: "Сохранить текущую очередь как шаблон",
    tt_del_preset: "Удалить шаблон",
    tt_folder_presets: "Открыть папку с шаблонами в Проводнике",
    tt_import_tasks: "Импортировать задачи из JSON",
    tt_export_tasks: "Экспортировать задачи в JSON",
    tt_clear_tasks: "Очистить все задачи",
    sub_select_task: "Выберите задачу слева для настройки",
    btn_clone: "Дублировать",
    tt_clone_task: "Дублировать эту задачу",
    btn_delete: "Удалить",
    tt_del_task: "Удалить эту задачу",
    empty_task_builder_desc: "Выберите задачу в списке слева или нажмите «+ Добавить задачу».",
    ph_scen_name: "Имя сценария",
    tt_scen_name: "Имя сценария",
    tt_select_scen: "Выбрать сценарий",
    tt_save_scen: "Сохранить сценарий",
    tt_new_scen: "Создать новый сценарий",
    tt_del_scen: "Удалить текущий сценарий",
    tt_folder_scen: "Открыть папку шаблонов в Проводнике",
    tt_validate_scen: "Проверить корректность блоков",
    tt_toggle_guide: "Свернуть / развернуть справку",
    modal_edit_block: "Редактирование действия",
    modal_insert_action: "Вставить действие",
    modal_insert_sub: "Выберите действие для вставки на этом шаге",
    modal_save_path_title: "Сохранить записанный маршрут",
    lbl_save_path_name: "Название маршрута WASD:",
    ph_save_path: "например: Моя точка или База",
    btn_discard: "Отменить",
    btn_save_path: "Сохранить маршрут",
    rec_popout_title: "Запись движения WASD",
    rec_popout_text: "Идите в игре · Пауза 1.8 сек сохранит путь",
    app_closed_title: "Панель закрыта",
    app_closed_text: "Макрос остановлен. Нажмите кнопку, чтобы открыть.",
    btn_reopen: "Открыть панель",
    restore_pill: "AE Macro · свёрнут",
    res_crafting_title: "Авто-крафт",
    res_crafting_enable: "Включить авто-крафт",
    res_crafting_enable_desc: "После каждых N побед переходит в зону крафта, создаёт выбранные спрайты и возвращается к фарму",
    res_craft_every: "Крафтить каждые",
    res_craft_every_desc: "Учитываются победы: Mastery (Story) и испытания Challenge",
    res_sprites_craft: "Спрайты для крафта",
    res_sprites_desc: "Список приоритета: Trait Crystal ×5, Mana Flask ×10, Cursed Boba ×2",
    btn_choose_sprites: "Выбрать спрайты",
    res_reset_progress: "Сбросить прогресс",
    res_reset_progress_desc: "Сбросить счётчик побед крафта на 0",
    btn_reset_counter: "Сбросить счётчик",
    res_fuel_title: "Авто-топливо",
    res_fuel_enable: "Включить авто-топливо",
    res_fuel_enable_desc: "Пополняет топливо в безопасные моменты между задачами",
    res_refill_interval: "Интервал пополнения",
    res_refill_desc: "Автопополнение каждые 8 часов или заданный интервал",
    btn_auto_8h: "Авто (8ч)",
    res_resource_drill: "Resource Drill (Бур)",
    res_gold_mine: "Gold Mine (Шахта)",
    res_walking_paths: "Маршруты ходьбы",
    res_paths_desc: "Запись и назначение 3 маршрутов внутри Expedition Hub",
    btn_configure_paths: "Настроить маршруты",
    res_reset_fuel_timer: "Сбросить таймер топлива",
    res_reset_fuel_desc: "Делает все ресурсы готовыми к немедленному сбору",
    btn_reset_timer: "Сбросить таймер",
    res_shop_title: "Авто-магазин",
    res_shop_enable: "Включить авто-магазин",
    res_shop_enable_desc: "Посещает магазины между задачами, ежедневный сброс по UTC",
    res_gold_shop_order: "Порядок покупок в Gold Shop",
    res_gold_shop_desc: "Предметы покупаются по приоритету до исчерпания запаса",
    res_challenge_title: "Авто-испытания (Challenge)",
    res_daily_challenge: "Включить Daily Challenge",
    res_regular_challenge: "Включить Regular Challenge",
    res_challenge_mode: "Режим игры Challenge",
    res_story_map_setup: "Настройка карт Story",
    res_stages_progress: "Прогресс этапов 1-3",
    res_reset_challenge_status: "Сбросить статус испытаний",
    btn_reset_counters: "Сбросить счётчики",
    btn_story_maps: "Карты Story",
    set_discord_connected: "Вебхук подключен",
    set_discord_url: "URL вебхука",
    set_mention_id: "ID для упоминания",
    set_notifications: "Уведомления о результатах",
    set_pings: "Оповещения о прогрессе",
    set_reports: "Периодические отчёты",
    btn_send_status_now: "Отправить статус сейчас",
    btn_test_hook: "Тестовое сообщение",
    set_theme: "Тема",
    set_density: "Плотность",
    set_corners: "Скругления",
    set_ambient_motion: "Фоновая анимация",
    opt_default: "По умолчанию",
    opt_soft: "Мягкие",
    opt_full: "Полная",
    opt_calm: "Спокойная",
    opt_off: "Отключена",
    set_diag_screenshot: "Сохранить скриншот",
    set_diag_screenshot_desc: "Снимок всего окна игры в папку отладки",
    set_diag_system: "Диагностика системы",
    set_diag_system_desc: "Полная проверка всех модулей и зрения",
    btn_health_check: "Запустить диагностику",
    set_diag_templates: "Проверить эталоны",
    set_diag_templates_desc: "Проверка файлов шаблонов поиска и координат",
    btn_check_templates: "Проверить шаблоны",
    set_diag_assets: "Папка Assets",
    set_diag_assets_desc: "Файлы картинок для визуального поиска",
    btn_open: "Открыть",
    set_diag_report: "Экспорт отчёта об ошибке",
    set_diag_report_desc: "Собрать архив с логами и скриншотами для отчёта",
    btn_export_zip: "Экспорт ZIP",
    rec_req_focus: "Требовать фокус окна игры",
    rec_req_focus_desc: "Останавливать повтор при потере фокуса игры",
    rec_start_delay: "Задержка старта",
    rec_start_delay_desc: "Пауза перед началом воспроизведения действий",
    rec_loops: "Количество циклов",
    rec_loops_desc: "Сколько раз повторить запись (0 = бесконечно)",
    rec_empty_note: "Режим записи воспроизводит ваши действия тик в тик. Не требует эталонов и настройки.",
    tt_export_bundle: "Экспорт записи",
    tt_import_bundle: "Импорт записи",
    tt_open_folder: "Открыть папку",
    ph_search_help: "Поиск вопросов (например: Act 3, вирус, камера, OCR, обновление)...",
    tt_clear_search: "Очистить поиск",
    // --- Newly localized keys ---
    hk_macro_start: "Старт макроса",
    hk_macro_stop: "Стоп макроса",
    hk_macro_pause: "Пауза макроса",
    hk_debug_screenshot: "Скриншот отладки",
    hk_toggle_game: "Показать/скрыть игру",
    hk_toggle_record: "Старт/стоп записи",
    hk_open_replay: "Открыть повтор",
    hk_toggle_walk_record: "Запись маршрута WASD",
    hk_note: "Нажмите на клавишу, затем нажмите новую комбинацию. <kbd>Esc</kbd> — отмена.",
    hk_reset_default: "Сбросить горячие клавиши",
    set_theme_desc: "Стеклянная атмосфера панели",
    set_density_desc: "Интервалы между строками",
    set_corners_desc: "Скругление карточек и кнопок",
    set_ambient_motion_desc: "Фоновые частицы и живые индикаторы",
    set_auto_update: "Устанавливать автоматически",
    set_auto_update_desc: "Скачивать и применять релизы в фоне",
    btn_check_upd: "Проверить",
    lbl_version: "Версия",
    upd_state_ok: "Актуальная версия",
    rec_status_not_rec: "Запись не идет",
    rec_hint_hotkey: "Запись управляется горячей клавишей. Сыграйте один матч вручную.",
    rec_settings_title: "Настройки записи",
    rec_note_f8: "Нажмите <kbd>F8</kbd> в любом месте для старта или остановки записи. Макрос записывает клики, клавиши и зажатия тик в тик без внедрения в игру.",
    res_daily_challenge_desc: "Сначала выполняет ежедневное испытание (сброс в 00:00 UTC)",
    res_regular_challenge_desc: "Проходит все готовые этапы один раз перед запуском очереди",
    res_challenge_mode_desc: "Соло или поиск группы для ежедневных и обычных этапов",
    res_story_map_desc: "Привязка макроса к картам испытаний сюжетного режима",
    res_stages_progress_desc: "Лимиты этапов, время восстановления и счетчики прохождений",
    res_reset_challenge_desc: "Сбросить статус ежедневных испытаний и таймеры",
  },
};

/* настоящий changelog релиза v1.1.10 с GitHub (Ponchik0/Anime-Expedition-Macro-ty-creams-) */
const CHANGELOG = [
  { title: { en: "Combat & Match Automation", ru: "Бой и автоматизация матчей" }, items: [
    { kind: "new", text: "Smart Start Game Modal Auto-Click" },
    { kind: "new", text: "Time-Based Infinite Wave Fallback" },
    { kind: "fix", text: "Seamless In-Game Restart Loop (Inf Summer)" },
    { kind: "fix", text: "Match Auto-Recovery on Join" },
  ]},
  { title: { en: "Lobby & Adaptive Resolution", ru: "Лобби и адаптивное разрешение" }, items: [
    { kind: "new", text: "Adaptive Multi-Anchor Lobby Detection" },
    { kind: "new", text: "Lobby Overlay Auto-Dismissal" },
    { kind: "new", text: "Expanded Multiscale Range (0.88, 1.13, 0.85, 1.15)" },
    { kind: "fix", text: "Summer Event Navigation Reliability" },
  ]},
  { title: { en: "Windows OCR & Diagnostics", ru: "Windows OCR и диагностика" }, items: [
    { kind: "new", text: "Bundled Windows OCR (winsdk) Native Binaries" },
    { kind: "new", text: "Multi-Language OCR Fallback" },
    { kind: "new", text: "Detailed Startup & Resolution Diagnostics" },
  ]},
  { title: { en: "Task Queue & Import", ru: "Очередь задач и импорт" }, items: [
    { kind: "new", text: "Universal JSON Import in Tasks" },
    { kind: "new", text: "Quick Macro Block Editor Shortcut" },
    { kind: "fix", text: "Task Auto-Transition Enforcement" },
  ]},
  { title: { en: "UI & Layout Scalability", ru: "Интерфейс и раскладка" }, items: [
    { kind: "new", text: "Horizontal Top Navigation Header" },
    { kind: "new", text: "Dynamic Resolution Auto-Layout" },
    { kind: "fix", text: "Resolution Scaling & Work Area Adaptation" },
    { kind: "fix", text: "Adaptive Controls & Overlap Protection" },
  ]},
  { title: { en: "Fishing & Hotbar Reliability", ru: "Рыбалка и хотбар" }, items: [
    { kind: "new", text: "Ironclad Multi-Rank Fishing Rod Verification" },
    { kind: "fix", text: "Bottom Hotbar & Placeable Fish Safety" },
    { kind: "fix", text: "Rod Unequip Prevention" },
  ]},
  { title: { en: "Quality", ru: "Качество" }, items: [
    { kind: "fix", text: "All 1,376 unit tests passing" },
  ]},
];

const t = key => (STR[LANG] && STR[LANG][key]) || STR.en[key] || key;

/* разрешение игры: держим в переменной, чтобы подпись жила на обоих языках.
   Объявлено ДО applyHash: тот вызывает applyLang -> updateGameSub, и обращение
   к let-переменной из будущего кода падало бы в TDZ, обрывая перевод. */
let GAME_RES = localStorage.getItem("ae_game_res") || "1152 × 756";
let activeResolution = (() => {
  try {
    const parts = GAME_RES.split(/[\s×x]+/).map(n => parseInt(n, 10));
    if (parts.length >= 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
      return { w: parts[0], h: parts[1] };
    }
  } catch (_) {}
  return { w: 1152, h: 756 };
})();
function updateGameSub() {
  const sub = $("#gameEmptySub");
  if (sub) sub.textContent = t("game_sub").replace("{res}", GAME_RES);
  const val = $("#gameResVal");
  if (val) val.textContent = GAME_RES;
  const tag = $("#resCurrentTag");
  if (tag) tag.textContent = GAME_RES.replace(/\s+/g, "");
}

function applyLang() {
  const isRu = (LANG === "ru");
  document.documentElement.lang = LANG;
  if (document.body) document.body.classList.toggle("is-ru", isRu);

  $$("[data-i18n]").forEach(el => {
    const val = t(el.dataset.i18n);
    if (val.includes("<") && val.includes(">")) {
      el.innerHTML = val;
    } else {
      el.textContent = val;
    }
  });
  $$("[data-i18n-title]").forEach(el => { el.title = t(el.dataset.i18nTitle); });
  $$("[data-i18n-placeholder]").forEach(el => { el.placeholder = t(el.dataset.i18nPlaceholder); });
  syncLangFlag();
  renderChangelog();
  renderNotes();
  renderRun();
  updateGameSub();
  if (typeof updateAutomationsDisplay === "function") updateAutomationsDisplay();
  if (typeof renderScenarioView === "function") renderScenarioView();
  if (typeof renderRealTasks === "function") renderRealTasks(realTasksList);
  if (typeof renderTaskBuilder === "function") renderTaskBuilder();
  if (typeof renderMiniQueue === "function") renderMiniQueue(realTasksList, lastRunStatus?.current_task, lastRunStatus?.current_repeat);
}

$("#langToggle").addEventListener("click", () => {
  LANG = LANG === "en" ? "ru" : "en";
  try {
    localStorage.setItem("ui_lang", LANG);
    localStorage.setItem("ae_lang", LANG);
  } catch (_) {}
  if (window.pywebview?.api?.set_setting) {
    try { window.pywebview.api.set_setting("lang", LANG); } catch (_) {}
  }
  applyLang();
  toast(LANG === "ru" ? "Язык переключен на русский (RU)" : "Language switched to English (EN)");
});

function syncLangFlag() {
  const btn = $("#langToggle");
  if (!btn) return;
  btn.classList.toggle("is-ru", LANG === "ru");
  const label = LANG === "en" ? "Переключить на русский (RU)" : "Switch to English (EN)";
  btn.title = label;
  btn.setAttribute("aria-label", label);
}

/* ------------------------------------------------------------------ toast */
let toastTimer = null;
function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 2400);
}

/* ----------------------------------------------------------- навигация */
let lastNonHomeScreen = "settings";

function setScreen(name) {
  if (name !== "home") {
    lastNonHomeScreen = name;
  }
  // Если ушли с экрана дашборда во время ручной записи — отменяем её и скрываем HUD
  if (name !== "home" && pendingPathRecordContext) {
    const popout = $("#recPopout");
    if (popout) {
      popout.hidden = true;
      popout.style.display = "none";
    }
    if (window.pywebview?.api?.cancel_path_recording) {
      try { window.pywebview.api.cancel_path_recording(); } catch (_) {}
    }
    pendingPathRecordContext = null;
  }
  document.body.dataset.screen = name;
  $$(".tnav").forEach(b => b.classList.toggle("is-active", b.dataset.screen === name));
  $$(".screen").forEach(s => s.classList.toggle("is-active", s.id === "screen-" + name));
  $("#content").scrollTop = 0;

  // Жизненный цикл экранов: опрос записей, загрузка настроек и очереди
  if (name === "recordings") {
    if (typeof loadRecordingsScreen === "function") loadRecordingsScreen();
  } else {
    if (typeof stopRecordingsPolling === "function") stopRecordingsPolling();
  }
  if (name === "tasks") {
    if (typeof loadTasksScreen === "function") loadTasksScreen();
  }
  if (name === "settings") {
    if (typeof loadSettingsScreen === "function") loadSettingsScreen();
  }
  if (name === "resources") {
    if (typeof loadResourcesScreen === "function") loadResourcesScreen();
  }
  if (name === "scenarios") {
    if (typeof refreshSavedWalkPaths === "function") refreshSavedWalkPaths();
    if (typeof refreshScenarioList === "function") refreshScenarioList();
    if (typeof renderScenarioView === "function") renderScenarioView();
  }

  // Прячем или показываем окно Roblox при смене вкладки:
  // Roblox прицеплен через Win32 SetParent поверх HTML вне потока CSS z-index.
  // Если не скрыть — игра остаётся видна насквозь поверх Задач/Настроек.
  try {
    if (window.pywebview && pywebview.api) {
      if (name === "home") {
        if (pywebview.api.show_game) pywebview.api.show_game();
      } else {
        if (pywebview.api.hide_game) pywebview.api.hide_game();
      }
    }
  } catch (_) {}
}

$$(".tnav").forEach(btn => btn.addEventListener("click", () => setScreen(btn.dataset.screen)));

/* deep-link: #screen=settings&tab=appearance&theme=pearl
   позволяет открыть концепт сразу на нужном экране/вкладке/теме */
function applyHash() {
  if (!location.hash) return;
  const params = new URLSearchParams(location.hash.slice(1));
  const screen = params.get("screen");
  if (screen && $("#screen-" + screen)) setScreen(screen);
  const tab = params.get("tab");
  if (tab && $('[data-panel="' + tab + '"]')) setTab(tab);
  const theme = params.get("theme");
  if (theme && $('[data-theme-set="' + theme + '"]')) {
    /* тема применяется до первой отрисовки переходами: иначе цвет текста
       успевает проехать переходом из Onyx и на кадр остаться светлым */
    document.documentElement.classList.add("theme-applying");
    document.documentElement.dataset.theme = theme;
    $$("#themePicker .theme-card").forEach(c => c.classList.toggle("is-on", c.dataset.themeSet === theme));
    requestAnimationFrame(() => requestAnimationFrame(() =>
      document.documentElement.classList.remove("theme-applying")));
  }
  const lang = params.get("lang");
  if (lang === "ru" || lang === "en") {
    LANG = lang;
    syncLangFlag();
    applyLang();
  }
  /* демо-сценарий для превью анимации: #demo=update открывает поповер
     и запускает скачивание без кликов */
  if (params.get("demo") === "update") {
    setTimeout(() => {
      $("#updBtn").click();
      setTimeout(() => $("#btnUpdDownload").click(), 1300);
    }, 500);
  }
}
/* вызов в конце файла: applyHash трогает renderRun/состояние прогона,
   которые к середине скрипта ещё не существуют (TDZ ронял весь скрипт) */

/* ------------------------------------------------------ вкладки настроек */
function setTab(name) {
  $$("#setTabs .tab").forEach(t => t.classList.toggle("is-on", t.dataset.tab === name));
  $$("[data-panel]").forEach(p => p.classList.toggle("is-on", p.dataset.panel === name));
}

$$("#setTabs .tab").forEach(tab => tab.addEventListener("click", () => setTab(tab.dataset.tab)));

/* ------------------------------------------------------ вкладки справки */
function setHelpTab(name) {
  $$("#helpTabs .tab").forEach(t => t.classList.toggle("is-on", t.dataset.htab === name));
  $$("[data-hpanel]").forEach(p => p.classList.toggle("is-on", p.dataset.hpanel === name));
}

$$("#helpTabs .tab").forEach(tab => tab.addEventListener("click", () => setHelpTab(tab.dataset.htab)));

/* ------------------------------------------------- mac-светофор окна */
/* Красная - закрыть панель, жёлтая - свернуть, зелёная - на весь экран.
   В приложении за ними стоят системные вызовы close_window / minimize_window. */
const appClosed = $("#appClosed");
const restorePill = $("#restorePill");

$("#tlClose").addEventListener("click", () => {
  if (window.pywebview && pywebview.api && pywebview.api.close_window) {
    pywebview.api.close_window();
    return;
  }
  document.body.classList.remove("ui-minimized");
  restorePill.hidden = true;
  appClosed.hidden = false;
});
$("#btnReopen").addEventListener("click", () => { appClosed.hidden = true; });
appClosed.addEventListener("click", e => { if (e.target === appClosed) appClosed.hidden = true; });
window.addEventListener("keydown", e => {
  if (e.key === "Escape" && !appClosed.hidden) appClosed.hidden = true;
});

$("#tlMin").addEventListener("click", () => {
  if (window.pywebview && pywebview.api && pywebview.api.minimize_window) {
    pywebview.api.minimize_window();
    return;
  }
  document.body.classList.add("ui-minimized");
  restorePill.hidden = false;
});
restorePill.addEventListener("click", () => {
  document.body.classList.remove("ui-minimized");
  restorePill.hidden = true;
});

const handleWindowMaximizeState = (isMax) => {
  const maxBtn = $("#tlMax");
  if (maxBtn) {
    maxBtn.setAttribute("aria-label", isMax ? "Restore" : "Maximize");
    maxBtn.setAttribute("title", isMax ? (LANG === "ru" ? "Восстановить" : "Restore") : (LANG === "ru" ? "Развернуть" : "Maximize"));
    maxBtn.setAttribute("data-tooltip", isMax ? (LANG === "ru" ? "Восстановить" : "Restore") : (LANG === "ru" ? "Развернуть" : "Maximize"));
  }
  // Переподтверждаем активное разрешение слота и окна игры, чтобы координаты и пропорции не сбивались
  if (typeof window.applyGameResolution === "function" && typeof activeResolution !== "undefined" && activeResolution) {
    window.applyGameResolution(activeResolution.w, activeResolution.h, true, true);
  }
  const modeText = isMax ? (LANG === "ru" ? "Полноэкранный режим" : "Fullscreen mode") : (LANG === "ru" ? "Оконный режим" : "Windowed mode");
  const winDesc = (LANG === "ru" ? "Окно игры" : "Game window");
  toast(`${modeText} · ${winDesc}: ${GAME_RES}`);
};

$("#tlMax").addEventListener("click", async () => {
  if (window.pywebview && pywebview.api && pywebview.api.toggle_maximize_window) {
    try {
      const isMax = await pywebview.api.toggle_maximize_window();
      handleWindowMaximizeState(isMax);
      return;
    } catch (_) {}
  }
  if (document.fullscreenElement) {
    document.exitFullscreen();
  } else if (document.documentElement.requestFullscreen) {
    document.documentElement.requestFullscreen().catch(() => toast(LANG === "ru" ? "Полноэкранный режим заблокирован" : "Fullscreen is blocked here"));
  } else {
    toast(LANG === "ru" ? "Полноэкранный режим недоступен" : "Fullscreen is unavailable");
  }
});
document.addEventListener("fullscreenchange", () => {
  const isFs = !!document.fullscreenElement;
  handleWindowMaximizeState(isFs);
});

// Двойной клик по области перемещения шапки окна: переключение развертывания / статического размера
const titlebarHeader = $(".titlebar");
if (titlebarHeader) {
  titlebarHeader.addEventListener("dblclick", async (e) => {
    // Игнорируем двойные клики по интерактивным элементам (кнопки, ссылки, инпуты, вкладки, выпадающие списки)
    if (e.target.closest("button, a, input, select, textarea, .tnav, .tab, .win-btn, .pop-anchor, .lang-flag")) {
      return;
    }
    if (window.pywebview && pywebview.api && pywebview.api.toggle_maximize_window) {
      try {
        const isMax = await pywebview.api.toggle_maximize_window();
        handleWindowMaximizeState(isMax);
      } catch (_) {}
    } else if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    } else if (document.documentElement.requestFullscreen) {
      document.documentElement.requestFullscreen().catch(() => {});
    }
  });

  // Перетаскивание окна за шапку (включая пространство панели навигации и логотипа)
  titlebarHeader.addEventListener("mousedown", (e) => {
    if (e.button !== 0) return; // только левая кнопка мыши
    // Игнорируем клики по интерактивным элементам управления
    if (e.target.closest("button, a, input, select, textarea, .tnav, .tab, .win-btn, .pop-anchor, .lang-flag")) {
      return;
    }
    // Если pywebview уже перехватил цель напрямую через класс .pywebview-drag-region, не дублируем
    if (e.target.matches && e.target.matches(".pywebview-drag-region")) {
      return;
    }
    if (window.pywebview && typeof window.pywebview._jsApiCallback === "function") {
      const initialX = e.clientX;
      const initialY = e.clientY;
      const onMove = (ev) => {
        const x = ev.screenX - initialX;
        const y = ev.screenY - initialY;
        window.pywebview._jsApiCallback("pywebviewMoveWindow", [x, y], "move");
      };
      const onUp = () => {
        window.removeEventListener("mousemove", onMove);
        window.removeEventListener("mouseup", onUp);
      };
      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", onUp);
    }
  });
}

/* ------------------------------------------------ проверка обновлений */
const updBtn = $("#updBtn");
const updPop = $("#updPop");

function syncUpdArrow() {
  if (updBtn && updPop) {
    const half = updBtn.offsetWidth / 2;
    updPop.style.setProperty("--arrow-left", Math.round(half) + "px");
  }
}

updBtn.addEventListener("click", async (e) => {
  // Shift+клик позволяет протестировать поповер обновления локально
  if ((e && e.shiftKey) || (window.event && window.event.shiftKey)) {
    if (updBtn.classList.contains("has-update")) {
      updBtn.classList.remove("has-update", "ready");
      updPop.hidden = true;
      toast(LANG === "ru" ? "Тестовое обновление скрыто" : "Test update hidden");
    } else {
      updBtn.classList.add("ready", "has-update");
      $("#updPopTitle").textContent = t("upd_title");
      renderChangelog();
      $(".upd-dl-label").textContent = t("upd_download");
      updPop.hidden = false;
      syncUpdArrow();
      if (bellPop) bellPop.hidden = true;
      toast(LANG === "ru" ? "Тестовое обновление показано" : "Test update shown");
    }
    return;
  }

  if (!updPop.hidden) { updPop.hidden = true; return; }
  syncUpdArrow();

  if (updBtn.classList.contains("has-update") || updBtn.classList.contains("ready")) {
    $("#updPopTitle").textContent = t("upd_title");
    renderChangelog();
    $(".upd-dl-label").textContent = t("upd_download");
    updPop.hidden = false;
    syncUpdArrow();
    if (bellPop) bellPop.hidden = true;
    return;
  }

  if (updBtn.classList.contains("checking")) return;
  updBtn.classList.add("checking");

  if (window.pywebview && pywebview.api && pywebview.api.check_for_update) {
    try {
      const res = await pywebview.api.check_for_update();
      updBtn.classList.remove("checking");
      if (res && res.available) {
        updBtn.classList.add("ready", "has-update");
        $("#updPopTitle").textContent = `${t("upd_title")} (${res.version})`;
        renderChangelog();
        updPop.hidden = false;
        syncUpdArrow();
        if (bellPop) bellPop.hidden = true;
      } else {
        toast(t("upd_latest"));
      }
      return;
    } catch (err) {
      updBtn.classList.remove("checking");
    }
  }

  // В автономном режиме (без Python)
  setTimeout(() => {
    updBtn.classList.remove("checking");
    toast(t("upd_latest"));
  }, 700);
});
window.addEventListener("resize", syncUpdArrow);

document.addEventListener("click", e => {
  if (!updPop.hidden && !e.target.closest(".upd-pop") && !e.target.closest("#updBtn")) {
    updPop.hidden = true;
  }
  if (!bellPop.hidden && !e.target.closest(".bell-pop") && !e.target.closest("#bellBtn")) {
    bellPop.hidden = true;
  }
});

/* ------------------------------------------------ колокол уведомлений */
/* Когда ничего нет: не закрашен (пустой контур), неподвижен.
   Когда есть предупреждение (.has-notes): закрашен белым (#ffffff) и качается (bellShake). */
const bellBtn = $("#bellBtn");
const bellPop = $("#bellPop");
let notesUnread = false;
let NOTES = [];

async function checkDiagnosticsGlass() {
  if (window.pywebview && pywebview.api && pywebview.api.get_diagnostics) {
    try {
      const res = await pywebview.api.get_diagnostics();
      if (res && Array.isArray(res.issues) && res.issues.length > 0) {
        NOTES = res.issues.map(iss => ({
          id: iss.id,
          kind: iss.severity === "warn" ? "warn" : "info",
          title: {
            en: iss.title || "System diagnostic",
            ru: iss.title === "Windows OCR unavailable" ? "Windows OCR недоступен" : (iss.title || "Диагностика")
          },
          text: {
            en: iss.detail || "",
            ru: (iss.detail && iss.detail.includes("Wave counter"))
              ? "Счётчик волн в fallback-режиме. Установите языковой пакет OCR en-US."
              : (iss.detail || "")
          },
          action: iss.action_label ? {
            en: iss.action_label,
            ru: iss.action_label === "Install" ? "Установить" : iss.action_label
          } : null,
          actionFn: iss.action
        }));
        notesUnread = true;
      } else {
        NOTES = [];
        notesUnread = false;
      }
    } catch (e) {
      NOTES = [];
      notesUnread = false;
    }
  }
  renderNotes();
}

window.testDiagBell = function(show = true) {
  if (show) {
    NOTES = [{
      id: "ocr_sim",
      kind: "warn",
      title: { en: "Windows OCR unavailable", ru: "Windows OCR недоступен" },
      text: {
        en: "Wave counter uses fallback mode. Install the en-US OCR language pack.",
        ru: "Счётчик волн в fallback-режиме. Установите языковой пакет OCR en-US."
      },
      action: { en: "Install", ru: "Установить" }
    }];
    notesUnread = true;
  } else {
    NOTES = [];
    notesUnread = false;
  }
  renderNotes();
};

function renderNotes() {
  const list = $("#bellList");
  if (!list) return;
  list.innerHTML = "";
  if (!NOTES.length) {
    const empty = document.createElement("div");
    empty.className = "bell-empty";
    empty.textContent = t("bell_empty");
    list.appendChild(empty);
  }
  NOTES.forEach(n => {
    const card = document.createElement("div");
    card.className = "note-card" + (n.kind === "info" ? " is-info" : "");
    const ic = document.createElement("span");
    ic.className = "note-ic";
    ic.innerHTML = '<svg class="ic"><use href="#' + (n.kind === "warn" ? "i-warn" : "i-bell") + '"/></svg>';
    const main = document.createElement("div");
    main.className = "note-main";
    const strong = document.createElement("strong");
    strong.textContent = n.title[LANG] || n.title.en;
    const span = document.createElement("span");
    span.textContent = n.text[LANG] || n.text.en;
    main.append(strong, span);
    if (n.action) {
      const act = document.createElement("button");
      act.className = "btn btn-ghost btn-sm note-act";
      act.textContent = n.action[LANG] || n.action.en;
      act.addEventListener("click", async () => {
        act.disabled = true;
        act.textContent = LANG === "ru" ? "Устанавливаю…" : "Installing…";
        if (window.pywebview && pywebview.api && pywebview.api.install_windows_ocr && n.actionFn === "install_windows_ocr") {
          try {
            await pywebview.api.install_windows_ocr();
          } catch (e) {}
        } else {
          await new Promise(r => setTimeout(r, 1200));
        }
        NOTES = NOTES.filter(x => x.id !== n.id);
        renderNotes();
        toast(LANG === "ru" ? "Windows OCR установлен" : "Windows OCR installed");
      });
      main.appendChild(act);
    }
    card.append(ic, main);
    const x = document.createElement("button");
    x.className = "icon-btn note-x";
    x.title = LANG === "ru" ? "Убрать" : "Dismiss";
    x.innerHTML = '<svg class="ic"><use href="#i-check"/></svg>';
    x.addEventListener("click", () => {
      NOTES = NOTES.filter(o => o.id !== n.id);
      renderNotes();
    });
    card.appendChild(x);
    list.appendChild(card);
  });
  bellBtn.classList.toggle("has-notes", notesUnread && NOTES.length > 0);
}

bellBtn.addEventListener("click", (e) => {
  // Shift+клик позволяет быстро переключить состояние колокольчика для проверки анимации
  if ((e && e.shiftKey) || (window.event && window.event.shiftKey)) {
    window.testDiagBell(!NOTES.length);
    toast(NOTES.length ? (LANG === "ru" ? "Тестовый колокольчик включен" : "Test bell on") : (LANG === "ru" ? "Тестовый колокольчик выключен" : "Test bell off"));
    return;
  }
  const open = bellPop.hidden;
  bellPop.hidden = !open;
  if (!open) return;
  updPop.hidden = true;
  notesUnread = false;
  renderNotes();
});

/* ------------------------------------------------ обновления: changelog */
function renderChangelog() {
  const box = $("#updChangelog");
  box.innerHTML = "";
  CHANGELOG.forEach(sec => {
    const label = document.createElement("div");
    label.className = "chg-sec-label";
    label.textContent = sec.title[LANG] || sec.title.en;
    box.appendChild(label);
    sec.items.forEach(item => {
      const row = document.createElement("div");
      row.className = "chg-item";
      const badge = document.createElement("i");
      badge.className = "chg-badge chg-" + item.kind;
      badge.textContent = item.kind === "new" ? "NEW" : "FIX";
      const text = document.createElement("span");
      text.textContent = item.text;
      row.append(badge, text);
      box.appendChild(row);
    });
  });
}

$("#btnUpdDownload").addEventListener("click", () => {
  const btn = $("#btnUpdDownload");
  if (btn.classList.contains("done") || btn.dataset.busy) return;
  btn.dataset.busy = "1";
  const fill = $(".upd-dl-fill", btn);
  const label = $(".upd-dl-label", btn);
  let p = 0;
  const timer = setInterval(() => {
    p = Math.min(100, p + 3 + Math.random() * 7);
    fill.style.width = p + "%";
    label.textContent = Math.floor(p) + "%";
    if (p >= 100) {
      clearInterval(timer);
      setTimeout(() => {
        btn.classList.add("done");
        updBtn.classList.remove("ready");
        updBtn.classList.remove("has-update");
        $("#updPopTitle").textContent = t("upd_installed");
        label.innerHTML =
          '<svg class="ic"><use href="#i-check"/></svg>' + t("upd_done_short");
        $("#updBadge").hidden = true;
        $("#appVer").textContent = "v2.0.0";
        $("#setVer").textContent = "2.0.0";
        const st = $("#updState");
        if (st) { st.textContent = "2.0.0 · " + t("upd_restart"); st.className = "upd-check"; }
        toast(t("upd_done"));
        delete btn.dataset.busy;
        setTimeout(() => { updPop.hidden = true; }, 2000);
      }, 400);
    }
  }, 120);
});

/* ------------------------------------------------------- прогон (Start) */
let realTasksList = [];

const run = {
  state: "idle",            // idle | running | paused
  seconds: 0,
  runs: 0,
  wins: 0,
  losses: 0,
  unknown: 0,
  allTimeWins: 0,
  allTimeLosses: 0,
  runsPerHour: "-",
  winStreak: 0,
  bestStreak: 0,
  autoRestartLoop: false
};

const fmtHMS = s => {
  const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), sec = s % 60;
  return (h > 0 ? h + ":" + String(m).padStart(2, "0") : String(m).padStart(2, "0")) + ":" + String(sec).padStart(2, "0");
};

function updateRateDisplay() {
  const stRate = $("#stRate");
  if (!stRate) return;
  if (run.runsPerHour && run.runsPerHour !== "-" && run.runsPerHour !== "—") {
    stRate.textContent = `${run.runsPerHour}/h`;
  } else if (run.runs > 0 && run.seconds > 0) {
    const rate = run.runs / (run.seconds / 3600);
    stRate.textContent = `${rate.toFixed(1)}/h`;
  } else {
    stRate.textContent = "—";
  }
}

let lastRunStatus = {};

function renderRunStateHeaders() {
  const isRunning = run.state === "running";
  const isPaused = run.state === "paused";
  const st = lastRunStatus;

  const lbl = $("#runStateLabel");
  const sub = $("#runStateSub");
  if (!lbl) return;

  if (isRunning) {
    const taskName = (st.current_task && st.current_task !== "-")
      ? st.current_task
      : (st.start_preview || (LANG === "ru" ? "Выполнение очереди" : "Running Queue"));
    lbl.textContent = taskName;

    let actionSub = "";
    if (st.action && st.action !== "-" && st.action !== "Idle" && st.action !== "Ожидание") {
      actionSub = st.action;
    } else if (st.map && st.map !== "-") {
      actionSub = `${st.map}${st.stage && st.stage !== "-" ? " · " + st.stage : ""}${st.mode && st.mode !== "-" ? " · " + st.mode : ""}`;
    } else {
      actionSub = LANG === "ru" ? "Авто-повтор активен" : "Auto-looping active";
    }
    if (sub) sub.textContent = actionSub;
  } else if (isPaused) {
    lbl.textContent = LANG === "ru" ? "На паузе" : "Session Paused";
    if (sub) {
      sub.textContent = (st.action && st.action !== "-" && st.action !== "Idle" && st.action !== "Ожидание")
        ? st.action
        : (LANG === "ru" ? "Макрос удерживает позицию. Нажмите Пауза или F5" : "Macro is holding position. Press Pause or F5");
    }
  } else {
    lbl.textContent = LANG === "ru" ? "Очередь задач" : "Task Queue";
    if (sub) sub.textContent = "";
  }
}

function updateSessionStats(data) {
  if (!data) return;
  lastRunStatus = Object.assign(lastRunStatus, data);
  if (data.wins !== undefined) run.wins = data.wins;
  if (data.losses !== undefined) run.losses = data.losses;
  if (data.unknown !== undefined) run.unknown = data.unknown;
  run.runs = run.wins + run.losses + run.unknown;
  if (data.seconds !== undefined) run.seconds = data.seconds;
  if (data.all_time_wins !== undefined) run.allTimeWins = data.all_time_wins;
  if (data.all_time_losses !== undefined) run.allTimeLosses = data.all_time_losses;
  if (data.runs_per_hour !== undefined) run.runsPerHour = data.runs_per_hour;

  const stRuns = $("#stRuns");
  if (stRuns) stRuns.textContent = run.runs;
  const stWins = $("#stWins");
  if (stWins) stWins.textContent = run.wins;
  const stLoss = $("#stLoss");
  if (stLoss) stLoss.textContent = run.losses;
  const stTime = $("#stTime");
  if (stTime) stTime.textContent = fmtHMS(run.seconds);

  const allTotal = run.allTimeWins + run.allTimeLosses;
  const allRate = allTotal > 0 ? Math.round((run.allTimeWins / allTotal) * 100) + "%" : "-";
  const stAllTime = $("#stAllTime");
  if (stAllTime) {
    stAllTime.textContent = allTotal > 0 ? `${run.allTimeWins}W ${run.allTimeLosses}L (${allRate})` : "0 / 0";
  }
  updateRateDisplay();

  // Живые метаданные очереди из текущего статуса макроса
  const runMetaTask = $("#runMetaTask");
  if (runMetaTask && data.current_task !== undefined) {
    const taskVal = data.current_task && data.current_task !== "-" ? data.current_task : "—";
    runMetaTask.textContent = taskVal;
    runMetaTask.title = taskVal;
  }
  const runMetaAction = $("#runMetaAction");
  if (runMetaAction && data.action !== undefined) {
    const actVal = (data.action && data.action !== "-" && data.action !== "Idle" && data.action !== "Ожидание") ? data.action : "—";
    runMetaAction.textContent = actVal;
    runMetaAction.title = actVal;
    runMetaAction.classList.toggle("is-active-action", actVal !== "—");
  }
  const runMetaRepeat = $("#runMetaRepeat");
  if (runMetaRepeat && data.current_repeat !== undefined) {
    runMetaRepeat.textContent = data.current_repeat && data.current_repeat !== "-" ? data.current_repeat : "—";
  }
  const runMetaMap = $("#runMetaMap");
  if (runMetaMap && data.map !== undefined) {
    let mapText = data.map && data.map !== "-" ? data.map : "—";
    if (data.stage && data.stage !== "-" && data.stage !== "" && mapText !== "—") {
      mapText += ` · ${data.stage}`;
    }
    runMetaMap.textContent = mapText;
    runMetaMap.title = mapText;
  }
  const runMetaMode = $("#runMetaMode");
  if (runMetaMode) {
    let modeText = data.mode && data.mode !== "-" ? data.mode : (data.play_mode && data.play_mode !== "-" ? data.play_mode : "—");
    if (data.difficulty && data.difficulty !== "-" && data.difficulty !== "" && modeText !== "—") {
      modeText += ` · ${data.difficulty}`;
    }
    runMetaMode.textContent = modeText;
    runMetaMode.title = modeText;
  }
  const runMetaLastRun = $("#runMetaLastRun");
  if (runMetaLastRun && data.last_run !== undefined) {
    runMetaLastRun.textContent = data.last_run && data.last_run !== "-" ? data.last_run : "—";
  }

  // Живая серия побед, рекорд и HUD телеметрия (Session Telemetry)
  if (data.win_streak !== undefined) run.winStreak = Number(data.win_streak) || 0;
  if (data.best_streak !== undefined) run.bestStreak = Number(data.best_streak) || 0;
  updateWinStreakDisplay(data);

  // Состояние Auto-Restart Loop
  if (data.auto_restart_loop !== undefined) {
    run.autoRestartLoop = !!data.auto_restart_loop;
    updateAutoRestartButton();
  }

  // Обновление компактного списка очередей задач
  renderMiniQueue(realTasksList, data.current_task, data.current_repeat);

  // Обновление блока фоновых сервисов автоматизации (Active Automations)
  if (data.automations) {
    updateAutomationsDisplay(data.automations);
  }

  renderRunStateHeaders();
}

function renderRun() {
  const isRunning = run.state === "running";
  const isPaused = run.state === "paused";
  const isIdle = run.state === "idle";

  const runCard = $("#runCard");
  if (runCard) {
    runCard.classList.toggle("is-running", isRunning);
    runCard.classList.toggle("is-paused", isPaused);
    runCard.classList.toggle("is-idle", isIdle);
  }

  const stateBadge = $("#runStateBadge");
  if (stateBadge) {
    stateBadge.classList.toggle("is-running", isRunning);
    stateBadge.classList.toggle("is-paused", isPaused);
    stateBadge.classList.toggle("is-idle", isIdle);
  }
  const badgeText = $("#runBadgeText");
  if (badgeText) {
    badgeText.textContent = isRunning ? (LANG === "ru" ? "В ЭФИРЕ" : "LIVE")
      : isPaused ? (LANG === "ru" ? "ПАУЗА" : "PAUSED")
      : (LANG === "ru" ? "ОЖИДАНИЕ" : "IDLE");
  }

  renderRunStateHeaders();

  $("#btnStart").disabled = isRunning;
  $("#btnPause").disabled = !isRunning && !isPaused;
  $("#btnStop").disabled = isIdle;
  $("#btnPauseText").textContent = isPaused ? t("btn_resume") : t("btn_pause");

  const liveChip = $("#liveChip");
  if (liveChip) {
    liveChip.classList.toggle("is-on", isRunning);
    liveChip.classList.toggle("is-running", isRunning);
    liveChip.classList.toggle("is-paused", isPaused);
    liveChip.classList.toggle("is-idle", isIdle);
  }
  const lt = $("#liveText");
  if (lt) {
    lt.textContent =
      isPaused ? (LANG === "ru" ? "ПАУЗА" : "PAUSED")
      : isRunning ? (LANG === "ru" ? "LIVE" : "LIVE")
      : (LANG === "ru" ? "IDLE" : "IDLE");
  }

  $("#footState").textContent =
    isRunning ? t("foot_play") : isPaused ? t("foot_hold") : t("foot_idle");
}

$("#btnStart").addEventListener("click", async () => {
  const popout = $("#recPopout");
  if (popout && pendingPathRecordContext) {
    popout.hidden = true;
    if (window.pywebview?.api?.cancel_path_recording) {
      try { await window.pywebview.api.cancel_path_recording(); } catch (_) {}
    }
    pendingPathRecordContext = null;
  }
  if (window.pywebview && pywebview.api && pywebview.api.start_macro) {
    try {
      const res = await pywebview.api.start_macro();
      if (!res || !res.ok) {
        const msg = (res && (res.message || (res.reason === 'already_running' ? (LANG === 'ru' ? 'уже запущен' : 'already running') : res.reason))) || '';
        toast((LANG === "ru" ? "Не удалось запустить: " : "Couldn't start: ") + msg);
        return;
      }
    } catch (e) {
      return;
    }
  } else {
    addLogLine("[Auto] Queue started: Summer Fishing (Event · repeat ×9999)");
    addLogLine("[Vision] Event tile matched (0.91)");
    addLogLine("[Preflight] Start Game clicked · macro loop active");
  }
  run.state = "running";
  renderRun();
});

$("#btnPause").addEventListener("click", async () => {
  if (window.pywebview && pywebview.api) {
    try {
      if (run.state === "running" && pywebview.api.pause_macro) {
        await pywebview.api.pause_macro();
      } else if (run.state === "paused" && pywebview.api.resume_macro) {
        await pywebview.api.resume_macro();
      }
    } catch (e) {}
  } else {
    addLogLine(run.state === "running" ? "[Runner] Paused by user (F5)" : "[Runner] Resumed by user (F5)");
  }
  run.state = run.state === "running" ? "paused" : "running";
  renderRun();
});

$("#btnStop").addEventListener("click", async () => {
  if (window.pywebview && pywebview.api && pywebview.api.stop_macro) {
    try { await pywebview.api.stop_macro(); } catch (e) {}
  } else {
    addLogLine("[Runner] Queue stopped by user (F2)");
  }
  run.state = "idle";
  renderRun();
});

/* Секундомер сессии: тикает при активном забеге */
setInterval(() => {
  if (run.state !== "running") return;
  run.seconds++;
  const stTime = $("#stTime");
  if (stTime) stTime.textContent = fmtHMS(run.seconds);
  const footUptime = $("#footUptime");
  if (footUptime) footUptime.textContent = t("uptime") + " " + fmtHMS(run.seconds);
  updateRateDisplay();
}, 1000);

/* -------------------------------------------------- серия побед (Streak) и HUD телеметрия */
function updateWinStreakDisplay(data) {
  const elStreak = $("#runStreakCount");
  const elBest = $("#runBestStreakCount");
  const elChal = $("#runChallengeTimer");
  const streak = run.winStreak || 0;
  if (elStreak) {
    elStreak.textContent = streak;
    elStreak.classList.toggle("is-hot", streak >= 3);
  }
  if (elBest) {
    elBest.textContent = run.bestStreak || 0;
  }
  if (elChal) {
    const tuc = (data && data.time_until_challenge !== undefined)
      ? data.time_until_challenge
      : (lastRunStatus && lastRunStatus.time_until_challenge);
    if (tuc && tuc !== "Disabled" && tuc !== "-") {
      elChal.textContent = tuc;
      elChal.title = LANG === "ru" ? `До челленджа: ${tuc}` : `Next Challenge: ${tuc}`;
    } else if (run.runs > 0 && (run.wins + run.losses) > 0) {
      const rate = Math.round((run.wins / (run.wins + run.losses)) * 100);
      elChal.textContent = `${rate}%`;
      elChal.title = LANG === "ru" ? `Винрейт сессии: ${rate}%` : `Session Win Rate: ${rate}%`;
    } else {
      elChal.textContent = "—";
      elChal.title = "";
    }
  }
}

/* --------------------------------------- быстрые действия и мини-очередь */
function updateAutoRestartButton() {
  const btn = $("#btnAutoRestartLoop");
  if (!btn) return;
  btn.classList.toggle("is-active", !!run.autoRestartLoop);
  const statusStr = run.autoRestartLoop
    ? (LANG === "ru" ? "активирован" : "enabled")
    : (LANG === "ru" ? "отключен" : "disabled");
  btn.title = `Auto-Restart Loop: ${statusStr} (F6)`;
}

/* --------------------------------- блок фоновых сервисов (Active Automations) */
let lastAutomationsData = null;

function updateAutomationsDisplay(automations) {
  if (automations) lastAutomationsData = automations;
  const data = automations || lastAutomationsData;
  if (!data) return;

  let activeCount = 0;

  // 1. Auto-Shop
  const cellShop = $("#autoCellShop");
  const pillShop = $("#autoShopPill");
  const subShop = $("#autoShopSub");
  if (data.shop) {
    const isAct = !!data.shop.enabled;
    if (isAct) activeCount++;
    if (cellShop) cellShop.classList.toggle("is-active", isAct);
    if (pillShop) {
      pillShop.classList.toggle("is-on", isAct);
      pillShop.textContent = isAct ? (LANG === "ru" ? "ВКЛ" : "ON") : (LANG === "ru" ? "ВЫКЛ" : "OFF");
    }
    if (subShop) subShop.textContent = isAct ? (data.shop.sub || (LANG === "ru" ? "Золото и События" : "Gold & Event")) : (LANG === "ru" ? "Выкл" : "Off");
  }

  // 2. Bounty Hunter
  const cellBounty = $("#autoCellBounty");
  const pillBounty = $("#autoBountyPill");
  const subBounty = $("#autoBountySub");
  if (data.bounty) {
    const isAct = !!data.bounty.enabled;
    if (isAct) activeCount++;
    if (cellBounty) cellBounty.classList.toggle("is-active", isAct);
    if (pillBounty) {
      pillBounty.classList.toggle("is-on", isAct);
      pillBounty.textContent = isAct ? (LANG === "ru" ? "ВКЛ" : "ON") : (LANG === "ru" ? "ВЫКЛ" : "OFF");
    }
    if (subBounty) subBounty.textContent = isAct ? (data.bounty.sub || (LANG === "ru" ? "Авто-квесты" : "Auto-Claim")) : (LANG === "ru" ? "Выкл" : "Off");
  }

  // 3. Auto-Crafting
  const cellCraft = $("#autoCellCraft");
  const pillCraft = $("#autoCraftPill");
  const subCraft = $("#autoCraftSub");
  if (data.crafting) {
    const isAct = !!data.crafting.enabled;
    if (isAct) activeCount++;
    if (cellCraft) cellCraft.classList.toggle("is-active", isAct);
    if (pillCraft) {
      pillCraft.classList.toggle("is-on", isAct);
      pillCraft.textContent = isAct ? (LANG === "ru" ? "ВКЛ" : "ON") : (LANG === "ru" ? "ВЫКЛ" : "OFF");
    }
    if (subCraft) subCraft.textContent = isAct ? (data.crafting.sub || (LANG === "ru" ? "Авто-крафт" : "Auto-Craft")) : (LANG === "ru" ? "Выкл" : "Off");
  }

  // 4. Fuel Watchdog
  const cellFuel = $("#autoCellFuel");
  const pillFuel = $("#autoFuelPill");
  const subFuel = $("#autoFuelSub");
  if (data.fuel) {
    const isAct = !!data.fuel.enabled;
    if (isAct) activeCount++;
    if (cellFuel) cellFuel.classList.toggle("is-active", isAct);
    if (pillFuel) {
      pillFuel.classList.toggle("is-on", isAct);
      pillFuel.textContent = isAct ? (LANG === "ru" ? "ВКЛ" : "ON") : (LANG === "ru" ? "ВЫКЛ" : "OFF");
    }
    if (subFuel) subFuel.textContent = isAct ? (data.fuel.sub || (LANG === "ru" ? "Защита ВКЛ" : "Safeguard ON")) : (LANG === "ru" ? "Выкл" : "Off");
  }

  const badgeCount = $("#automationsActiveCount");
  if (badgeCount) {
    badgeCount.textContent = `${activeCount}/4 ` + (LANG === "ru" ? "активно" : "active");
  }
}

function renderMiniQueue(tasks, activeTaskName, activeRepeat) {
  const container = $("#miniQueueList");
  const countBadge = $("#miniQueueCount");
  if (!container) return;

  const allTasks = Array.isArray(tasks) ? tasks : [];
  // Отображаем на панели только активные (включённые) задачи
  const validTasks = allTasks.filter(t => t && t.enabled !== false);
  if (countBadge) {
    countBadge.textContent = String(validTasks.length);
  }

  if (validTasks.length === 0) {
    const hasDisabledTasks = allTasks.length > 0;
    container.innerHTML = `
      <div class="mini-queue-empty" id="miniQueueEmpty">
        <span class="mini-queue-empty-text">${hasDisabledTasks ? (LANG === "ru" ? "Все задачи отключены в настройках" : "All tasks are disabled in Tasks") : (LANG === "ru" ? "Очередь пуста · Быстрые шаблоны:" : "Queue empty · Quick presets:")}</span>
        ${!hasDisabledTasks ? `
        <div class="mini-preset-chips">
          <button type="button" class="mini-preset-chip" data-preset="summer"><span class="chip-plus">+</span> ${LANG === "ru" ? "Летний ивент" : "Summer Event"}</button>
          <button type="button" class="mini-preset-chip" data-preset="infinite"><span class="chip-plus">+</span> ${LANG === "ru" ? "Бесконечный сюжет" : "Story Infinite"}</button>
          <button type="button" class="mini-preset-chip" data-preset="challenge"><span class="chip-plus">+</span> ${LANG === "ru" ? "Испытание" : "Challenge"}</button>
        </div>` : `
        <div style="margin-top:6px;">
          <button type="button" class="btn btn-ghost btn-xxs" onclick="setScreen('tasks')">${LANG === "ru" ? "Перейти в задачи" : "Open Tasks"}</button>
        </div>`}
      </div>
    `;
    container.querySelectorAll(".mini-preset-chip").forEach(btn => {
      btn.addEventListener("click", () => addPresetTask(btn.dataset.preset));
    });
    return;
  }

  // Рендерим активные задачи очереди (до 6 с адаптивным скроллом)
  const slice = validTasks.slice(0, 6);
  const isRunning = run.state === "running";
  container.innerHTML = "";

  slice.forEach((task, idx) => {
    const item = document.createElement("div");
    const isActive = isRunning && (idx === 0 || (activeTaskName && (task.name === activeTaskName || task.map === activeTaskName)));
    item.className = "mini-queue-item" + (isActive ? " is-active" : "");

    const left = document.createElement("div");
    left.className = "mini-queue-left";
    left.innerHTML = `<span class="mini-queue-dot"></span><span class="mini-queue-order mono">#${idx + 1}</span>`;

    const name = document.createElement("span");
    name.className = "mini-queue-name";
    const displayName = task.name || task.map || task.mode || `Task #${idx + 1}`;
    name.textContent = displayName;
    name.title = displayName;
    left.appendChild(name);
    item.appendChild(left);

    const tags = document.createElement("div");
    tags.className = "mini-queue-tags";

    if (task.map) {
      const tagMap = document.createElement("span");
      tagMap.className = "mini-tag tag-map";
      tagMap.textContent = task.map;
      tagMap.title = task.map;
      tags.appendChild(tagMap);
    }

    if (task.macro) {
      const tagMacro = document.createElement("span");
      tagMacro.className = "mini-tag tag-macro";
      tagMacro.textContent = task.macro;
      tagMacro.title = LANG === "ru" ? `Сценарий: ${task.macro}` : `Macro: ${task.macro}`;
      tags.appendChild(tagMacro);
    }

    const diff = task.difficulty || task.mode || "";
    if (diff) {
      const diffRu = { Normal: "Обычный", Hard: "Сложный", Nightmare: "Кошмар", story: "Сюжет", raid: "Рейд", event: "Ивент", tower: "Башня", portals: "Порталы" };
      const tagMode = document.createElement("span");
      tagMode.className = "mini-tag tag-mode";
      tagMode.textContent = (LANG === "ru" && diffRu[diff]) ? diffRu[diff] : diff;
      tags.appendChild(tagMode);
    }

    // Дополнительный этап/волна (чистый текст, без эмодзи)
    if (task.infinite_wave_limit) {
      const tagW = document.createElement("span");
      tagW.className = "mini-tag mono";
      tagW.textContent = `W${task.infinite_wave_limit}`;
      tags.appendChild(tagW);
    } else if (task.stage && task.stage !== "infinite" && task.stage !== "-") {
      const tagS = document.createElement("span");
      tagS.className = "mini-tag mono";
      tagS.textContent = `St.${task.stage}`;
      tags.appendChild(tagS);
    }

    const tagRep = document.createElement("span");
    tagRep.className = "mini-tag tag-repeat mono";
    let repText = "";
    if (isActive && activeRepeat && activeRepeat !== "-") {
      repText = activeRepeat;
    } else if (parseInt(task.repeat, 10) >= 9999 || String(task.stage).toLowerCase() === "infinite") {
      repText = "×9999";
    } else {
      repText = `×${task.repeat || 1}`;
    }
    tagRep.textContent = repText;
    tags.appendChild(tagRep);

    item.appendChild(tags);
    container.appendChild(item);
  });
}

async function addPresetTask(presetType) {
  let newTask = null;
  const now = Date.now();
  if (presetType === "summer") {
    newTask = {
      id: `task_summer_${now}`,
      mode: "event",
      map: "Summer",
      stage: "infinite",
      difficulty: "Normal",
      infinite_wave_limit: 30,
      repeat: 9999,
      macro: "Inf Summer",
      play_mode: "solo",
      enabled: true
    };
  } else if (presetType === "infinite") {
    newTask = {
      id: `task_story_${now}`,
      mode: "story",
      map: "Windmill Village",
      stage: "infinite",
      difficulty: "Normal",
      infinite_wave_limit: 50,
      repeat: 5,
      macro: "Default",
      play_mode: "solo",
      enabled: true
    };
  } else if (presetType === "challenge") {
    newTask = {
      id: `task_challenge_${now}`,
      mode: "challenge",
      map: "Regular Challenge",
      stage: "1",
      difficulty: "Normal",
      repeat: 3,
      macro: "Challenge",
      play_mode: "solo",
      enabled: true
    };
  }
  if (!newTask) return;

  if (!Array.isArray(realTasksList)) realTasksList = [];
  realTasksList.push(newTask);
  renderRealTasks(realTasksList);
  renderMiniQueue(realTasksList, lastRunStatus.current_task, lastRunStatus.current_repeat);
  toast(LANG === "ru" ? "Задача добавлена в очередь" : "Task added to queue");

  if (window.pywebview && pywebview.api && pywebview.api.save_tasks) {
    try {
      await pywebview.api.save_tasks(realTasksList);
    } catch (e) {
      console.warn("Failed to save tasks:", e);
    }
  }
}

// Привязка кнопок быстрого управления
const btnAutoRestart = $("#btnAutoRestartLoop");
if (btnAutoRestart) {
  btnAutoRestart.addEventListener("click", async () => {
    if (window.pywebview && pywebview.api && pywebview.api.toggle_auto_restart_loop) {
      try {
        const res = await pywebview.api.toggle_auto_restart_loop();
        if (res && res.ok) {
          run.autoRestartLoop = !!res.enabled;
          updateAutoRestartButton();
          toast(run.autoRestartLoop ? t("auto_restart_enabled") : t("auto_restart_disabled"));
        }
      } catch (err) {
        console.warn("toggle_auto_restart_loop failed:", err);
      }
    } else {
      run.autoRestartLoop = !run.autoRestartLoop;
      updateAutoRestartButton();
      toast(run.autoRestartLoop ? t("auto_restart_enabled") : t("auto_restart_disabled"));
    }
  });
}

const btnVipRejoin = $("#btnVipRejoin");
if (btnVipRejoin) {
  btnVipRejoin.addEventListener("click", async () => {
    toast(t("vip_rejoin_triggered"));
    if (window.pywebview && pywebview.api && pywebview.api.vip_lobby_rejoin) {
      try {
        await pywebview.api.vip_lobby_rejoin();
      } catch (err) {
        console.warn("vip_lobby_rejoin failed:", err);
      }
    }
  });
}

const btnMiniQueueManage = $("#btnMiniQueueManage");
if (btnMiniQueueManage) {
  btnMiniQueueManage.addEventListener("click", () => {
    setScreen("tasks");
  });
}

// Интерактивное переключение сервисов по клику на карточку
function setupAutomationCell(cellId, apiFnName, optKey, nameEn, nameRu) {
  const cell = $(cellId);
  if (!cell) return;

  const doToggle = async () => {
    // В режиме кастомизации клик не переключает сервис
    const homeEl = $("#screen-home");
    if (homeEl && homeEl.classList.contains("is-customizing")) return;

    const isCurrentlyActive = cell.classList.contains("is-active");
    const willEnable = !isCurrentlyActive;

    if (window.pywebview && pywebview.api && typeof pywebview.api[apiFnName] === "function") {
      try {
        const res = await pywebview.api[apiFnName](willEnable);
        if (willEnable && res && res.ok === false) {
          if (lastAutomationsData && lastAutomationsData[optKey]) {
            lastAutomationsData[optKey].enabled = false;
          }
          updateAutomationsDisplay();
          const reasonMsg = optKey === "bounty"
            ? (LANG === "ru" ? "Bounty: настройте макросы для всех карт в Настройках" : "Bounty: assign macros to all Story maps in Settings first")
            : (LANG === "ru" ? "Не удалось включить сервис" : "Failed to enable service");
          toast(reasonMsg);
          return;
        }
        if (lastAutomationsData && lastAutomationsData[optKey]) {
          lastAutomationsData[optKey].enabled = willEnable;
        }
        updateAutomationsDisplay();
        const title = LANG === "ru" ? nameRu : nameEn;
        const statusMsg = willEnable
          ? (LANG === "ru" ? `${title}: включен` : `${title}: enabled`)
          : (LANG === "ru" ? `${title}: выключен` : `${title}: disabled`);
        toast(statusMsg);
      } catch (err) {
        updateAutomationsDisplay();
      }
    } else {
      // Режим предпросмотра в браузере без Python бэкенда
      if (lastAutomationsData && lastAutomationsData[optKey]) {
        lastAutomationsData[optKey].enabled = willEnable;
      }
      updateAutomationsDisplay();
      const title = LANG === "ru" ? nameRu : nameEn;
      toast(willEnable
        ? (LANG === "ru" ? `${title}: включен` : `${title}: enabled`)
        : (LANG === "ru" ? `${title}: выключен` : `${title}: disabled`));
    }
  };

  cell.addEventListener("click", (e) => {
    if (e.target.closest(".auto-cell-hide-btn")) return;
    doToggle();
  });
  cell.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      doToggle();
    }
  });
}

setupAutomationCell("#autoCellShop", "set_auto_shop_enabled", "shop", "Auto-Shop", "Auto-Shop");
setupAutomationCell("#autoCellBounty", "set_bounty_enabled", "bounty", "Bounty Hunter", "Bounty Hunter");
setupAutomationCell("#autoCellCraft", "set_crafting_enabled", "crafting", "Auto-Craft", "Авто-крафт");
setupAutomationCell("#autoCellFuel", "set_fuel_enabled", "fuel", "Fuel Watchdog", "Контроль топлива");

async function skipCurrentTask() {
  if (window.pywebview && pywebview.api && pywebview.api.skip_current_task) {
    try {
      const res = await pywebview.api.skip_current_task();
      if (res && res.ok) {
        if (res.running) {
          toast(LANG === "ru" ? "Пропуск задачи: завершение текущего матча..." : "Skipping task: finishing current match...");
        } else {
          toast(LANG === "ru" ? "Задача перемещена в конец очереди" : "Task moved to end of queue");
          if (Array.isArray(res.tasks)) {
            realTasksList = res.tasks;
            renderRealTasks(realTasksList);
            renderMiniQueue(realTasksList, lastRunStatus.current_task, lastRunStatus.current_repeat);
          }
        }
      } else {
        toast(LANG === "ru" ? "Нечего пропускать" : "Nothing to skip");
      }
    } catch (err) {
      console.warn("skip_current_task failed:", err);
    }
  } else {
    // Fallback локальная ротация очереди при открытии в браузере без Python
    if (Array.isArray(realTasksList) && realTasksList.length > 1) {
      const skipped = realTasksList.shift();
      realTasksList.push(skipped);
      renderRealTasks(realTasksList);
      renderMiniQueue(realTasksList, lastRunStatus.current_task, lastRunStatus.current_repeat);
      toast(LANG === "ru" ? "Задача перемещена в конец очереди" : "Task moved to end of queue");
    }
  }
}

const btnMiniQueueSkip = $("#btnMiniQueueSkip");
if (btnMiniQueueSkip) {
  btnMiniQueueSkip.addEventListener("click", skipCurrentTask);
}

/* --------------------------------------------------------- журнал */
const FEED = $("#logFeed");

function getLogKindFromLine(line) {
  const l = String(line || "").toLowerCase();
  if (l.includes("error") || l.includes("err") || l.includes("fail") || l.includes("defeat")) return "err";
  if (l.includes("warn") || l.includes("missed") || l.includes("retry")) return "warn";
  if (l.includes("victory") || l.includes("success") || l.includes("ok") || l.includes("completed")) return "ok";
  if (l.includes("vision") || l.includes("matched") || l.includes("found")) return "vision";
  if (l.includes("wave") || l.includes("task") || l.includes("runner") || l.includes("auto")) return "info";
  return "dim";
}

function addLogLine(line) {
  if (!FEED) return;
  const timeStr = new Date().toLocaleTimeString("en-GB", { hour12: false });
  const row = document.createElement("div");
  const kind = getLogKindFromLine(line);
  row.className = "log-line log-" + kind;

  const tSpan = document.createElement("span");
  tSpan.className = "log-t";
  tSpan.textContent = timeStr;

  const msgSpan = document.createElement("span");
  msgSpan.className = "log-msg";

  const tagMatch = /^\[([^\]]+)\]\s*(.*)$/.exec(line);
  if (tagMatch) {
    const tag = document.createElement("span");
    tag.className = "log-tag";
    tag.textContent = `[${tagMatch[1]}]`;
    tag.style.marginRight = "6px";
    tag.style.fontWeight = "600";
    msgSpan.append(tag, document.createTextNode(tagMatch[2]));
  } else {
    msgSpan.textContent = line;
  }

  row.append(tSpan, msgSpan);
  FEED.appendChild(row);
  while (FEED.children.length > 250) FEED.firstChild.remove();
  FEED.scrollTop = FEED.scrollHeight;
}

// Глобальные мосты для evaluate_js из Python
window.addLog = function(line) {
  addLogLine(line);
};

window.appendLogBatch = function(lines) {
  if (!Array.isArray(lines)) return;
  lines.forEach(addLogLine);
};

window.clearLogView = function() {
  if (FEED) FEED.innerHTML = "";
};

/* Стартовые реальные строки запуска макроса */
addLogLine("[Runner] Anime Expeditions Macro v2.0.0 ready");
addLogLine("[Vision] Virtual screen resolution: 1152 × 756");
addLogLine("[Diagnostics] System checks complete · All components ok");
addLogLine("[Task] Queue idle · Press Start (F1) to begin");

/* ------------------------------------------------ история забегов */
let currentRunHistory = [];

function renderRunHistory(runs) {
  currentRunHistory = runs || [];
  const list = $("#histList");
  if (!list) return;
  list.innerHTML = "";
  if (!currentRunHistory.length) {
    const empty = document.createElement("div");
    empty.className = "hist-empty";
    empty.setAttribute("data-i18n", "no_runs_yet");
    empty.textContent = t("no_runs_yet") || (LANG === "ru" ? "Забегов пока нет" : "No runs yet");
    list.appendChild(empty);
    return;
  }
  for (const r of currentRunHistory) {
    const row = document.createElement("div");
    row.className = "hist-row";

    const dot = document.createElement("i");
    const isWin = r.result === "win";
    const isLoss = r.result === "loss";
    dot.className = "rdot " + (isWin ? "r-vic" : (isLoss ? "r-def" : "r-unk"));

    const main = document.createElement("div");
    main.className = "hist-main";
    const strong = document.createElement("strong");
    strong.textContent = r.map || (LANG === "ru" ? "Матч" : "Match");
    const meta = document.createElement("span");
    const parts = [];
    if (r.kind) parts.push(t(r.kind) || r.kind);
    if (r.source === "replay") parts.push(LANG === "ru" ? "Повтор" : "Replay");
    else if (!r.kind) parts.push(LANG === "ru" ? "Авто" : "Auto");
    meta.textContent = parts.join(" · ") || "Auto";
    main.append(strong, meta);

    const right = document.createElement("div");
    right.className = "hist-right";
    const dur = document.createElement("span");
    dur.className = "mono";
    dur.textContent = r.duration || "-";
    const time = document.createElement("span");
    time.className = "hist-time";
    time.textContent = r.ago || t("now") || (LANG === "ru" ? "только что" : "just now");
    right.append(dur, time);

    row.append(dot, main, right);
    list.appendChild(row);
  }
}

function addHistoryEntry(entry) {
  const runs = [entry, ...currentRunHistory];
  if (runs.length > 50) runs.pop();
  renderRunHistory(runs);
}

// Очистка истории через кнопку в карточке
function clearRunHistoryUI() {
  if (window.pywebview && pywebview.api && pywebview.api.clear_run_history) {
    try { pywebview.api.clear_run_history(); } catch (e) {}
  }
  renderRunHistory([]);
  updateSessionStats({ wins: 0, losses: 0, unknown: 0, seconds: 0, all_time_wins: 0, all_time_losses: 0, runs_per_hour: "-", win_streak: 0, best_streak: 0 });
  toast(t("hist_cleared") || (LANG === "ru" ? "История очищена" : "History cleared"));
}

const histClearBtn = $("#histClear");
if (histClearBtn) {
  histClearBtn.addEventListener("click", clearRunHistoryUI);
}

// Очистка и копирование логов
const logClearBtn = $("#logClear");
if (logClearBtn) {
  logClearBtn.addEventListener("click", () => {
    if (window.pywebview && pywebview.api && pywebview.api.clear_logs) {
      try { pywebview.api.clear_logs(); } catch (e) {}
    }
    window.clearLogView();
    toast(t("log_cleared") || (LANG === "ru" ? "Журнал очищен" : "Log cleared"));
  });
}

const logCopyBtn = $("#logCopy");
if (logCopyBtn) {
  logCopyBtn.addEventListener("click", async () => {
    const lines = $$(".log-line", FEED).map(line => {
      const t = line.querySelector(".log-t")?.textContent.trim() || "";
      const m = line.querySelector(".log-msg")?.textContent.trim() || "";
      return t ? `[${t}] ${m}` : m;
    }).filter(Boolean);
    const text = lines.join("\n");
    if (!text) {
      toast(LANG === "ru" ? "Журнал пуст" : "Log is empty");
      return;
    }
    let copied = false;
    try {
      await navigator.clipboard.writeText(text);
      copied = true;
    } catch (err) {
      try {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.left = "-9999px";
        ta.style.top = "-9999px";
        document.body.appendChild(ta);
        ta.select();
        copied = document.execCommand("copy");
        ta.remove();
      } catch (e) {}
    }
    if (copied) {
      toast(t("log_copied") || (LANG === "ru" ? "Журнал скопирован в буфер" : "Log copied to clipboard"));
    }
  });
}

// Инициализация при старте
updateSessionStats({ runs: 0, wins: 0, losses: 0, unknown: 0, seconds: 0, all_time_wins: 0, all_time_losses: 0, runs_per_hour: "-" });
renderRunHistory([]);
checkDiagnosticsGlass();

// Опрос реального состояния из Python при запуске внутри макроса
if (typeof window !== "undefined") {
  setInterval(async () => {
    if (!window.pywebview || !pywebview.api) return;
    try {
      if (pywebview.api.get_status) {
        const st = await pywebview.api.get_status();
        if (st) {
          updateSessionStats(st);
          if (st.run_history) {
            renderRunHistory(st.run_history);
          }
        }
      }
      if (pywebview.api.is_macro_running) {
        const macro = await pywebview.api.is_macro_running();
        if (macro) {
          run.state = macro.running ? (macro.paused ? "paused" : "running") : "idle";
          renderRun();
        }
      }
    } catch (e) {}
  }, 1500);
}

/* --------------------------------------------------------------- тумблеры */
document.addEventListener("change", e => {
  const input = e.target;
  const row = input.closest(".task-row");
  if (row && input.type === "checkbox") {
    row.classList.toggle("is-off", !input.checked);
  }
});

/* ------------------------------------------------------------- сценарии */
/* Полнофункциональный редактор сценариев автобоя (4 фазы: prestart, battle, loop_a, loop_b).
   Полностью совместим с форматом шаблонов Templates/*.json основного макроса. */

/**
 * Возвращает исчерпывающее понятное объяснение любого действия макроса
 * для всех 15 типов блоков с учетом координат, хоткеев, фазы и параметров.
 * Гарантирует непустую понятную подпись на выбранном языке (RU/EN).
 */
function getActionExplanation(block, phaseKey = "battle", isRu = true) {
  if (!block) return "";
  const t = block.type;
  const p = block.params || {};

  if (t === "place_unit") {
    const name = p.name || block.name || (isRu ? "юнит" : "unit");
    const hk = block.hotkey || "1";
    const x = p.x ?? block.x ?? 0;
    const y = p.y ?? block.y ?? 0;
    const retry = Boolean(block.retryUntilPlaced);
    if (isRu) {
      return `Выставить [${name}] по слоту [${hk}] в (${x}, ${y})${retry ? " (с повтором)" : ""}`;
    }
    return `Place [${name}] via slot [${hk}] at (${x}, ${y})${retry ? " (retry)" : ""}`;
  }

  if (t === "upgrade_unit") {
    const u = block.unit || p.unit || p.index || 1;
    const upg = block.upgrades || p.upgrades || p.times || 1;
    if (isRu) {
      return `Прокачать юнита #${u} на +${upg} ур.`;
    }
    return `Upgrade unit #${u} by +${upg} level(s)`;
  }

  if (t === "auto_upgrade_unit") {
    const u = block.unit || p.unit || p.index || 1;
    if (isRu) {
      return `Авто-прокачка юнита #${u} при наличии денег`;
    }
    return `Auto-upgrade unit #${u} when affordable`;
  }

  if (t === "sell_unit") {
    const u = block.unit || p.unit || p.index || 1;
    if (isRu) {
      return `Продать установленного юнита #${u}`;
    }
    return `Sell placed unit #${u}`;
  }

  if (t === "target_priority") {
    const u = block.unit || p.unit || p.index || 1;
    const prio = block.priority || p.priority || "Strongest";
    if (isRu) {
      return `Приоритет цели юнита #${u} → ${prio}`;
    }
    return `Target priority for unit #${u} → ${prio}`;
  }

  if (t === "walk_path") {
    const sprint = Boolean(block.sprint);
    if (block.mode === "none") {
      return isRu ? "Оставаться на месте у спавна (без ходьбы)" : "Stay put at spawn (no movement)";
    }
    if (block.mode === "auto") {
      return isRu ? `Маршрут карты по умолчанию${sprint ? " (спринт)" : ""}` : `Map default route${sprint ? " (sprint)" : ""}`;
    }
    const name = block.pathName || p.path || (isRu ? "Свой маршрут" : "Custom route");
    return isRu ? `Маршрут ходьбы "${name}"${sprint ? " (спринт)" : ""}` : `Walk route "${name}"${sprint ? " (sprint)" : ""}`;
  }

  if (t === "walk") {
    const isRec = Boolean(block.recordOnReach || p.recordOnReach);
    if (isRec) {
      return isRu ? "Запись движения WASD на ходу при старте" : "Live WASD recording on macro start";
    }
    const name = block.pathName || p.path || (isRu ? "сохранённый" : "saved");
    const sprint = Boolean(block.sprint);
    return isRu ? `Воспроизведение движения "${name}"${sprint ? " (спринт)" : ""}` : `Replay walk path "${name}"${sprint ? " (sprint)" : ""}`;
  }

  if (t === "wait_ms") {
    const ms = p.ms || block.ms || 1000;
    if (ms >= 1000) {
      const sec = (ms / 1000).toFixed(1);
      return isRu ? `Пауза ${sec} сек перед следующим шагом` : `Pause ${sec}s before next step`;
    }
    return isRu ? `Пауза ${ms} мс для стабилизации интерфейса` : `Short ${ms}ms pause for UI settle`;
  }

  if (t === "wait_wave") {
    const wave = p.wave || block.wave || 1;
    return isRu ? `Ожидание старта волны #${wave}` : `Wait until wave #${wave} starts`;
  }

  if (t === "leave_at_minute") {
    const min = p.minutes || block.minutes || 10;
    return isRu ? `Выход в лобби на ${min}-й минуте матча` : `Return to lobby at minute ${min}`;
  }

  if (t === "click") {
    const x = p.x ?? block.x ?? 0;
    const y = p.y ?? block.y ?? 0;
    // Слот хотбара 1 (удочка или стартовый предмет)
    if (Math.abs(x - 74) <= 25 && Math.abs(y - 670) <= 25) {
      return isRu ? "Хотбар: Слот 1 (взять удочку / предмет)" : "Hotbar: Slot 1 (equip rod/item)";
    }
    // Заброс удочки в воду (локация озера)
    if (Math.abs(x - 150) <= 30 && Math.abs(y - 500) <= 35) {
      return isRu ? "Озеро: Заброс удочки в воду" : "Lake: Cast fishing rod into water";
    }
    // Центр экрана: подсечь улов, кнопка 'Next'/'Replay', подтверждение
    if (Math.abs(x - 576) <= 25 && Math.abs(y - 601) <= 25) {
      return isRu ? "Центр: Подсечь рыбу / Replay / Забрать" : "Center: Reel in catch / Replay / Confirm";
    }
    // Дополнительные точки ловли в озере (автоклик)
    if ((Math.abs(x - 867) <= 30 && Math.abs(y - 557) <= 30) || (Math.abs(x - 669) <= 30 && Math.abs(y - 476) <= 30)) {
      return isRu ? "Озеро: Клик по поплавку / воде" : "Lake: Bobber / water click";
    }
    // По фазе выполнения
    if (phaseKey === "prestart") {
      return isRu ? `Стартовый клик в (${x}, ${y})` : `Pre-start click at (${x}, ${y})`;
    }
    if (phaseKey === "battle") {
      return isRu ? `Клик в бою по координатам (${x}, ${y})` : `Battle click at coordinates (${x}, ${y})`;
    }
    if (phaseKey === "loop_a" || phaseKey === "loop_b") {
      return isRu ? `Циклический клик в (${x}, ${y})` : `Continuous loop click at (${x}, ${y})`;
    }
    return isRu ? `Клик мышью в (${x}, ${y})` : `Mouse click at (${x}, ${y})`;
  }

  if (t === "drag") {
    const x1 = p.x1 ?? 0;
    const y1 = p.y1 ?? 0;
    const x2 = p.x2 ?? 0;
    const y2 = p.y2 ?? 0;
    const steps = p.steps || 30;
    return isRu ? `Перетаскивание (${x1}, ${y1}) → (${x2}, ${y2}) за ${steps} шаг.` : `Drag (${x1}, ${y1}) → (${x2}, ${y2}) in ${steps} steps`;
  }

  if (t === "send_key") {
    const key = p.key || block.key || "e";
    const hold = p.hold_ms || 0;
    if (hold > 0) {
      return isRu ? `Удержание клавиши "${key}" (${hold} мс)` : `Hold key "${key}" for ${hold}ms`;
    }
    return isRu ? `Быстрое нажатие клавиши "${key}"` : `Key tap "${key}"`;
  }

  if (t === "record") {
    const file = block.file || (isRu ? "пользовательская запись" : "custom sequence");
    return isRu ? `Повтор записи действий "${file}"` : `Replay action recording "${file}"`;
  }

  if (t === "detect") {
    const img = block.image || p.image || "";
    if (/game_results/i.test(img)) {
      return isRu ? "Проверка исхода матча (Победа / Поражение)" : "Match outcome check (Victory / Defeat)";
    }
    if (/fishing/i.test(img)) {
      return isRu ? "Проверка окна улова или ранга рыбалки" : "Fishing catch / rank dialog check";
    }
    if (/unit_exist/i.test(img)) {
      return isRu ? "Проверка наличия юнита на клетке" : "Unit existence check on tile";
    }
    return isRu ? `Проверка картинки "${img || "Шаблон"}"` : `Detect image "${img || "Template"}"`;
  }

  const def = BLOCK_DEFS[t];
  if (def) {
    return isRu ? (def.labelRu || def.label) : def.label;
  }
  return isRu ? `Действие: ${t}` : `Action: ${t}`;
}

/**
 * Обратная совместимость с вызовами getSmartHint(block, isRu).
 */
function getSmartHint(block, isRu) {
  return getActionExplanation(block, "battle", isRu);
}

const BLOCK_DEFS = {
  place_unit: {
    label: "Place Unit",
    labelRu: "Поставить юнита",
    icon: "i-up",
    defaultParams: () => ({ name: "farm", x: 470, y: 430 }),
    defaultExtra: () => ({ hotkey: "5", retryUntilPlaced: true }),
    formatTitle: b => {
      const isRu = (LANG === "ru");
      const name = b.params?.name || b.name || (isRu ? "юнит" : "unit");
      return isRu ? `Поставить юнита (${name})` : `Place Unit (${name})`;
    },
    formatMeta: b => {
      const isRu = (LANG === "ru");
      const keyStr = isRu ? `Клавиша [${b.hotkey || "1"}]` : `Key [${b.hotkey || "1"}]`;
      const retryStr = b.retryUntilPlaced ? (isRu ? " · с повтором" : " · retry") : "";
      return `${keyStr} · (${b.params?.x ?? 0}, ${b.params?.y ?? 0})${retryStr}`;
    },
  },
  upgrade_unit: {
    label: "Upgrade Unit",
    labelRu: "Прокачать юнита",
    icon: "i-up",
    defaultParams: () => ({}),
    defaultExtra: () => ({ unit: 1, upgrades: 1 }),
    formatTitle: b => (LANG === "ru" ? `Прокачать юнита #${b.unit || 1}` : `Upgrade Unit #${b.unit || 1}`),
    formatMeta: b => (LANG === "ru" ? `Цель: юнит #${b.unit || 1} · +${b.upgrades || 1} ур.` : `Target unit #${b.unit || 1} · +${b.upgrades || 1} level`),
  },
  auto_upgrade_unit: {
    label: "Auto Upgrade",
    labelRu: "Авто-прокачка",
    icon: "i-up",
    defaultParams: () => ({}),
    defaultExtra: () => ({ unit: 1 }),
    formatTitle: b => (LANG === "ru" ? `Авто-прокачка #${b.unit || 1}` : `Auto Upgrade #${b.unit || 1}`),
    formatMeta: b => (LANG === "ru" ? `Качает #${b.unit || 1} при наличии денег` : `Keeps upgrading unit #${b.unit || 1} when affordable`),
  },
  sell_unit: {
    label: "Sell Unit",
    labelRu: "Продать юнита",
    icon: "i-tag",
    defaultParams: () => ({}),
    defaultExtra: () => ({ unit: 1 }),
    formatTitle: b => (LANG === "ru" ? `Продать юнита #${b.unit || 1}` : `Sell Unit #${b.unit || 1}`),
    formatMeta: b => (LANG === "ru" ? `Продажа установленного юнита #${b.unit || 1}` : `Sells placed unit #${b.unit || 1}`),
  },
  target_priority: {
    label: "Target Priority",
    labelRu: "Приоритет цели",
    icon: "i-activity",
    defaultParams: () => ({}),
    defaultExtra: () => ({ unit: 1, priority: "Strongest" }),
    formatTitle: b => {
      const isRu = (LANG === "ru");
      const pMap = { Strongest: "Сильнейший", First: "Первый", Last: "Последний", Weakest: "Слабейший", Closest: "Ближайший" };
      const prio = isRu ? (pMap[b.priority] || b.priority || "Сильнейший") : (b.priority || "Strongest");
      return isRu ? `Приоритет цели (${prio})` : `Target Priority (${prio})`;
    },
    formatMeta: b => {
      const isRu = (LANG === "ru");
      const pMap = { Strongest: "Сильнейший", First: "Первый", Last: "Последний", Weakest: "Слабейший", Closest: "Ближайший" };
      const prio = isRu ? (pMap[b.priority] || b.priority || "Сильнейший") : (b.priority || "Strongest");
      return isRu ? `Юнит #${b.unit || 1} → ${prio}` : `Unit #${b.unit || 1} → ${prio}`;
    },
  },
  walk_path: {
    label: "Walk Path",
    labelRu: "Путь ходьбы",
    icon: "i-route",
    defaultParams: () => ({ path: "" }),
    defaultExtra: () => ({ mode: "auto", pathName: "", sprint: false }),
    formatTitle: b => {
      const isRu = (LANG === "ru");
      const modeText = b.mode === "none"
        ? (isRu ? "На месте" : "None")
        : (b.pathName || b.params?.path || (b.mode === "auto" ? (isRu ? "Авто" : "Auto") : (isRu ? "Свой" : "Custom")));
      return isRu ? `Путь ходьбы (${modeText})` : `Walk Path (${modeText})`;
    },
    formatMeta: b => {
      const isRu = (LANG === "ru");
      const modeMap = { auto: "авто", none: "на месте", custom: "свой" };
      const modeVal = isRu ? (modeMap[b.mode] || b.mode || "авто") : (b.mode || "auto");
      return (isRu ? "Режим: " : "Mode: ") + modeVal + (b.pathName || b.params?.path ? " · " + (b.pathName || b.params?.path) : "") + (b.sprint ? (isRu ? " · спринт" : " · sprint") : "");
    },
  },
  walk: {
    label: "Walk",
    labelRu: "Ходьба",
    icon: "i-route",
    defaultParams: () => ({ path: "", recordOnReach: true }),
    defaultExtra: () => ({ pathName: "", sprint: false, recordOnReach: true }),
    formatTitle: b => {
      const isRu = (LANG === "ru");
      const isRec = Boolean(b.recordOnReach || b.params?.recordOnReach);
      if (isRec) return isRu ? `Ходьба (Запись на ходу)` : `Walk (Record on run)`;
      return isRu ? `Ходьба (${b.pathName || b.params?.path || (isRu ? "Пусто" : "Empty")})` : `Walk (${b.pathName || b.params?.path || "Empty"})`;
    },
    formatMeta: b => {
      const isRec = Boolean(b.recordOnReach || b.params?.recordOnReach);
      if (isRec) return (LANG === "ru" ? "Запишет движение WASD прямо в игре, сохранит и продолжит" : "Records live WASD in Roblox, saves & continues");
      const defName = LANG === "ru" ? "по умолчанию" : "default";
      return (LANG === "ru" ? "Воспроизведение маршрута: " : "Replays recorded walk: ") + (b.pathName || b.params?.path || defName) + (b.sprint ? (LANG === "ru" ? " · спринт" : " · sprint") : "");
    },
  },
  wait_ms: {
    label: "Wait (ms)",
    labelRu: "Пауза (мс)",
    icon: "i-clock",
    defaultParams: () => ({ ms: 1000 }),
    defaultExtra: () => ({}),
    formatTitle: b => {
      const ms = b.params?.ms || b.ms || 1000;
      return (LANG === "ru" ? `Пауза ${ms} мс` : `Wait ${ms} ms`);
    },
    formatMeta: b => {
      const sec = ((b.params?.ms || b.ms || 1000) / 1000).toFixed(1);
      return (LANG === "ru" ? `Ожидание ${sec} сек перед следующим шагом` : `Delay ${sec}s for UI/action`);
    },
  },
  wait_wave: {
    label: "Wait Wave",
    labelRu: "Ждать волну",
    icon: "i-clock",
    defaultParams: () => ({ wave: 10 }),
    defaultExtra: () => ({}),
    formatTitle: b => (LANG === "ru" ? `Ждать волну ${b.params?.wave || b.wave || 1}` : `Wait for Wave ${b.params?.wave || b.wave || 1}`),
    formatMeta: b => (LANG === "ru" ? `Пауза до старта волны ${b.params?.wave || b.wave || 1}` : `Holds phase until wave ${b.params?.wave || b.wave || 1} starts`),
  },
  leave_at_minute: {
    label: "Leave Minute",
    labelRu: "Выход на минуте",
    icon: "i-clock",
    defaultParams: () => ({ minutes: 10 }),
    defaultExtra: () => ({}),
    formatTitle: b => (LANG === "ru" ? `Выход на минуте ${b.params?.minutes || b.minutes || 10}` : `Leave at Minute ${b.params?.minutes || b.minutes || 10}`),
    formatMeta: b => (LANG === "ru" ? `Возврат в лобби после ${b.params?.minutes || b.minutes || 10} мин.` : `Returns to lobby after ${b.params?.minutes || b.minutes || 10} minutes`),
  },
  click: {
    label: "Click",
    labelRu: "Клик мышью",
    icon: "i-mouse",
    defaultParams: () => ({ x: 576, y: 601 }),
    defaultExtra: () => ({}),
    formatTitle: b => (LANG === "ru" ? `Клик (${b.params?.x ?? 0}, ${b.params?.y ?? 0})` : `Click (${b.params?.x ?? 0}, ${b.params?.y ?? 0})`),
    formatMeta: b => (LANG === "ru" ? `Клик по координатам окна игры` : `Fixed click at client coordinates`),
  },
  drag: {
    label: "Drag",
    labelRu: "Перетаскивание",
    icon: "i-mouse",
    defaultParams: () => ({ x1: 500, y1: 500, x2: 600, y2: 500, steps: 30, duration_ms: 600 }),
    defaultExtra: () => ({}),
    formatTitle: b => (LANG === "ru" ? `Перетаскивание (${b.params?.x1 ?? 0}, ${b.params?.y1 ?? 0}) → (${b.params?.x2 ?? 0}, ${b.params?.y2 ?? 0})` : `Drag (${b.params?.x1 ?? 0}, ${b.params?.y1 ?? 0}) → (${b.params?.x2 ?? 0}, ${b.params?.y2 ?? 0})`),
    formatMeta: b => (LANG === "ru" ? `${b.params?.steps || 30} шагов · ${b.params?.duration_ms || 600} мс` : `${b.params?.steps || 30} steps · ${b.params?.duration_ms || 600} ms`),
  },
  send_key: {
    label: "Send Key",
    labelRu: "Нажать клавишу",
    icon: "i-sliders",
    defaultParams: () => ({ key: "e", hold_ms: 0 }),
    defaultExtra: () => ({}),
    formatTitle: b => (LANG === "ru" ? `Нажать клавишу "${b.params?.key || b.key || "e"}"` : `Send Key "${b.params?.key || b.key || "e"}"`),
    formatMeta: b => {
      if (b.params?.hold_ms) {
        return (LANG === "ru" ? `Удерживать ${b.params.hold_ms} мс` : `Hold for ${b.params.hold_ms} ms`);
      }
      return (LANG === "ru" ? "Быстрое нажатие клавиши" : "Key tap");
    },
  },
  record: {
    label: "Record",
    labelRu: "Повтор записи",
    icon: "i-rec",
    defaultParams: () => ({}),
    defaultExtra: () => ({ file: "" }),
    formatTitle: b => (LANG === "ru" ? `Повтор записи действий` : `Record Sequence`),
    formatMeta: b => (LANG === "ru" ? `Файл: ${b.file || "пользовательская запись"}` : `Replay: ${b.file || "custom sequence"}`),
  },
  detect: {
    label: "Detect",
    labelRu: "Проверка картинки",
    icon: "i-branch",
    defaultParams: () => ({}),
    defaultExtra: () => ({ image: "Game_results", mode: "single", then: [], else: [] }),
    formatTitle: b => (LANG === "ru" ? `Проверка "${b.image || "Game_results"}"` : `Detect "${b.image || "Game_results"}"`),
    formatMeta: b => {
      const isRu = (LANG === "ru");
      const thenStr = isRu ? `${b.then?.length || 0} Если есть` : `${b.then?.length || 0} Then`;
      const elseStr = isRu ? `${b.else?.length || 0} Иначе` : `${b.else?.length || 0} Else`;
      const modeMap = { single: "один раз", loop: "цикл", timeout: "таймаут" };
      const modeVal = isRu ? (modeMap[b.mode] || b.mode || "один раз") : (b.mode || "single");
      const modeStr = isRu ? `Режим: ${modeVal}` : `Mode: ${modeVal}`;
      return `${modeStr} · ${thenStr}, ${elseStr}`;
    },
  }
};

/* Встроенные шаблоны (точно такие же, как в папке Templates/*.json) */
const DEFAULT_TEMPLATES = {
  "Inf Summer": {
    name: "Inf Summer",
    blocks: {
      team: "",
      equipment: "include",
      prestart: [
        { type: "wait_ms", params: { ms: 1000 }, once: true, comment: "Пауза перед экипировкой" },
        { type: "click", params: { x: 74, y: 670 }, once: true, comment: "Взять удочку (Слот 1 хотбара)" },
        { type: "wait_ms", params: { ms: 500 }, once: true, comment: "Пауза на доставание удочки" },
        { type: "click", params: { x: 150, y: 500 }, once: true, comment: "Первый заброс удочки в озеро" }
      ],
      battle: [
        {
          type: "detect",
          params: {},
          once: false,
          mode: "single",
          image: "Game_results",
          comment: "Проверка окончания матча",
          then: [{ type: "click", params: { x: 576, y: 601 }, once: false, comment: "Подтвердить победу / Replay" }],
          else: []
        }
      ],
      loop_a: [
        { type: "click", params: { x: 150, y: 500 }, once: false, comment: "Заброс удочки в воду" },
        { type: "click", params: { x: 576, y: 601 }, once: false, comment: "Подсечь рыбу / забрать улов" }
      ],
      loop_b: []
    }
  },
  "auto click": {
    name: "auto click",
    blocks: {
      team: "",
      equipment: "include",
      prestart: [
        { type: "walk_path", params: {}, once: true, mode: "auto", pathName: "", sprint: false, comment: "Идти на позицию по карте" }
      ],
      battle: [
        {
          type: "detect",
          params: {},
          once: false,
          mode: "single",
          image: "Fishing rank",
          comment: "Проверка окна ранга рыбалки",
          then: [{ type: "click", params: { x: 577, y: 601 }, once: false, comment: "Забрать награду ранга" }],
          else: [{ type: "click", params: { x: 74, y: 670 }, once: false, comment: "Достать удочку (Слот 1)" }]
        },
        {
          type: "detect",
          params: {},
          once: false,
          mode: "single",
          image: "Game_results",
          comment: "Проверка окончания матча",
          then: [{ type: "click", params: { x: 577, y: 601 }, once: false, comment: "Подтвердить результат" }],
          else: []
        }
      ],
      loop_a: [
        { type: "click", params: { x: 867, y: 557 }, once: false, comment: "Клик по воде озера 1" },
        { type: "click", params: { x: 669, y: 476 }, once: false, comment: "Клик по воде озера 2" }
      ],
      loop_b: []
    }
  },
  "raid": {
    name: "raid",
    blocks: {
      team: "",
      equipment: "include",
      prestart: [
        { type: "walk_path", params: {}, once: true, mode: "auto", pathName: "", sprint: false, comment: "Маршрут к позиции рейда" },
        { type: "place_unit", params: { name: "farm", x: 476, y: 426 }, once: false, hotkey: "5", comment: "Фарма #1" },
        { type: "place_unit", params: { name: "farm", x: 470, y: 430 }, once: false, hotkey: "5", comment: "Фарма #2" },
        { type: "place_unit", params: { name: "farm", x: 467, y: 440 }, once: false, hotkey: "5", comment: "Фарма #3" },
        { type: "place_unit", params: { name: "farm", x: 514, y: 425 }, once: false, hotkey: "6", comment: "Фарма #4" },
        { type: "place_unit", params: { name: "dps", x: 680, y: 409 }, once: false, hotkey: "1", comment: "DPS юнит #1" },
        { type: "place_unit", params: { name: "dps", x: 710, y: 408 }, once: false, hotkey: "2", comment: "DPS юнит #2" },
        { type: "place_unit", params: { name: "dps", x: 750, y: 409 }, once: false, hotkey: "3", comment: "DPS юнит #3" },
        { type: "place_unit", params: { name: "dps", x: 1004, y: 565 }, once: false, hotkey: "4", comment: "DPS юнит #4" }
      ],
      battle: [],
      loop_a: [],
      loop_b: []
    }
  },
  "Fairy": {
    name: "Fairy",
    blocks: {
      team: "",
      equipment: "include",
      prestart: [
        { type: "walk_path", params: {}, once: true, mode: "auto", pathName: "", comment: "Маршрут к Fairy" },
        { type: "place_unit", params: { name: "farm", x: 757, y: 336 }, once: false, hotkey: "5", retryUntilPlaced: true, comment: "Фарма #1" },
        { type: "place_unit", params: { name: "farm", x: 758, y: 316 }, once: false, hotkey: "5", retryUntilPlaced: true, comment: "Фарма #2" },
        { type: "place_unit", params: { name: "farm", x: 782, y: 329 }, once: false, hotkey: "5", retryUntilPlaced: true, comment: "Фарма #3" },
        { type: "place_unit", params: { name: "farm", x: 730, y: 359 }, once: false, hotkey: "6", retryUntilPlaced: true, comment: "Фарма #4" },
        { type: "place_unit", params: { name: "dps", x: 495, y: 340 }, once: false, hotkey: "1", retryUntilPlaced: true, comment: "DPS #1" },
        { type: "place_unit", params: { name: "dps", x: 525, y: 340 }, once: false, hotkey: "2", retryUntilPlaced: true, comment: "DPS #2" },
        { type: "place_unit", params: { name: "dps", x: 505, y: 282 }, once: false, hotkey: "3", retryUntilPlaced: true, comment: "DPS #3" }
      ],
      battle: [],
      loop_a: [],
      loop_b: []
    }
  },
  "Flower Forest": {
    name: "Flower Forest",
    blocks: {
      team: "",
      equipment: "include",
      prestart: [
        { type: "walk_path", params: {}, once: true, mode: "auto", pathName: "", comment: "Маршрут к Flower Forest" },
        { type: "place_unit", params: { name: "farm", x: 510, y: 567 }, once: false, hotkey: "5", retryUntilPlaced: true, comment: "Фарма #1" },
        { type: "place_unit", params: { name: "farm", x: 490, y: 575 }, once: false, hotkey: "5", retryUntilPlaced: true, comment: "Фарма #2" },
        { type: "place_unit", params: { name: "dps", x: 506, y: 436 }, once: false, hotkey: "1", retryUntilPlaced: true, comment: "DPS #1" },
        { type: "place_unit", params: { name: "dps", x: 528, y: 438 }, once: false, hotkey: "2", retryUntilPlaced: true, comment: "DPS #2" }
      ],
      battle: [],
      loop_a: [],
      loop_b: []
    }
  },
  "lightning god": {
    name: "lightning god",
    blocks: {
      team: "",
      equipment: "include",
      prestart: [
        { type: "walk_path", params: {}, once: true, mode: "auto", pathName: "", sprint: false, comment: "Маршрут к Lightning God" },
        { type: "place_unit", params: { name: "farm", x: 245, y: 319 }, once: false, hotkey: "5", comment: "Фарма #1" },
        { type: "place_unit", params: { name: "farm", x: 232, y: 348 }, once: false, hotkey: "5", comment: "Фарма #2" },
        { type: "place_unit", params: { name: "farm", x: 233, y: 373 }, once: false, hotkey: "5", comment: "Фарма #3" }
      ],
      battle: [
        { type: "place_unit", params: { name: "friren", x: 604, y: 326 }, once: false, hotkey: "1", comment: "Фрирен" },
        { type: "place_unit", params: { name: "sinbad", x: 586, y: 458 }, once: false, hotkey: "4", comment: "Синдбад" },
        { type: "place_unit", params: { name: "itachi", x: 376, y: 380 }, once: false, hotkey: "2", comment: "Итачи" }
      ],
      loop_a: [],
      loop_b: []
    }
  }
};

let currentScenario = JSON.parse(JSON.stringify(DEFAULT_TEMPLATES["Inf Summer"]));
let activePhaseCol = "battle";
let editingBlockContext = null; // { phase, index, block }

/* Хранилище локальных сценариев (для демо/standalone без pywebview) */
function getLocalScenarios() {
  try {
    const raw = localStorage.getItem("ae_glass_scenarios");
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveLocalScenario(scen) {
  try {
    const all = getLocalScenarios();
    all[scen.name] = scen;
    localStorage.setItem("ae_glass_scenarios", JSON.stringify(all));
  } catch {}
}

function deleteLocalScenario(name) {
  try {
    const all = getLocalScenarios();
    delete all[name];
    localStorage.setItem("ae_glass_scenarios", JSON.stringify(all));
  } catch {}
}

/* Список сохранённых маршрутов ходьбы (WASD paths) */
let savedWalkPaths = [
  "Auto Fuel - Hub to Gold Mine",
  "Auto Fuel - Hub to Resource Drill",
  "Auto Fuel - Resource Drill to Gold Mine",
  "Expedition Encounter - East Town",
  "Expedition Encounter - Flower Forest",
  "Expedition Encounter - Rose Kingdom",
  "Expedition Encounter - School Grounds",
  "Fairy King Forest",
  "Kings Tomb",
  "Spirit Act3",
  "Summer",
  "Villian1",
  "Villian2"
];

async function refreshSavedWalkPaths() {
  if (window.pywebview?.api?.list_paths) {
    try {
      const list = await window.pywebview.api.list_paths();
      if (Array.isArray(list) && list.length) {
        savedWalkPaths = list;
      }
    } catch (e) {}
  }
  return savedWalkPaths;
}

/* Отрисовка списка сценариев в select */
async function refreshScenarioList(preferredSelect = null) {
  const select = $("#scenSelect");
  if (!select) return;

  let names = [];
  if (window.pywebview?.api?.list_templates) {
    try {
      names = await window.pywebview.api.list_templates();
    } catch {}
  }
  if (!names || !names.length) {
    const local = getLocalScenarios();
    names = Array.from(new Set([...Object.keys(DEFAULT_TEMPLATES), ...Object.keys(local)]));
  }

  select.innerHTML = "";
  names.forEach(n => {
    const opt = document.createElement("option");
    opt.value = n;
    opt.textContent = n;
    select.appendChild(opt);
  });

  const toSelect = preferredSelect || currentScenario.name || names[0];
  if (toSelect && [...select.options].some(o => o.value === toSelect)) {
    select.value = toSelect;
  }
}

/* Загрузка сценария по имени */
async function loadScenario(name) {
  if (window.pywebview?.api?.load_template) {
    try {
      const data = await window.pywebview.api.load_template(name);
      if (data && data.blocks) {
        currentScenario = { name: data.name || name, blocks: data.blocks };
        renderScenarioView();
        return;
      }
    } catch {}
  }

  const local = getLocalScenarios();
  if (local[name]) {
    currentScenario = JSON.parse(JSON.stringify(local[name]));
  } else if (DEFAULT_TEMPLATES[name]) {
    currentScenario = JSON.parse(JSON.stringify(DEFAULT_TEMPLATES[name]));
  } else {
    currentScenario = {
      name,
      blocks: {
        team: "",
        equipment: "include",
        prestart: [{ type: "walk_path", params: {}, once: true, mode: "auto", pathName: "", sprint: false }],
        battle: [],
        loop_a: [],
        loop_b: []
      }
    };
  }
  renderScenarioView();
}

/* Словарь перевода типовых заметок к шагам сценария (RU <-> EN) */
const KNOWN_COMMENTS = {
  "Оставаться на месте у спавна": "Stay put at spawn",
  "Пауза перед экипировкой": "Pause before equipping",
  "Пауза перед экипировкой удочки": "Pause before equipping fishing rod",
  "Взять удочку (Слот 1 хотбара)": "Equip rod (Hotbar Slot 1)",
  "Пауза на доставание удочки": "Pause to draw rod",
  "Пауза на доставание удочки в руки": "Pause to draw rod in hands",
  "Первый заброс удочки в озеро": "First cast into lake",
  "Проверка окончания матча": "Check match completion",
  "Проверка окончания матча (результаты)": "Check match completion (results)",
  "Подтвердить победу / Replay": "Confirm victory / Replay",
  "Подтвердить результат / Replay": "Confirm result / Replay",
  "Подтвердить победу / Повтор": "Confirm victory / Replay",
  "Подтвердить результат / Повтор": "Confirm result / Replay",
  "Заброс удочки в воду": "Cast rod into water",
  "Повторный заброс удочки в воду": "Cast rod again into water",
  "Подсечь рыбу / забрать улов": "Reel in fish / collect catch",
  "Идти на позицию по карте": "Walk to map position",
  "Проверка окна ранга рыбалки": "Check fishing rank popup",
  "Забрать награду ранга": "Claim rank reward",
  "Достать удочку (Слот 1)": "Equip rod (Slot 1)",
  "Подтвердить результат": "Confirm result",
  "Клик по воде озера 1": "Click on lake water 1",
  "Клик по воде озера 2": "Click on lake water 2",
  "Маршрут к позиции рейда": "Route to raid position",
  "Фарма #1": "Farm #1",
  "Фарма #2": "Farm #2",
  "Фарма #3": "Farm #3",
  "Фарма #4": "Farm #4",
  "DPS юнит #1": "DPS unit #1",
  "DPS юнит #2": "DPS unit #2",
  "DPS юнит #3": "DPS unit #3",
  "DPS юнит #4": "DPS unit #4",
  "DPS #1": "DPS #1",
  "DPS #2": "DPS #2",
  "DPS #3": "DPS #3",
  "Маршрут к Fairy": "Route to Fairy",
  "Маршрут к Flower Forest": "Route to Flower Forest",
  "Маршрут к Lightning God": "Route to Lightning God",
  "Взять удочку": "Equip rod",
  "Подсечь рыбу": "Reel in fish",
  "Забрать улов": "Collect catch",
  "Первый заброс удочки": "First cast of fishing rod",
  "Заброс удочки": "Cast fishing rod",
  "Проверка исхода матча": "Check match outcome",
  "Победа / Replay": "Victory / Replay",
  "Поражение / Replay": "Defeat / Replay",
  "Фрирен": "Frieren",
  "Синдбад": "Sinbad",
  "Итачи": "Itachi"
};

function translateComment(comment, isRu) {
  if (!comment) return "";
  if (!isRu) {
    return KNOWN_COMMENTS[comment] || comment;
  }
  for (const [ru, en] of Object.entries(KNOWN_COMMENTS)) {
    if (en === comment) return ru;
  }
  return comment;
}

/* Отрисовка сценария в интерфейсе */
function renderScenarioView() {
  const isRu = (LANG === "ru");
  const blocks = currentScenario.blocks || {};
  const phases = ["prestart", "battle", "loop_a", "loop_b"];

  const titleEl = $("#scenTitle");
  if (titleEl) titleEl.textContent = currentScenario.name;

  const nameInput = $("#scenNameInput");
  if (nameInput) nameInput.value = currentScenario.name;

  let totalCount = 0;

  phases.forEach(phaseKey => {
    const colEl = $(`[data-col="${phaseKey}"]`);
    if (!colEl) return;

    colEl.innerHTML = "";
    const list = blocks[phaseKey] || [];
    totalCount += list.length;

    const countBadge = $(`#count${phaseKey.charAt(0).toUpperCase() + phaseKey.slice(1).replace("_", "")}`);
    if (countBadge) countBadge.textContent = list.length;

    colEl.classList.toggle("block-col-empty", list.length === 0);
    colEl.setAttribute("data-empty-hint", isRu ? "Перетащите блоки сюда" : "Drop blocks here");

    list.forEach((b, idx) => {
      const def = BLOCK_DEFS[b.type] || {
        label: b.type,
        icon: "i-blocks",
        formatTitle: () => b.type,
        formatMeta: () => JSON.stringify(b.params || {})
      };

      const card = document.createElement("div");
      card.className = "block";
      card.draggable = true;
      card.dataset.phase = phaseKey;
      card.dataset.index = idx;

      const isRu = (LANG === "ru");
      const title = def.formatTitle ? def.formatTitle(b) : (isRu && def.labelRu ? def.labelRu : def.label);
      const meta = def.formatMeta ? def.formatMeta(b) : "";
      const smartHint = getActionExplanation(b, phaseKey, isRu);

      let commentHtml = "";
      if (b.comment) {
        const dispComment = translateComment(b.comment, isRu);
        commentHtml = `<div class="block-comment" title="${escapeHtml(dispComment)}"><svg class="ic"><use href="#i-pencil"/></svg><span>${escapeHtml(dispComment)}</span></div>`;
      } else if (smartHint) {
        commentHtml = `<div class="block-smart-hint" title="${escapeHtml(smartHint)}"><svg class="ic"><use href="#i-help"/></svg><span>${escapeHtml(smartHint)}</span></div>`;
      }

      let branchHtml = "";
      if (b.type === "detect") {
        const actionWord = isRu ? "действ." : "action(s)";
        const noneWord = isRu ? "Нет" : "None";
        const thenDesc = b.then?.length ? `${b.then.length} ${actionWord}` : noneWord;
        const elseDesc = b.else?.length ? `${b.else.length} ${actionWord}` : noneWord;
        branchHtml = `
          <div class="branch-body">
            <div class="branch then"><em>${isRu ? "Тогда" : "Then"}</em><span>${thenDesc}</span></div>
            <div class="branch else"><em>${isRu ? "Иначе" : "Else"}</em><span>${elseDesc}</span></div>
          </div>
        `;
      }

      card.innerHTML = `
        <div class="block-ic">
          <svg class="ic"><use href="#${def.icon}"/></svg>
        </div>
        <div class="block-main">
          <div class="block-main-head">
            <strong>${escapeHtml(title)}</strong>
            ${b.once ? `<span class="block-badge-once">${isRu ? "1 раз" : "once"}</span>` : ""}
            ${Boolean(b.recordOnReach || b.params?.recordOnReach) ? `<span class="block-badge-rec"><span class="rec-dot-pulse"></span>${isRu ? "запись при старте" : "record on run"}</span>` : ""}
          </div>
          ${commentHtml}
          <span>${escapeHtml(meta)}</span>
          ${branchHtml}
        </div>
        <div class="block-acts">
          <button class="icon-btn" title="${isRu ? "Вставить действие после" : "Insert action after"}" data-act="insert"><svg class="ic"><use href="#i-plus"/></svg></button>
          <button class="icon-btn" title="${isRu ? "Редактировать" : "Edit"}" data-act="edit"><svg class="ic"><use href="#i-pencil"/></svg></button>
          <button class="icon-btn" title="${isRu ? "Дублировать" : "Duplicate"}" data-act="dup"><svg class="ic"><use href="#i-copy"/></svg></button>
          <button class="icon-btn btn-danger-hover" title="${isRu ? "Удалить" : "Delete"}" data-act="del"><svg class="ic"><use href="#i-trash"/></svg></button>
        </div>
      `;

      bindBlockDrag(card, phaseKey, idx);
      colEl.appendChild(card);
    });
  });

  const statsEl = $("#scenStats");
  if (statsEl) {
    statsEl.textContent = isRu ? `4 фазы · ${totalCount} блоков` : `4 phases · ${totalCount} blocks`;
  }
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[m]);
}

/* Привязка drag-событий к карточке блока */
function bindBlockDrag(el, phase, index) {
  el.addEventListener("dragstart", e => {
    e.stopPropagation();
    el.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("application/ae-block-phase", phase);
    e.dataTransfer.setData("application/ae-block-index", String(index));
  });

  el.addEventListener("dragend", () => {
    el.classList.remove("dragging");
    $$(".block-col").forEach(c => c.classList.remove("drag-over-col"));
    $$(".block-drop-placeholder").forEach(p => p.remove());
  });
}

/**
 * Вычисляет индекс вставки карточки внутри колонки фазы по координате Y курсора.
 * Исключает перетаскиваемый блок (.dragging), чтобы расчет шел по оставшимся элементам.
 */
function getDropIndex(col, clientY) {
  const cards = [...col.querySelectorAll(".block:not(.dragging)")];
  for (let i = 0; i < cards.length; i++) {
    const box = cards[i].getBoundingClientRect();
    const midY = box.top + box.height / 2;
    if (clientY < midY) {
      return i;
    }
  }
  return cards.length;
}

/* Drag & drop на колонки */
$$(".block-col").forEach(col => {
  const phaseKey = col.dataset.col;

  col.addEventListener("click", () => {
    activePhaseCol = phaseKey;
    $$(".block-col").forEach(c => c.style.outline = c === col ? "1px solid rgba(255,255,255,0.25)" : "none");
  });

  col.addEventListener("dragover", e => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    col.classList.add("drag-over-col");

    const cards = [...col.querySelectorAll(".block:not(.dragging)")];
    const dropIndex = getDropIndex(col, e.clientY);

    let placeholder = col.querySelector(".block-drop-placeholder");
    if (!placeholder) {
      // Убираем плейсхолдеры из других колонок при быстром перемещении
      $$(".block-drop-placeholder").forEach(p => p.remove());
      placeholder = document.createElement("div");
      placeholder.className = "block-drop-placeholder";
    }

    const refNode = cards[dropIndex] || null;
    if (placeholder.nextSibling !== refNode) {
      col.insertBefore(placeholder, refNode);
    }
  });

  col.addEventListener("dragleave", e => {
    // Удаляем подсветку и плейсхолдер только если курсор покинул саму колонку
    if (!col.contains(e.relatedTarget)) {
      col.classList.remove("drag-over-col");
      col.querySelectorAll(".block-drop-placeholder").forEach(p => p.remove());
    }
  });

  col.addEventListener("drop", e => {
    e.preventDefault();
    col.classList.remove("drag-over-col");

    // Вычисляем точный индекс: если был виден плейсхолдер, берем позицию ровно в нем
    let dropIndex = 0;
    const placeholder = col.querySelector(".block-drop-placeholder");
    if (placeholder) {
      const allChildren = [...col.children];
      let count = 0;
      for (const child of allChildren) {
        if (child === placeholder) {
          dropIndex = count;
          break;
        }
        if (child.classList.contains("block") && !child.classList.contains("dragging")) {
          count++;
        }
      }
      placeholder.remove();
    } else {
      dropIndex = getDropIndex(col, e.clientY);
    }
    $$(".block-drop-placeholder").forEach(p => p.remove());

    const kind = e.dataTransfer.getData("application/ae-palette-kind");
    const srcPhase = e.dataTransfer.getData("application/ae-block-phase");
    const srcIndexStr = e.dataTransfer.getData("application/ae-block-index");

    const list = currentScenario.blocks[phaseKey] || (currentScenario.blocks[phaseKey] = []);

    if (kind) {
      // Дроп нового блока из палитры на точную позицию
      const def = BLOCK_DEFS[kind];
      if (!def) return;
      const newBlock = {
        type: kind,
        params: def.defaultParams(),
        once: false,
        ...def.defaultExtra()
      };
      newBlock.comment = getActionExplanation(newBlock, phaseKey, LANG === "ru");
      dropIndex = Math.max(0, Math.min(dropIndex, list.length));
      list.splice(dropIndex, 0, newBlock);
      activePhaseCol = phaseKey;
      renderScenarioView();

      const targetCol = $(`[data-col="${phaseKey}"]`);
      if (targetCol) {
        const droppedCard = targetCol.querySelectorAll(".block")[dropIndex];
        if (droppedCard) {
          droppedCard.classList.add("block-new");
          droppedCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
      }
      toast(`Added "${def.label}" to ${phaseKey}`);
      return;
    }

    if (srcPhase && srcIndexStr !== "") {
      const srcIndex = parseInt(srcIndexStr, 10);
      const srcList = currentScenario.blocks[srcPhase];
      if (srcList && srcList[srcIndex]) {
        const [moved] = srcList.splice(srcIndex, 1);
        dropIndex = Math.max(0, Math.min(dropIndex, list.length));
        list.splice(dropIndex, 0, moved);
        activePhaseCol = phaseKey;
        renderScenarioView();

        const targetCol = $(`[data-col="${phaseKey}"]`);
        if (targetCol) {
          const droppedCard = targetCol.querySelectorAll(".block")[dropIndex];
          if (droppedCard) {
            droppedCard.classList.add("block-new");
            droppedCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }
        }
        toast(srcPhase === phaseKey ? `Reordered block in ${phaseKey}` : `Moved block to ${phaseKey}`);
      }
    }
  });
});

/* Палитра: клик добавляет в активную фазу, drag переносит в любую колонку */
$$("#palette .chip-btn").forEach(chip => {
  const kind = chip.dataset.kind;

  chip.addEventListener("dragstart", e => {
    e.dataTransfer.effectAllowed = "copy";
    e.dataTransfer.setData("application/ae-palette-kind", kind);
  });

  chip.addEventListener("dragend", () => {
    $$(".block-col").forEach(c => c.classList.remove("drag-over-col"));
    $$(".block-drop-placeholder").forEach(p => p.remove());
  });

  chip.addEventListener("click", () => {
    const def = BLOCK_DEFS[kind];
    if (!def) return;
    const targetPhase = activePhaseCol || "battle";
    const list = currentScenario.blocks[targetPhase] || (currentScenario.blocks[targetPhase] = []);
    const newBlock = {
      type: kind,
      params: def.defaultParams(),
      once: false,
      ...def.defaultExtra()
    };
    newBlock.comment = getActionExplanation(newBlock, targetPhase, LANG === "ru");
    list.push(newBlock);
    renderScenarioView();

    const col = $(`[data-col="${targetPhase}"]`);
    if (col && col.lastElementChild) {
      col.lastElementChild.classList.add("block-new");
      col.lastElementChild.scrollIntoView({ behavior: scrollBehavior, block: "nearest" });
    }
    toast(LANG === "ru" ? `Добавлено "${def.labelRu || def.label}" в ${targetPhase}` : `Added "${def.label}" to ${targetPhase}`);
  });
});

/* Действия по клику внутри колонок: Edit, Duplicate, Delete */
document.addEventListener("click", e => {
  const actBtn = e.target.closest ? e.target.closest(".block-acts button") : null;
  if (!actBtn) return;

  const card = actBtn.closest(".block");
  if (!card) return;

  const phase = card.dataset.phase;
  const index = parseInt(card.dataset.index, 10);
  const list = currentScenario.blocks[phase];
  if (!list || !list[index]) return;

  const act = actBtn.dataset.act;
  if (act === "insert") {
    openInsertActionModal(phase, index);
  } else if (act === "edit") {
    openBlockModal(phase, index, list[index]);
  } else if (act === "dup") {
    const clone = JSON.parse(JSON.stringify(list[index]));
    list.splice(index + 1, 0, clone);
    renderScenarioView();
    toast(LANG === "ru" ? "Блок продублирован" : "Block duplicated");
  } else if (act === "del") {
    list.splice(index, 1);
    renderScenarioView();
    toast(LANG === "ru" ? "Блок удален" : "Block removed");
  }
});

/* Модалка вставки действия между шагами сценария */
let insertTargetPhase = null;
let insertTargetIndex = null;

function openInsertActionModal(phase, index) {
  insertTargetPhase = phase;
  insertTargetIndex = index;

  const modal = $("#insertActionModal");
  const grid = $("#insertActionGrid");
  const sub = $("#insertActionSub");
  if (!modal || !grid) return;

  const currentList = currentScenario.blocks[phase] || [];
  const currentBlock = currentList[index];
  const stepNum = index + 1;
  const currentLabel = currentBlock
    ? ((LANG === "ru" && BLOCK_DEFS[currentBlock.type]?.labelRu) ? BLOCK_DEFS[currentBlock.type].labelRu : (BLOCK_DEFS[currentBlock.type]?.label || currentBlock.type))
    : (LANG === "ru" ? "шага" : "step");

  if (sub) {
    sub.textContent = LANG === "ru"
      ? `Вставить действие после шага #${stepNum} (${currentLabel})`
      : `Insert action after step #${stepNum} (${currentLabel})`;
  }

  const actionsList = [
    { kind: "walk_path", label: "Walk Path", labelRu: "Путь ходьбы", desc: "Follow recorded path route", ru: "Движение по маршруту", icon: "i-route" },
    { kind: "walk", label: "Walk (WASD)", labelRu: "Ходьба WASD", desc: "Movement in direction for duration", ru: "Шаги WASD в сторону", icon: "i-route" },
    { kind: "wait_ms", label: "Wait (ms)", labelRu: "Ждать (мс)", desc: "Pause between actions", ru: "Пауза в миллисекундах", icon: "i-clock" },
    { kind: "click", label: "Click", labelRu: "Клик мышью", desc: "Click coordinate on window", ru: "Клик по координатам", icon: "i-mouse" },
    { kind: "place_unit", label: "Place Unit", labelRu: "Поставить юнита", desc: "Place unit on field", ru: "Расстановка юнита", icon: "i-up" },
    { kind: "upgrade_unit", label: "Upgrade Unit", labelRu: "Прокачать юнита", desc: "Upgrade placed unit", ru: "Улучшение юнита", icon: "i-up" },
    { kind: "send_key", label: "Send Key", labelRu: "Нажать клавишу", desc: "Simulate keyboard key press", ru: "Нажатие клавиши", icon: "i-sliders" },
    { kind: "detect", label: "Detect Image", labelRu: "Проверка картинки", desc: "Vision branch on sighting", ru: "Проверка картинки / ветвление", icon: "i-branch" },
    { kind: "wait_wave", label: "Wait Wave", labelRu: "Ждать волну", desc: "Wait until specific wave begins", ru: "Ожидание волны", icon: "i-clock" },
    { kind: "sell_unit", label: "Sell Unit", labelRu: "Продать юнита", desc: "Sell targeted unit", ru: "Продажа юнита", icon: "i-tag" },
  ];

  grid.innerHTML = "";
  actionsList.forEach(act => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "insert-action-btn";
    const titleText = (LANG === "ru" && act.labelRu) ? act.labelRu : act.label;
    btn.innerHTML = `
      <div class="block-ic"><svg class="ic"><use href="#${act.icon}"/></svg></div>
      <div>
        <strong>${escapeHtml(titleText)}</strong>
        <span>${LANG === "ru" ? act.ru : act.desc}</span>
      </div>
    `;
    btn.addEventListener("click", () => {
      const def = BLOCK_DEFS[act.kind];
      if (!def) return;
      const newBlock = {
        type: act.kind,
        params: def.defaultParams(),
        once: phase === "prestart",
        ...def.defaultExtra()
      };
      newBlock.comment = getActionExplanation(newBlock, phase, LANG === "ru");
      currentList.splice(index + 1, 0, newBlock);
      closeInsertActionModal();
      renderScenarioView();
      openBlockModal(phase, index + 1, newBlock);
      toast((LANG === "ru" ? "Вставлено действие: " : "Inserted action: ") + titleText);
    });
    grid.appendChild(btn);
  });

  modal.hidden = false;
}

function closeInsertActionModal() {
  const modal = $("#insertActionModal");
  if (modal) modal.hidden = true;
  insertTargetPhase = null;
  insertTargetIndex = null;
}

$("#insertActionClose")?.addEventListener("click", closeInsertActionModal);
$("#insertActionModal")?.addEventListener("click", (e) => {
  if (e.target === $("#insertActionModal")) closeInsertActionModal();
});

/* Двойной клик открывает редактирование */
document.addEventListener("dblclick", e => {
  const card = e.target.closest ? e.target.closest(".block") : null;
  if (card && !e.target.closest(".block-acts")) {
    const phase = card.dataset.phase;
    const index = parseInt(card.dataset.index, 10);
    const list = currentScenario.blocks[phase];
    if (list && list[index]) openBlockModal(phase, index, list[index]);
  }
});

/* ========================================================= ДИНАМИЧЕСКАЯ МОДАЛКА БЛОКА === */
const blockModal = $("#blockModal");
const blockModalBody = $("#blockModalBody");

function openBlockModal(phase, index, block) {
  editingBlockContext = { phase, index, block };
  const def = BLOCK_DEFS[block.type] || { label: block.type };
  const isRu = (LANG === "ru");

  $("#blockModalTitle").textContent = isRu ? `Редактирование: ${def.labelRu || def.label}` : `Edit: ${def.label}`;

  const smartHint = getActionExplanation(block, phase, isRu);

  let fieldsHtml = `
    <div class="field" style="margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--glass-line-2);">
      <label for="bmComment">${isRu ? "Заметка к действию (для чего этот шаг)" : "Step Note / Comment"}</label>
      <div style="display:flex; gap:8px; align-items:center;">
        <input type="text" id="bmComment" value="${escapeHtml(block.comment || "")}" placeholder="${isRu ? "например: Взять удочку, Заброс в озеро, Поставить Годжо..." : "e.g.: Equip rod, Cast into lake, Place Gojo..."}">
        ${smartHint ? `<button type="button" class="btn btn-ghost btn-xs" id="bmApplySmartHint" style="white-space:nowrap; padding: 5px 9px; font-size: 11px;" title="${isRu ? "Использовать автоподпись" : "Use auto-signature"}">${isRu ? "Автоподпись" : "Auto-sign"}</button>` : ""}
      </div>
      ${smartHint ? `<div class="field-hint" style="color:var(--tx-2); font-size:11px; margin-top:5px; display:flex; align-items:center; gap:5px;"><svg class="ic" style="width:12px; height:12px; opacity:0.8;"><use href="#i-help"/></svg><span>${isRu ? "Авто-пояснение действия: " : "Smart explanation: "}<strong>${escapeHtml(smartHint)}</strong></span></div>` : ""}
    </div>
  `;

  const params = block.params || {};

  // Динамические поля формы в зависимости от типа блока
  if (block.type === "place_unit") {
    fieldsHtml += `
      <div class="form-grid-2">
        <div class="field">
          <label for="bmUnitName">${isRu ? "Имя юнита" : "Unit Name"}</label>
          <input type="text" id="bmUnitName" value="${escapeHtml(params.name || "")}" placeholder="${isRu ? "farm или имя юнита" : "farm"}">
        </div>
        <div class="field">
          <label for="bmHotkey">${isRu ? "Горячая клавиша (1-6)" : "Hotkey (1-6)"}</label>
          <input type="text" id="bmHotkey" value="${escapeHtml(block.hotkey || "1")}" maxlength="2" placeholder="5">
        </div>
      </div>
      <div class="form-grid-2">
        <div class="field">
          <label for="bmX">${isRu ? "Координата X" : "Coordinate X"}</label>
          <input type="number" id="bmX" value="${params.x ?? 0}" min="0" max="1152">
        </div>
        <div class="field">
          <label for="bmY">${isRu ? "Координата Y" : "Coordinate Y"}</label>
          <input type="number" id="bmY" value="${params.y ?? 0}" min="0" max="756">
        </div>
      </div>
      <div class="field field-checkbox">
        <input type="checkbox" id="bmRetry" ${block.retryUntilPlaced ? "checked" : ""}>
        <label for="bmRetry">${isRu ? "Повторять установку до успеха" : "Retry placement until successful"}</label>
      </div>
    `;
  } else if (block.type === "click") {
    fieldsHtml = `
      <div class="form-grid-2">
        <div class="field">
          <label for="bmX">${isRu ? "Координата X (0 - 1152)" : "X (0 - 1152)"}</label>
          <input type="number" id="bmX" value="${params.x ?? 0}" min="0" max="1152">
        </div>
        <div class="field">
          <label for="bmY">${isRu ? "Координата Y (0 - 756)" : "Y (0 - 756)"}</label>
          <input type="number" id="bmY" value="${params.y ?? 0}" min="0" max="756">
        </div>
      </div>
    `;
  } else if (block.type === "drag") {
    fieldsHtml = `
      <div class="form-grid-4">
        <div class="field"><label>${isRu ? "X1 (Старт)" : "X1"}</label><input type="number" id="bmX1" value="${params.x1 ?? 0}"></div>
        <div class="field"><label>${isRu ? "Y1 (Старт)" : "Y1"}</label><input type="number" id="bmY1" value="${params.y1 ?? 0}"></div>
        <div class="field"><label>${isRu ? "X2 (Конец)" : "X2"}</label><input type="number" id="bmX2" value="${params.x2 ?? 0}"></div>
        <div class="field"><label>${isRu ? "Y2 (Конец)" : "Y2"}</label><input type="number" id="bmY2" value="${params.y2 ?? 0}"></div>
      </div>
      <div class="form-grid-2">
        <div class="field"><label>${isRu ? "Шагов перемещения" : "Steps"}</label><input type="number" id="bmSteps" value="${params.steps || 30}"></div>
        <div class="field"><label>${isRu ? "Длительность (мс)" : "Duration (ms)"}</label><input type="number" id="bmDur" value="${params.duration_ms || 600}"></div>
      </div>
    `;
  } else if (block.type === "wait_ms") {
    fieldsHtml = `
      <div class="field">
        <label for="bmMs">${isRu ? "Длительность ожидания (мс)" : "Wait Duration (ms)"}</label>
        <input type="number" id="bmMs" value="${params.ms ?? block.ms ?? 1000}" min="10" step="50">
      </div>
    `;
  } else if (block.type === "wait_wave") {
    fieldsHtml = `
      <div class="field">
        <label for="bmWave">${isRu ? "Номер целевой волны" : "Target Wave Number"}</label>
        <input type="number" id="bmWave" value="${params.wave ?? block.wave ?? 1}" min="1" max="150">
      </div>
    `;
  } else if (block.type === "leave_at_minute") {
    fieldsHtml = `
      <div class="field">
        <label for="bmMinutes">${isRu ? "Минута выхода из матча" : "Match Duration (minutes)"}</label>
        <input type="number" id="bmMinutes" value="${params.minutes ?? block.minutes ?? 10}" min="1" max="120">
      </div>
    `;
  } else if (block.type === "walk_path") {
    const isRu = (LANG === "ru");
    const currentPath = block.pathName || block.params?.path || "";
    const optionsHtml = savedWalkPaths.map(p =>
      `<option value="${escapeHtml(p)}" ${p === currentPath ? "selected" : ""}>${escapeHtml(p)}</option>`
    ).join("");

    fieldsHtml = `
      <div class="field">
        <label for="bmMode">${isRu ? "Режим маршрута" : "Walk Mode"}</label>
        <select id="bmMode">
          <option value="auto" ${block.mode === "auto" ? "selected" : ""}>${isRu ? "Авто (Маршрут по умолчанию)" : "Auto (Map default path)"}</option>
          <option value="custom" ${block.mode === "custom" ? "selected" : ""}>${isRu ? "Свой (Выбрать или записать)" : "Custom (Select or record path)"}</option>
          <option value="none" ${block.mode === "none" ? "selected" : ""}>${isRu ? "Без движения (Стоять на месте)" : "None (Stay put at spawn)"}</option>
        </select>
      </div>
      <div id="bmCustomPathWrap" style="${block.mode === "custom" ? "" : "display:none;"}">
        <div class="field" style="margin-top: 10px;">
          <label for="bmPathSelect">${isRu ? "Выбрать сохранённый маршрут" : "Select Recorded Path"}</label>
          <div style="display:flex; gap:8px; align-items:center;">
            <select id="bmPathSelect" style="flex:1;">
              <option value="">${isRu ? "-- Выберите маршрут --" : "-- Choose saved path --"}</option>
              ${optionsHtml}
            </select>
            <button type="button" class="btn btn-ghost btn-sm" id="bmBtnRecordPath" style="white-space:nowrap; gap:6px;">
              <svg class="ic" style="width:14px; height:14px;"><use href="#i-route"/></svg>
              <span>${isRu ? "Записать WASD" : "Record WASD"}</span>
            </button>
          </div>
        </div>
        <div class="field" style="margin-top: 8px;">
          <label for="bmPathName">${isRu ? "Или имя файла маршрута" : "Or type path name"}</label>
          <input type="text" id="bmPathName" value="${escapeHtml(currentPath)}" placeholder="${isRu ? "например Summer или East Town" : "e.g. Summer or East Town"}">
        </div>
      </div>
      <div class="field field-checkbox" style="margin-top: 10px;">
        <input type="checkbox" id="bmSprint" ${block.sprint ? "checked" : ""}>
        <label for="bmSprint">${isRu ? "Бег с зажатым Shift при ходьбе" : "Sprint with Shift while walking"}</label>
      </div>
    `;
  } else if (block.type === "walk") {
    const isRu = (LANG === "ru");
    const currentPath = block.pathName || block.params?.path || "";
    const isRecordOnReach = Boolean(block.recordOnReach || block.params?.recordOnReach || (!currentPath && block.recordOnReach !== false));
    const optionsHtml = savedWalkPaths.map(p =>
      `<option value="${escapeHtml(p)}" ${p === currentPath ? "selected" : ""}>${escapeHtml(p)}</option>`
    ).join("");

    fieldsHtml = `
      <div class="block-teachin-card">
        <div class="block-teachin-head">
          <div class="block-teachin-meta">
            <div class="block-teachin-ic">
              <svg class="ic"><use href="#i-route"/></svg>
            </div>
            <div class="block-teachin-texts">
              <strong>${isRu ? "Записать маршрут на ходу (Teach-In)" : "Record movement on first run (Teach-In)"}</strong>
              <span>${isRu ? "При первом прогоне макрос активирует Roblox, запишет вашу ходьбу на WASD и сам продолжит сценарий после паузы (1.8с)." : "When reached, macro focuses Roblox, captures your WASD path, auto-saves on pause (1.8s), and continues."}</span>
            </div>
          </div>
          <label class="switch">
            <input type="checkbox" id="bmRecordOnReach" ${isRecordOnReach ? "checked" : ""}>
            <i></i>
          </label>
        </div>
      </div>
      <div class="field">
        <label for="bmPathSelect">${isRu ? "Выбрать сохранённый маршрут" : "Select Recorded Path"}</label>
        <div style="display:flex; gap:8px; align-items:center;">
          <select id="bmPathSelect" style="flex:1;">
            <option value="">${isRu ? "-- Выберите маршрут --" : "-- Choose saved path --"}</option>
            ${optionsHtml}
          </select>
          <button type="button" class="btn btn-ghost btn-sm" id="bmBtnRecordPath" style="white-space:nowrap; gap:6px;">
            <svg class="ic" style="width:14px; height:14px;"><use href="#i-route"/></svg>
            <span>${isRu ? "Записать WASD" : "Record WASD"}</span>
          </button>
        </div>
      </div>
      <div class="field" style="margin-top: 8px;">
        <label for="bmPathName">${isRu ? "Или имя файла маршрута" : "Or type path name"}</label>
        <input type="text" id="bmPathName" value="${escapeHtml(currentPath)}" placeholder="${isRu ? "например Summer или East Town" : "e.g. Summer or East Town"}">
      </div>
      <div class="field field-checkbox" style="margin-top: 10px;">
        <input type="checkbox" id="bmSprint" ${block.sprint ? "checked" : ""}>
        <label for="bmSprint">${isRu ? "Бег с зажатым Shift при ходьбе" : "Sprint with Shift while walking"}</label>
      </div>
    `;
  } else if (block.type === "upgrade_unit" || block.type === "auto_upgrade_unit" || block.type === "sell_unit") {
    fieldsHtml = `
      <div class="form-grid-2">
        <div class="field">
          <label for="bmUnit">${isRu ? "Номер юнита #" : "Unit #"}</label>
          <input type="number" id="bmUnit" value="${block.unit || params.unit || 1}" min="1" max="20">
        </div>
        ${block.type === "upgrade_unit" ? `
        <div class="field">
          <label for="bmUpgrades">${isRu ? "Количество улучшений" : "Upgrades Count"}</label>
          <input type="number" id="bmUpgrades" value="${block.upgrades || params.upgrades || 1}" min="1" max="15">
        </div>` : ""}
      </div>
    `;
  } else if (block.type === "target_priority") {
    fieldsHtml = `
      <div class="form-grid-2">
        <div class="field">
          <label for="bmUnit">${isRu ? "Номер юнита #" : "Unit #"}</label>
          <input type="number" id="bmUnit" value="${block.unit || 1}" min="1" max="20">
        </div>
        <div class="field">
          <label for="bmPriority">${isRu ? "Приоритет цели" : "Priority"}</label>
          <select id="bmPriority">
            <option value="Strongest" ${block.priority === "Strongest" ? "selected" : ""}>${isRu ? "Сильнейший (Strongest)" : "Strongest"}</option>
            <option value="First" ${block.priority === "First" ? "selected" : ""}>${isRu ? "Первый (First)" : "First"}</option>
            <option value="Last" ${block.priority === "Last" ? "selected" : ""}>${isRu ? "Последний (Last)" : "Last"}</option>
            <option value="Weakest" ${block.priority === "Weakest" ? "selected" : ""}>${isRu ? "Слабейший (Weakest)" : "Weakest"}</option>
            <option value="Closest" ${block.priority === "Closest" ? "selected" : ""}>${isRu ? "Ближайший (Closest)" : "Closest"}</option>
          </select>
        </div>
      </div>
    `;
  } else if (block.type === "send_key") {
    fieldsHtml = `
      <div class="form-grid-2">
        <div class="field">
          <label for="bmKey">${isRu ? "Клавиша" : "Key"}</label>
          <input type="text" id="bmKey" value="${escapeHtml(params.key || block.key || "e")}" maxlength="10">
        </div>
        <div class="field">
          <label for="bmHold">${isRu ? "Время удержания (мс)" : "Hold Duration (ms)"}</label>
          <input type="number" id="bmHold" value="${params.hold_ms || 0}" min="0">
        </div>
      </div>
    `;
  } else if (block.type === "detect") {
    fieldsHtml = `
      <div class="form-grid-2">
        <div class="field">
          <label for="bmImage">${isRu ? "Имя шаблона картинки" : "Template Image"}</label>
          <input type="text" id="bmImage" value="${escapeHtml(block.image || "")}" placeholder="Game_results">
        </div>
        <div class="field">
          <label for="bmDetMode">${isRu ? "Режим проверки" : "Mode"}</label>
          <select id="bmDetMode">
            <option value="single" ${block.mode === "single" ? "selected" : ""}>${isRu ? "Одно изображение (Single)" : "Single image"}</option>
            <option value="all" ${block.mode === "all" ? "selected" : ""}>${isRu ? "Все совпадения (All)" : "All"}</option>
          </select>
        </div>
      </div>
    `;
  } else {
    fieldsHtml = `
      <div class="field">
        <label for="bmRaw">${isRu ? "Сырые параметры (JSON)" : "Raw parameters (JSON)"}</label>
        <input type="text" id="bmRaw" value="${escapeHtml(JSON.stringify(params))}">
      </div>
    `;
  }

  // Общее поле для всех блоков: "выполнять один раз за матч"
  fieldsHtml += `
    <div class="field field-checkbox" style="margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--glass-line-2);">
      <input type="checkbox" id="bmOnce" ${block.once ? "checked" : ""}>
      <label for="bmOnce">${isRu ? "Выполнять один раз за матч (пропускать в циклах)" : "Run once per match (ignore in subsequent loops)"}</label>
    </div>
  `;

  blockModalBody.innerHTML = fieldsHtml;
  blockModal.hidden = false;

  const btnApplySmart = $("#bmApplySmartHint");
  if (btnApplySmart) {
    btnApplySmart.addEventListener("click", () => {
      const commentInput = $("#bmComment");
      if (commentInput && smartHint) {
        commentInput.value = smartHint;
        commentInput.focus();
      }
    });
  }

  // Динамические обработчики для выбора и записи маршрутов ходьбы
  const modeSelect = $("#bmMode");
  const customWrap = $("#bmCustomPathWrap");
  if (modeSelect && customWrap) {
    modeSelect.addEventListener("change", () => {
      customWrap.style.display = modeSelect.value === "custom" ? "" : "none";
    });
  }

  const pathSelect = $("#bmPathSelect");
  const pathInput = $("#bmPathName");
  if (pathSelect && pathInput) {
    pathSelect.addEventListener("change", () => {
      if (pathSelect.value) {
        pathInput.value = pathSelect.value;
      }
    });
  }

  const recordBtn = $("#bmBtnRecordPath");
  if (recordBtn) {
    recordBtn.addEventListener("click", () => {
      startPathRecordingFlow(phase, index, block);
    });
  }
}

function closeBlockModal() {
  blockModal.hidden = true;
  editingBlockContext = null;
}

$("#blockSave")?.addEventListener("click", () => {
  if (!editingBlockContext) return closeBlockModal();
  const { block } = editingBlockContext;

  block.once = $("#bmOnce") ? $("#bmOnce").checked : false;

  if (block.type === "place_unit") {
    block.params = block.params || {};
    block.params.name = $("#bmUnitName") ? $("#bmUnitName").value.trim() : "farm";
    block.hotkey = $("#bmHotkey") ? $("#bmHotkey").value.trim() : "1";
    block.params.x = parseInt($("#bmX")?.value || 0, 10);
    block.params.y = parseInt($("#bmY")?.value || 0, 10);
    block.retryUntilPlaced = $("#bmRetry") ? $("#bmRetry").checked : false;
  } else if (block.type === "click") {
    block.params = block.params || {};
    block.params.x = parseInt($("#bmX")?.value || 0, 10);
    block.params.y = parseInt($("#bmY")?.value || 0, 10);
  } else if (block.type === "drag") {
    block.params = block.params || {};
    block.params.x1 = parseInt($("#bmX1")?.value || 0, 10);
    block.params.y1 = parseInt($("#bmY1")?.value || 0, 10);
    block.params.x2 = parseInt($("#bmX2")?.value || 0, 10);
    block.params.y2 = parseInt($("#bmY2")?.value || 0, 10);
    block.params.steps = parseInt($("#bmSteps")?.value || 30, 10);
    block.params.duration_ms = parseInt($("#bmDur")?.value || 600, 10);
  } else if (block.type === "wait_ms") {
    block.params = block.params || {};
    block.params.ms = parseInt($("#bmMs")?.value || 1000, 10);
  } else if (block.type === "wait_wave") {
    block.params = block.params || {};
    block.params.wave = parseInt($("#bmWave")?.value || 1, 10);
  } else if (block.type === "leave_at_minute") {
    block.params = block.params || {};
    block.params.minutes = parseInt($("#bmMinutes")?.value || 10, 10);
  } else if (block.type === "walk_path") {
    block.mode = $("#bmMode")?.value || "auto";
    const chosen = $("#bmPathName")?.value.trim() || $("#bmPathSelect")?.value || "";
    block.pathName = chosen;
    block.params = block.params || {};
    block.params.path = chosen;
    block.sprint = $("#bmSprint") ? $("#bmSprint").checked : false;
  } else if (block.type === "walk") {
    const chosen = $("#bmPathName")?.value.trim() || $("#bmPathSelect")?.value || "";
    block.pathName = chosen;
    block.params = block.params || {};
    block.params.path = chosen;
    block.sprint = $("#bmSprint") ? $("#bmSprint").checked : false;
    const recOnReach = $("#bmRecordOnReach") ? $("#bmRecordOnReach").checked : false;
    block.recordOnReach = recOnReach;
    block.params.recordOnReach = recOnReach;
  } else if (block.type === "upgrade_unit" || block.type === "auto_upgrade_unit" || block.type === "sell_unit") {
    block.unit = parseInt($("#bmUnit")?.value || 1, 10);
    if (block.type === "upgrade_unit") block.upgrades = parseInt($("#bmUpgrades")?.value || 1, 10);
  } else if (block.type === "target_priority") {
    block.unit = parseInt($("#bmUnit")?.value || 1, 10);
    block.priority = $("#bmPriority")?.value || "Strongest";
  } else if (block.type === "send_key") {
    block.params = block.params || {};
    block.params.key = $("#bmKey")?.value.trim() || "e";
    block.params.hold_ms = parseInt($("#bmHold")?.value || 0, 10);
  } else if (block.type === "detect") {
    block.image = $("#bmImage")?.value.trim() || "";
    block.mode = $("#bmDetMode")?.value || "single";
  }

  const commentVal = $("#bmComment")?.value.trim() || "";
  if (commentVal) {
    block.comment = commentVal;
  } else {
    delete block.comment;
  }

  closeBlockModal();
  renderScenarioView();
  toast(LANG === "ru" ? "Действие сохранено" : "Block saved");
});

/* ========================================================= ЗАПИСЬ МАРШРУТА WASD === */
let pendingPathRecordContext = null;

async function startPathRecordingFlow(phase, index, block) {
  pendingPathRecordContext = { phase, index, block };
  closeBlockModal();

  if (window.pywebview?.api?.start_path_recording) {
    setScreen("home");
    await new Promise(r => setTimeout(r, 220));
    try {
      const res = await window.pywebview.api.start_path_recording();
      if (!res || !res.ok) {
        toast((LANG === "ru" ? "Не удалось начать запись: " : "Could not start recording: ") + (res?.reason || "Roblox not found"));
        setScreen("scenarios");
        pendingPathRecordContext = null;
        return;
      }
    } catch (err) {
      toast((LANG === "ru" ? "Ошибка записи: " : "Recording error: ") + err);
      setScreen("scenarios");
      pendingPathRecordContext = null;
      return;
    }
  }

  const popout = $("#recPopout");
  const popoutTitle = $("#recPopoutTitle");
  const popoutText = $("#recPopoutText");
  if (popoutTitle) {
    popoutTitle.textContent = (LANG === "ru") ? "Запись маршрута WASD" : "Recording WASD Path";
  }
  if (popoutText) {
    popoutText.textContent = (LANG === "ru") ? "Идите в игре на WASD · Таймер с первой клавиши" : "Walk in game with WASD · Timer starts on first key";
  }
  if (popout) {
    popout.hidden = false;
    popout.style.display = "flex";
  }
  toast(LANG === "ru" ? "Запись начата! Идите в игре на WASD. Таймер стартует с первой клавиши." : "Recording started! Walk in game with WASD. Timer starts on first key.");
}

async function stopPathRecordingFlow() {
  const popout = $("#recPopout");
  if (popout) {
    popout.hidden = true;
    popout.style.display = "none";
  }

  if (!pendingPathRecordContext) {
    // Живая запись движения на ходу во время выполнения макроса (Teach-In)
    if (window.pywebview?.api?.finish_live_walk_record) {
      try { await window.pywebview.api.finish_live_walk_record(); } catch (e) {}
    }
    return;
  }

  let stopResult = null;
  if (window.pywebview?.api?.stop_path_capture) {
    try {
      stopResult = await window.pywebview.api.stop_path_capture();
    } catch (e) {}
  } else {
    stopResult = { ok: true, count: 5 };
  }

  if (!stopResult || !stopResult.count) {
    toast(LANG === "ru" ? "Движение не обнаружено, запись отменена" : "No movement detected, recording cancelled");
    if (window.pywebview?.api?.discard_pending_path) {
      try { await window.pywebview.api.discard_pending_path(); } catch (e) {}
    }
    pendingPathRecordContext = null;
    setScreen("scenarios");
    return;
  }

  // Переключаемся на сценарии и скрываем окно Roblox до показа модалки:
  // Roblox прицеплен через SetParent и перекрывает HTML-модалки на экране Home.
  setScreen("scenarios");
  if (window.pywebview?.api?.hide_game) {
    try { await window.pywebview.api.hide_game(); } catch (_) {}
  }

  const saveModal = $("#savePathModal");
  const saveInput = $("#savePathInput");
  if (saveModal && saveInput) {
    const suggested = currentScenario?.name ? `${currentScenario.name} Walk` : "Custom Walk";
    saveInput.value = suggested;
    saveModal.hidden = false;
    setTimeout(() => { saveInput.focus(); saveInput.select(); }, 60);
  }
}

async function confirmSaveRecordedPath() {
  const saveModal = $("#savePathModal");
  const saveInput = $("#savePathInput");
  const name = saveInput?.value.trim() || ("Walk " + new Date().toLocaleTimeString());

  if (window.pywebview?.api?.save_pending_path) {
    try {
      await window.pywebview.api.save_pending_path(name);
    } catch (e) {}
  }

  if (saveModal) saveModal.hidden = true;

  await refreshSavedWalkPaths();

  if (pendingPathRecordContext) {
    const { block } = pendingPathRecordContext;
    block.pathName = name;
    block.params = block.params || {};
    block.params.path = name;
    if (block.type === "walk_path") {
      block.mode = "custom";
    }
  }
  pendingPathRecordContext = null;

  setScreen("scenarios");
  renderScenarioView();
  toast((LANG === "ru" ? "Маршрут сохранён: " : "Saved path: ") + name);
}

async function discardRecordedPath() {
  const saveModal = $("#savePathModal");
  if (saveModal) saveModal.hidden = true;

  if (window.pywebview?.api?.discard_pending_path) {
    try { await window.pywebview.api.discard_pending_path(); } catch (e) {}
  }
  pendingPathRecordContext = null;
  setScreen("scenarios");
  toast(LANG === "ru" ? "Запись отменена" : "Recording discarded");
}

$("#btnStopPathRec")?.addEventListener("click", stopPathRecordingFlow);
$("#savePathConfirm")?.addEventListener("click", confirmSaveRecordedPath);
$("#savePathDiscard")?.addEventListener("click", discardRecordedPath);
$("#savePathClose")?.addEventListener("click", discardRecordedPath);
$("#savePathInput")?.addEventListener("keydown", e => {
  if (e.key === "Enter") confirmSaveRecordedPath();
  if (e.key === "Escape") discardRecordedPath();
});

window.onLiveWalkRecordStart = function(data) {
  const popout = $("#recPopout");
  const popoutTitle = $("#recPopoutTitle");
  const popoutText = $("#recPopoutText");
  if (popout) {
    const isRu = (LANG === "ru");
    const phaseStr = data?.phase || "Battle";
    if (popoutTitle) {
      popoutTitle.textContent = isRu
        ? `Запись движения (${phaseStr} #${data?.block_num || 1})`
        : `WASD Recording (${phaseStr} #${data?.block_num || 1})`;
    }
    if (popoutText) {
      popoutText.textContent = isRu
        ? "Идите на WASD в Roblox · Остановка на 1.8с сохранит путь"
        : "Walk with WASD in Roblox · 1.8s pause auto-saves";
    }
    popout.hidden = false;
    popout.style.display = "flex";
  }
  toast(LANG === "ru"
    ? "Запись движения начата! Идите на WASD в Roblox. Остановка на 1.8с сохранит путь."
    : "Movement recording started! Walk with WASD in Roblox. Pause 1.8s to save.");
};

window.onLiveWalkRecordDone = function(data) {
  const popout = $("#recPopout");
  if (popout) {
    popout.hidden = true;
    popout.style.display = "none";
  }
  if (data && data.saved) {
    toast(LANG === "ru"
      ? `Маршрут "${data.path_name}" сохранён! Продолжаем сценарий...`
      : `Path "${data.path_name}" saved! Continuing scenario...`);
    if (window.pywebview?.api?.list_paths) {
      window.pywebview.api.list_paths().then(p => {
        if (Array.isArray(p)) savedWalkPaths = p;
      }).catch(() => {});
    }
  }
};

$("#blockDelete")?.addEventListener("click", () => {
  if (!editingBlockContext) return closeBlockModal();
  const { phase, index } = editingBlockContext;
  const list = currentScenario.blocks[phase];
  if (list && list[index]) {
    list.splice(index, 1);
  }
  const popout = $("#recPopout");
  if (popout && pendingPathRecordContext) {
    popout.hidden = true;
    popout.style.display = "none";
    if (window.pywebview?.api?.cancel_path_recording) {
      try { window.pywebview.api.cancel_path_recording(); } catch (e) {}
    }
    pendingPathRecordContext = null;
  }
  closeBlockModal();
  renderScenarioView();
  toast(LANG === "ru" ? "Действие удалено" : "Block deleted");
});

$("#blockCancel")?.addEventListener("click", closeBlockModal);
$("#blockModalClose")?.addEventListener("click", closeBlockModal);
blockModal?.addEventListener("click", e => { if (e.target === blockModal) closeBlockModal(); });
window.addEventListener("keydown", e => {
  if (e.key === "Escape" && blockModal && !blockModal.hidden) {
    e.stopPropagation();
    closeBlockModal();
  }
});

/* ========================================================= ТУЛБАР СЦЕНАРИЕВ === */
$("#scenSelect")?.addEventListener("change", e => {
  loadScenario(e.target.value);
  toast(`Loaded scenario: ${e.target.value}`);
});

/* Сохранить сценарий */
$("#btnSaveScen")?.addEventListener("click", async () => {
  const popout = $("#recPopout");
  if (popout && pendingPathRecordContext) {
    popout.hidden = true;
    popout.style.display = "none";
    if (window.pywebview?.api?.cancel_path_recording) {
      try { await window.pywebview.api.cancel_path_recording(); } catch (_) {}
    }
    pendingPathRecordContext = null;
  }
  const newName = $("#scenNameInput")?.value.trim() || currentScenario.name || "Untitled";
  currentScenario.name = newName;

  if (window.pywebview?.api?.save_template) {
    try {
      await window.pywebview.api.save_template(newName, currentScenario.blocks);
    } catch (err) {
      toast("Error saving template via API");
    }
  }

  saveLocalScenario(currentScenario);
  await refreshScenarioList(newName);
  renderScenarioView();
  toast(`Scenario "${newName}" saved`);
});

/* Создать новый сценарий */
$("#btnNewScen")?.addEventListener("click", () => {
  const name = "New Scenario " + Math.floor(Math.random() * 100 + 1);
  currentScenario = {
    name,
    blocks: {
      team: "",
      equipment: "include",
      prestart: [{ type: "walk_path", params: {}, once: true, mode: "auto", pathName: "", sprint: false }],
      battle: [],
      loop_a: [],
      loop_b: []
    }
  };
  saveLocalScenario(currentScenario);
  refreshScenarioList(name);
  renderScenarioView();
  toast(`Created new scenario: "${name}"`);
});

/* Удалить сценарий */
$("#btnDelScen")?.addEventListener("click", async () => {
  const name = currentScenario.name;
  if (!name) return;

  if (window.pywebview?.api?.delete_template) {
    try {
      await window.pywebview.api.delete_template(name);
    } catch {}
  }
  deleteLocalScenario(name);
  toast(`Deleted scenario "${name}"`);

  await refreshScenarioList();
  const select = $("#scenSelect");
  const next = select?.value || "Inf Summer";
  await loadScenario(next);
});

/* Открыть папку Templates */
$("#btnFolderScen")?.addEventListener("click", () => {
  if (window.pywebview?.api?.open_templates_folder) {
    window.pywebview.api.open_templates_folder();
  } else {
    toast("Opening Templates folder in Explorer");
  }
});

/* Тестовый прогон: валидация всех блоков и координат */
$("#btnTestRun")?.addEventListener("click", () => {
  const blocks = currentScenario.blocks || {};
  const issues = [];
  let totalBlocks = 0;

  ["prestart", "battle", "loop_a", "loop_b"].forEach(phaseKey => {
    const list = blocks[phaseKey] || [];
    totalBlocks += list.length;
    list.forEach((b, i) => {
      const p = b.params || {};
      if (b.type === "click" || b.type === "place_unit") {
        const x = p.x ?? b.x;
        const y = p.y ?? b.y;
        if (x == null || y == null || isNaN(x) || isNaN(y)) {
          issues.push(`${phaseKey} #${i + 1} (${b.type}): invalid coordinates`);
        } else if (x < 0 || x > 1152 || y < 0 || y > 756) {
          issues.push(`${phaseKey} #${i + 1} (${b.type}): (${x}, ${y}) is outside 1152×756 window`);
        }
      }
      if (b.type === "wait_ms") {
        const ms = p.ms ?? b.ms;
        if (ms == null || isNaN(ms) || ms <= 0) issues.push(`${phaseKey} #${i + 1}: wait must be > 0ms`);
      }
      if (b.type === "wait_wave") {
        const wave = p.wave ?? b.wave;
        if (wave == null || isNaN(wave) || wave < 1) issues.push(`${phaseKey} #${i + 1}: wave must be >= 1`);
      }
    });
  });

  if (totalBlocks === 0) {
    toast("Dry run: Scenario is empty (0 blocks)");
    return;
  }

  if (issues.length > 0) {
    toast(`Validation warning: ${issues[0]}`);
  } else {
    toast(`Dry run passed: all ${totalBlocks} blocks valid. Coordinates inside 1152×756.`);
  }
});

/* Сворачивание и разворачивание подсказки по фазам сценария */
function initScenarioGuideToggle() {
  const btn = $("#btnToggleScenGuide");
  const body = $("#scenGuideBody");
  const txt = $("#scenGuideToggleText");
  if (!btn || !body) return;

  const isCollapsed = localStorage.getItem("ae_glass_scen_guide_collapsed") === "true";
  if (isCollapsed) {
    body.style.display = "none";
    if (txt) {
      txt.dataset.i18n = "scen_guide_show";
      txt.textContent = t("scen_guide_show");
    }
  }

  btn.addEventListener("click", () => {
    const nowHidden = (body.style.display !== "none");
    body.style.display = nowHidden ? "none" : "";
    localStorage.setItem("ae_glass_scen_guide_collapsed", nowHidden ? "true" : "false");
    if (txt) {
      const key = nowHidden ? "scen_guide_show" : "scen_guide_hide";
      txt.dataset.i18n = key;
      txt.textContent = t(key);
    }
  });
}

/* Первичная инициализация сценариев */
initScenarioGuideToggle();
refreshScenarioList("Inf Summer");
renderScenarioView();


/* ------------------------------------------------ вкладки ресурсов */
function initResources() {
  $$("#resTabs .tab").forEach(tab => {
    tab.addEventListener("click", () => {
      $$("#resTabs .tab").forEach(x => x.classList.toggle("is-on", x === tab));
      $$("[data-rpanel]").forEach(p => p.classList.toggle("is-on", p.dataset.rpanel === tab.dataset.rtab));
    });
  });

  $("#btnFuelAuto")?.addEventListener("click", () => {
    toast("Auto fuel schedule active (every 8 hours)");
  });
  $("#btnCraftingReset")?.addEventListener("click", () => {
    const p = $("#craftingProgress");
    if (p) p.textContent = "0 / 20";
    toast("Crafting win counter reset to 0");
  });
  $("#btnFuelReset")?.addEventListener("click", () => {
    toast("Fuel timers reset: all drills ready now");
  });
  $("#btnChallengeReset")?.addEventListener("click", () => {
    toast("Challenge counters and cooldowns reset");
  });

  // 1. Модальное окно выбора спрайтов крафта
  const craftingModal = $("#craftingSpritesModal");
  const craftingList = $("#craftingSpritesList");
  const CRAFTABLE_SPRITES = [
    { id: "Trait Crystal", label: "Trait Crystal", defaultAmount: 5 },
    { id: "Mana Flask", label: "Mana Flask", defaultAmount: 10 },
    { id: "Cursed Boba", label: "Cursed Boba", defaultAmount: 2 },
    { id: "Spirit Stone", label: "Spirit Stone", defaultAmount: 1 }
  ];

  const openCraftingModal = async () => {
    if (!craftingModal || !craftingList) return;
    let s = null;
    if (window.pywebview && pywebview.api && pywebview.api.get_crafting_settings) {
      try { s = await pywebview.api.get_crafting_settings(); } catch (_) {}
    }
    craftingList.innerHTML = "";
    CRAFTABLE_SPRITES.forEach(item => {
      const isEnabled = s && s.items && s.items[item.id] !== undefined ? !!s.items[item.id].enabled : true;
      const amount = s && s.items && s.items[item.id] !== undefined ? s.items[item.id].amount : item.defaultAmount;
      const row = document.createElement("div");
      row.className = "opt-row";
      row.style.background = "rgba(255, 255, 255, 0.03)";
      row.style.borderRadius = "var(--r-inner, 8px)";
      row.style.padding = "8px 12px";
      row.innerHTML = `
        <div class="opt-ic"><svg class="ic"><use href="#i-droplet"/></svg></div>
        <div class="opt-main">
          <strong>${escapeHtml(item.label)}</strong>
          <span>${t("craft_priority_item") || "Priority crafting target"}</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <label style="font-size:11px; color:var(--tx-3);">x</label>
          <input type="number" class="craft-item-amount mono" data-item="${escapeHtml(item.id)}" value="${amount}" min="1" max="99" style="width:48px; padding:4px 6px; border-radius:var(--r-sm,6px); background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.12); color:var(--tx); text-align:center;">
          <label class="switch"><input type="checkbox" class="craft-item-toggle" data-item="${escapeHtml(item.id)}" ${isEnabled ? "checked" : ""}><i></i></label>
        </div>
      `;
      craftingList.appendChild(row);
    });
    craftingModal.hidden = false;
  };

  const closeCraftingModal = () => {
    if (craftingModal) craftingModal.hidden = true;
  };

  $("#btnCraftingSprites")?.addEventListener("click", openCraftingModal);
  $("#craftingSpritesClose")?.addEventListener("click", closeCraftingModal);
  $("#craftingSpritesCancel")?.addEventListener("click", closeCraftingModal);
  craftingModal?.addEventListener("click", e => { if (e.target === craftingModal) closeCraftingModal(); });

  $("#craftingSpritesSave")?.addEventListener("click", async () => {
    if (!craftingList) return;
    const toggles = $$(".craft-item-toggle", craftingList);
    const amounts = $$(".craft-item-amount", craftingList);

    for (const tog of toggles) {
      const itemId = tog.dataset.item;
      const isEnabled = tog.checked;
      const amtInput = amounts.find(a => a.dataset.item === itemId);
      const amt = amtInput ? parseInt(amtInput.value, 10) || 1 : 1;

      if (window.pywebview && pywebview.api) {
        try {
          if (pywebview.api.set_crafting_item_enabled) await pywebview.api.set_crafting_item_enabled(itemId, isEnabled);
          if (pywebview.api.set_crafting_item_amount) await pywebview.api.set_crafting_item_amount(itemId, amt);
        } catch (_) {}
      }
    }

    closeCraftingModal();
    toast(t("craft_saved") || "Crafting sprites priority saved");
  });

  // 2. Модальное окно настройки путей топлива
  const fuelModal = $("#fuelPathsModal");
  const fuelList = $("#fuelPathsList");
  const FUEL_ROUTES = [
    { key: "hub_to_well", label: "Water Well", desc: "Route from lobby spawn to Well" },
    { key: "hub_to_mine", label: "Crystal Mine", desc: "Route from lobby spawn to Mine" },
    { key: "hub_to_drill", label: "Resource Drill", desc: "Route from lobby spawn to Drill" }
  ];

  const openFuelModal = async () => {
    if (!fuelModal || !fuelList) return;
    await refreshSavedWalkPaths();
    let fState = null;
    if (window.pywebview && pywebview.api && pywebview.api.get_fuel_settings) {
      try { fState = await pywebview.api.get_fuel_settings(); } catch (_) {}
    }
    fuelList.innerHTML = "";
    FUEL_ROUTES.forEach(route => {
      const assigned = (fState && fState.paths && fState.paths[route.key]) || "";
      const pathOpts = ['<option value="">Not assigned</option>']
        .concat(savedWalkPaths.map(p => `<option value="${escapeHtml(p)}" ${p === assigned ? "selected" : ""}>${escapeHtml(p)}</option>`))
        .join("");

      const row = document.createElement("div");
      row.className = "opt-row";
      row.style.background = "rgba(255, 255, 255, 0.03)";
      row.style.borderRadius = "var(--r-inner, 8px)";
      row.style.padding = "8px 12px";
      row.innerHTML = `
        <div class="opt-ic"><svg class="ic"><use href="#i-route"/></svg></div>
        <div class="opt-main" style="min-width:130px;">
          <strong>${escapeHtml(route.label)}</strong>
          <span>${escapeHtml(route.desc)}</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <select class="fuel-path-select block-input" data-route="${escapeHtml(route.key)}" style="width:160px; font-size:11px;">
            ${pathOpts}
          </select>
          <button type="button" class="btn btn-ghost btn-xs btn-rec-fuel-path" data-route-label="${escapeHtml(route.label)}" title="Record route with WASD recorder">
            <svg class="ic"><use href="#i-camera"/></svg>
            <span>Record WASD</span>
          </button>
        </div>
      `;
      fuelList.appendChild(row);
    });

    $$(".fuel-path-select", fuelList).forEach(sel => {
      sel.addEventListener("change", async () => {
        const routeKey = sel.dataset.route;
        const val = sel.value;
        if (window.pywebview && pywebview.api && pywebview.api.set_fuel_path) {
          try { await pywebview.api.set_fuel_path(routeKey, val); } catch (_) {}
        }
        toast(val ? `Path "${val}" assigned to ${routeKey}` : `Path cleared for ${routeKey}`);
      });
    });

    $$(".btn-rec-fuel-path", fuelList).forEach(btn => {
      btn.addEventListener("click", () => {
        const defaultName = btn.dataset.routeLabel || "Hub Route";
        closeFuelModal();
        startPathRecordingFlow(defaultName);
      });
    });

    fuelModal.hidden = false;
  };

  const closeFuelModal = () => {
    if (fuelModal) fuelModal.hidden = true;
  };

  $("#btnFuelPaths")?.addEventListener("click", openFuelModal);
  $("#fuelPathsClose")?.addEventListener("click", closeFuelModal);
  $("#fuelPathsDone")?.addEventListener("click", closeFuelModal);
  fuelModal?.addEventListener("click", e => { if (e.target === fuelModal) closeFuelModal(); });

  // 3. Модальное окно привязки макросов к картам испытаний
  const challengeModal = $("#challengeMapsModal");
  const challengeList = $("#challengeMapsList");
  const CHALLENGE_STORY_MAPS = ['School Grounds', 'Rose Kingdom', 'Fairy King Forest', "King's Tomb", 'Flower Forest', 'East Town'];

  const openChallengeModal = async () => {
    if (!challengeModal || !challengeList) return;
    if ((!taskTemplates || taskTemplates.length === 0) && window.pywebview && pywebview.api && pywebview.api.list_templates) {
      try { taskTemplates = await pywebview.api.list_templates() || []; } catch (_) {}
    }
    let chState = null;
    if (window.pywebview && pywebview.api && pywebview.api.get_challenge_settings) {
      try { chState = await pywebview.api.get_challenge_settings(); } catch (_) {}
    }
    challengeList.innerHTML = "";
    CHALLENGE_STORY_MAPS.forEach(mapName => {
      const assignedMacro = (chState && chState.maps && chState.maps[mapName]) ? chState.maps[mapName].macro : "";
      const macroOpts = ['<option value="">No Macro</option>']
        .concat(taskTemplates.map(t => `<option value="${escapeHtml(t)}" ${t === assignedMacro ? "selected" : ""}>▶ ${escapeHtml(t)}</option>`))
        .join("");

      const row = document.createElement("div");
      row.className = "opt-row";
      row.style.background = "rgba(255, 255, 255, 0.03)";
      row.style.borderRadius = "var(--r-inner, 8px)";
      row.style.padding = "8px 12px";
      row.innerHTML = `
        <div class="opt-ic"><svg class="ic"><use href="#i-route"/></svg></div>
        <div class="opt-main" style="min-width:140px;">
          <strong>${escapeHtml(mapName)}</strong>
          <span>Story challenge map</span>
        </div>
        <select class="challenge-macro-select block-input" data-map="${escapeHtml(mapName)}" style="width:190px; font-size:11px;">
          ${macroOpts}
        </select>
      `;
      challengeList.appendChild(row);
    });

    $$(".challenge-macro-select", challengeList).forEach(sel => {
      sel.addEventListener("change", async () => {
        const map = sel.dataset.map;
        const val = sel.value;
        if (window.pywebview && pywebview.api && pywebview.api.set_challenge_map_macro) {
          try { await pywebview.api.set_challenge_map_macro(map, val); } catch (_) {}
        }
        toast(val ? `Macro "${val}" assigned to ${map}` : `Macro cleared for ${map}`);
      });
    });

    challengeModal.hidden = false;
  };

  const closeChallengeModal = () => {
    if (challengeModal) challengeModal.hidden = true;
  };

  $("#btnChallengeMaps")?.addEventListener("click", openChallengeModal);
  $("#challengeMapsClose")?.addEventListener("click", closeChallengeModal);
  $("#challengeMapsDone")?.addEventListener("click", closeChallengeModal);
  challengeModal?.addEventListener("click", e => { if (e.target === challengeModal) closeChallengeModal(); });
}
initResources();

/* ------------------------------------------------ справка: FAQ с живым поиском */
function initFaq() {
  const searchInput = $("#faqSearchInput");
  const searchClear = $("#faqSearchClear");
  const items = $$(".faq-item");

  $$(".faq-q").forEach(q => {
    q.addEventListener("click", () => {
      const item = q.closest(".faq-item");
      const wasOpen = item.classList.contains("open");
      item.classList.toggle("open", !wasOpen);
    });
  });

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      const query = searchInput.value.trim().toLowerCase();
      if (searchClear) searchClear.hidden = !query;

      items.forEach(item => {
        const text = (item.textContent + " " + (item.dataset.keywords || "")).toLowerCase();
        const matches = !query || text.includes(query);
        item.classList.toggle("is-hidden", !matches);
        if (query && matches) item.classList.add("open");
      });
    });

    if (searchClear) {
      searchClear.addEventListener("click", () => {
        searchInput.value = "";
        searchClear.hidden = true;
        items.forEach(item => {
          item.classList.remove("is-hidden");
          item.classList.remove("open");
        });
        searchInput.focus();
      });
    }
  }

  const openExternal = (url) => {
    if (window.pywebview && pywebview.api && pywebview.api.open_url) {
      pywebview.api.open_url(url);
    } else {
      window.open(url, "_blank", "noopener");
    }
  };

  $("#btnOurFork")?.addEventListener("click", () => {
    openExternal("https://github.com/Ponchik0/ae");
  });

  $("#btnCreamsMacro")?.addEventListener("click", () => {
    openExternal("https://github.com/Cweamy/Anime-Expeditions-Creams-Macro/commits/main/");
  });

  $("#btnYoutubeGuide")?.addEventListener("click", () => {
    openExternal("https://www.youtube.com/watch?v=TO9NDQjX7rE&pp=ygUMQ3dlYW15");
  });

  $("#btnExportReport")?.addEventListener("click", async () => {
    if (window.pywebview && pywebview.api && pywebview.api.export_failure_report) {
      try {
        const res = await pywebview.api.export_failure_report();
        if (res && res.path) {
          toast((LANG === "ru" ? "Отчёт сохранён: " : "Report saved: ") + res.path);
        } else if (res && res.ok) {
          toast(LANG === "ru" ? "Отчёт об ошибках успешно создан" : "Failure report exported");
        } else {
          toast(LANG === "ru" ? "Ошибка экспорта отчёта" : "Failed to export report");
        }
      } catch (err) {
        toast("Export error: " + err);
      }
    } else {
      toast(LANG === "ru" ? "Отчёт сохранён на Рабочий стол" : "Report exported to Desktop");
    }
  });
}
initFaq();

/* ------------------------------------------------ модульная сетка дашборда */
/* Свободное размещение карточек: перетаскивание для обмена ячейками (drag to swap),
   скрытие и включение карточек, сохранение в localStorage, адаптивное распределение
   высоты и ширины при скрытии карточек без навязчивых рельс-разделителей. */

const DEFAULT_DASH_LAYOUT = {
  slots: {
    slotMain: "game",
    slotSideTop: "controls",
    slotSideBottom: "stats",
    slotLowerLeft: "log",
    slotLowerRight: "history"
  },
  hidden: [],
  sizes: {
    lowerHeight: 240,
    sideBottomHeight: 140,
    sideTopHeight: null,
    lowerLeftFlex: "1 1 50%",
    lowerRightFlex: "1 1 50%"
  },
  density: "normal"
};

const CARD_NAMES = {
  game: "card_game",
  controls: "card_controls",
  stats: "card_stats",
  log: "card_log",
  history: "card_history"
};

const CARD_SHORT_NAMES = {
  controls: "chip_controls",
  stats: "chip_stats",
  log: "chip_log",
  history: "chip_history"
};

function updateGameAspect(res) {
  const home = $("#screen-home");
  if (!home) return;
  const target = res || GAME_RES;
  const parts = target.split(/[×xX?]/);
  if (parts.length >= 2) {
    const w = parseFloat(parts[0].trim());
    const h = parseFloat(parts[1].trim());
    if (w > 0 && h > 0) {
      home.style.setProperty("--game-aspect", `${w} / ${h}`);
    }
  }
}

function initDashboardLayout() {
  const home = $("#screen-home");
  if (!home) return;

  const btnEdit = $("#btnEditLayout");
  const restoreBanner = $("#dashRestoreBanner");
  const restoreChips = $("#restoreBannerChips");
  const btnRestoreAll = $("#btnRestoreAllCards");
  const btnSetReset = $("#btnSetResetLayout");
  const btnSetResetDashboard = $("#btnSetResetDashboard");
  const btnSetOpenCustom = $("#btnSetOpenCustom");


  // Загрузка сохранённой конфигурации
  let layout = (() => {
    try {
      const raw = localStorage.getItem("ae_dashboard_layout");
      if (!raw) return JSON.parse(JSON.stringify(DEFAULT_DASH_LAYOUT));
      const parsed = JSON.parse(raw);
      if (!parsed.slots || typeof parsed.slots !== "object") throw new Error();
      if (!Array.isArray(parsed.hidden)) parsed.hidden = [];
      if (!parsed.sizes || typeof parsed.sizes !== "object") {
        parsed.sizes = JSON.parse(JSON.stringify(DEFAULT_DASH_LAYOUT.sizes));
      }
      // Окно Roblox всегда строго статично в slotMain и никогда не скрывается
      parsed.slots.slotMain = "game";
      parsed.hidden = parsed.hidden.filter(id => id !== "game");

      const allDynamicCards = ["controls", "stats", "log", "history"];
      const assignedCards = Object.values(parsed.slots);
      for (const c of allDynamicCards) {
        if (!assignedCards.includes(c)) return JSON.parse(JSON.stringify(DEFAULT_DASH_LAYOUT));
      }
      return parsed;
    } catch (_) {
      return JSON.parse(JSON.stringify(DEFAULT_DASH_LAYOUT));
    }
  })();

  const saveLayout = () => {
    try {
      localStorage.setItem("ae_dashboard_layout", JSON.stringify(layout));
    } catch (_) {}
  };

  // Применение раскладки и сохранённых размеров к DOM
  const applyLayout = () => {
    const allCards = $$(".dash-card", home);
    const cardMap = {};
    allCards.forEach(c => { cardMap[c.dataset.cardId] = c; });

    // Применяем сохранённые размеры
    const sizes = layout.sizes || DEFAULT_DASH_LAYOUT.sizes;
    if (sizes.lowerHeight === "auto") {
      home.style.setProperty("--lower-h", "auto");
      home.style.setProperty("--lower-flex", "1 1 0");
    } else {
      const lh = parseInt(sizes.lowerHeight) || 240;
      home.style.setProperty("--lower-h", lh + "px");
      home.style.setProperty("--lower-flex", `0 0 ${lh}px`);
    }
    home.style.setProperty("--side-bottom-h", (sizes.sideBottomHeight || 140) + "px");
    if (sizes.sideTopHeight) {
      home.style.setProperty("--side-top-h", sizes.sideTopHeight + "px");
    } else {
      home.style.removeProperty("--side-top-h");
    }
    home.style.setProperty("--lower-left-flex", sizes.lowerLeftFlex || "1 1 50%");
    home.style.setProperty("--lower-right-flex", sizes.lowerRightFlex || "1 1 50%");

    if (layout.density) {
      document.documentElement.setAttribute("data-card-density", layout.density);
    } else {
      document.documentElement.removeAttribute("data-card-density");
    }

    updateGameAspect(GAME_RES);

    // 1. Расставляем карточки по слотам (Roblox всегда в slotMain)
    layout.slots.slotMain = "game";
    for (const [slotId, cardId] of Object.entries(layout.slots)) {
      const slot = document.getElementById(slotId);
      const card = cardMap[cardId];
      if (slot && card && card.parentElement !== slot) {
        slot.appendChild(card);
      }
    }

    // 2. Управляем видимостью скрытых карточек
    allCards.forEach(c => {
      const cardId = c.dataset.cardId;
      const isHidden = layout.hidden.includes(cardId);
      const slot = c.closest(".dash-slot");
      if (slot) {
        slot.classList.toggle("is-hidden", isHidden);
      }
      c.classList.toggle("is-hidden", isHidden);
    });

    // 3. Динамическая балансировка сетки при скрытии карточек
    const homeGrid = $("#homeGrid");
    const homeSide = $("#homeSide");
    const homeLower = $("#homeLower");

    // Нижний ярус
    const slotLL = $("#slotLowerLeft");
    const slotLR = $("#slotLowerRight");
    const llHidden = !slotLL || slotLL.classList.contains("is-hidden");
    const lrHidden = !slotLR || slotLR.classList.contains("is-hidden");

    if (homeLower) {
      if (llHidden && lrHidden) {
        homeLower.classList.add("is-all-hidden");
        homeLower.classList.remove("has-one-child");
      } else if (llHidden || lrHidden) {
        homeLower.classList.remove("is-all-hidden");
        homeLower.classList.add("has-one-child");
      } else {
        homeLower.classList.remove("is-all-hidden");
        homeLower.classList.remove("has-one-child");
      }
    }

    // Боковая колонка
    const slotST = $("#slotSideTop");
    const slotSB = $("#slotSideBottom");
    const stHidden = !slotST || slotST.classList.contains("is-hidden");
    const sbHidden = !slotSB || slotSB.classList.contains("is-hidden");

    if (homeSide) {
      if (stHidden && sbHidden) {
        homeSide.classList.add("is-hidden");
        homeSide.classList.remove("has-one-child");
      } else if (stHidden || sbHidden) {
        homeSide.classList.remove("is-hidden");
        homeSide.classList.add("has-one-child");
      } else {
        homeSide.classList.remove("is-hidden");
        homeSide.classList.remove("has-one-child");
      }
    }

    // Верхний ярус
    const slotMain = $("#slotMain");
    const mainHidden = !slotMain || slotMain.classList.contains("is-hidden");
    if (homeGrid) {
      homeGrid.classList.toggle("side-all-hidden", stHidden && sbHidden);
      homeGrid.classList.toggle("main-hidden", mainHidden);
    }
    // Скрываем разделители, если в блоке осталась одна карточка или все скрыты
    const sideResizer = $("#sideResizer");
    if (sideResizer) sideResizer.style.display = (stHidden || sbHidden) ? "none" : "";
    const lowerResizer = $("#lowerResizer");
    if (lowerResizer) lowerResizer.style.display = (llHidden || lrHidden) ? "none" : "";

    // 4. Синхронизируем чекбоксы в Настройках и плашку восстановления
    ["controls", "stats", "log", "history"].forEach(id => {
      const sw = document.getElementById("setToggleCard_" + id);
      if (sw) {
        sw.checked = !layout.hidden.includes(id);
      }
    });
    updateRestoreBanner();
  };

  const updateRestoreBanner = () => {
    if (!restoreBanner || !restoreChips) return;
    const hidden = layout.hidden || [];
    if (hidden.length === 0) {
      restoreBanner.hidden = true;
      restoreChips.innerHTML = "";
      return;
    }

    restoreBanner.hidden = false;
    restoreChips.innerHTML = "";
    hidden.forEach(id => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "restore-chip";
      const name = t(CARD_NAMES[id] || id);
      chip.innerHTML = `<span>${name}</span><span class="restore-chip-plus">+</span>`;
      chip.title = `${t("dash_card_shown").replace("{name}", name)}`;
      chip.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleCardVisibility(id, true);
      });
      restoreChips.appendChild(chip);
    });
  };

  const toggleCardVisibility = (cardId, forceVisible) => {
    if (cardId === "game") return; // Roblox нельзя скрыть
    const isHidden = layout.hidden.includes(cardId);
    const targetHidden = forceVisible !== undefined ? !forceVisible : !isHidden;

    if (targetHidden && !isHidden) {
      layout.hidden.push(cardId);
      const name = t(CARD_NAMES[cardId] || cardId);
      toast(t("dash_card_hidden").replace("{name}", name));
    } else if (!targetHidden && isHidden) {
      layout.hidden = layout.hidden.filter(id => id !== cardId);
      const name = t(CARD_NAMES[cardId] || cardId);
      toast(t("dash_card_shown").replace("{name}", name));
      animateCardRestoration(cardId);
      return;
    }
    saveLayout();
    applyLayout();
  };

  // Плавная анимация добавления/восстановления карточек через CSS keyframe (без конфликтов и стилистических блокировок)
  const animateCardRestoration = (cardId) => {
    saveLayout();
    applyLayout();
    const card = $(`[data-card-id="${cardId}"]`);
    const slot = card?.closest(".dash-slot");
    if (slot) {
      slot.classList.remove("slot-restoring");
      void slot.offsetWidth; // перезапуск CSS анимации
      slot.classList.add("slot-restoring");
      slot.addEventListener("animationend", () => {
        slot.classList.remove("slot-restoring");
      }, { once: true });
    }
  };

  // =========================================================================
  // Режим кастомизации дашборда: переключение через кнопку в шапке Macro Engine
  // =========================================================================
  const setCustomizing = (active) => {
    if (active) {
      home.classList.add("is-customizing");
      if (btnEdit) {
        btnEdit.classList.add("is-active");
        btnEdit.innerHTML = `<svg class="ic"><use href="#i-check"/></svg><span>Done</span>`;
        btnEdit.title = t("btn_save") || "Save layout";
      }
    } else {
      home.classList.remove("is-customizing");
      if (btnEdit) {
        btnEdit.classList.remove("is-active");
        btnEdit.innerHTML = `<svg class="ic"><use href="#i-sliders"/></svg><span data-i18n="dash_customize">${t("dash_customize")}</span>`;
        btnEdit.title = t("dash_customize") || "Customize dashboard";
      }
    }
  };

  if (btnEdit) {
    btnEdit.addEventListener("click", () => {
      const isCustom = home.classList.contains("is-customizing");
      setCustomizing(!isCustom);
      if (isCustom) {
        toast(t("dash_layout_sec") + ": " + t("btn_save"));
      }
    });
  }

  if (btnRestoreAll) {
    btnRestoreAll.addEventListener("click", (e) => {
      e.stopPropagation();
      if (layout.hidden && layout.hidden.length > 0) {
        layout.hidden = [];
        saveLayout();
        applyLayout();
        toast(t("dash_reset_done"));
      }
    });
  }

  // Развертывание/восстановление лога и истории на весь ярус
  const logExpand = $("#logExpand");
  const histExpand = $("#histExpand");

  if (logExpand) {
    logExpand.addEventListener("click", () => {
      const slotLL = $("#slotLowerLeft");
      const slotLR = $("#slotLowerRight");
      if (!slotLL) return;
      const isExp = slotLL.classList.toggle("is-expanded");
      if (slotLR) slotLR.classList.toggle("is-collapsed-sibling", isExp);
      const useEl = $("use", logExpand);
      if (useEl) useEl.setAttribute("href", isExp ? "#i-minimize" : "#i-maximize");
      toast(isExp ? t("card_expanded").replace("{name}", t("card_log")) : t("card_restored_width").replace("{name}", t("card_log")));
    });
  }

  if (histExpand) {
    histExpand.addEventListener("click", () => {
      const slotLL = $("#slotLowerLeft");
      const slotLR = $("#slotLowerRight");
      if (!slotLR) return;
      const isExp = slotLR.classList.toggle("is-expanded");
      if (slotLL) slotLL.classList.toggle("is-collapsed-sibling", isExp);
      const useEl = $("use", histExpand);
      if (useEl) useEl.setAttribute("href", isExp ? "#i-minimize" : "#i-maximize");
      toast(isExp ? t("card_expanded").replace("{name}", t("card_history")) : t("card_restored_width").replace("{name}", t("card_history")));
    });
  }

  // Сброс раскладки и размеров к стандарту
  const resetLayout = () => {
    layout = JSON.parse(JSON.stringify(DEFAULT_DASH_LAYOUT));
    saveLayout();
    applyLayout();
    try { localStorage.removeItem("ae_custom_bar_pos"); } catch (_) {}
    if (typeof window.resetControlsSubLayout === "function") {
      window.resetControlsSubLayout();
    }
    toast(t("dash_reset_done"));
  };

  if (btnSetReset) btnSetReset.addEventListener("click", resetLayout);
  if (btnSetResetDashboard) btnSetResetDashboard.addEventListener("click", resetLayout);

  if (btnSetOpenCustom) {
    btnSetOpenCustom.addEventListener("click", () => {
      const navHome = document.querySelector(".topnav [data-screen='home']");
      if (navHome) navHome.click();
      setTimeout(() => {
        setCustomizing(true);
      }, 150);
    });
  }

  // Привязка чекбоксов в Настройках
  ["controls", "stats", "log", "history"].forEach(id => {
    const sw = document.getElementById("setToggleCard_" + id);
    if (sw) {
      sw.addEventListener("change", () => {
        toggleCardVisibility(id, sw.checked);
      });
    }
  });

  // Кнопки скрытия на самих карточках
  $$(".card-hide-btn", home).forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const card = btn.closest(".dash-card");
      if (card && card.dataset.cardId) {
        toggleCardVisibility(card.dataset.cardId, false);
      }
    });
  });

  // =========================================================================
  // Drag & Drop: зажатие в любом месте карточки (Hold & Drag to Swap)
  // =========================================================================
  const SWAPPABLE_SLOTS = ["slotSideTop", "slotSideBottom", "slotLowerLeft", "slotLowerRight"];
  const dynamicCards = $$(".dash-card:not(.is-static)", home);

  function getSlotUnderPointer(x, y) {
    for (const slotId of SWAPPABLE_SLOTS) {
      const slot = document.getElementById(slotId);
      if (!slot) continue;
      const rect = slot.getBoundingClientRect();
      if (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom) {
        return slot;
      }
    }
    return null;
  }

  const clearSwapPreviews = () => {
    $$(".swap-preview-overlay").forEach(el => el.remove());
    $$(".drop-target").forEach(el => el.classList.remove("drop-target"));
    $$(".is-swap-source").forEach(el => el.classList.remove("is-swap-source"));
  };

  dynamicCards.forEach(card => {
    card.addEventListener("pointerdown", (e) => {
      if (!home.classList.contains("is-customizing")) return;
      if (e.button !== 0) return;
      // Карточку разрешено перемещать ТОЛЬКО за шапку (.run-card-top, .card-head, .stats-head-row) или ручку .card-drag-handle.
      // Вся остальная рабочая область (Task Queue, кнопки Start/Stop, логи, статы) не инициирует drag,
      // полностью совпадая с курсором мыши и устраняя путаницу.
      const isHeaderZone = !!e.target.closest(".run-card-top, .card-head, .stats-head-row, .card-drag-grip, .card-drag-handle");
      if (!isHeaderZone) return;
      if (e.target.closest("button, input, select, textarea, a, .run-mode-chip, .card-hide-btn, .stat-tiles-manage, .stat-add-pop")) return;

      const cardId = card.dataset.cardId;
      if (!cardId || cardId === "game") return;

      const startX = e.clientX;
      const startY = e.clientY;
      const cardRect = card.getBoundingClientRect();
      const grabOffsetX = startX - cardRect.left;
      const grabOffsetY = startY - cardRect.top;
      let isDragging = false;
      let ghost = null;
      let animFrameId = null;
      let activeTargetSlot = null;

      // Физические параметры движения (Spring & Inertial Tilt Physics)
      let currentX = cardRect.left;
      let currentY = cardRect.top;
      let targetX = currentX;
      let targetY = currentY;
      let currentTilt = 0;
      let targetTilt = 0;
      let currentScale = 1.0;
      let targetScale = 1.025;
      let lastPointerX = startX;
      let lastPointerTime = performance.now();
      let vx = 0; // px/ms

      const renderPhysics = () => {
        if (!isDragging || !ghost) return;

        // Плавное следование с ощущением физической массы и инерции (LERP 0.28)
        currentX += (targetX - currentX) * 0.28;
        currentY += (targetY - currentY) * 0.28;

        // Динамический пружинный наклон при движении мышью (Inertial dynamic tilt)
        currentTilt += (targetTilt - currentTilt) * 0.20;
        targetTilt *= 0.86;

        // Эффект плавного подъема карточки над плоскостью (Lift scale)
        currentScale += (targetScale - currentScale) * 0.18;

        ghost.style.transform = `translate3d(${currentX.toFixed(1)}px, ${currentY.toFixed(1)}px, 0) rotate(${currentTilt.toFixed(2)}deg) scale(${currentScale.toFixed(3)})`;

        animFrameId = requestAnimationFrame(renderPhysics);
      };

      const onPointerMove = (me) => {
        const dx = me.clientX - startX;
        const dy = me.clientY - startY;

        if (!isDragging && Math.hypot(dx, dy) > 4) {
          isDragging = true;
          card.classList.add("is-drag-source");

          // Создаем полноценный клон карточки в полном формате (настоящая карточка)
          ghost = card.cloneNode(true);
          ghost.removeAttribute("id");
          ghost.querySelectorAll("[id]").forEach(el => el.removeAttribute("id"));

          // Сохраняем все исходные классы карточки (glass-card, run-card и т.д.), чтобы не сбивались padding и верстка
          ghost.classList.remove("is-drag-source");
          ghost.classList.add("dash-drag-card-ghost");
          ghost.style.position = "fixed";
          ghost.style.top = "0px";
          ghost.style.left = "0px";
          ghost.style.width = cardRect.width + "px";
          ghost.style.height = cardRect.height + "px";
          const px = Math.round(currentX);
          const py = Math.round(currentY);
          ghost.style.transform = `translate3d(${px}px, ${py}px, 0) scale(1.0)`;
          document.body.appendChild(ghost);

          animFrameId = requestAnimationFrame(renderPhysics);
        }

        if (isDragging && ghost) {
          const now = performance.now();
          const dt = Math.max(now - lastPointerTime, 8);
          const instantVx = (me.clientX - lastPointerX) / dt;
          lastPointerX = me.clientX;
          lastPointerTime = now;

          vx = vx * 0.35 + instantVx * 0.65;
          targetX = me.clientX - grabOffsetX;
          targetY = me.clientY - grabOffsetY;
          targetTilt = Math.max(-6.5, Math.min(6.5, vx * 4.8));

          // Предварительный просмотр обмена (Live Swap Preview)
          const targetSlot = getSlotUnderPointer(me.clientX, me.clientY);
          const isValidTarget = targetSlot && targetSlot !== card.parentElement && SWAPPABLE_SLOTS.includes(targetSlot.dataset.slot);

          if (isValidTarget) {
            if (activeTargetSlot !== targetSlot) {
              clearSwapPreviews();
              activeTargetSlot = targetSlot;
              targetSlot.classList.add("drop-target");

              const targetSlotId = targetSlot.dataset.slot;
              const targetCardId = layout.slots[targetSlotId];
              const nameA = t(CARD_NAMES[cardId] || cardId);
              const nameB = targetCardId ? t(CARD_NAMES[targetCardId] || targetCardId) : "";

              // Превью на целевом слоте
              const ovTarget = document.createElement("div");
              ovTarget.className = "swap-preview-overlay";
              ovTarget.innerHTML = `<div class="swap-preview-pill"><svg class="ic"><use href="#i-refresh"/></svg><span>${t("preview_swap_here").replace("{name}", nameA)}</span></div>`;
              targetSlot.appendChild(ovTarget);

              // Превью на исходном слоте
              const sourceSlot = card.parentElement;
              if (sourceSlot && nameB) {
                sourceSlot.classList.add("is-swap-source");
                const ovSource = document.createElement("div");
                ovSource.className = "swap-preview-overlay";
                ovSource.innerHTML = `<div class="swap-preview-pill is-source"><svg class="ic"><use href="#i-refresh"/></svg><span>${t("preview_swap_yield").replace("{name}", nameB)}</span></div>`;
                sourceSlot.appendChild(ovSource);
              }
            }
          } else {
            if (activeTargetSlot) {
              clearSwapPreviews();
              activeTargetSlot = null;
            }
          }
        }
      };

      const onPointerUp = (ue) => {
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerup", onPointerUp);
        window.removeEventListener("pointercancel", onPointerUp);

        if (animFrameId) {
          cancelAnimationFrame(animFrameId);
          animFrameId = null;
        }

        if (ghost) {
          ghost.remove();
          ghost = null;
        }
        card.classList.remove("is-drag-source");
        clearSwapPreviews();

        if (!isDragging) return;

        const targetSlot = getSlotUnderPointer(ue.clientX, ue.clientY);
        if (!targetSlot) return;
        const targetSlotId = targetSlot.dataset.slot;
        if (!targetSlotId || !SWAPPABLE_SLOTS.includes(targetSlotId)) return;

        let sourceSlotId = null;
        for (const [sId, cId] of Object.entries(layout.slots)) {
          if (cId === cardId) {
            sourceSlotId = sId;
            break;
          }
        }
        if (!sourceSlotId || sourceSlotId === targetSlotId) return;

        const targetCardId = layout.slots[targetSlotId];
        layout.slots[sourceSlotId] = targetCardId;
        layout.slots[targetSlotId] = cardId;
        saveLayout();
        applyLayout();

        const nameA = t(CARD_NAMES[cardId] || cardId);
        const nameB = t(CARD_NAMES[targetCardId] || targetCardId);
        toast(t("dash_swap_done").replace("{a}", nameA).replace("{b}", nameB));
      };

      window.addEventListener("pointermove", onPointerMove);
      window.addEventListener("pointerup", onPointerUp);
      window.addEventListener("pointercancel", onPointerUp);
    });
  });

  // =========================================================================
  // Управление мини-карточками внутри блока Session (перемещение и скрытие)
  // =========================================================================
  const initSessionStatTiles = () => {
    const statGrid = $("#statGrid");
    const btnRestore = $("#btnRestoreStats");
    const btnAdd = $("#btnAddStatTile");
    const addPop = $("#statAddPop");
    const addList = $("#statAddList");
    if (!statGrid) return;

    const defaultOrder = ["runs", "wins", "losses", "time"];
    let tileOrder = defaultOrder.slice();
    let hiddenTiles = [];

    // Загрузка сохранённого порядка и скрытых плиток
    try {
      const savedOrder = JSON.parse(localStorage.getItem("ae_stat_tiles_order") || "null");
      if (Array.isArray(savedOrder) && savedOrder.length) {
        tileOrder = savedOrder.filter(id => defaultOrder.includes(id));
        defaultOrder.forEach(id => {
          if (!tileOrder.includes(id)) tileOrder.push(id);
        });
      }
      const savedHidden = JSON.parse(localStorage.getItem("ae_stat_tiles_hidden") || "null");
      if (Array.isArray(savedHidden)) {
        hiddenTiles = savedHidden.filter(id => defaultOrder.includes(id));
      }
    } catch (_) {}

    // Отрисовка выпадающего меню добавления скрытых плиток через кнопку [+]
    const renderStatAddList = () => {
      if (!addList) return;
      addList.innerHTML = "";

      const icons = {
        runs: "#i-play",
        wins: "#i-check",
        losses: "#i-warn",
        time: "#i-clock"
      };

      defaultOrder.forEach(id => {
        const isHidden = hiddenTiles.includes(id);
        const name = t("st_" + id) || id;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "stat-add-item" + (isHidden ? " is-hidden-item" : " is-active");
        btn.innerHTML = `
          <span class="stat-add-item-name">
            <svg class="ic" style="width:12px;height:12px;"><use href="${icons[id] || '#i-mark'}"/></svg>
            <span>${name}</span>
          </span>
          <span class="stat-add-item-badge">${isHidden ? "+" : "✓"}</span>
        `;
        if (isHidden) {
          btn.addEventListener("click", (e) => {
            e.stopPropagation();
            hiddenTiles = hiddenTiles.filter(tId => tId !== id);
            try {
              localStorage.setItem("ae_stat_tiles_hidden", JSON.stringify(hiddenTiles));
            } catch (_) {}
            applyOrder();
            renderStatAddList();
            toast(t("stat_tile_restored").replace("{name}", name));
          });
        }
        addList.appendChild(btn);
      });
    };

    const updateStatGridLayout = () => {
      const tiles = $$(".stat", statGrid);
      const visibleTiles = tiles.filter(t => !hiddenTiles.includes(t.dataset.statId));

      tiles.forEach(t => {
        const isHidden = hiddenTiles.includes(t.dataset.statId);
        t.classList.toggle("is-hidden", isHidden);
      });

      const hasTime = visibleTiles.some(t => t.dataset.statId === "time");
      const count = visibleTiles.length;

      let emptyMsg = $(".stat-all-hidden-msg", statGrid);
      if (count === 0) {
        if (!emptyMsg) {
          emptyMsg = document.createElement("div");
          emptyMsg.className = "stat-all-hidden-msg";
          emptyMsg.textContent = t("stat_all_hidden");
          statGrid.appendChild(emptyMsg);
        }
        statGrid.style.gridTemplateColumns = "1fr";
      } else {
        if (emptyMsg) emptyMsg.remove();
        if (count === 4) {
          statGrid.style.gridTemplateColumns = "repeat(3, 1fr) 1.34fr";
        } else if (count === 3) {
          statGrid.style.gridTemplateColumns = hasTime ? "1fr 1fr 1.3fr" : "repeat(3, 1fr)";
        } else if (count === 2) {
          statGrid.style.gridTemplateColumns = hasTime ? "1fr 1.25fr" : "1fr 1fr";
        } else {
          statGrid.style.gridTemplateColumns = "1fr";
        }
      }

      // Кнопка Reset stats всегда доступна в блоке Session
      if (btnRestore) {
        btnRestore.style.display = "inline-flex";
      }

      renderStatAddList();
    };

    const applyOrder = () => {
      const tileMap = {};
      $$(".stat", statGrid).forEach(t => { tileMap[t.dataset.statId] = t; });
      tileOrder.forEach(id => {
        if (tileMap[id]) statGrid.appendChild(tileMap[id]);
      });
      updateStatGridLayout();
    };

    // Скрытие отдельной плитки по кнопке ×
    statGrid.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-hide-stat]");
      if (!btn) return;
      e.stopPropagation();
      const statId = btn.dataset.hideStat;
      if (!hiddenTiles.includes(statId)) {
        hiddenTiles.push(statId);
        try {
          localStorage.setItem("ae_stat_tiles_hidden", JSON.stringify(hiddenTiles));
        } catch (_) {}
        updateStatGridLayout();
        toast(t("stat_tile_hidden"));
      }
    });

    // Кнопка [+] — меню добавления скрытых показателей
    if (btnAdd && addPop) {
      btnAdd.addEventListener("click", (e) => {
        e.stopPropagation();
        addPop.hidden = !addPop.hidden;
        if (!addPop.hidden) {
          const btnRect = btnAdd.getBoundingClientRect();
          const openUp = (btnRect.bottom + 160 > window.innerHeight) || (btnRect.top > 280);
          addPop.classList.toggle("pop-upwards", openUp);
          renderStatAddList();
        }
      });

      document.addEventListener("click", (e) => {
        if (!addPop.hidden && !e.target.closest("#statAddWrap")) {
          addPop.hidden = true;
        }
      });
    }

    // Восстановление и сброс статистики сессии / плиток
    if (btnRestore) {
      btnRestore.addEventListener("click", (e) => {
        e.stopPropagation();
        hiddenTiles = [];
        tileOrder = defaultOrder.slice();
        try {
          localStorage.removeItem("ae_stat_tiles_hidden");
          localStorage.removeItem("ae_stat_tiles_order");
        } catch (_) {}

        // Сброс экранных значений текущей сессии
        const elRuns = $("#stRuns"); if (elRuns) elRuns.textContent = "0";
        const elWins = $("#stWins"); if (elWins) elWins.textContent = "0";
        const elLoss = $("#stLoss"); if (elLoss) elLoss.textContent = "0";
        const elTime = $("#stTime"); if (elTime) elTime.textContent = "00:00";

        if (addPop) addPop.hidden = true;
        applyOrder();
        toast(t("stat_tiles_restored"));
      });
    }

    // Перетаскивание плиток для смены порядка внутри Session с физикой FLIP и плавным приземлением
    let draggedTile = null;
    let statGhost = null;
    let statAnimFrame = null;

    statGrid.addEventListener("pointerdown", (e) => {
      const tile = e.target.closest(".stat");
      if (!tile || e.target.closest(".stat-remove-btn")) return;
      if (!home.classList.contains("is-customizing")) return;
      if (e.button !== 0) return;

      const startX = e.clientX;
      const startY = e.clientY;
      const tileRect = tile.getBoundingClientRect();
      const grabOffsetX = startX - tileRect.left;
      const grabOffsetY = startY - tileRect.top;
      let isDragging = false;

      // Физика движения мини-плитки (Spring & Inertial Tilt)
      let curX = tileRect.left;
      let curY = tileRect.top;
      let targetX = curX;
      let targetY = curY;
      let curTilt = 0;
      let targetTilt = 0;
      let curScale = 1.0;
      let targetScale = 1.08;
      let lastX = startX;
      let lastTime = performance.now();
      let vx = 0;

      const renderStatPhysics = () => {
        if (!isDragging || !statGhost) return;

        // Физическое следование с приятной массой (LERP)
        curX += (targetX - curX) * 0.32;
        curY += (targetY - curY) * 0.32;

        // Пружинный наклон при быстром горизонтальном перемещении
        curTilt += (targetTilt - curTilt) * 0.22;
        targetTilt *= 0.85;

        // Плавный подъем
        curScale += (targetScale - curScale) * 0.20;

        statGhost.style.transform = `translate3d(${curX.toFixed(1)}px, ${curY.toFixed(1)}px, 0) rotate(${curTilt.toFixed(2)}deg) scale(${curScale.toFixed(3)})`;
        statAnimFrame = requestAnimationFrame(renderStatPhysics);
      };

      const onPointerMove = (me) => {
        const dx = me.clientX - startX;
        const dy = me.clientY - startY;

        if (!isDragging && Math.hypot(dx, dy) > 3) {
          isDragging = true;
          draggedTile = tile;
          tile.classList.add("is-stat-dragging");

          // Создаем видимую летающую карточку-призрак
          statGhost = tile.cloneNode(true);
          statGhost.classList.remove("is-stat-dragging");
          statGhost.classList.add("stat-drag-ghost");
          statGhost.style.position = "fixed";
          statGhost.style.top = "0px";
          statGhost.style.left = "0px";
          statGhost.style.width = tileRect.width + "px";
          statGhost.style.height = tileRect.height + "px";
          statGhost.style.transform = `translate3d(${curX.toFixed(1)}px, ${curY.toFixed(1)}px, 0) scale(1.0)`;
          document.body.appendChild(statGhost);

          statAnimFrame = requestAnimationFrame(renderStatPhysics);
        }

        if (isDragging && statGhost) {
          const now = performance.now();
          const dt = Math.max(now - lastTime, 8);
          const instantVx = (me.clientX - lastX) / dt;
          lastX = me.clientX;
          lastTime = now;

          vx = vx * 0.35 + instantVx * 0.65;
          targetX = me.clientX - grabOffsetX;
          targetY = me.clientY - grabOffsetY;
          targetTilt = Math.max(-5.5, Math.min(5.5, vx * 4.0));

          // Определяем целевую плитку под курсором в сетке
          const target = document.elementFromPoint(me.clientX, me.clientY)?.closest(".stat");
          if (target && target !== tile && target.parentElement === statGrid) {
            $$(".stat", statGrid).forEach(s => s.classList.remove("is-stat-drag-over"));
            target.classList.add("is-stat-drag-over");

            const rect = target.getBoundingClientRect();
            const next = me.clientX > rect.left + rect.width / 2;
            const insertBeforeNode = next ? target.nextSibling : target;

            // Выполняем FLIP-анимацию только тогда, когда позиция в DOM реально меняется
            if (tile !== insertBeforeNode && tile.nextSibling !== insertBeforeNode) {
              // 1. FIRST: замеряем исходные координаты всех плиток сетки кроме перетаскиваемой
              const siblings = $$(".stat", statGrid).filter(s => s !== tile);
              const firstRects = new Map();
              siblings.forEach(s => firstRects.set(s, s.getBoundingClientRect()));

              // 2. DOM Move: меняем порядок в сетке
              statGrid.insertBefore(tile, insertBeforeNode);

              tileOrder = $$(".stat", statGrid).map(t => t.dataset.statId);
              try {
                localStorage.setItem("ae_stat_tiles_order", JSON.stringify(tileOrder));
              } catch (_) {}
              updateStatGridLayout();

              // 3. LAST + INVERT + PLAY: плавно скользим плитками на их новые позиции
              siblings.forEach(s => {
                const first = firstRects.get(s);
                if (!first) return;
                const last = s.getBoundingClientRect();
                const deltaX = first.left - last.left;
                const deltaY = first.top - last.top;
                if (Math.abs(deltaX) > 0.5 || Math.abs(deltaY) > 0.5) {
                  s.style.transition = "none";
                  s.style.transform = `translate3d(${deltaX}px, ${deltaY}px, 0)`;
                  s.offsetHeight; // форсируем перерасчёт стилей браузером
                  s.style.transition = "transform 0.28s cubic-bezier(0.16, 1, 0.3, 1)";
                  s.style.transform = "translate3d(0, 0, 0)";
                  const onEnd = () => {
                    s.style.transition = "";
                    s.style.transform = "";
                    s.removeEventListener("transitionend", onEnd);
                  };
                  s.addEventListener("transitionend", onEnd);
                }
              });
            }
          }
        }
      };

      const onPointerUp = () => {
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerup", onPointerUp);
        window.removeEventListener("pointercancel", onPointerUp);

        if (statAnimFrame) {
          cancelAnimationFrame(statAnimFrame);
          statAnimFrame = null;
        }

        $$(".stat", statGrid).forEach(s => s.classList.remove("is-stat-drag-over"));

        if (isDragging && statGhost && tile) {
          isDragging = false;
          // Плавное приземление карточки-призрака прямо в слот сетки
          const destRect = tile.getBoundingClientRect();
          statGhost.style.transition = "transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s ease, opacity 0.22s ease";
          statGhost.style.transform = `translate3d(${destRect.left.toFixed(1)}px, ${destRect.top.toFixed(1)}px, 0) rotate(0deg) scale(1.0)`;
          statGhost.style.boxShadow = "0 2px 8px rgba(0, 0, 0, 0.25)";
          statGhost.style.opacity = "0.9";

          setTimeout(() => {
            if (statGhost) {
              statGhost.remove();
              statGhost = null;
            }
            if (tile) {
              tile.classList.remove("is-stat-dragging");
            }
            draggedTile = null;
          }, 220);
        } else {
          if (statGhost) {
            statGhost.remove();
            statGhost = null;
          }
          if (tile) {
            tile.classList.remove("is-stat-dragging");
          }
          draggedTile = null;
        }
      };

      window.addEventListener("pointermove", onPointerMove);
      window.addEventListener("pointerup", onPointerUp);
      window.addEventListener("pointercancel", onPointerUp);
    });

    applyOrder();
  };
  initSessionStatTiles();

  // =========================================================================
  // Ресайзеры рамок (Интерактивное изменение высоты и ширины панелей с RAF и PointerCapture)
  // =========================================================================
  const sideResizer = $("#sideResizer");
  const lowerResizer = $("#lowerResizer");

  // 1. Рамка между верхней и нижней карточкой боковой колонки (Высота Queue controls / Session)
  if (sideResizer) {
    sideResizer.addEventListener("pointerdown", (e) => {
      if (!home.classList.contains("is-customizing")) return;
      if (e.button !== 0) return;
      e.preventDefault();
      try { sideResizer.setPointerCapture(e.pointerId); } catch (_) {}
      sideResizer.classList.add("is-active");
      home.classList.add("is-resizing");
      document.body.classList.add("is-resizing", "resizing-ns");

      const slotST = $("#slotSideTop");
      const slotSB = $("#slotSideBottom");
      const homeSide = $("#homeSide");
      const stHidden = !slotST || slotST.classList.contains("is-hidden");
      const sbHidden = !slotSB || slotSB.classList.contains("is-hidden");
      const startY = e.clientY;
      let pendingH = null;
      let rafId = null;

      if (sbHidden && !stHidden) {
        // Нижняя карточка (Session) скрыта: ползунок регулирует высоту Queue controls (slotSideTop)
        const startH = slotST ? slotST.offsetHeight : 300;
        const maxH = homeSide ? Math.max(200, homeSide.offsetHeight - 16) : 520;

        const onMove = (me) => {
          const deltaY = me.clientY - startY; // движение вниз увеличивает высоту, вверх — уменьшает
          pendingH = Math.max(140, Math.min(maxH, Math.round(startH + deltaY)));
          if (!rafId) {
            rafId = requestAnimationFrame(() => {
              rafId = null;
              if (pendingH !== null) {
                layout.sizes.sideTopHeight = pendingH;
                home.style.setProperty("--side-top-h", pendingH + "px");
              }
            });
          }
        };

        const onUp = (ue) => {
          try { sideResizer.releasePointerCapture(ue.pointerId); } catch (_) {}
          sideResizer.classList.remove("is-active");
          home.classList.remove("is-resizing");
          document.body.classList.remove("is-resizing", "resizing-ns");
          if (rafId) {
            cancelAnimationFrame(rafId);
            rafId = null;
          }
          if (pendingH !== null) {
            layout.sizes.sideTopHeight = pendingH;
            home.style.setProperty("--side-top-h", pendingH + "px");
          }
          window.removeEventListener("pointermove", onMove);
          window.removeEventListener("pointerup", onUp);
          window.removeEventListener("pointercancel", onUp);
          saveLayout();
        };

        window.addEventListener("pointermove", onMove);
        window.addEventListener("pointerup", onUp);
        window.addEventListener("pointercancel", onUp);
        return;
      }

      // Стандартный режим (обе карточки на месте или только нижняя):
      const startH = slotSB ? slotSB.offsetHeight : 140;
      const onMove = (me) => {
        const deltaY = startY - me.clientY;
        // Ограничитель: минимум 140px, чтобы блок All time и Rate никогда не обрезался
        pendingH = Math.max(140, Math.min(320, Math.round(startH + deltaY)));
        if (!rafId) {
          rafId = requestAnimationFrame(() => {
            rafId = null;
            if (pendingH !== null) {
              layout.sizes.sideBottomHeight = pendingH;
              home.style.setProperty("--side-bottom-h", pendingH + "px");
            }
          });
        }
      };

      const onUp = (ue) => {
        try { sideResizer.releasePointerCapture(ue.pointerId); } catch (_) {}
        sideResizer.classList.remove("is-active");
        home.classList.remove("is-resizing");
        document.body.classList.remove("is-resizing", "resizing-ns");
        if (rafId) {
          cancelAnimationFrame(rafId);
          rafId = null;
        }
        if (pendingH !== null) {
          layout.sizes.sideBottomHeight = pendingH;
          home.style.setProperty("--side-bottom-h", pendingH + "px");
        }
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        window.removeEventListener("pointercancel", onUp);
        saveLayout();
      };

      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
      window.addEventListener("pointercancel", onUp);
    });
  }

  // 3. Рамка между левой и правой карточкой нижнего яруса (Ширина Activity / Runs)
  if (lowerResizer) {
    lowerResizer.addEventListener("pointerdown", (e) => {
      if (!home.classList.contains("is-customizing")) return;
      if (e.button !== 0) return;
      e.preventDefault();
      try { lowerResizer.setPointerCapture(e.pointerId); } catch (_) {}
      lowerResizer.classList.add("is-active");
      home.classList.add("is-resizing");
      document.body.classList.add("is-resizing", "resizing-ew");

      const homeLower = $("#homeLower");
      const rect = homeLower ? homeLower.getBoundingClientRect() : null;
      const containerLeft = rect ? rect.left : 0;
      const containerW = homeLower ? Math.max(300, homeLower.offsetWidth - 16) : 600;
      let pendingLeftFlex = null;
      let pendingRightFlex = null;
      let rafId = null;

      const onMove = (me) => {
        if (!homeLower || containerW <= 0) return;
        const curW = me.clientX - containerLeft - 8;
        const rawPct = (curW / containerW) * 100;
        // Округляем до десятых процента (0.1%), чтобы разделение было плавным и без резких рывков
        const pct = Math.max(20, Math.min(80, Math.round(rawPct * 10) / 10));
        pendingLeftFlex = `1 1 ${pct}%`;
        pendingRightFlex = `1 1 ${(100 - pct).toFixed(1)}%`;

        if (!rafId) {
          rafId = requestAnimationFrame(() => {
            rafId = null;
            if (pendingLeftFlex !== null && pendingRightFlex !== null) {
              layout.sizes.lowerLeftFlex = pendingLeftFlex;
              layout.sizes.lowerRightFlex = pendingRightFlex;
              home.style.setProperty("--lower-left-flex", pendingLeftFlex);
              home.style.setProperty("--lower-right-flex", pendingRightFlex);
            }
          });
        }
      };

      const onUp = (ue) => {
        try { lowerResizer.releasePointerCapture(ue.pointerId); } catch (_) {}
        lowerResizer.classList.remove("is-active");
        home.classList.remove("is-resizing");
        document.body.classList.remove("is-resizing", "resizing-ew");
        if (rafId) {
          cancelAnimationFrame(rafId);
          rafId = null;
        }
        if (pendingLeftFlex !== null && pendingRightFlex !== null) {
          layout.sizes.lowerLeftFlex = pendingLeftFlex;
          layout.sizes.lowerRightFlex = pendingRightFlex;
          home.style.setProperty("--lower-left-flex", pendingLeftFlex);
          home.style.setProperty("--lower-right-flex", pendingRightFlex);
        }
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        window.removeEventListener("pointercancel", onUp);
        saveLayout();
      };

      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
      window.addEventListener("pointercancel", onUp);
    });
  }

  // Первоначальное применение
  applyLayout();
}
initDashboardLayout();

/* =========================================================================
   Controls Sub-Block Customization System (Стрик, Параметры, Очередь, Сервисы)
   ========================================================================= */
const DEFAULT_SUB_LAYOUT = {
  order: ["streak", "meta", "queue", "automations"],
  hidden: [],
  autoOrder: ["shop", "bounty", "craft", "fuel"],
  autoHidden: []
};

const SUB_BLOCK_NAMES = {
  streak: { en: "Streak", ru: "Стрик", fullEn: "Streak & Stats", fullRu: "Стрик и статистика" },
  meta: { en: "Params", ru: "Параметры", fullEn: "Task Details", fullRu: "Параметры задачи" },
  queue: { en: "Queue", ru: "Очередь", fullEn: "Upcoming Queue", fullRu: "Очередь задач" },
  automations: { en: "Services", ru: "Сервисы", fullEn: "Active Automations", fullRu: "Автоматизации" }
};

const AUTO_CELL_NAMES = {
  shop: { en: "Shop", ru: "Торговец", fullEn: "Auto-Shop", fullRu: "Автомагазин" },
  bounty: { en: "Bounty", ru: "Квесты", fullEn: "Bounty Hunter", fullRu: "Охотник за наградой" },
  craft: { en: "Craft", ru: "Крафт", fullEn: "Auto-Crafting", fullRu: "Автокрафт" },
  fuel: { en: "Fuel", ru: "Топливо", fullEn: "Fuel Watchdog", fullRu: "Контроль топлива" }
};

function initControlsSubLayout() {
  const container = $("#runSubBlocksWrap");
  if (!container) return;

  const home = $("#screen-home");

  let subLayout = (() => {
    try {
      const raw = localStorage.getItem("ae_controls_sub_layout");
      if (!raw) return JSON.parse(JSON.stringify(DEFAULT_SUB_LAYOUT));
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed.order)) parsed.order = [...DEFAULT_SUB_LAYOUT.order];
      if (!Array.isArray(parsed.hidden)) parsed.hidden = [];
      if (!Array.isArray(parsed.autoOrder)) parsed.autoOrder = [...DEFAULT_SUB_LAYOUT.autoOrder];
      if (!Array.isArray(parsed.autoHidden)) parsed.autoHidden = [];
      for (const id of DEFAULT_SUB_LAYOUT.order) {
        if (!parsed.order.includes(id)) parsed.order.push(id);
      }
      for (const id of DEFAULT_SUB_LAYOUT.autoOrder) {
        if (!parsed.autoOrder.includes(id)) parsed.autoOrder.push(id);
      }
      return parsed;
    } catch (_) {
      return JSON.parse(JSON.stringify(DEFAULT_SUB_LAYOUT));
    }
  })();

  const saveSubLayout = () => {
    try {
      localStorage.setItem("ae_controls_sub_layout", JSON.stringify(subLayout));
    } catch (_) {}
  };

  const applySubLayout = () => {
    // 1. Упорядочиваем подблоки внутри #runSubBlocksWrap
    const blockMap = {};
    $$(".run-sub-block", container).forEach(b => {
      blockMap[b.dataset.subId] = b;
    });

    for (const subId of subLayout.order) {
      const el = blockMap[subId];
      if (el) container.appendChild(el);
    }

    // 2. Управляем видимостью подблоков
    $$(".run-sub-block", container).forEach(b => {
      const subId = b.dataset.subId;
      const isHidden = subLayout.hidden.includes(subId);
      b.classList.toggle("is-hidden", isHidden);
    });

    // 3. Упорядочиваем и скрываем ячейки автоматизаций
    const autoGrid = $("#automationsGrid");
    if (autoGrid) {
      const cellMap = {};
      $$(".auto-cell", autoGrid).forEach(c => {
        cellMap[c.dataset.autoId] = c;
      });

      for (const autoId of subLayout.autoOrder) {
        const c = cellMap[autoId];
        if (c) autoGrid.appendChild(c);
      }

      $$(".auto-cell", autoGrid).forEach(c => {
        const autoId = c.dataset.autoId;
        const isHidden = subLayout.autoHidden.includes(autoId);
        c.classList.toggle("is-hidden", isHidden);
      });
    }
  };

  const toggleSubBlockVisibility = (subId, forceVisible) => {
    const isHidden = subLayout.hidden.includes(subId);
    const targetHidden = forceVisible !== undefined ? !forceVisible : !isHidden;
    if (targetHidden && !isHidden) {
      subLayout.hidden.push(subId);
      const nameObj = SUB_BLOCK_NAMES[subId];
      const name = LANG === "ru" ? (nameObj?.fullRu || subId) : (nameObj?.fullEn || subId);
      toast((LANG === "ru" ? `Раздел «${name}» скрыт` : `Section "${name}" hidden`));
    } else if (!targetHidden && isHidden) {
      subLayout.hidden = subLayout.hidden.filter(x => x !== subId);
      const nameObj = SUB_BLOCK_NAMES[subId];
      const name = LANG === "ru" ? (nameObj?.fullRu || subId) : (nameObj?.fullEn || subId);
      toast((LANG === "ru" ? `Раздел «${name}» восстановлен` : `Section "${name}" restored`));
    }
    saveSubLayout();
    applySubLayout();
  };

  const toggleAutoCellVisibility = (autoId, forceVisible) => {
    const isHidden = subLayout.autoHidden.includes(autoId);
    const targetHidden = forceVisible !== undefined ? !forceVisible : !isHidden;
    if (targetHidden && !isHidden) {
      subLayout.autoHidden.push(autoId);
      const nameObj = AUTO_CELL_NAMES[autoId];
      const name = LANG === "ru" ? (nameObj?.fullRu || autoId) : (nameObj?.fullEn || autoId);
      toast((LANG === "ru" ? `Сервис «${name}» скрыт` : `Service "${name}" hidden`));
    } else if (!targetHidden && isHidden) {
      subLayout.autoHidden = subLayout.autoHidden.filter(x => x !== autoId);
      const nameObj = AUTO_CELL_NAMES[autoId];
      const name = LANG === "ru" ? (nameObj?.fullRu || autoId) : (nameObj?.fullEn || autoId);
      toast((LANG === "ru" ? `Сервис «${name}» восстановлен` : `Service "${name}" restored`));
    }
    saveSubLayout();
    applySubLayout();
  };

  // Кнопки скрытия подблоков по клику на ×
  $$(".run-sub-block", container).forEach(block => {
    const subId = block.dataset.subId;
    const hideBtn = block.querySelector(".sub-btn-hide");
    if (hideBtn) {
      hideBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleSubBlockVisibility(subId, false);
      });
    }
  });

  // Плавное перетаскивание подблоков с плейсхолдером (как и везде у нас: .task-row-placeholder)
  let draggedSubBlock = null;
  let subPlaceholder = null;

  container.addEventListener("pointerdown", (e) => {
    if (!home || !home.classList.contains("is-customizing")) return;
    if (e.button !== 0) return;
    // Игнорируем клики по интерактивным элементам и ячейкам сервисов
    if (e.target.closest("button, input, select, textarea, a, .sub-btn-hide, .auto-cell")) return;

    const block = e.target.closest(".run-sub-block");
    if (!block || !container.contains(block)) return;

    draggedSubBlock = block;
    const startY = e.clientY;
    const blockRect = block.getBoundingClientRect();
    const grabOffsetX = e.clientX - blockRect.left;
    const grabOffsetY = e.clientY - blockRect.top;

    // Сохраняем начальные позиции всех видимых подблоков для точного расчета превью смены мест
    const visibleBlocks = $$(".run-sub-block:not(.is-hidden)", container);
    const sourceIndex = visibleBlocks.indexOf(draggedSubBlock);
    const initialTops = visibleBlocks.map(b => b.getBoundingClientRect().top);

    let isMoving = false;
    let subGhost = null;
    let animFrameId = null;
    let currentX = blockRect.left;
    let currentY = blockRect.top;
    let targetX = currentX;
    let targetY = currentY;
    let currentTilt = 0;
    let targetTilt = 0;
    let vy = 0;
    let lastPointerY = e.clientY;
    let lastPointerTime = performance.now();
    let currentSwapTarget = null;

    const renderPhysics = () => {
      if (!subGhost) return;
      currentX += (targetX - currentX) * 0.35;
      currentY += (targetY - currentY) * 0.35;
      currentTilt += (targetTilt - currentTilt) * 0.25;

      const px = Math.round(currentX);
      const py = Math.round(currentY);
      const tilt = Math.round(currentTilt * 10) / 10;
      subGhost.style.transform = `translate3d(${px}px, ${py}px, 0) rotate(${tilt}deg)`;
      animFrameId = requestAnimationFrame(renderPhysics);
    };

    const onPointerMove = (ev) => {
      if (!draggedSubBlock) return;
      const dy = ev.clientY - startY;
      if (!isMoving && Math.abs(dy) > 3) {
        isMoving = true;
        subPlaceholder = document.createElement("div");
        subPlaceholder.className = "sub-block-placeholder";
        subPlaceholder.style.height = `${blockRect.height}px`;

        // Создаем клон подблока в том же стиле, что и перемещаемая карточка
        subGhost = draggedSubBlock.cloneNode(true);
        subGhost.removeAttribute("id");
        subGhost.querySelectorAll("[id]").forEach(el => el.removeAttribute("id"));
        subGhost.classList.remove("is-dragging", "is-drag-source");
        subGhost.classList.add("dash-drag-card-ghost", "sub-block-drag-ghost");
        subGhost.style.position = "fixed";
        subGhost.style.top = "0px";
        subGhost.style.left = "0px";
        subGhost.style.width = blockRect.width + "px";
        subGhost.style.height = blockRect.height + "px";
        subGhost.style.transform = `translate3d(${Math.round(currentX)}px, ${Math.round(currentY)}px, 0)`;
        document.body.appendChild(subGhost);

        draggedSubBlock.classList.add("is-drag-source");
        draggedSubBlock.after(subPlaceholder);

        animFrameId = requestAnimationFrame(renderPhysics);
      }

      if (isMoving && subPlaceholder) {
        ev.preventDefault();
        targetX = ev.clientX - grabOffsetX;
        targetY = ev.clientY - grabOffsetY;

        const now = performance.now();
        const dt = Math.max(now - lastPointerTime, 8);
        const instantVy = (ev.clientY - lastPointerY) / dt;
        lastPointerY = ev.clientY;
        lastPointerTime = now;
        vy = vy * 0.35 + instantVy * 0.65;
        targetTilt = Math.max(-2.5, Math.min(2.5, vy * 2.2));

        // Живой Swap Preview: определяем, над каким блоком находится курсор
        let targetBlock = null;
        let targetIndex = -1;

        for (let i = 0; i < visibleBlocks.length; i++) {
          if (i === sourceIndex) continue;
          const top = initialTops[i];
          const height = visibleBlocks[i].offsetHeight;
          if (ev.clientY >= top && ev.clientY <= top + height) {
            targetBlock = visibleBlocks[i];
            targetIndex = i;
            break;
          }
        }

        if (targetBlock && targetIndex !== -1) {
          if (currentSwapTarget !== targetBlock) {
            currentSwapTarget = targetBlock;
            // Блок, на который навелись, плавно перемещается на старое место перетаскиваемого блока
            const dyTarget = initialTops[sourceIndex] - initialTops[targetIndex];
            targetBlock.style.transform = `translateY(${dyTarget}px)`;
            targetBlock.classList.add("is-swap-displaced");

            // Плейсхолдер перетаскиваемого блока занимает место целевого блока
            const dyPlaceholder = initialTops[targetIndex] - initialTops[sourceIndex];
            subPlaceholder.style.transform = `translateY(${dyPlaceholder}px)`;

            // Все остальные блоки сбрасывают смещение
            visibleBlocks.forEach((b, idx) => {
              if (idx !== targetIndex && idx !== sourceIndex) {
                b.style.transform = "translateY(0px)";
                b.classList.remove("is-swap-displaced");
              }
            });
          }
        } else {
          // Если курсор вне других блоков — возвращаем всё на исходные позиции
          if (currentSwapTarget) {
            currentSwapTarget = null;
            visibleBlocks.forEach(b => {
              b.style.transform = "translateY(0px)";
              b.classList.remove("is-swap-displaced");
            });
            subPlaceholder.style.transform = "translateY(0px)";
          }
        }
      }
    };

    const onPointerUp = () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("pointercancel", onPointerUp);

      if (animFrameId) {
        cancelAnimationFrame(animFrameId);
        animFrameId = null;
      }

      if (subGhost) {
        subGhost.remove();
        subGhost = null;
      }

      if (isMoving && draggedSubBlock) {
        if (currentSwapTarget) {
          // Фиксируем обмен местами в subLayout.order
          const idA = draggedSubBlock.dataset.subId;
          const idB = currentSwapTarget.dataset.subId;
          const idxA = subLayout.order.indexOf(idA);
          const idxB = subLayout.order.indexOf(idB);
          if (idxA !== -1 && idxB !== -1) {
            subLayout.order[idxA] = idB;
            subLayout.order[idxB] = idA;
            saveSubLayout();
            toast(LANG === "ru" ? "Разделы поменялись местами" : "Sections swapped");
          }
        }

        // Сбрасываем временные стили и классы
        visibleBlocks.forEach(b => {
          b.style.transform = "";
          b.classList.remove("is-swap-displaced", "is-drag-source");
        });
        if (subPlaceholder) {
          subPlaceholder.remove();
          subPlaceholder = null;
        }

        draggedSubBlock.classList.remove("is-drag-source", "is-dragging");
        applySubLayout();
      } else if (draggedSubBlock) {
        draggedSubBlock.classList.remove("is-drag-source", "is-dragging");
        if (subPlaceholder) {
          subPlaceholder.remove();
          subPlaceholder = null;
        }
      }

      currentSwapTarget = null;
      draggedSubBlock = null;
    };

    window.addEventListener("pointermove", onPointerMove, { passive: false });
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointercancel", onPointerUp);
  });

  // Кнопки скрытия и Drag and Drop ячеек автоматизаций
  const autoGrid = $("#automationsGrid");
  if (autoGrid) {
    $$(".auto-cell", autoGrid).forEach(cell => {
      const autoId = cell.dataset.autoId;
      const hideBtn = cell.querySelector(".auto-cell-hide-btn");
      if (hideBtn) {
        hideBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          toggleAutoCellVisibility(autoId, false);
        });
      }

      cell.draggable = true;
      cell.addEventListener("dragstart", (e) => {
        const homeEl = $("#screen-home");
        if (!homeEl || !homeEl.classList.contains("is-customizing")) {
          e.preventDefault();
          return;
        }
        e.dataTransfer.setData("text/auto-cell", autoId);
        e.dataTransfer.effectAllowed = "move";
        cell.classList.add("is-dragging");
      });
      cell.addEventListener("dragend", () => {
        cell.classList.remove("is-dragging");
        $$(".auto-cell", autoGrid).forEach(c => c.classList.remove("drag-over"));
      });
      cell.addEventListener("dragover", (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        cell.classList.add("drag-over");
      });
      cell.addEventListener("dragleave", () => {
        cell.classList.remove("drag-over");
      });
      cell.addEventListener("drop", (e) => {
        e.preventDefault();
        cell.classList.remove("drag-over");
        const srcId = e.dataTransfer.getData("text/auto-cell");
        if (!srcId || srcId === autoId) return;

        const oldIdx = subLayout.autoOrder.indexOf(srcId);
        const newIdx = subLayout.autoOrder.indexOf(autoId);
        if (oldIdx !== -1 && newIdx !== -1) {
          subLayout.autoOrder.splice(oldIdx, 1);
          subLayout.autoOrder.splice(newIdx, 0, srcId);
          saveSubLayout();
          applySubLayout();
        }
      });
    });
  }

  window.resetControlsSubLayout = () => {
    subLayout = JSON.parse(JSON.stringify(DEFAULT_SUB_LAYOUT));
    saveSubLayout();
    applySubLayout();
  };

  // Первоначальное применение
  applySubLayout();
}
initControlsSubLayout();

/* -------------------------------------------------- выбор разрешения окна */
function initGameResolution() {
  const chip = $("#gameResChip");
  const pop = $("#resPop");
  const valEl = $("#gameResVal");
  const tagEl = $("#resCurrentTag");
  const presetList = $("#resPresetList");
  const customW = $("#resCustomW");
  const customH = $("#resCustomH");
  const btnApply = $("#btnApplyCustomRes");

  activeResolution = activeResolution || { w: 1152, h: 756 };

  const setResolution = async (w, h, fromBackend = false, skipToast = false) => {
    w = parseInt(w, 10);
    h = parseInt(h, 10);
    if (isNaN(w) || isNaN(h) || w <= 0 || h <= 0) return;

    const isSame = activeResolution.w === w && activeResolution.h === h;
    activeResolution = { w, h };

    GAME_RES = `${w} × ${h}`;
    try {
      localStorage.setItem("ae_game_res", GAME_RES);
    } catch (_) {}

    // Устанавливаем CSS переменные для окна и слота игры
    document.documentElement.style.setProperty("--game-w", `${w}px`);
    document.documentElement.style.setProperty("--game-h", `${h}px`);
    document.documentElement.style.setProperty("--game-aspect", `${w} / ${h}`);

    const home = $("#screen-home");
    if (home) {
      home.style.setProperty("--game-w", `${w}px`);
      home.style.setProperty("--game-h", `${h}px`);
      home.style.setProperty("--game-aspect", `${w} / ${h}`);
    }

    if (valEl) valEl.textContent = GAME_RES;
    if (tagEl) tagEl.textContent = `${w}×${h}`;

    updateGameAspect(GAME_RES);
    updateGameSub();

    if (presetList) {
      $$(".res-item", presetList).forEach(btn => {
        const bw = parseInt(btn.dataset.w, 10);
        const bh = parseInt(btn.dataset.h, 10);
        btn.classList.toggle("is-active", bw === w && bh === h);
      });
    }

    const homePills = $$("#gameResPills .res-pill");
    homePills.forEach(p => {
      const pw = parseInt(p.dataset.w, 10);
      const ph = parseInt(p.dataset.h, 10);
      p.classList.toggle("is-on", pw === w && ph === h);
    });
    const gameSub = $("#gameEmptySub");
    if (gameSub) gameSub.textContent = `Embedded game window · ${w} × ${h}`;

    if (customW) customW.value = w;
    if (customH) customH.value = h;

    // Закрываем меню (если присутствуют старые элементы)
    if (pop) pop.hidden = true;
    if (chip) chip.classList.remove("is-active");

    // Вызываем бэкенд, ТОЛЬКО если действие инициировано пользователем в UI и разрешение изменилось.
    // Если вызов пришел из бэкенда (fromBackend = true), повторный вызов заблокирован, чтобы не было пинг-понга.
    if (!fromBackend && !isSame) {
      try {
        if (window.pywebview && pywebview.api && pywebview.api.set_game_resolution) {
          await pywebview.api.set_game_resolution(w, h);
        }
      } catch (err) {
        console.error("Failed to set game resolution in backend:", err);
      }
      if (!skipToast) {
        toast(t("res_changed").replace("{res}", GAME_RES));
      }
    }
  };

  window.applyGameResolution = setResolution;

  if (chip && pop) {
    // Открытие / закрытие выпадающего меню
    chip.addEventListener("click", (e) => {
      e.stopPropagation();
      const willOpen = pop.hidden;
      pop.hidden = !willOpen;
      chip.classList.toggle("is-active", willOpen);
    });

    // Закрытие при клике вне меню
    document.addEventListener("click", (e) => {
      if (!pop.hidden && !e.target.closest("#resAnchor")) {
        pop.hidden = true;
        chip.classList.remove("is-active");
      }
    });

    // Закрытие по Escape
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !pop.hidden) {
        pop.hidden = true;
        chip.classList.remove("is-active");
      }
    });
  }

  // Пресеты
  if (presetList) {
    $$(".res-item", presetList).forEach(btn => {
      btn.addEventListener("click", () => {
        const w = btn.dataset.w;
        const h = btn.dataset.h;
        setResolution(w, h);
      });
    });
  }

  // Границы допустимого разрешения:
  // Мин: 1024 × 720 (или 1024 × 768 для экранов 4:3), ниже макрос не видит кнопки и ломается поиск шаблонов.
  // Макс: 1920 × 1080 (FHD), выше окно выходит за границы экрана, а OpenCV тратит слишком много CPU на поиск.
  const MIN_W = 1024, MAX_W = 1920;
  const MIN_H = 720, MAX_H = 1080;

  // Применение кастомного разрешения
  const applyCustom = () => {
    if (!customW || !customH) return;
    let w = parseInt(customW.value, 10);
    let h = parseInt(customH.value, 10);
    if (isNaN(w) || isNaN(h)) return;

    let clamped = false;
    if (w < MIN_W) { w = MIN_W; clamped = true; }
    if (w > MAX_W) { w = MAX_W; clamped = true; }
    if (h < MIN_H) { h = MIN_H; clamped = true; }
    if (h > MAX_H) { h = MAX_H; clamped = true; }

    customW.value = w;
    customH.value = h;
    setResolution(w, h);
    if (clamped) {
      toast(t("res_clamped_hint"));
    }
  };

  if (btnApply) {
    btnApply.addEventListener("click", applyCustom);
  }

  // Быстрое применение по Enter прямо из полей ввода
  if (customW) {
    customW.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); applyCustom(); }
    });
  }
  if (customH) {
    customH.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); applyCustom(); }
    });
  }

  // Кнопки разрешения на экране Home (#gameResPills)
  const homePills = $$("#gameResPills .res-pill");
  if (homePills.length) {
    homePills.forEach(pill => {
      pill.addEventListener("click", () => {
        const w = pill.dataset.w;
        const h = pill.dataset.h;
        setResolution(w, h);
      });
    });
  }

  // Экспорт функции синхронизации разрешения с бэкендом
  window.loadResolutionUI = async () => {
    if (window.pywebview?.api?.get_game_resolution) {
      try {
        const res = await pywebview.api.get_game_resolution();
        if (res && res.width && res.height) {
          setResolution(res.width, res.height, true);
        }
      } catch (_) {}
    }
  };

  // Восстановление сохранённого разрешения при старте
  try {
    const saved = localStorage.getItem("ae_game_res");
    if (saved) {
      const parts = saved.split(/[×xX]/);
      if (parts.length >= 2) {
        setResolution(parts[0].trim(), parts[1].trim(), true);
      }
    }
  } catch (_) {}
}
initGameResolution();

/* ---------------------------------------------------- сортировка задач */
function initTaskReordering() {
  const queueCard = $("#screen-tasks .glass-card");
  if (!queueCard) return;

  let draggedRow = null;
  let placeholder = null;
  let ghost = null;
  let startX = 0;
  let startY = 0;
  let grabOffsetX = 0;
  let grabOffsetY = 0;
  let isDraggingActive = false;

  queueCard.addEventListener("pointerdown", (e) => {
    // Драг активируется по ручке .grip или по телу строки (кроме интерактивных контролов)
    const grip = e.target.closest(".grip");
    const row = e.target.closest(".task-row");
    if (!row) return;
    if (!grip && e.target.closest("input, button, label, .switch, a")) return;
    if (e.button !== 0) return;

    draggedRow = row;
    startX = e.clientX;
    startY = e.clientY;
    isDraggingActive = false;

    const rowRect = row.getBoundingClientRect();
    grabOffsetX = e.clientX - rowRect.left;
    grabOffsetY = e.clientY - rowRect.top;

    const onPointerMove = (ev) => {
      if (!draggedRow) return;

      const dx = ev.clientX - startX;
      const dy = ev.clientY - startY;

      // Порог сдвига в 4px защищает обычные клики выбора задачи от случайного срыва в драг
      if (!isDraggingActive) {
        if (Math.hypot(dx, dy) < 4) return;
        isDraggingActive = true;

        const height = draggedRow.offsetHeight;
        const width = rowRect.width;

        placeholder = document.createElement("div");
        placeholder.className = "task-row-placeholder";
        placeholder.style.height = `${height}px`;

        ghost = draggedRow.cloneNode(true);
        ghost.className = "task-drag-ghost";
        ghost.style.width = `${width}px`;
        ghost.style.left = `${ev.clientX - grabOffsetX}px`;
        ghost.style.top = `${ev.clientY - grabOffsetY}px`;
        document.body.appendChild(ghost);

        draggedRow.after(placeholder);
        draggedRow.classList.add("is-dragging");
      }

      ev.preventDefault();

      if (ghost) {
        ghost.style.left = `${ev.clientX - grabOffsetX}px`;
        ghost.style.top = `${ev.clientY - grabOffsetY}px`;
      }

      const rows = $$("#screen-tasks .task-row:not(.is-dragging)");
      for (const other of rows) {
        const rect = other.getBoundingClientRect();
        const mid = rect.top + rect.height / 2;
        if (ev.clientY < mid) {
          other.before(placeholder);
          return;
        }
      }
      const last = rows[rows.length - 1];
      if (last) {
        last.after(placeholder);
      }
    };

    const onPointerUp = () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("pointercancel", onPointerUp);

      if (ghost) {
        ghost.remove();
        ghost = null;
      }

      if (isDraggingActive && draggedRow && placeholder) {
        placeholder.replaceWith(draggedRow);
        draggedRow.classList.remove("is-dragging");

        // Синхронизируем массив realTasksList с новым DOM-порядком карточек
        const newIds = $$("#taskQueueList .task-row").map(r => r.dataset.taskId).filter(Boolean);
        if (newIds.length === realTasksList.length) {
          const taskMap = new Map(realTasksList.map(t => [t.id, t]));
          realTasksList = newIds.map(id => taskMap.get(id)).filter(Boolean);
          saveTasksDebounced();
          renderMiniQueue(realTasksList, lastRunStatus?.current_task, lastRunStatus?.current_repeat);
        }
        toast(t("task_reordered"));
      } else if (draggedRow) {
        draggedRow.classList.remove("is-dragging");
        if (placeholder) placeholder.remove();
      }

      placeholder = null;
      draggedRow = null;
      isDraggingActive = false;
    };

    window.addEventListener("pointermove", onPointerMove, { passive: false });
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointercancel", onPointerUp);
  });
}
initTaskReordering();

/* ------------------------------------------------------------ записи */
/* Запись управляется ТОЛЬКО хоткеем F8: на панели нет кнопки записи,
   как и в реальном replay.py: клики по собственной панели в запись не
   попадают, а здесь просто нечему попадать. */
const rec = { on: false, seconds: 0, timer: null };

function renderRec() {
  $("#recStatus").classList.toggle("is-on", rec.on);
  $("#recTitle").textContent = rec.on ? "Recording" : "Not recording";
  $("#recHint").textContent = rec.on
    ? "Capturing mouse and keys · press F8 to stop"
    : "Recording runs entirely from the hotkey. Play one match by hand.";
}

function toggleRecording() {
  rec.on = !rec.on;
  clearInterval(rec.timer);
  if (rec.on) {
    rec.seconds = 0;
    $("#recTimer").textContent = "00:00";
    rec.timer = setInterval(() => {
      rec.seconds++;
      $("#recTimer").textContent =
        String(Math.floor(rec.seconds / 60)).padStart(2, "0") + ":" + String(rec.seconds % 60).padStart(2, "0");
    }, 1000);
    log("info", "Recording started (F8)");
  } else {
    log("ok", "Recording saved: " + $("#recTimer").textContent);
    $("#recTimer").textContent = "00:00";
  }
  renderRec();
}

window.addEventListener("keydown", e => {
  if (e.key === "F8") {
    e.preventDefault();
    toggleRecording();
  } else if (e.key === "F6") {
    e.preventDefault();
    if (typeof window.toggleAutoRestartLoop === "function") window.toggleAutoRestartLoop();
  } else if (e.key === "F10") {
    e.preventDefault();
    if (typeof window.triggerVipRejoin === "function") window.triggerVipRejoin();
  }
});
renderRec();

/* ------------------------------------------------------------ настройки */
/* разрешение игры */
$$("#resChips .chip-btn").forEach(chip => {
  chip.addEventListener("click", () => {
    $$("#resChips .chip-btn").forEach(c => c.classList.remove("is-on"));
    chip.classList.add("is-on");
    const rawRes = chip.dataset.res || "";
    const parts = rawRes.split(/[\s×x]+/).map(n => parseInt(n, 10));
    if (parts.length >= 2 && !isNaN(parts[0]) && !isNaN(parts[1]) && typeof window.applyGameResolution === "function") {
      window.applyGameResolution(parts[0], parts[1]);
    } else {
      GAME_RES = rawRes;
      updateGameSub();
      updateGameAspect(GAME_RES);
      toast(t("game_sub").replace("{res}", GAME_RES));
    }
  });
});


/* внешний вид: темы, плотность, углы, движение */
function bindPicker(containerSel, attr, defaultVal = "default") {
  const container = $(containerSel);
  if (!container) return;
  $$(containerSel + " [data-" + attr + "-set]").forEach(btn => {
    btn.addEventListener("click", () => {
      $$(containerSel + " [data-" + attr + "-set]").forEach(b => b.classList.remove("is-on"));
      btn.classList.add("is-on");
      const val = btn.dataset[attr + "Set"];
      if (val === "default" || (attr === "theme" && val === "onyx") || (attr === "motion" && val === "full")) {
        delete document.documentElement.dataset[attr];
      } else {
        document.documentElement.dataset[attr] = val;
      }
      try {
        localStorage.setItem("ae_" + attr, val);
      } catch (_) {}
    });
  });
  const saved = localStorage.getItem("ae_" + attr) || defaultVal;
  const curBtn = $(containerSel + ` [data-${attr}-set="${saved}"]`);
  if (curBtn) curBtn.click();
}
bindPicker("#themePicker", "theme", "onyx");
bindPicker("#densitySeg", "density", "default");
bindPicker("#cornersSeg", "corners", "default");
bindPicker("#motionSeg", "motion", "full");

// Выбор масштаба шрифта (Font Scale)
const fontScaleSeg = $("#fontScaleSeg");
if (fontScaleSeg) {
  $$("button", fontScaleSeg).forEach(btn => {
    btn.addEventListener("click", () => {
      const scale = btn.dataset.fontScaleSet;
      $$("button", fontScaleSeg).forEach(b => b.classList.toggle("is-on", b === btn));
      if (scale === "default") {
        delete document.documentElement.dataset.fontScale;
      } else {
        document.documentElement.dataset.fontScale = scale;
      }
      localStorage.setItem("ae_font_scale", scale);
    });
  });
  const savedScale = localStorage.getItem("ae_font_scale") || "default";
  const curScaleBtn = $(`[data-font-scale-set="${savedScale}"]`, fontScaleSeg);
  if (curScaleBtn) curScaleBtn.click();
}

// Выбор интенсивности размытия стекла (Glass Blur)
const glassBlurSeg = $("#glassBlurSeg");
if (glassBlurSeg) {
  $$("button", glassBlurSeg).forEach(btn => {
    btn.addEventListener("click", () => {
      const blur = btn.dataset.glassBlurSet;
      $$("button", glassBlurSeg).forEach(b => b.classList.toggle("is-on", b === btn));
      if (blur === "ultra") {
        delete document.documentElement.dataset.glassBlur;
      } else {
        document.documentElement.dataset.glassBlur = blur;
      }
      localStorage.setItem("ae_glass_blur", blur);
    });
  });
  const savedBlur = localStorage.getItem("ae_glass_blur") || "ultra";
  const curBlurBtn = $(`[data-glass-blur-set="${savedBlur}"]`, glassBlurSeg);
  if (curBlurBtn) curBlurBtn.click();
}

// Звуковое оповещение через Web Audio API (приятный двухтональный аккорд)
function playSoundAlert(isWin = true) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(isWin ? 587.33 : 349.23, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(isWin ? 880 : 220, ctx.currentTime + 0.16);
    gain.gain.setValueAtTime(0.18, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.35);
  } catch (_) {}
}

const btnTestSound = $("#btnTestSound");
if (btnTestSound) {
  btnTestSound.addEventListener("click", () => {
    playSoundAlert(true);
    toast(LANG === "ru" ? "Звуковое оповещение проверено" : "Sound notification tested");
  });
}

// Привязка чекбокса звуковых оповещений
const swSoundAlerts = $("#swSoundAlerts");
if (swSoundAlerts) {
  swSoundAlerts.addEventListener("change", () => {
    localStorage.setItem("ae_sound_alerts", swSoundAlerts.checked);
  });
}

// Привязка порога поражений (Loss Streak Stop)
const selLossStreakStop = $("#selLossStreakStop");
if (selLossStreakStop) {
  selLossStreakStop.addEventListener("change", async () => {
    const val = parseInt(selLossStreakStop.value, 10);
    if (window.pywebview && pywebview.api && pywebview.api.set_setting) {
      try {
        await pywebview.api.set_setting("replay_loss_streak_stop", val);
      } catch (_) {}
    }
    localStorage.setItem("ae_loss_streak_stop", val);
  });
}

// Привязка контроля фокуса (Focus Guard)
const swFocusGuard = $("#swFocusGuard");
if (swFocusGuard) {
  swFocusGuard.addEventListener("change", async () => {
    const val = swFocusGuard.checked;
    if (window.pywebview && pywebview.api && pywebview.api.set_setting) {
      try {
        await pywebview.api.set_setting("replay_require_focus", val);
      } catch (_) {}
    }
    localStorage.setItem("ae_require_focus", val);
  });
}

// Привязка авто-скриншота при сбое
const swAutoScreenshot = $("#swAutoScreenshot");
if (swAutoScreenshot) {
  swAutoScreenshot.addEventListener("change", () => {
    localStorage.setItem("ae_auto_screenshot", swAutoScreenshot.checked);
  });
}

// Привязка хуманизатора кликов
const swClickHumanizer = $("#swClickHumanizer");
if (swClickHumanizer) {
  swClickHumanizer.addEventListener("change", () => {
    localStorage.setItem("ae_click_humanizer", swClickHumanizer.checked);
  });
}

// Привязка ссылки на приватный сервер
const setVipLink = $("#setVipLink");
if (setVipLink) {
  setVipLink.addEventListener("change", async () => {
    const val = setVipLink.value.trim();
    if (window.pywebview && pywebview.api && pywebview.api.set_setting) {
      try {
        await pywebview.api.set_setting("private_server_link", val);
        toast(LANG === "ru" ? "VIP ссылка сохранена" : "VIP link saved");
      } catch (_) {}
    }
    localStorage.setItem("ae_vip_link", val);
  });
}

$("#btnAttach").addEventListener("click", async () => {
  if (window.pywebview && pywebview.api) {
    try {
      if (pywebview.api.launch_roblox) {
        await pywebview.api.launch_roblox();
        toast(LANG === "ru" ? "Запуск Roblox..." : "Launching Roblox...");
        return;
      }
    } catch (_) {}
  }
  toast(LANG === "ru" ? "Ожидание окна Roblox..." : "Waiting for Roblox window...");
});

// --- Game Window Settings ---
const selRobloxWindow = $("#selRobloxWindow");
const btnAttachRoblox = $("#btnAttachRoblox");
const btnUnattachRoblox = $("#btnUnattachRoblox");
const btnForceRejoin = $("#btnForceRejoin");
const swFlickerFree = $("#swFlickerFree");
const swWgcCapture = $("#swWgcCapture");

async function refreshRobloxWindowsList() {
  if (!selRobloxWindow || !window.pywebview?.api?.list_roblox_windows) return;
  try {
    const wins = await pywebview.api.list_roblox_windows();
    const curVal = selRobloxWindow.value;
    selRobloxWindow.innerHTML = `<option value="">${LANG === "ru" ? "Авто-поиск Roblox" : "Auto-detect Roblox"}</option>`;
    if (Array.isArray(wins)) {
      wins.forEach(w => {
        const opt = document.createElement("option");
        opt.value = String(w.hwnd);
        opt.textContent = `${w.title || "Roblox"} (pid: ${w.pid || "?"}, hwnd: ${w.hwnd})`;
        if (String(w.hwnd) === curVal) opt.selected = true;
        selRobloxWindow.appendChild(opt);
      });
    }
  } catch (_) {}
}

if (selRobloxWindow) {
  selRobloxWindow.addEventListener("focus", refreshRobloxWindowsList);
}

if (btnAttachRoblox) {
  btnAttachRoblox.addEventListener("click", async () => {
    if (!window.pywebview?.api) return;
    const hwnd = selRobloxWindow ? selRobloxWindow.value : "";
    try {
      if (hwnd && pywebview.api.attach_roblox_window) {
        const res = await pywebview.api.attach_roblox_window(hwnd);
        toast(res?.ok ? (LANG === "ru" ? "Окно привязано" : "Roblox attached") : (LANG === "ru" ? "Ошибка привязки" : "Attach failed"));
      } else if (pywebview.api.launch_roblox) {
        await pywebview.api.launch_roblox();
        toast(LANG === "ru" ? "Запуск и привязка Roblox..." : "Launching & attaching Roblox...");
      }
    } catch (e) {
      toast("Attach error: " + e);
    }
  });
}

if (btnUnattachRoblox) {
  btnUnattachRoblox.addEventListener("click", async () => {
    if (!window.pywebview?.api?.detach_roblox_window) return;
    try {
      await pywebview.api.detach_roblox_window();
      toast(LANG === "ru" ? "Окно отвязано" : "Roblox unattached");
    } catch (e) {
      toast("Detach error: " + e);
    }
  });
}

if (btnForceRejoin) {
  btnForceRejoin.addEventListener("click", async () => {
    if (!window.pywebview?.api?.debug_force_rejoin) return;
    try {
      toast(LANG === "ru" ? "Перезапуск и вход в лобби..." : "Force rejoining lobby...");
      const res = await pywebview.api.debug_force_rejoin();
      if (!res?.ok && res?.reason) {
        toast("Rejoin failed: " + res.reason);
      }
    } catch (e) {
      toast("Rejoin error: " + e);
    }
  });
}

if (swFlickerFree) {
  swFlickerFree.addEventListener("change", async () => {
    const val = swFlickerFree.checked;
    if (window.pywebview?.api?.set_setting) {
      try { await pywebview.api.set_setting("flicker_free_capture", val); } catch (_) {}
    }
    localStorage.setItem("ae_flicker_free", val);
  });
}

if (swWgcCapture) {
  swWgcCapture.addEventListener("change", async () => {
    const val = swWgcCapture.checked;
    if (window.pywebview?.api?.set_setting) {
      try { await pywebview.api.set_setting("use_wgc_capture", val); } catch (_) {}
    }
    localStorage.setItem("ae_wgc_capture", val);
  });
}

$$(".card-actions .icon-btn[title='Pop out']").forEach(btn => {
  btn.addEventListener("click", async () => {
    if (window.pywebview?.api?.pop_out_logs) {
      try { await pywebview.api.pop_out_logs(); return; } catch (_) {}
    }
    toast(LANG === "ru" ? "Окно журнала открыто" : "Log window popped out");
  });
});

const btnTestHook = $("#btnTestHook");
if (btnTestHook) {
  btnTestHook.addEventListener("click", async (e) => {
    const b = e.currentTarget;
    if (window.pywebview && pywebview.api && pywebview.api.test_webhook) {
      b.disabled = true;
      b.textContent = "...";
      try {
        const res = await pywebview.api.test_webhook();
        b.textContent = res && res.ok ? (LANG === "ru" ? "Отправлено!" : "Sent!") : (LANG === "ru" ? "Ошибка" : "Error");
        toast(res && res.ok ? (LANG === "ru" ? "Тестовое сообщение отправлено в Discord" : "Discord test embed sent successfully") : (res && res.error ? res.error : "Webhook failed"));
      } catch (err) {
        b.textContent = "Error";
        toast("Failed: " + err);
      } finally {
        setTimeout(() => { b.disabled = false; b.textContent = "Send test"; }, 2200);
      }
      return;
    }
    b.textContent = "Sent";
    toast(LANG === "ru" ? "Тестовое сообщение отправлено в Discord" : "Test card posted to Discord");
    setTimeout(() => { b.textContent = "Send test"; }, 1600);
  });
}

// Привязка настроек Discord Webhook
const setWebhookUrl = $("#setWebhookUrl");
if (setWebhookUrl) {
  setWebhookUrl.addEventListener("change", async () => {
    if (window.pywebview && pywebview.api && pywebview.api.set_setting) {
      try {
        await pywebview.api.set_setting("discord_webhook_url", setWebhookUrl.value.trim());
        toast(LANG === "ru" ? "Webhook URL сохранён" : "Webhook URL saved");
      } catch (_) {}
    }
  });
}

const swWebhookResults = $("#swWebhookResults");
if (swWebhookResults) {
  swWebhookResults.addEventListener("change", async () => {
    if (window.pywebview && pywebview.api && pywebview.api.set_setting) {
      try {
        await pywebview.api.set_setting("discord_alerts_enabled", swWebhookResults.checked);
      } catch (_) {}
    }
  });
}

const swWebhookPings = $("#swWebhookPings");
if (swWebhookPings) {
  swWebhookPings.addEventListener("change", async () => {
    if (window.pywebview && pywebview.api && pywebview.api.set_setting) {
      try {
        await pywebview.api.set_setting("discord_pings_enabled", swWebhookPings.checked);
      } catch (_) {}
    }
  });
}

const selWebhookInterval = $("#selWebhookInterval");
if (selWebhookInterval) {
  selWebhookInterval.addEventListener("change", async () => {
    if (window.pywebview && pywebview.api && pywebview.api.set_setting) {
      try {
        await pywebview.api.set_setting("discord_status_interval", parseInt(selWebhookInterval.value, 10));
      } catch (_) {}
    }
  });
}

const btnCheckUpd = $("#btnCheckUpd");
if (btnCheckUpd) {
  btnCheckUpd.addEventListener("click", async () => {
    const state = $("#updState");
    if (state) {
      state.textContent = t("upd_checking") || "Checking...";
      state.className = "upd-check";
    }
    if (window.pywebview && pywebview.api && pywebview.api.check_for_updates) {
      try {
        const res = await pywebview.api.check_for_updates();
        if (res && res.update_available) {
          if (state) {
            state.textContent = (LANG === "ru" ? "Доступно: " : "Available: ") + res.latest_version;
            state.className = "upd-warn";
          }
          toast((LANG === "ru" ? "Найдена новая версия: " : "New version available: ") + res.latest_version);
        } else {
          if (state) {
            state.textContent = t("upd_latest") || "Up to date";
            state.className = "upd-ok";
          }
          toast(t("upd_latest") || "Up to date");
        }
      } catch (e) {
        if (state) {
          state.textContent = "Check failed";
          state.className = "upd-err";
        }
      }
      return;
    }
    setTimeout(() => {
      if (state) {
        state.textContent = t("upd_latest");
        state.className = "upd-ok";
      }
      toast(t("upd_latest"));
    }, 1500);
  });
}

// Отладочные действия
const btnDebugScreenshot = $("#btnDebugScreenshot");
if (btnDebugScreenshot) {
  btnDebugScreenshot.addEventListener("click", async () => {
    if (window.pywebview && pywebview.api && pywebview.api.save_debug_screenshot) {
      try {
        await pywebview.api.save_debug_screenshot();
        toast(LANG === "ru" ? "Отладочный скриншот сохранён" : "Debug screenshot saved");
        return;
      } catch (_) {}
    }
    toast(LANG === "ru" ? "Отладочный скриншот сохранён" : "Debug screenshot saved");
  });
}

const btnOpenAssetsFolder = $("#btnOpenAssetsFolder");
if (btnOpenAssetsFolder) {
  btnOpenAssetsFolder.addEventListener("click", async () => {
    if (window.pywebview && pywebview.api && pywebview.api.open_assets_folder) {
      try {
        await pywebview.api.open_assets_folder();
        return;
      } catch (_) {}
    }
    toast(LANG === "ru" ? "Папка Assets открыта" : "Assets folder opened");
  });
}

const btnExportFailureReport = $("#btnExportFailureReport");
if (btnExportFailureReport) {
  btnExportFailureReport.addEventListener("click", async () => {
    if (window.pywebview && pywebview.api && pywebview.api.export_failure_report) {
      try {
        const res = await pywebview.api.export_failure_report();
        toast(res && res.ok ? (LANG === "ru" ? "Отчёт сформирован: " + res.path : "Failure report exported") : "Export failed");
        return;
      } catch (_) {}
    }
    toast(LANG === "ru" ? "Отчёт сформирован" : "Failure report exported");
  });
}

// Переключатель режима макроса (Auto / Replay)
const runModeChip = $("#runModeChip");
if (runModeChip) {
  runModeChip.addEventListener("click", async () => {
    const next = (run.mode === "replay") ? "auto" : "replay";
    run.mode = next;
    const txt = $("#runModeText");
    if (txt) txt.textContent = next === "replay" ? "Replay" : "Auto";
    if (window.pywebview && pywebview.api && pywebview.api.set_run_mode) {
      try {
        await pywebview.api.set_run_mode(next);
      } catch (_) {}
    }
    toast((LANG === "ru" ? "Режим: " : "Mode: ") + (next === "replay" ? "Replay" : "Auto"));
  });
}

/* =========================================================================
   Модуль экрана «Задачи» (Task Queue & Task Builder)
   ========================================================================= */

const TASK_DATA = {
  story: {
    label: 'Story',
    labelRu: 'Сюжет',
    maps: ['School Grounds', 'Rose Kingdom', 'Fairy King Forest', "King's Tomb", 'Flower Forest', 'East Town'],
    stages: ['1', '2', '3', '4', '5', 'Infinite', 'Mastery'],
    difficulties: ['Normal', 'Hard'],
  },
  raid: {
    label: 'Raid',
    labelRu: 'Рейд',
    maps: ['Spirit City'],
    stages: ['1', '2', '3'],
    fixedDifficulty: 'Hard',
  },
  expedition: {
    label: 'Expedition',
    labelRu: 'Экспедиция',
    maps: ['School Grounds', 'Flower Forest', 'Rose Kingdom', 'East Town'],
    difficulties: ['1', '2', '3'],
    extractAfter: ['0', '1', '2', '3', '4', '5'],
  },
  event: {
    label: 'Event',
    labelRu: 'Ивент',
    stages: ['infinite', 'portal'],
    isEvent: true,
  },
  tournament: {
    label: 'Tournament',
    labelRu: 'Турнир',
    maps: ['Solo Tournament'],
    isTournament: true,
  },
  tower: {
    label: 'Tower',
    labelRu: 'Башня',
    maps: ['Rose Kingdom'],
    stages: ['1'],
    isTower: true,
  },
  portals: {
    label: 'Portals',
    labelRu: 'Порталы',
    isPortals: true,
  },
};

let selectedTaskId = null;
let taskTemplates = [];
let taskSaveDebounce = null;
const DEFAULT_INFINITE_WAVE_LIMIT = 20;

function newTaskId() {
  return 't' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

function defaultTask() {
  return {
    id: newTaskId(),
    mode: 'story',
    map: TASK_DATA.story.maps[0],
    stage: '1',
    difficulty: 'Normal',
    infinite_wave_limit: DEFAULT_INFINITE_WAVE_LIMIT,
    extract_after: '1',
    repeat: 1,
    team: '',
    equipment: 'include',
    play_mode: 'solo',
    macro: '',
    auto_play: 'macro',
    timer_minutes: 0,
    timer_next_enabled: false,
    timer_next: '',
    stop_on_failure: false,
    on_complete_enabled: true,
    on_complete_action: 'next',
    on_complete_target: '',
    enabled: true
  };
}

function saveTasksDebounced() {
  clearTimeout(taskSaveDebounce);
  taskSaveDebounce = setTimeout(async () => {
    if (window.pywebview && pywebview.api && pywebview.api.save_tasks) {
      try {
        await pywebview.api.save_tasks(realTasksList);
      } catch (_) {}
    }
  }, 250);
}

async function loadTasksScreen() {
  if (window.pywebview && pywebview.api) {
    if (pywebview.api.list_templates) {
      try {
        taskTemplates = await pywebview.api.list_templates() || [];
      } catch (_) {}
    }
    if (pywebview.api.get_tasks) {
      try {
        const tasks = await pywebview.api.get_tasks();
        realTasksList = Array.isArray(tasks) ? tasks : [];
      } catch (_) {}
    }
    await refreshTaskPresets();
  }
  if (!selectedTaskId && realTasksList.length > 0) {
    selectedTaskId = realTasksList[0].id;
  }
  renderRealTasks(realTasksList);
  renderTaskBuilder();
}

function renderRealTasks(tasks) {
  realTasksList = Array.isArray(tasks) ? tasks : [];
  renderMiniQueue(realTasksList, lastRunStatus.current_task, lastRunStatus.current_repeat);

  const isRu = (LANG === "ru");
  const countBadge = $("#taskQueueCount");
  if (countBadge) {
    const len = realTasksList.length;
    countBadge.textContent = isRu
      ? `${len} ${len === 1 ? 'задача' : (len > 1 && len < 5 ? 'задачи' : 'задач')}`
      : `${len} ${len === 1 ? 'task' : 'tasks'}`;
  }

  const container = $("#taskQueueList");
  if (!container) return;
  container.innerHTML = "";

  if (realTasksList.length === 0) {
    container.innerHTML = `<div class="empty-task-builder" style="padding: 24px 0;"><svg class="ic"><use href="#i-queue"/></svg><span>${isRu ? "Очередь пуста. Нажмите «+ Добавить задачу», чтобы начать." : "Queue is empty. Click \"+ Add Task\" to begin."}</span></div>`;
    return;
  }

  realTasksList.forEach((task, idx) => {
    const row = document.createElement("div");
    row.className = "task-row" + (task.enabled === false ? " is-off" : "") + (task.id === selectedTaskId ? " is-selected" : "");
    row.dataset.taskId = task.id;

    const grip = document.createElement("span");
    grip.innerHTML = `<svg class="ic grip"><use href="#i-grip"/></svg>`;
    row.appendChild(grip.firstElementChild);

    const ic = document.createElement("div");
    ic.className = "task-ic";
    const iconType = task.mode === "raid" ? "#i-branch" : task.mode === "challenge" ? "#i-shield" : task.mode === "portals" ? "#i-blocks" : "#i-activity";
    ic.innerHTML = `<svg class="ic"><use href="${iconType}"/></svg>`;
    row.appendChild(ic);

    const main = document.createElement("div");
    main.className = "task-main";
    const title = task.name || task.map || task.mode || (isRu ? `Задача #${idx + 1}` : `Task #${idx + 1}`);
    const modeLabel = isRu ? (TASK_DATA[task.mode]?.labelRu || TASK_DATA[task.mode]?.label || task.mode) : (TASK_DATA[task.mode]?.label || task.mode || "Story");
    const modeBadge = `<span class="chip">${modeLabel}</span>`;
    const metaParts = [];
    if (task.map && task.name) metaParts.push(task.map);
    if (task.stage) {
      const stageStr = task.stage === "infinite"
        ? (isRu ? "Бесконечный" : "Infinite")
        : (task.stage === "portal" ? (isRu ? "Портал" : "Portal") : (isRu ? `Этап ${task.stage}` : `Stage ${task.stage}`));
      metaParts.push(stageStr);
    }
    if (task.difficulty) {
      const diffRu = { Normal: "Обычный", Hard: "Сложный", Nightmare: "Кошмар" };
      metaParts.push(isRu ? (diffRu[task.difficulty] || task.difficulty) : task.difficulty);
    }
    if (task.repeat && task.mode !== "portals") {
      metaParts.push(isRu ? `повторов <b class="mono">×${task.repeat}</b>` : `repeat <b class="mono">×${task.repeat}</b>`);
    }
    if (task.macro) {
      metaParts.push(isRu ? `сценарий <b>${task.macro}</b>` : `macro <b>${task.macro}</b>`);
    }
    if (task.timer_minutes > 0) {
      metaParts.push(isRu ? `таймер <b>${task.timer_minutes} мин</b>` : `timer <b>${task.timer_minutes}m</b>`);
    }

    main.innerHTML = `
      <div class="task-name">${title} ${modeBadge}</div>
      <div class="task-meta">${metaParts.join(" · ") || (isRu ? "Стандартное выполнение" : "Standard execution")}</div>
    `;
    row.appendChild(main);

    // Выбор задачи для редактирования в Task Builder
    row.addEventListener("click", (e) => {
      if (e.target.closest(".switch") || e.target.closest("input")) return;
      selectedTaskId = task.id;
      renderRealTasks(realTasksList);
      renderTaskBuilder();
    });

    const swLabel = document.createElement("label");
    swLabel.className = "switch";
    const swInput = document.createElement("input");
    swInput.type = "checkbox";
    swInput.checked = task.enabled !== false;
    swInput.addEventListener("change", () => {
      task.enabled = swInput.checked;
      row.classList.toggle("is-off", !swInput.checked);
      saveTasksDebounced();
    });
    swLabel.appendChild(swInput);
    swLabel.appendChild(document.createElement("i"));
    row.appendChild(swLabel);

    container.appendChild(row);
  });
}

function renderTaskBuilder() {
  const body = $("#taskBuilderBody");
  const actions = $("#taskBuilderActions");
  const sub = $("#taskBuilderSubtitle");
  if (!body) return;

  const isRu = (LANG === "ru");
  const task = realTasksList.find(t => t.id === selectedTaskId);
  if (!task) {
    if (actions) actions.style.display = "none";
    if (sub) sub.textContent = isRu ? "Выберите задачу слева для настройки" : "Select a task on the left to edit";
    body.innerHTML = `
      <div class="empty-task-builder">
        <svg class="ic"><use href="#i-queue"/></svg>
        <span>${isRu ? "Выберите задачу слева для настройки или нажмите «+ Добавить задачу» для создания новой." : "Select a task on the left to configure it, or click \"+ Add Task\" to create one."}</span>
      </div>`;
    return;
  }

  if (actions) actions.style.display = "flex";
  const idx = realTasksList.indexOf(task) + 1;
  const modeData = TASK_DATA[task.mode] || TASK_DATA.story;
  const modeLabel = isRu ? (modeData.labelRu || modeData.label || task.mode) : (modeData.label || task.mode);
  if (sub) sub.textContent = `${isRu ? "Задача #" : "Task #"}${idx} · ${modeLabel}`;

  let html = `
    <!-- Режим игры и количество повторов -->
    <div class="task-builder-row-2">
      <div class="task-builder-field">
        <label>${isRu ? "Режим игры" : "Game Mode"}</label>
        <label class="select-wrap">
          <select id="tbMode">
            ${Object.keys(TASK_DATA).map(k => `<option value="${k}" ${k === task.mode ? 'selected' : ''}>${isRu ? (TASK_DATA[k].labelRu || TASK_DATA[k].label) : TASK_DATA[k].label}</option>`).join('')}
          </select>
        </label>
      </div>
      ${task.mode !== 'portals' ? `
      <div class="task-builder-field">
        <label>${isRu ? "Количество повторов" : "Repeat Count"}</label>
        <input type="number" id="tbRepeat" min="1" max="9999" value="${task.repeat || 1}" class="tasks-preset-input" style="width: 100%;">
      </div>` : `
      <div class="task-builder-field">
        <label>${isRu ? "Поисковый запрос портала" : "Portal Query"}</label>
        <input type="text" id="tbPortalName" value="${escapeHtml(task.map || 'summer')}" placeholder="${isRu ? 'например, summer' : 'e.g. summer'}" class="tasks-preset-input" style="width: 100%;">
      </div>`}
    </div>
  `;

  // Карта и стадия
  if (task.mode === 'story' || task.mode === 'raid') {
    html += `
      <div class="task-builder-row-2">
        <div class="task-builder-field">
          <label>${isRu ? "Карта" : "Map"}</label>
          <label class="select-wrap">
            <select id="tbMap">
              ${(modeData.maps || []).map(m => `<option value="${m}" ${m === task.map ? 'selected' : ''}>${m}</option>`).join('')}
            </select>
          </label>
        </div>
        <div class="task-builder-field">
          <label>${isRu ? "Этап" : "Stage"}</label>
          <label class="select-wrap">
            <select id="tbStage">
              ${(modeData.stages || []).map(s => {
                const sLabel = /^\d+$/.test(s) ? (isRu ? 'Этап ' + s : 'Stage ' + s) : (isRu && s === 'Infinite' ? 'Бесконечный' : (isRu && s === 'Mastery' ? 'Мастерство' : s));
                return `<option value="${s}" ${s === task.stage ? 'selected' : ''}>${sLabel}</option>`;
              }).join('')}
            </select>
          </label>
        </div>
      </div>
    `;
  } else if (task.mode === 'expedition') {
    html += `
      <div class="task-builder-row-2">
        <div class="task-builder-field">
          <label>${isRu ? "Карта экспедиции" : "Expedition Map"}</label>
          <label class="select-wrap">
            <select id="tbMap">
              ${(modeData.maps || []).map(m => `<option value="${m}" ${m === task.map ? 'selected' : ''}>${m}</option>`).join('')}
            </select>
          </label>
        </div>
        <div class="task-builder-field">
          <label>${isRu ? "Эвакуация после" : "Extract After"} <span class="hint">${isRu ? "запросов" : "prompts"}</span></label>
          <input type="number" id="tbExtractAfter" min="0" max="999" value="${task.extract_after || '1'}" class="tasks-preset-input" style="width: 100%;">
        </div>
      </div>
    `;
  } else if (task.mode === 'event') {
    html += `
      <div class="task-builder-field">
        <label>${isRu ? "Тип ивента" : "Event Type"}</label>
        <label class="select-wrap">
          <select id="tbStage">
            <option value="infinite" ${task.stage === 'infinite' ? 'selected' : ''}>${isRu ? "Бесконечный режим и рыбалка" : "Infinite & Fishing"}</option>
            <option value="portal" ${task.stage === 'portal' ? 'selected' : ''}>${isRu ? "Режим портала" : "Portal Mode"}</option>
          </select>
        </label>
      </div>
    `;
  } else if (task.mode === 'tournament') {
    html += `
      <div class="task-builder-field">
        <label>${isRu ? "Тип турнира" : "Tournament Type"}</label>
        <label class="select-wrap">
          <select id="tbMap">
            ${(modeData.maps || []).map(m => `<option value="${m}" ${m === task.map ? 'selected' : ''}>${m}</option>`).join('')}
          </select>
        </label>
      </div>
    `;
  } else if (task.mode === 'tower') {
    html += `
      <div class="task-builder-field">
        <label>${isRu ? "Режим башни" : "Tower Mode"}</label>
        <label class="select-wrap">
          <select id="tbTowerMode">
            <option value="normal" ${task.tower_mode !== 'traitless' ? 'selected' : ''}>${isRu ? "Обычный" : "Normal"}</option>
            <option value="traitless" ${task.tower_mode === 'traitless' ? 'selected' : ''}>${isRu ? "Без трейтов" : "Traitless"}</option>
          </select>
        </label>
      </div>
    `;
  }

  // Сложность и лимит волн
  const isInfinite = (task.mode === 'story' && task.stage === 'Infinite') || (task.mode === 'event' && task.stage === 'infinite');
  const isSpecialStage = task.mode === 'story' && (task.stage === 'Infinite' || task.stage === 'Mastery');
  const fixedDiff = modeData.fixedDifficulty || isSpecialStage;

  html += `
    <div class="task-builder-row-2">
      <div class="task-builder-field">
        <label>${isRu ? "Сложность" : "Difficulty"}</label>
        ${fixedDiff ? `
          <div style="padding: 6px 12px; border-radius: 8px; background: var(--glass-deep); border: 1px solid var(--glass-line-2); font-size: 12px; color: var(--tx-2);">
            ${isRu ? "Сложный" : "Hard"} <span style="opacity: .6; font-size: 10.5px;">(${isRu ? "зафиксировано" : "locked"})</span>
          </div>
        ` : `
          <label class="select-wrap">
            <select id="tbDifficulty">
              ${(modeData.difficulties || ['Normal', 'Hard']).map(d => {
                const dLabel = isRu ? (d === 'Normal' ? 'Обычный' : (d === 'Hard' ? 'Сложный' : d)) : d;
                return `<option value="${d}" ${d === task.difficulty ? 'selected' : ''}>${dLabel}</option>`;
              }).join('')}
            </select>
          </label>
        `}
      </div>

      ${isInfinite ? `
      <div class="task-builder-field">
        <label>${isRu ? "Остановить после волны" : "Stop After Wave"}</label>
        <input type="number" id="tbWaveLimit" min="1" max="999" value="${task.infinite_wave_limit || DEFAULT_INFINITE_WAVE_LIMIT}" class="tasks-preset-input" style="width: 100%;">
      </div>` : `
      <div class="task-builder-field">
        <label>${isRu ? "Режим игры" : "Play Mode"}</label>
        <label class="select-wrap">
          <select id="tbPlayMode">
            <option value="solo" ${task.play_mode !== 'matchmaking' ? 'selected' : ''}>${isRu ? "В одиночку" : "Solo"}</option>
            <option value="matchmaking" ${task.play_mode === 'matchmaking' ? 'selected' : ''}>${isRu ? "Подбор игроков" : "Matchmaking"}</option>
          </select>
        </label>
      </div>`}
    </div>
  `;

  // Макросценарий и автобой
  html += `
    <div class="task-builder-row-2">
      <div class="task-builder-field">
        <label>${isRu ? "Сценарий макроса" : "Macro Operation"}</label>
        <label class="select-wrap">
          <select id="tbMacro">
            <option value="">${isRu ? "(Нет / Авто в игре)" : "(None / In-game Auto)"}</option>
            ${taskTemplates.map(tpl => `<option value="${tpl}" ${tpl === task.macro ? 'selected' : ''}>${tpl}</option>`).join('')}
          </select>
        </label>
      </div>

      <div class="task-builder-field">
        <label>${isRu ? "Управление боем" : "Combat Control"}</label>
        <label class="select-wrap">
          <select id="tbAutoPlay">
            <option value="macro" ${task.auto_play !== 'in-game' ? 'selected' : ''}>${isRu ? "Сценарий макроса" : "Scenario Macro"}</option>
            <option value="in-game" ${task.auto_play === 'in-game' ? 'selected' : ''}>${isRu ? "Авто-бой Roblox" : "Roblox Auto-play"}</option>
          </select>
        </label>
      </div>
    </div>
  `;

  // Таймер задачи
  html += `
    <div class="task-builder-row-2">
      <div class="task-builder-field">
        <label>${isRu ? "Таймер" : "Timer"} <span class="hint">${isRu ? "0 = выкл (мин)" : "0 = disabled (min)"}</span></label>
        <input type="number" id="tbTimerMinutes" min="0" max="1440" value="${task.timer_minutes || 0}" class="tasks-preset-input" style="width: 100%;">
      </div>

      <div class="task-builder-field">
        <label>${isRu ? "После таймера" : "After Timer"}</label>
        <label class="select-wrap">
          <select id="tbTimerNext" ${(task.timer_minutes || 0) <= 0 ? 'disabled' : ''}>
            <option value="">${isRu ? "Следующая в очереди" : "Next in queue"}</option>
            ${realTasksList.filter(o => o.id !== task.id).map(o => {
              const num = realTasksList.indexOf(o) + 1;
              const name = o.map || (isRu ? (TASK_DATA[o.mode]?.labelRu || TASK_DATA[o.mode]?.label) : TASK_DATA[o.mode]?.label) || (isRu ? 'задача' : 'task');
              return `<option value="${o.id}" ${task.timer_next === o.id ? 'selected' : ''}>#${num}. ${name}</option>`;
            }).join('')}
          </select>
        </label>
      </div>
    </div>
  `;

  body.innerHTML = html;

  // Слушатели изменений полей
  $("#tbMode")?.addEventListener("change", (e) => {
    task.mode = e.target.value;
    const nd = TASK_DATA[task.mode];
    if (nd.maps && nd.maps.length > 0) task.map = nd.maps[0];
    if (nd.stages && nd.stages.length > 0) task.stage = nd.stages[0];
    if (nd.difficulties && nd.difficulties.length > 0) task.difficulty = nd.difficulties[0];
    renderRealTasks(realTasksList);
    renderTaskBuilder();
    saveTasksDebounced();
  });

  $("#tbRepeat")?.addEventListener("input", (e) => {
    task.repeat = Math.max(1, parseInt(e.target.value, 10) || 1);
    renderRealTasks(realTasksList);
    saveTasksDebounced();
  });

  $("#tbPortalName")?.addEventListener("input", (e) => {
    task.map = e.target.value;
    renderRealTasks(realTasksList);
    saveTasksDebounced();
  });

  $("#tbMap")?.addEventListener("change", (e) => {
    task.map = e.target.value;
    renderRealTasks(realTasksList);
    saveTasksDebounced();
  });

  $("#tbStage")?.addEventListener("change", (e) => {
    task.stage = e.target.value;
    renderRealTasks(realTasksList);
    renderTaskBuilder();
    saveTasksDebounced();
  });

  $("#tbDifficulty")?.addEventListener("change", (e) => {
    task.difficulty = e.target.value;
    renderRealTasks(realTasksList);
    saveTasksDebounced();
  });

  $("#tbWaveLimit")?.addEventListener("input", (e) => {
    task.infinite_wave_limit = Math.max(1, parseInt(e.target.value, 10) || DEFAULT_INFINITE_WAVE_LIMIT);
    saveTasksDebounced();
  });

  $("#tbExtractAfter")?.addEventListener("input", (e) => {
    task.extract_after = String(Math.max(0, parseInt(e.target.value, 10) || 0));
    saveTasksDebounced();
  });

  $("#tbPlayMode")?.addEventListener("change", (e) => {
    task.play_mode = e.target.value;
    saveTasksDebounced();
  });

  $("#tbTowerMode")?.addEventListener("change", (e) => {
    task.tower_mode = e.target.value;
    saveTasksDebounced();
  });

  $("#tbMacro")?.addEventListener("change", (e) => {
    task.macro = e.target.value;
    renderRealTasks(realTasksList);
    saveTasksDebounced();
  });

  $("#tbAutoPlay")?.addEventListener("change", (e) => {
    task.auto_play = e.target.value;
    saveTasksDebounced();
  });

  $("#tbTimerMinutes")?.addEventListener("input", (e) => {
    const mins = Math.max(0, parseInt(e.target.value, 10) || 0);
    task.timer_minutes = mins;
    const nextSel = $("#tbTimerNext");
    if (nextSel) nextSel.disabled = mins <= 0;
    renderRealTasks(realTasksList);
    saveTasksDebounced();
  });

  $("#tbTimerNext")?.addEventListener("change", (e) => {
    task.timer_next = e.target.value;
    task.timer_next_enabled = !!e.target.value;
    saveTasksDebounced();
  });
}

function addNewTask() {
  const t = defaultTask();
  realTasksList.push(t);
  selectedTaskId = t.id;
  renderRealTasks(realTasksList);
  renderTaskBuilder();
  saveTasksDebounced();
  toast(LANG === "ru" ? "Задача добавлена в очередь" : "Task added to queue");
}

function cloneSelectedTask() {
  if (!selectedTaskId) return;
  const idx = realTasksList.findIndex(t => t.id === selectedTaskId);
  if (idx === -1) return;
  const copy = JSON.parse(JSON.stringify(realTasksList[idx]));
  copy.id = newTaskId();
  realTasksList.splice(idx + 1, 0, copy);
  selectedTaskId = copy.id;
  renderRealTasks(realTasksList);
  renderTaskBuilder();
  saveTasksDebounced();
  toast(LANG === "ru" ? "Задача скопирована" : "Task cloned");
}

function deleteSelectedTask() {
  if (!selectedTaskId) return;
  const idx = realTasksList.findIndex(t => t.id === selectedTaskId);
  if (idx === -1) return;
  realTasksList.splice(idx, 1);
  if (realTasksList.length > 0) {
    selectedTaskId = realTasksList[Math.min(idx, realTasksList.length - 1)].id;
  } else {
    selectedTaskId = null;
  }
  renderRealTasks(realTasksList);
  renderTaskBuilder();
  saveTasksDebounced();
  toast(LANG === "ru" ? "Задача удалена" : "Task deleted");
}

function clearTaskQueue() {
  if (realTasksList.length === 0) {
    toast(LANG === "ru" ? "Очередь уже пуста" : "Queue is already empty");
    return;
  }
  const btn = $("#btnClearTasks");
  if (btn && !btn.dataset.confirming) {
    btn.dataset.confirming = "1";
    const oldText = btn.innerHTML;
    btn.innerHTML = `<svg class="ic"><use href="#i-trash"/></svg><span>Sure?</span>`;
    setTimeout(() => {
      btn.dataset.confirming = "";
      btn.innerHTML = oldText;
    }, 2800);
    return;
  }
  if (btn) btn.dataset.confirming = "";
  realTasksList = [];
  selectedTaskId = null;
  renderRealTasks(realTasksList);
  renderTaskBuilder();
  saveTasksDebounced();
  toast(LANG === "ru" ? "Очередь задач очищена" : "All tasks cleared");
}

// ── Пресеты задач ──
async function refreshTaskPresets(selectName) {
  const sel = $("#selTaskPreset");
  if (!sel) return;
  if (!window.pywebview || !pywebview.api || !pywebview.api.list_task_presets) return;

  try {
    const list = await pywebview.api.list_task_presets() || [];
    sel.innerHTML = list.length === 0
      ? `<option value="">No saved presets</option>`
      : list.map(name => `<option value="${name}" ${name === selectName ? 'selected' : ''}>${name}</option>`).join('');
  } catch (_) {}
}

async function loadSelectedPreset() {
  const sel = $("#selTaskPreset");
  const name = sel ? sel.value : "";
  if (!name) {
    toast(LANG === "ru" ? "Выберите пресет для загрузки" : "Select a preset first");
    return;
  }
  if (!window.pywebview || !pywebview.api || !pywebview.api.load_task_preset) return;

  try {
    const res = await pywebview.api.load_task_preset(name);
    if (res && res.ok && Array.isArray(res.tasks)) {
      realTasksList = res.tasks;
      selectedTaskId = realTasksList.length > 0 ? realTasksList[0].id : null;
      renderRealTasks(realTasksList);
      renderTaskBuilder();
      saveTasksDebounced();
      toast((LANG === "ru" ? "Пресет загружен: " : "Preset loaded: ") + name);
      if (res.missing_macros && res.missing_macros.length > 0) {
        toast("Note: some referenced macros are missing: " + res.missing_macros.join(", "));
      }
    } else {
      toast("Failed to load preset: " + (res?.error || "unknown error"));
    }
  } catch (err) {
    toast("Error loading preset: " + err);
  }
}

async function saveCurrentPreset() {
  const inp = $("#inpTaskPresetName");
  let name = inp ? inp.value.trim() : "";
  if (!name) {
    const sel = $("#selTaskPreset");
    name = sel ? sel.value : "";
  }
  if (!name) {
    toast(LANG === "ru" ? "Введите имя пресета" : "Enter preset name");
    return;
  }
  if (realTasksList.length === 0) {
    toast(LANG === "ru" ? "Очередь пуста — нечего сохранять" : "Queue is empty");
    return;
  }
  if (!window.pywebview || !pywebview.api || !pywebview.api.save_task_preset) return;

  try {
    const res = await pywebview.api.save_task_preset(name, realTasksList);
    if (res && res.ok) {
      await refreshTaskPresets(name);
      if (inp) inp.value = "";
      toast((LANG === "ru" ? "Пресет сохранён: " : "Preset saved: ") + name);
    } else {
      toast("Failed to save preset: " + (res?.error || "unknown error"));
    }
  } catch (err) {
    toast("Error saving preset: " + err);
  }
}

async function deleteSelectedPreset() {
  const sel = $("#selTaskPreset");
  const name = sel ? sel.value : "";
  if (!name) return;
  if (!window.pywebview || !pywebview.api || !pywebview.api.delete_task_preset) return;

  try {
    const res = await pywebview.api.delete_task_preset(name);
    if (res && res.ok) {
      await refreshTaskPresets();
      toast((LANG === "ru" ? "Пресет удалён: " : "Preset deleted: ") + name);
    }
  } catch (_) {}
}

async function openTaskPresetsFolder() {
  if (window.pywebview && pywebview.api && pywebview.api.open_task_presets_folder) {
    try {
      await pywebview.api.open_task_presets_folder();
      await refreshTaskPresets();
    } catch (_) {}
  }
}

// ── Импорт и Экспорт очереди задач ──
async function exportTasksQueue() {
  if (realTasksList.length === 0) {
    toast(LANG === "ru" ? "Очередь задач пуста" : "Queue is empty");
    return;
  }
  if (!window.pywebview || !pywebview.api || !pywebview.api.export_tasks_file) return;

  try {
    const templates = {};
    if (pywebview.api.load_template) {
      for (const t of realTasksList) {
        if (t.macro && !templates[t.macro]) {
          try {
            templates[t.macro] = await pywebview.api.load_template(t.macro);
          } catch (_) {}
        }
      }
    }
    const payload = {
      kind: "anime-expeditions-tasks",
      version: 2,
      exported: new Date().toISOString(),
      tasks: realTasksList,
      templates
    };
    const res = await pywebview.api.export_tasks_file(payload);
    if (res && res.ok) {
      toast(LANG === "ru" ? "Задачи экспортированы в файл" : "Tasks exported successfully");
    } else if (res && res.reason !== "cancelled") {
      toast("Export failed: " + (res.reason || "error"));
    }
  } catch (err) {
    toast("Export error: " + err);
  }
}

async function importTasksQueue() {
  if (!window.pywebview || !pywebview.api || !pywebview.api.import_tasks_file) return;
  try {
    const res = await pywebview.api.import_tasks_file("tasks");
    if (!res || !res.ok) {
      if (res && res.reason !== "cancelled") toast("Import failed: " + (res.reason || "error"));
      return;
    }
    const data = res.data || {};
    if (Array.isArray(data.tasks)) {
      realTasksList = data.tasks;
      selectedTaskId = realTasksList.length > 0 ? realTasksList[0].id : null;
      renderRealTasks(realTasksList);
      renderTaskBuilder();
      saveTasksDebounced();
      toast(LANG === "ru" ? "Задачи успешно импортированы" : "Tasks imported successfully");
    }
  } catch (err) {
    toast("Import error: " + err);
  }
}

// Привязка кнопок тулбара Задач
$("#btnNewTask")?.addEventListener("click", addNewTask);
$("#btnCloneTask")?.addEventListener("click", cloneSelectedTask);
$("#btnDeleteTask")?.addEventListener("click", deleteSelectedTask);
$("#btnClearTasks")?.addEventListener("click", clearTaskQueue);
$("#btnLoadTaskPreset")?.addEventListener("click", loadSelectedPreset);
$("#btnSaveTaskPreset")?.addEventListener("click", saveCurrentPreset);
$("#btnDeleteTaskPreset")?.addEventListener("click", deleteSelectedPreset);
$("#btnOpenTaskPresetsFolder")?.addEventListener("click", openTaskPresetsFolder);
$("#btnExportTasks")?.addEventListener("click", exportTasksQueue);
$("#btnImportTasks")?.addEventListener("click", importTasksQueue);

/* =========================================================================
   Модуль настроек: Горячие клавиши (Hotkeys) и Сервисы
   ========================================================================= */

let listeningHotkeyAction = null;
let hotkeyKeydownHandler = null;

async function loadHotkeys() {
  if (!window.pywebview || !pywebview.api || !pywebview.api.get_hotkeys) return;
  try {
    const hotkeys = await pywebview.api.get_hotkeys();
    if (!hotkeys) return;
    $$("[data-hotkey]").forEach(btn => {
      const action = btn.dataset.hotkey;
      const val = hotkeys[action];
      btn.textContent = val ? val.toUpperCase() : "—";
    });
    const kbdRestart = $("#kbdAutoRestart");
    if (kbdRestart) kbdRestart.textContent = (hotkeys.auto_restart_loop || "Alt+F5").toUpperCase();
    const kbdVip = $("#kbdVipRejoin");
    if (kbdVip) kbdVip.textContent = (hotkeys.vip_rejoin || "Alt+F6").toUpperCase();
  } catch (_) {}
}

function initHotkeys() {
  $$("[data-hotkey]").forEach(btn => {
    btn.addEventListener("click", () => {
      const action = btn.dataset.hotkey;
      if (listeningHotkeyAction === action) {
        stopListeningHotkey();
        return;
      }
      stopListeningHotkey();

      listeningHotkeyAction = action;
      btn.textContent = LANG === "ru" ? "Нажмите комбинацию..." : "Press combination...";
      btn.classList.add("is-listening");

      hotkeyKeydownHandler = async (e) => {
        e.preventDefault();
        e.stopPropagation();

        if (e.key === "Escape") {
          stopListeningHotkey();
          await loadHotkeys();
          return;
        }

        // Если нажат только модификатор (Alt, Ctrl, Shift, Meta), ждём вторую клавишу
        const isMod = ["Control", "Alt", "Shift", "Meta"].includes(e.key);
        if (isMod) {
          const activeMods = [];
          if (e.ctrlKey || e.key === "Control") activeMods.push("Ctrl");
          if (e.altKey || e.key === "Alt") activeMods.push("Alt");
          if (e.shiftKey || e.key === "Shift") activeMods.push("Shift");
          btn.textContent = activeMods.join("+") + " + ...";
          return; // Не завершаем запись, ожидаем целевую клавишу!
        }

        let keyName = e.key;
        if (e.code && e.code.startsWith("Digit")) {
          keyName = e.code.replace("Digit", "");
        } else if (e.code && e.code.startsWith("Key")) {
          keyName = e.code.replace("Key", "");
        } else if (keyName.length === 1) {
          keyName = keyName.toUpperCase();
        } else if (keyName.startsWith("Arrow")) {
          keyName = keyName.replace("Arrow", "");
        } else if (/^f\d+$/i.test(keyName)) {
          keyName = keyName.toUpperCase();
        }

        const parts = [];
        if (e.ctrlKey) parts.push("Ctrl");
        if (e.altKey) parts.push("Alt");
        if (e.shiftKey) parts.push("Shift");
        parts.push(keyName);

        const hotkeyStr = parts.join("+");
        if (window.pywebview && pywebview.api && pywebview.api.set_hotkey) {
          try {
            await pywebview.api.set_hotkey(action, hotkeyStr);
            toast((LANG === "ru" ? "Горячая клавиша: " : "Hotkey set: ") + `${action} → ${hotkeyStr}`);
          } catch (_) {}
        }
        stopListeningHotkey();
        await loadHotkeys();
      };

      window.addEventListener("keydown", hotkeyKeydownHandler, { capture: true });
    });
  });

  // Кнопки быстрого сброса/очистки бинда (крестик ×)
  $$("[data-hotkey-clear]").forEach(clearBtn => {
    clearBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const action = clearBtn.dataset.hotkeyClear;
      if (listeningHotkeyAction === action) {
        stopListeningHotkey();
      }
      if (window.pywebview && pywebview.api && pywebview.api.set_hotkey) {
        try {
          await pywebview.api.set_hotkey(action, "");
          toast((LANG === "ru" ? "Горячая клавиша очищена: " : "Hotkey cleared: ") + action);
        } catch (_) {}
      }
      await loadHotkeys();
    });
  });

  $("#btnResetHotkeys")?.addEventListener("click", async () => {
    if (window.pywebview && pywebview.api && pywebview.api.reset_hotkeys) {
      try {
        await pywebview.api.reset_hotkeys();
        await loadHotkeys();
        toast(LANG === "ru" ? "Горячие клавиши сброшены по умолчанию" : "Hotkeys reset to defaults");
      } catch (_) {}
    }
  });
}

function stopListeningHotkey() {
  if (hotkeyKeydownHandler) {
    window.removeEventListener("keydown", hotkeyKeydownHandler, { capture: true });
    hotkeyKeydownHandler = null;
  }
  if (listeningHotkeyAction) {
    $$(`[data-hotkey="${listeningHotkeyAction}"]`).forEach(b => b.classList.remove("is-listening"));
    listeningHotkeyAction = null;
  }
}
initHotkeys();

// Привязка дополнительных опций настроек
$("#btnSendStatusNow")?.addEventListener("click", async () => {
  if (window.pywebview && pywebview.api && pywebview.api.send_status_report_now) {
    try {
      const res = await pywebview.api.send_status_report_now();
      toast(res && res.ok ? (LANG === "ru" ? "Сводка отправлена в Discord" : "Status report sent") : "Failed to send report");
    } catch (err) {
      toast("Error: " + err);
    }
  }
});

const setWebhookMention = $("#setWebhookMention");
if (setWebhookMention) {
  setWebhookMention.addEventListener("change", async () => {
    if (window.pywebview && pywebview.api && pywebview.api.set_setting) {
      try {
        await pywebview.api.set_setting("discord_webhook_mention", setWebhookMention.value.trim());
        toast(LANG === "ru" ? "Mention ID сохранён" : "Mention ID saved");
      } catch (_) {}
    }
  });
}

$("#btnHealthCheck")?.addEventListener("click", async () => {
  toast(LANG === "ru" ? "Запуск проверки системы..." : "Running diagnostics...");
  if (window.pywebview && pywebview.api && pywebview.api.run_health_check) {
    try {
      const res = await pywebview.api.run_health_check();
      if (res && res.ok) {
        toast(LANG === "ru" ? "Диагностика завершена: всё в норме" : "Diagnostics passed: all subsystems healthy");
      } else {
        toast("Diagnostics issues found: " + (res?.summary || "see logs"));
      }
    } catch (e) {
      toast("Diagnostics error: " + e);
    }
  }
});

$("#btnCheckTemplates")?.addEventListener("click", async () => {
  if (window.pywebview && pywebview.api && pywebview.api.check_templates) {
    try {
      const res = await pywebview.api.check_templates();
      if (res && res.ok) {
        toast(LANG === "ru" ? "Шаблоны проверены: ошибок нет" : "All templates verified successfully");
      } else {
        toast("Template check issues: " + (res?.error || "missing templates"));
      }
    } catch (e) {
      toast("Check error: " + e);
    }
  }
});

async function loadSettingsScreen() {
  await loadHotkeys();
  if (window.pywebview && pywebview.api) {
    try {
      if (pywebview.api.get_settings) {
        const s = await pywebview.api.get_settings();
        if (s) {
          const mentionInput = $("#setWebhookMention");
          if (mentionInput && s.discord_webhook_mention !== undefined) {
            mentionInput.value = s.discord_webhook_mention || "";
          }
          const hookInput = $("#setWebhookUrl");
          if (hookInput && s.discord_webhook_url !== undefined) {
            hookInput.value = s.discord_webhook_url || "";
          }
        }
      }
    } catch (_) {}
  }
}

/* =========================================================================
   Модуль экрана «Ресурсы» (Resources & Automations)
   ========================================================================= */

async function loadResourcesScreen() {
  if (!window.pywebview || !pywebview.api) return;

  // 1. Auto Crafting
  try {
    if (pywebview.api.get_crafting_settings) {
      const c = await pywebview.api.get_crafting_settings();
      if (c) {
        const toggle = $("#toggleCrafting");
        if (toggle) toggle.checked = !!c.enabled;
        const sel = $("#craftingEvery");
        if (sel) sel.value = `${c.every} wins`;
        const prog = $("#craftingProgress");
        if (prog) prog.textContent = `${c.current_count || 0} / ${c.every || 20}`;
      }
    }
  } catch (_) {}

  // 2. Auto Fuel
  try {
    if (pywebview.api.get_fuel_settings) {
      const f = await pywebview.api.get_fuel_settings();
      if (f) {
        const toggle = $("#toggleFuel");
        if (toggle) toggle.checked = !!f.enabled;
      }
    }
  } catch (_) {}

  // 3. Auto Shop
  try {
    if (pywebview.api.get_auto_shop_settings) {
      const s = await pywebview.api.get_auto_shop_settings();
      if (s) {
        const toggle = $("#toggleShop");
        if (toggle) toggle.checked = !!s.enabled;
      }
    }
  } catch (_) {}

  // 4. Auto Challenge
  try {
    if (pywebview.api.get_challenge_settings) {
      const ch = await pywebview.api.get_challenge_settings();
      if (ch) {
        const dToggle = $("#toggleDailyChallenge");
        if (dToggle) dToggle.checked = !!ch.daily_enabled;
        const rToggle = $("#toggleRegularChallenge");
        if (rToggle) rToggle.checked = !!ch.enabled;
        const playMode = $("#challengePlayMode");
        if (playMode) playMode.value = ch.play_mode === "matchmaking" ? "Matchmaking" : "Solo";
      }
    }
  } catch (_) {}
}

// Привязка контроллеров ресурсов
$("#toggleCrafting")?.addEventListener("change", async (e) => {
  if (window.pywebview?.api?.set_crafting_enabled) {
    try { await pywebview.api.set_crafting_enabled(e.target.checked); } catch (_) {}
  }
});

$("#craftingEvery")?.addEventListener("change", async (e) => {
  const num = parseInt(e.target.value, 10);
  if (num && window.pywebview?.api?.set_crafting_every) {
    try { await pywebview.api.set_crafting_every(num); } catch (_) {}
  }
});

$("#toggleFuel")?.addEventListener("change", async (e) => {
  if (window.pywebview?.api?.set_fuel_enabled) {
    try { await pywebview.api.set_fuel_enabled(e.target.checked); } catch (_) {}
  }
});

$("#toggleShop")?.addEventListener("change", async (e) => {
  if (window.pywebview?.api?.set_auto_shop_enabled) {
    try { await pywebview.api.set_auto_shop_enabled(e.target.checked); } catch (_) {}
  }
});

$("#toggleDailyChallenge")?.addEventListener("change", async (e) => {
  if (window.pywebview?.api?.set_daily_challenge_enabled) {
    try { await pywebview.api.set_daily_challenge_enabled(e.target.checked); } catch (_) {}
  }
});

$("#toggleRegularChallenge")?.addEventListener("change", async (e) => {
  if (window.pywebview?.api?.set_challenge_enabled) {
    try { await pywebview.api.set_challenge_enabled(e.target.checked); } catch (_) {}
  }
});

$("#challengePlayMode")?.addEventListener("change", async (e) => {
  const mode = e.target.value.toLowerCase();
  if (window.pywebview?.api?.set_challenge_play_mode) {
    try { await pywebview.api.set_challenge_play_mode(mode); } catch (_) {}
  }
});

/* =========================================================================
   Модуль экрана «Записи» (Recordings / Replay System)
   ========================================================================= */
let recordingsList = [];
let renamingRecording = null;
let recordingPollTimer = null;
let lastRecordingState = false;

async function loadRecordingsScreen() {
  await renderRecordings();
  await loadRecordingSettings();
  startRecordingsPolling();
}

function stopRecordingsPolling() {
  if (recordingPollTimer) {
    clearInterval(recordingPollTimer);
    recordingPollTimer = null;
  }
}

function startRecordingsPolling() {
  stopRecordingsPolling();
  pollRecordingStatus();
  recordingPollTimer = setInterval(pollRecordingStatus, 800);
}

async function loadRecordingSettings() {
  if (!window.pywebview || !pywebview.api || !pywebview.api.get_settings) return;
  try {
    const s = await pywebview.api.get_settings();
    if (!s) return;
    const swFocus = $("#swRecFocusOnly");
    if (swFocus && s.replay_focus_only !== undefined) {
      swFocus.checked = !!s.replay_focus_only;
    }
    const selDelay = $("#selRecStartDelay");
    if (selDelay && s.replay_start_delay_ms !== undefined) {
      selDelay.value = String(s.replay_start_delay_ms);
    }
    const inpLoops = $("#inpRecLoops");
    if (inpLoops && s.replay_loops !== undefined) {
      inpLoops.value = String(s.replay_loops);
    }
  } catch (_) {}
}

async function renderRecordings() {
  const el = $("#recList");
  if (!el) return;
  if (!window.pywebview || !pywebview.api || !pywebview.api.replay_list) {
    return;
  }
  try {
    recordingsList = (await pywebview.api.replay_list()) || [];
  } catch (_) {
    recordingsList = [];
  }

  if (recordingsList.length === 0) {
    el.innerHTML = `
      <div style="padding: 24px 16px; text-align: center; color: var(--tx-3); font-size: 13px;">
        <div>${LANG === "ru" ? "Записей пока нет" : "No recordings found"}</div>
        <div style="margin-top: 6px; font-size: 11.5px; opacity: 0.8;">
          ${LANG === "ru" ? "Нажмите <kbd style=\"padding: 2px 5px; border-radius: 4px; background: rgba(255,255,255,0.08);\">F8</kbd> в игре для старта/остановки записи" : "Press <kbd style=\"padding: 2px 5px; border-radius: 4px; background: rgba(255,255,255,0.08);\">F8</kbd> in-game to start or stop recording"}
        </div>
      </div>`;
    return;
  }

  el.innerHTML = recordingsList.map((r) => {
    const isRenaming = r.name === renamingRecording;
    const duration = formatReplayDuration(r.seconds || 0);
    const actions = r.actions || 0;
    const dateStr = r.created ? r.created.slice(0, 10) : "";

    if (isRenaming) {
      return `
        <div class="rec-row is-renaming" style="padding: 6px 8px; gap: 8px; align-items: center;">
          <input type="text" id="inpRenameRec" class="block-input" value="${escapeHtml(r.name)}"
                 style="flex: 1; padding: 4px 8px; font-size: 13px; border-radius: var(--r-sm, 6px); background: rgba(255,255,255,0.08); border: 1px solid var(--accent); color: var(--tx);"
                 onkeydown="if(event.key==='Enter') commitRenameRecording('${escapeHtml(r.name)}', this.value); else if(event.key==='Escape') cancelRenameRecording();">
          <button class="icon-btn" onclick="commitRenameRecording('${escapeHtml(r.name)}', document.getElementById('inpRenameRec').value)" title="Save"><svg class="ic"><use href="#i-save"/></svg></button>
          <button class="icon-btn" onclick="cancelRenameRecording()" title="Cancel">&times;</button>
        </div>`;
    }

    return `
      <div class="rec-row" data-name="${escapeHtml(r.name)}">
        <svg class="ic rec-ic"><use href="#i-rec"/></svg>
        <div class="rec-main">
          <strong>${escapeHtml(r.name)}</strong>
          <span class="mono">${duration} · ${actions} ${LANG === "ru" ? "действий" : "acts"}${dateStr ? ` · ${dateStr}` : ""}</span>
        </div>
        <div class="rec-acts">
          <button class="icon-btn" onclick="playSelectedRecording('${escapeHtml(r.name)}')" title="Play"><svg class="ic"><use href="#i-play"/></svg></button>
          <button class="icon-btn" onclick="startRenameRecording('${escapeHtml(r.name)}')" title="Rename"><svg class="ic"><use href="#i-pencil"/></svg></button>
          <button class="icon-btn rec-btn-del" onclick="deleteSelectedRecording('${escapeHtml(r.name)}', this)" title="Delete"><svg class="ic"><use href="#i-trash"/></svg></button>
        </div>
      </div>`;
  }).join("");

  const renameInp = $("#inpRenameRec");
  if (renameInp) {
    renameInp.focus();
    renameInp.select();
  }
}

function formatReplayDuration(totalSec) {
  const m = Math.floor(totalSec / 60);
  const s = Math.floor(totalSec % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

async function playSelectedRecording(name) {
  if (!window.pywebview || !pywebview.api) return;
  try {
    await pywebview.api.set_setting("run_mode", "replay");
    await pywebview.api.set_setting("replay_file", name);
    if (typeof applyRunMode === "function") applyRunMode("replay");
    await pywebview.api.start_macro();
    toast((LANG === "ru" ? "Запущен повтор: " : "Started replay: ") + name);
    setScreen("home");
  } catch (err) {
    toast("Error: " + err);
  }
}

function startRenameRecording(name) {
  renamingRecording = name;
  renderRecordings();
}

function cancelRenameRecording() {
  renamingRecording = null;
  renderRecordings();
}

async function commitRenameRecording(oldName, newName) {
  if (!window.pywebview || !pywebview.api || !pywebview.api.replay_rename) return;
  const cleanNew = (newName || "").trim();
  if (!cleanNew || cleanNew === oldName) {
    cancelRenameRecording();
    return;
  }
  try {
    const res = await pywebview.api.replay_rename(oldName, cleanNew);
    if (res && res.ok) {
      toast((LANG === "ru" ? "Переименовано в: " : "Renamed to: ") + res.name);
    } else {
      toast((LANG === "ru" ? "Ошибка переименования: " : "Rename failed: ") + (res?.reason || "error"));
    }
  } catch (err) {
    toast("Error: " + err);
  }
  renamingRecording = null;
  renderRecordings();
}

async function deleteSelectedRecording(name, btn) {
  if (!window.pywebview || !pywebview.api || !pywebview.api.replay_delete) return;
  if (!btn.dataset.confirming) {
    btn.dataset.confirming = "1";
    btn.style.color = "#ef4444";
    btn.title = LANG === "ru" ? "Нажмите ещё раз для удаления" : "Click again to confirm deletion";
    setTimeout(() => {
      delete btn.dataset.confirming;
      btn.style.color = "";
      btn.title = "Delete";
    }, 3000);
    return;
  }
  delete btn.dataset.confirming;
  try {
    await pywebview.api.replay_delete(name);
    toast((LANG === "ru" ? "Запись удалена: " : "Deleted recording: ") + name);
    renderRecordings();
  } catch (err) {
    toast("Failed: " + err);
  }
}

async function pollRecordingStatus() {
  if (!window.pywebview || !pywebview.api || !pywebview.api.replay_recording_status) return;
  try {
    const st = await pywebview.api.replay_recording_status();
    if (!st) return;

    if (lastRecordingState && !st.recording) {
      renderRecordings();
    }
    lastRecordingState = !!st.recording;

    const elStatus = $("#recStatus");
    const elTitle = $("#recTitle");
    const elHint = $("#recHint");
    const elTimer = $("#recTimer");

    if (st.recording) {
      if (elStatus) elStatus.classList.add("is-on");
      if (elTitle) elTitle.textContent = LANG === "ru" ? "Идёт запись..." : "Recording in progress...";
      if (elHint) elHint.textContent = LANG === "ru" ? `Записано ${st.recorded || 0} событий. Нажмите F8 для сохранения.` : `Captured ${st.recorded || 0} events. Press F8 to save.`;
      if (elTimer) elTimer.textContent = formatReplayDuration(st.seconds || 0);
    } else if (st.state === "running") {
      if (elStatus) elStatus.classList.add("is-on");
      if (elTitle) elTitle.textContent = (LANG === "ru" ? "Воспроизведение: " : "Replaying: ") + (st.name || "");
      if (elHint) elHint.textContent = (LANG === "ru" ? `Круг ${st.loop || 1} · Действие ${st.index || 0}/${st.total || 0}` : `Loop ${st.loop || 1} · Action ${st.index || 0}/${st.total || 0}`) + (st.matches ? ` · Matches: ${st.matches}` : "");
      if (elTimer) elTimer.textContent = formatReplayDuration(st.seconds || 0);
    } else if (st.countdown > 0) {
      if (elStatus) elStatus.classList.add("is-on");
      if (elTitle) elTitle.textContent = (LANG === "ru" ? "Старт через " : "Starting in ") + `${st.countdown.toFixed(1)}s...`;
      if (elHint) elHint.textContent = LANG === "ru" ? "Ожидание фокуса окна Roblox" : "Waiting for Roblox window focus";
      if (elTimer) elTimer.textContent = `00:0${Math.ceil(st.countdown)}`;
    } else {
      if (elStatus) elStatus.classList.remove("is-on");
      if (elTitle) elTitle.textContent = LANG === "ru" ? "Запись не ведётся" : "Not recording";
      if (elHint) elHint.textContent = LANG === "ru" ? "Запись управляется клавишей F8. Пройдите один матч вручную." : "Recording runs entirely from the hotkey. Play one match by hand.";
      if (elTimer) elTimer.textContent = "00:00";
    }
  } catch (_) {}
}

function initRecordingsEvents() {
  $("#btnOpenRecordingsFolder")?.addEventListener("click", async () => {
    if (window.pywebview && pywebview.api && pywebview.api.open_recordings_folder) {
      try { await pywebview.api.open_recordings_folder(); } catch (_) {}
    }
  });

  $("#btnExportRecordings")?.addEventListener("click", async () => {
    if (!window.pywebview || !pywebview.api || !pywebview.api.export_recordings_bundle) return;
    try {
      const names = recordingsList.map(r => r.name);
      if (names.length === 0) {
        toast(LANG === "ru" ? "Нет записей для экспорта" : "No recordings to export");
        return;
      }
      const bundle = await pywebview.api.export_recordings_bundle(names);
      if (bundle) {
        const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `ae_recordings_bundle_${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
        toast(LANG === "ru" ? "Бандл записей экспортирован" : "Recordings bundle exported");
      }
    } catch (e) {
      toast("Export error: " + e);
    }
  });

  $("#btnImportRecordings")?.addEventListener("click", () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json";
    input.onchange = async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      try {
        const text = await file.text();
        const data = JSON.parse(text);
        if (window.pywebview && pywebview.api && pywebview.api.import_recordings_bundle) {
          const res = await pywebview.api.import_recordings_bundle(data);
          if (res && res.ok) {
            toast((LANG === "ru" ? "Импортировано записей: " : "Imported recordings: ") + (res.added || 0));
            renderRecordings();
          } else {
            toast(LANG === "ru" ? "Ошибка формата бандла" : "Invalid bundle format");
          }
        }
      } catch (err) {
        toast("Import error: " + err);
      }
    };
    input.click();
  });

  $("#swRecFocusOnly")?.addEventListener("change", async (e) => {
    if (window.pywebview && pywebview.api && pywebview.api.set_setting) {
      try { await pywebview.api.set_setting("replay_focus_only", e.target.checked); } catch (_) {}
    }
  });

  $("#selRecStartDelay")?.addEventListener("change", async (e) => {
    if (window.pywebview && pywebview.api && pywebview.api.set_setting) {
      try { await pywebview.api.set_setting("replay_start_delay_ms", parseInt(e.target.value, 10)); } catch (_) {}
    }
  });

  $("#inpRecLoops")?.addEventListener("change", async (e) => {
    if (window.pywebview && pywebview.api && pywebview.api.set_setting) {
      try { await pywebview.api.set_setting("replay_loops", Math.max(0, parseInt(e.target.value, 10) || 0)); } catch (_) {}
    }
  });
}

initRecordingsEvents();

/* =========================================================================
   Интеграционный мост с Python (main.py / pywebview)
   Эти функции вызываются бэкендом через evaluate_js / push_ui.
   ========================================================================= */

// Логи: бэкенд шлёт пачками через appendLogBatch или по одной строке через addLog
window.addLog = function(line) {
  addLogLine(line);
};

window.appendLogBatch = function(batch) {
  if (Array.isArray(batch)) {
    batch.forEach(line => addLogLine(line));
  }
};

// Событие: окно Roblox успешно найдено и встроено в макрос
window.showDocked = function() {
  const empty = $("#gameFrame .game-empty");
  if (empty) empty.style.display = "none";
  const foot = $("#footState");
  if (foot) {
    foot.textContent = LANG === "ru" ? "Roblox подключен" : "Roblox docked";
    foot.style.color = "var(--good)";
  }
  if (document.body.dataset.screen === "home") {
    try {
      if (window.pywebview && pywebview.api && pywebview.api.show_game) {
        pywebview.api.show_game();
      }
    } catch (_) {}
  }
};

// Событие: ожидание запуска/встраивания Roblox
window.showWaiting = function() {
  const empty = $("#gameFrame .game-empty");
  if (empty) empty.style.display = "";
  const foot = $("#footState");
  if (foot) {
    foot.textContent = LANG === "ru" ? "Ожидание Roblox..." : "Waiting for Roblox...";
    foot.style.color = "";
  }
};

// Горячие клавиши и триггеры от main.py
window.startMacro = function() {
  const b = $("#btnStart");
  if (b && !b.disabled) b.click();
};

window.stopMacro = function() {
  const b = $("#btnStop");
  if (b && !b.disabled) b.click();
};

window.togglePauseMacro = function() {
  const b = $("#btnPause");
  if (b && !b.disabled) b.click();
};

window.toggleGameScreenHotkey = function() {
  const cur = document.body.dataset.screen || "home";
  setScreen(cur === "home" ? lastNonHomeScreen : "home");
};

/* =========================================================================
   Шторка записей по F10 (Recordings Drawer от правой стенки)
   ========================================================================= */

let isRecDrawerOpen = false;
let recDrawerSearchTerm = "";
let recDrawerSelectedName = "";

async function openRecordingsDrawer() {
  if (isRecDrawerOpen) return;
  const drawer = $("#recDrawer");
  const backdrop = $("#recDrawerBackdrop");
  if (!drawer || !backdrop) return;

  isRecDrawerOpen = true;
  drawer.hidden = false;
  backdrop.hidden = false;

  // Прячем нативное окно Roblox, чтобы оно не перекрывало шторку
  try {
    if (window.pywebview && pywebview.api && pywebview.api.hide_game) {
      await pywebview.api.hide_game();
    }
  } catch (_) {}

  // Плавный выезд шторки от правой стенки
  requestAnimationFrame(() => {
    drawer.classList.add("is-open");
    backdrop.classList.add("is-open");
  });

  await updateDrawerModeDisplay();
  await renderRecordingsDrawer();

  const searchInp = $("#recDrawerSearch");
  if (searchInp) {
    searchInp.value = "";
    recDrawerSearchTerm = "";
  }
}

async function closeRecordingsDrawer(restoreGame = true) {
  if (!isRecDrawerOpen) return;
  const drawer = $("#recDrawer");
  const backdrop = $("#recDrawerBackdrop");
  if (!drawer || !backdrop) return;

  drawer.classList.remove("is-open");
  backdrop.classList.remove("is-open");
  isRecDrawerOpen = false;

  setTimeout(() => {
    if (!isRecDrawerOpen) {
      drawer.hidden = true;
      backdrop.hidden = true;
    }
  }, 280);

  // Возвращаем Roblox только если мы на Панели (home)
  if (restoreGame && document.body.dataset.screen === "home") {
    try {
      if (window.pywebview && pywebview.api && pywebview.api.show_game) {
        await pywebview.api.show_game();
      }
    } catch (_) {}
  }
}

function toggleRecordingsDrawer() {
  if (isRecDrawerOpen) {
    closeRecordingsDrawer();
  } else {
    openRecordingsDrawer();
  }
}

async function updateDrawerModeDisplay() {
  if (!window.pywebview || !pywebview.api || !pywebview.api.get_run_mode) return;
  try {
    const m = await pywebview.api.get_run_mode();
    const mode = m.mode === "replay" ? "replay" : "auto";
    recDrawerSelectedName = m.recording || "";
    const modeBtn = $("#btnDrawerToggleMode");
    const modeText = $("#recDrawerModeText");
    const modeDesc = $("#recDrawerModeDesc");
    const isReplay = mode === "replay";
    if (modeText) modeText.textContent = isReplay ? (LANG === "ru" ? "Повтор" : "Replay") : (LANG === "ru" ? "Автомат" : "Auto");
    if (modeBtn) modeBtn.classList.toggle("is-on", isReplay);
    if (modeDesc) modeDesc.textContent = isReplay ? t("desc_start_mode_replay") : t("desc_start_mode_auto");
  } catch (_) {}
}

async function renderRecordingsDrawer(filter = "") {
  const listEl = $("#recDrawerList");
  const countEl = $("#recDrawerCount");
  if (!listEl) return;

  let recs = [];
  if (window.pywebview && pywebview.api && pywebview.api.replay_list) {
    try { recs = (await pywebview.api.replay_list()) || []; } catch (_) { recs = []; }
  }
  if (countEl) countEl.textContent = String(recs.length);

  const term = (filter || "").trim().toLowerCase();
  const filtered = term ? recs.filter(r => (r.name || "").toLowerCase().includes(term)) : recs;

  if (filtered.length === 0) {
    listEl.innerHTML = `
      <div style="padding: 32px 16px; text-align: center; color: var(--tx-3); font-size: 12.5px;">
        <svg class="ic" style="width: 28px; height: 28px; margin: 0 auto 8px; opacity: 0.4;"><use href="#i-rec"/></svg>
        <div>${LANG === "ru" ? "Записи не найдены" : "No recordings found"}</div>
      </div>`;
    return;
  }

  listEl.innerHTML = filtered.map(r => {
    const isSelected = r.name === recDrawerSelectedName;
    const duration = formatReplayDuration(r.seconds || 0);
    const actions = r.actions || 0;
    const dateStr = r.created ? r.created.slice(0, 10) : "";

    return `
      <div class="rec-drawer-item${isSelected ? " is-selected" : ""}" data-rec-name="${escapeHtml(r.name)}">
        <div class="rec-drawer-item-left" onclick="selectDrawerRecording('${escapeHtml(r.name)}')">
          <svg class="ic" style="width: 18px; height: 18px; color: ${isSelected ? "var(--primary-bg, #38bdf8)" : "var(--tx-3)"};"><use href="#i-rec"/></svg>
          <div class="rec-drawer-item-info">
            <strong class="rec-drawer-item-name">${escapeHtml(r.name)}</strong>
            <span class="rec-drawer-item-meta mono">${duration} · ${actions} ${LANG === "ru" ? "действ." : "acts"}${dateStr ? ` · ${dateStr}` : ""}${isSelected ? (LANG === "ru" ? " · ✓ Выбрано" : " · ✓ Active") : ""}</span>
          </div>
        </div>
        <div class="rec-drawer-item-acts">
          <button type="button" class="btn btn-ghost btn-xxs" onclick="selectDrawerRecording('${escapeHtml(r.name)}')" title="${LANG === "ru" ? "Выбрать для запуска" : "Select for replay"}">
            <svg class="ic" style="width: 11px; height: 11px;"><use href="#i-check"/></svg>
            <span>${isSelected ? t("btn_selected") : t("btn_select")}</span>
          </button>
          <button type="button" class="btn btn-primary btn-xxs" onclick="playDrawerRecording('${escapeHtml(r.name)}')" title="${LANG === "ru" ? "Запустить сейчас" : "Play now"}">
            <svg class="ic" style="width: 11px; height: 11px;"><use href="#i-play"/></svg>
            <span>${LANG === "ru" ? "Старт" : "Play"}</span>
          </button>
        </div>
      </div>`;
  }).join("");
}

async function selectDrawerRecording(name) {
  if (!window.pywebview || !pywebview.api) return;
  try {
    await pywebview.api.set_setting("run_mode", "replay");
    await pywebview.api.set_setting("replay_file", name);
    recDrawerSelectedName = name;
    if (typeof applyRunMode === "function") applyRunMode("replay");
    await updateDrawerModeDisplay();
    await renderRecordingsDrawer(recDrawerSearchTerm);
    toast((LANG === "ru" ? "Выбрана запись: " : "Selected recording: ") + name);
  } catch (err) {
    toast("Error: " + err);
  }
}

async function playDrawerRecording(name) {
  await closeRecordingsDrawer(false);
  await playSelectedRecording(name);
}

function initRecordingsDrawer() {
  $("#recDrawerClose")?.addEventListener("click", () => closeRecordingsDrawer());
  $("#btnDrawerDone")?.addEventListener("click", () => closeRecordingsDrawer());
  $("#recDrawerBackdrop")?.addEventListener("click", () => closeRecordingsDrawer());

  $("#btnDrawerNewRec")?.addEventListener("click", () => {
    closeRecordingsDrawer(false);
    setScreen("recordings");
  });

  $("#recDrawerSearch")?.addEventListener("input", (e) => {
    recDrawerSearchTerm = e.target.value;
    renderRecordingsDrawer(recDrawerSearchTerm);
  });

  $("#btnDrawerToggleMode")?.addEventListener("click", async () => {
    if (!window.pywebview || !pywebview.api) return;
    try {
      const m = await pywebview.api.get_run_mode();
      const nextMode = m.mode === "replay" ? "auto" : "replay";
      await pywebview.api.set_run_mode(nextMode);
      if (typeof applyRunMode === "function") applyRunMode(nextMode);
      await updateDrawerModeDisplay();
    } catch (_) {}
  });
}
initRecordingsDrawer();

window.toggleRecordingsOverlay = function() {
  toggleRecordingsDrawer();
};

window.toggleAutoRestartLoop = async function() {
  const b = $("#btnAutoRestartLoop");
  if (b) b.click();
};

window.triggerVipRejoin = async function() {
  const b = $("#btnVipRejoin");
  if (b) b.click();
};

window.startWalkRecordHotkey = function() {
  if (typeof startPathRecordingFlow === "function") {
    startPathRecordingFlow();
  }
};

window.stopWalkRecordHotkey = function() {
  if (typeof stopPathRecordingFlow === "function") {
    stopPathRecordingFlow();
  }
};

// Перехват хоткеев в активном окне (F10 для шторки записей, Alt+9 / Ctrl+9 для WASD)
window.addEventListener("keydown", (e) => {
  if (e.key === "F10") {
    if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")) return;
    e.preventDefault();
    toggleRecordingsDrawer();
    return;
  }
  if (e.key === "Escape" && isRecDrawerOpen) {
    e.preventDefault();
    closeRecordingsDrawer();
    return;
  }

  const isAlt9 = (e.altKey && !e.ctrlKey && !e.shiftKey && (e.code === "Digit9" || e.key === "9"));
  const isCtrl9 = (e.ctrlKey && !e.altKey && !e.shiftKey && (e.code === "Digit9" || e.key === "9"));
  if (isAlt9 || isCtrl9) {
    if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")) return;
    e.preventDefault();
    const isRecActive = !!(pendingPathRecordContext || ($("#recPopout") && !$("#recPopout").hidden));
    if (isRecActive) {
      stopPathRecordingFlow();
    } else {
      startPathRecordingFlow();
    }
  }
});


window.loadResolutionUI = async function() {
  if (window.pywebview && pywebview.api && pywebview.api.get_game_resolution) {
    try {
      const res = await pywebview.api.get_game_resolution();
      if (res && res.width && res.height) {
        const w = parseInt(res.width, 10);
        const h = parseInt(res.height, 10);
        if (typeof window.applyGameResolution === "function") {
          window.applyGameResolution(w, h, true, true);
        } else {
          document.documentElement.style.setProperty("--game-w", `${w}px`);
          document.documentElement.style.setProperty("--game-h", `${h}px`);
          document.documentElement.style.setProperty("--game-aspect", `${w} / ${h}`);
          const home = $("#screen-home");
          if (home) {
            home.style.setProperty("--game-w", `${w}px`);
            home.style.setProperty("--game-h", `${h}px`);
            home.style.setProperty("--game-aspect", `${w} / ${h}`);
          }
          const homePills = $$("#gameResPills .res-pill");
          homePills.forEach(p => {
            const pw = parseInt(p.dataset.w, 10);
            const ph = parseInt(p.dataset.h, 10);
            p.classList.toggle("is-on", pw === w && ph === h);
          });
          const emptySub = $("#gameEmptySub");
          if (emptySub) emptySub.textContent = `Embedded game window · ${w} × ${h}`;
        }
      }
    } catch (_) {}
  }
};

window.showScaleWarning = function() {
  toast(LANG === "ru" ? "Предупреждение: Масштаб экрана Windows не 100%" : "Warning: Display scale is not 100%");
};

window.showUpdateAvailable = function() {
  const anchor = $("#updAnchor");
  if (anchor) anchor.classList.add("has-update");
  toast(LANG === "ru" ? "Доступно обновление!" : "Update available!");
};

window.skipWaiting = function() {
  const btn = $("#btnAttach");
  if (btn) btn.click();
};

window.saveDebugScreenshot = function() {
  toast(LANG === "ru" ? "Отладочный скриншот сохранен" : "Debug screenshot saved");
};

// Первичная инициализация данных из Python
async function initPywebviewBridge() {
  if (!window.pywebview || !pywebview.api) return;

  // 1. Версия
  try {
    if (pywebview.api.get_version) {
      const ver = await pywebview.api.get_version();
      if (ver) {
        const vStr = typeof ver === "string" ? ver : (ver.version || "2.0.0");
        const bVer = $("#appVer");
        const sVer = $("#setVer");
        if (bVer) bVer.textContent = "v" + vStr.replace(/^v/, "");
        if (sVer) sVer.textContent = vStr.replace(/^v/, "");
      }
    }
  } catch (_) {}

  // 2. Режим макроса (Auto / Replay)
  try {
    if (pywebview.api.get_run_mode) {
      const rm = await pywebview.api.get_run_mode();
      if (rm) {
        run.mode = rm;
        const txt = $("#runModeText");
        if (txt) txt.textContent = rm === "replay" ? "Replay" : "Auto";
      }
    }
  } catch (_) {}

  // 3. Загрузка настроек (Webhook, hotkeys, etc.)
  try {
    if (pywebview.api.get_settings) {
      const s = await pywebview.api.get_settings();
      if (s) {
        if (s.lang && (s.lang === "ru" || s.lang === "en")) {
          if (s.lang !== LANG) {
            LANG = s.lang;
            try {
              localStorage.setItem("ui_lang", LANG);
              localStorage.setItem("ae_lang", LANG);
            } catch (_) {}
            applyLang();
          }
        } else if (window.pywebview?.api?.set_setting) {
          try { window.pywebview.api.set_setting("lang", LANG); } catch (_) {}
        }

        const urlInp = $("#setWebhookUrl");
        if (urlInp && s.discord_webhook_url) urlInp.value = s.discord_webhook_url;
        const swRes = $("#swWebhookResults");
        if (swRes && s.discord_alerts_enabled !== undefined) swRes.checked = !!s.discord_alerts_enabled;
        const swPing = $("#swWebhookPings");
        if (swPing && s.discord_pings_enabled !== undefined) swPing.checked = !!s.discord_pings_enabled;
        const selInt = $("#selWebhookInterval");
        if (selInt && s.discord_status_interval) selInt.value = String(s.discord_status_interval);

        // Настройки автоматизации
        const selLoss = $("#selLossStreakStop");
        const lossVal = s.replay_loss_streak_stop !== undefined ? s.replay_loss_streak_stop : localStorage.getItem("ae_loss_streak_stop");
        if (selLoss && lossVal !== null && lossVal !== undefined) selLoss.value = String(lossVal);

        const swFocus = $("#swFocusGuard");
        const focusVal = s.replay_require_focus !== undefined ? s.replay_require_focus : (localStorage.getItem("ae_require_focus") !== "false");
        if (swFocus && focusVal !== null) swFocus.checked = !!focusVal;

        const vipInp = $("#setVipLink");
        const vipVal = s.private_server_link || localStorage.getItem("ae_vip_link");
        if (vipInp && vipVal) vipInp.value = vipVal;

        const swSound = $("#swSoundAlerts");
        const soundVal = localStorage.getItem("ae_sound_alerts");
        if (swSound && soundVal !== null) swSound.checked = soundVal !== "false";

        const swShot = $("#swAutoScreenshot");
        const shotVal = localStorage.getItem("ae_auto_screenshot");
        if (swShot && shotVal !== null) swShot.checked = shotVal !== "false";

        const swHum = $("#swClickHumanizer");
        const humVal = localStorage.getItem("ae_click_humanizer");
        if (swHum && humVal !== null) swHum.checked = humVal !== "false";

        // Настройки захвата и окна игры
        if (swFlickerFree && s.flicker_free_capture !== undefined) {
          swFlickerFree.checked = !!s.flicker_free_capture;
        }
        if (swWgcCapture && s.use_wgc_capture !== undefined) {
          swWgcCapture.checked = !!s.use_wgc_capture;
        }
        refreshRobloxWindowsList();
      }
    }
  } catch (_) {}

  // 4. Очередь задач
  try {
    if (pywebview.api.get_tasks) {
      const tasks = await pywebview.api.get_tasks();
      renderRealTasks(tasks || []);
    } else {
      renderRealTasks(realTasksList);
    }
  } catch (_) {
    renderRealTasks(realTasksList);
  }

  // 5. Разрешение игры
  try {
    if (window.loadResolutionUI) await window.loadResolutionUI();
  } catch (_) {}

  // 6. Немедленная синхронизация телеметрии и статистики без ожидания интервала
  try {
    if (pywebview.api.get_status) {
      const st = await pywebview.api.get_status();
      if (st) {
        updateSessionStats(st);
        if (st.run_history) {
          renderRunHistory(st.run_history);
        }
      }
    }
    if (pywebview.api.is_macro_running) {
      const macro = await pywebview.api.is_macro_running();
      if (macro) {
        run.state = macro.running ? (macro.paused ? "paused" : "running") : "idle";
        renderRun();
      }
    }
  } catch (_) {}
}

if (window.pywebview && pywebview.api) {
  initPywebviewBridge();
} else {
  window.addEventListener("pywebviewready", initPywebviewBridge);
}

applyHash();
applyLang();
renderRealTasks(realTasksList);

// Гарантируем, что плавающий HUD записи движения строго скрыт при запуске приложения
const initRecPopout = $("#recPopout");
if (initRecPopout) {
  initRecPopout.hidden = true;
  initRecPopout.style.display = "none";
}
