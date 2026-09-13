# Changelog

All notable changes to Anime Expeditions (Cream's Macro) are documented here.

## [1.1.9] - 2026-09-13

### New
- **Copy Logs Button**: Added a dedicated "Copy Logs" button to the Dashboard log viewer with visual confirmation.

### Fixed
- **Bottom Panel / Hotbar Safety**: Removed automatic bottom hotbar clicks and slot key cycling (1–6) during matches. This prevents targeting/placement mode lockups caused by placeable buff fish items requiring unit placement.
- **Task Auto-Transition Logic**: Fixed an issue where the runner could advance to the next task even when "Auto Transition" was disabled. Toggling Auto Transition to Off now strictly repeats the current task or stops as selected. Also handles mid-task glitches and recovery safely without skipping tasks.
- **Resolution Scaling & Event Navigation**:
  - Event mode navigation (`core/runner_event.py`) now dynamically handles pre-selected tabs and screens, eliminated accidental toggling/closing of the Event modal, and uses resolution-tolerant matching thresholds (`0.78`).
  - Stage confirmation checks whether `nav_start` is already visible before attempting to find and click `nav_select_stage`.
  - Aspect ratio distortion correction is now refreshed across all capture paths (`_capture_window_gray`, `_capture_window_bgr`), ensuring pixel-perfect clicks on non-standard resolutions (such as 1024x768).

### Improved
- **Newcomer .exe Experience & Import/Export**:
  - Standard user folders (`Templates/`, `Templates/Tasks/`, `Recordings/`, `Paths/`, `debug/`) are automatically created on startup for fresh .exe installs, eliminating missing directory errors.
  - Template and task import now accepts raw arrays, direct phase dictionaries (`{ pre_start, battle, loop }`), single-template JSONs, and CREAM share codes.

## [1.1.8] - 2026-09-09

### New
- **Summer Event (Tidal Siege)**: Replaced retired Villain Invasion mode.
  - **Infinite & Fishing**: Endless wave farming with lake fishing under Autoplay defense and a configurable `Stop After Wave` exit limit.
  - **Portal Mode**: Automated Summer portal entry, activation, and post-victory re-selection.
- **Portals Inventory Mode**: Automated inventory-based portal runner via `nav_inv` -> `normal_portals_nav` -> query search -> tier selection -> post-win `select_new_portal`.
- **Drag Block**: Added interactive swipe/drag mouse action in the Setup group with configurable `(x1, y1)` and `(x2, y2)` coordinates, steps, and duration.
- **East Town Map**: Added to Challenge and Bounty map lists with OCR aliases and stopwords.
- **Summer Fishing Automation**: Added default `Summer` walk path to the lake and ready-to-run `Inf Summer` scenario featuring rod casting, `Fishing rank` detection, and reel mini-game clicking.

### Improved
- **English Log Normalization**: Unified all internal macro runner, replay system, and status card logs in standard English for seamless international audience compatibility.
- **Russian UI Localization**: Comprehensive translation of all new UI labels, tooltips, and presets in `ui/i18n.js`.
- **Cleaned Retired Assets**: Deprecated Villain Invasion / Act 4 divert code and coordinates cleanly migrated to the modern Summer Event pipeline.

## [0.19.0] - 2026-08-11

### New
- **East Town map**: added to the expedition and story map lists.
- **Tower game mode**: Play -> Tower -> Select Stage -> Start (solo). Wins advance floors with `Next_Floor`; defeats retry with `Repeat_Floor`. Supports Normal and Traitless Tower. No map dropdown in the builder; Rose Kingdom is the internal default.
- **Auto Fuel custom interval**: set any refill interval in minutes or hours (e.g. 30 minutes, 1 hour), or leave it on Auto to keep the per-amount default behavior.

### Improved
- **Event mode**: waits for the Event gamemode screen, clicks a user-configurable card coordinate, then image-clicks the Event Gamemode button.
- **Disconnect recovery**: kills a stuck Roblox client before deep-link relaunch, still respecting the multi-window guard.
- **File dialogs**: cancelled or failed native file dialogs now return clean results instead of rejected JS promises.
- **Auto Upgrade Unit**: bounded wait for the unit info panel before searching `priority_upgrade`, so slow-rendering panels are no longer skipped. New `quote_on` / `quote_off` reference images for user-built Detect conditions.
- **OCR overhaul**:
  - Auto Bounty wave OCR: wave-anchored parsing with card-local crops and contrast voting. Clipped wave numbers (`6`, `6C`) now resolve to `60` instead of ending the run at wave 6.
  - Optional RapidOCR engine layer (separate `requirements-rapidocr.txt`, Python 3.13-safe) with a RapidOCR -> Windows OCR -> Tesseract fallback chain.
  - Windows OCR output is always filtered by the config whitelist, preserving stats/wave/shop reads.
  - Daily Challenge map OCR keeps the HUD-anchored crop primary and adds a fixed relative top-right crop as fallback.
- **Packaging**: PyInstaller keeps `winsdk`/`winrt` collection and adds RapidOCR data only when installed.

### Fixed
- Auto Bounty no longer exits early on wave-60 bounties when OCR clips the trailing zero.
- Challenge map OCR recovers when the Daily Challenge HUD label is not found.
