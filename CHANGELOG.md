# Changelog

All notable changes to Anime Expeditions (Cream's Macro) are documented here.

## [2.0.1] - 2026-09-22

### Interactive UI & Version Badge
- `new` **Animated Version Badge** — smooth continuous rotation for the version icon with interactive hover acceleration (1.8s), distinct tactile active feedback (`:active { transform: scale(0.96) }`), and enhanced hover states.
- `fix` **Update Modal Occlusion & Toggle** — eliminated accidental modal dismissals and fixed child window occlusion to ensure the update window always opens cleanly over the game.
- `fix` **Settings Anchor Precision** — checking for updates from Settings now directly targets the update action button.

### Installer & Reliability
- `new` **Native Windows COM Shortcuts** — replaced brittle PowerShell script invocation with direct Windows `IShellLinkW` / `IPersistFile` COM interface for 100% reliable shortcut creation on Desktop and Start Menu.
- `new` **Clean Modern Installer UI** — redesigned setup wizard matching the macro's obsidian/brass aesthetic with small-caps header typography and clean system icons.
- `new` **Resumable & Chunked Downloads** — chunked HTTP streaming with resume support (`Range` headers) for large package downloads, with fallback mirrors and zero memory spikes.
- `fix` **Match Restart Stop Handling** — graceful exit on macro stop during in-game match restarts, preventing unnecessary repeat iterations.

## [2.0.0] - 2026-09-17

## v2.0.0 — Modern Glass UI, WASD Walk System & Next-Gen Automation

### Next-Gen Interface & Modular Dashboard
- `new` **New Modern UI System** — completely redesigned sleek aesthetic with dynamic backdrop blur, refined tactile feedback, and customizable theme settings (Onyx/Pearl).
- `new` **Modular Dashboard & Drag-and-Drop Layout** — fully customizable dashboard grid allowing Macro Engine, Session Stats, Process Log, and Run History cards to be rearranged, hidden, or restored on the fly.
- `new` **Intelligent Cursor & Header Grab Handles** — clean, dedicated drag handles (`⋮⋮`) with zero button clutter, active strictly within header bounds while keeping card contents and controls intuitively clickable.
- `new` **Sidebar Restore Banner** — non-intrusive restore bar that dynamically appears when cards are hidden, offering instant one-click restoration without polluting card headers.
- `new` **Thematic Modal Cross Icons** — replaced all ambiguous close buttons across all modal dialogs with vector `#i-close` icons and `.btn-danger-hover` styling.

### Live Sub-Block Customization & Swap Physics (Macro Engine)
- `new` **Sub-Block Reordering with Live Swap Preview** — all 4 sub-sections (Streak & Stats, Run Info, Mini Queue, Active Automations) support dynamic reordering. Dragged blocks feature smooth inertia physics (`lerp * 0.35` with velocity tilt), while target blocks smoothly glide out of the way to preview the new layout in real time.
- `new` **Win Streak & Record Telemetry Strip** — real-time HUD telemetry tracking consecutive wins (`STREAK`), all-time session record (`BEST`), and auto-timer for upcoming Challenge rotations.
- `new` **Loss Streak Safety Stop** — configurable safety threshold that automatically pauses macro execution after consecutive defeats to safeguard winrate and stats.
- `new` **Quick Action Bar (Auto-Restart & VIP Rejoin)** — dedicated fast-action controls for immediate round restart looping (`Alt+F5`) and 1-click private server reconnection (`Alt+F6`) with dynamic hotkey badge synchronization.
- `fix` **Dashboard Mini Queue Filtering & Adaptive Scroll** — the Dashboard upcoming queue now strictly displays active tasks (`enabled !== false`) with accurate counter badge, alternating zebra striping for high readability, and responsive clamp height (`clamp(140px, 22vh, 230px)`).

### WASD Walk Recording & Visual Route Navigation
- `new` **Live WASD Walk Recording System** — record in-game movement routes on the fly without cluttering the main replay. Activates via global hotkey (`Alt+9`) or directly in Scenario Builder with an on-screen recording HUD (`recPopout`).
- `new` **Intelligent Idle Auto-Save & Manual Stop** — automatically concludes and saves movement routes after 1.8s of idle input or via the on-screen Stop button, prompting for route name and saving to `Paths/`.
- `new` **Visual Walking Path Picker** — integrated walking path selector into Move/Walk scenario blocks and the Expedition Hub walking paths manager, allowing stored WASD routes to be assigned with one click.

### Recordings Drawer & Quick Replay Selector (F10)
- `new` **Sliding Glass Recordings Drawer (`F10`)** — full-height drawer sliding smoothly from the right edge with live search, route length, action count, and creation date.
- `new` **Instant Route Selection & Fast Play** — 1-click selection to mark a recording as active without launching, or direct `Play` (▶) button for instant replay execution.
- `new` **Native Window Occlusion Protection** — automatically hides embedded Roblox window (`hide_game()`) when opening the drawer and restores it upon closing, preventing the game from overlapping the route list.
- `new` **Start Button Mode Selector** — switch between Task Queue (Auto) and Replay mode directly from the drawer footer.
- `new` **Harmonious Drawer Header & Pill Badge** — clean inline layout with dedicated `.rec-drawer-title-row` and glass pill count badge vertically aligned right next to the title.

### Hotkey Management & Multi-Key Combinations
- `new` **Two-Key / Modifier Hotkey Recording** — full support for recording combination shortcuts (`Alt+9`, `Alt+F5`, `Alt+F6`, `Ctrl+Shift+R`). Holding a modifier shows a pending state (`Alt + ...`) and waits for the target key before saving.
- `new` **Tactile Hotkey Reset/Clear Button (`×`)** — dedicated quick-clear button on every hotkey row to instantly unbind shortcuts.
- `new` **Automated Default Hotkey Migration** — seamless auto-migration of legacy default keys (`F6` -> `Alt+F5`, `F10` -> `Alt+F6`, `F9` -> `F10`) for both fresh installs and existing users upgrading from previous versions.

### Scenarios, Templates & Management
- `new` **Open Templates Folder Button** — added a dedicated 1-click button in Scenarios and Tasks headers to open the `Templates/` directory directly in Windows Explorer.
- `new` **Pre-Shipped Endless Templates** — shipped pre-calibrated `Inf Summer` and `Summer Fishing` task templates with repeat set to 9999 for out-of-the-box 24/7 farming.

### Engine Reliability, Bugfixes & Navigation
- `fix` **Anti-Reparenting Leak (Browser Docking)** — Roblox window could dock into Chrome/Edge because window search matched browser tabs titled "Anime Expeditions"; fixed by strictly filtering window handles by macro process ID (`pid=os.getpid()`).
- `fix` **Adaptive Resolution & Display Scaling** — mouse clicks and vision templates drifted on non-1080p resolutions (1024×768) or 125%/150% Windows DPI; fixed with aspect ratio distortion correction and work area boundary checks (`SPI_GETWORKAREA`).
- `fix` **Inf Summer Infinite Loop & Restart Fallback** — endless runs could accidentally exit to lobby on defeat or restart stalls; fixed with 5-stage restart verification and an unconditional lobby exit lock for Inf Summer scenarios.
- `fix` **Start Game Modal Auto-Click** — stage and event loading occasionally halted on an unhandled green "Start Game" confirmation dialog; added visual template matching and automatic click dispatch.
- `fix` **Windows OCR Bundled Dependencies** — PyInstaller `.exe` builds omitted WinRT OCR assemblies, causing silent OCR failures on clean Windows installs; explicitly bundled `winsdk.windows.media.ocr` and globalization modules.
- `fix` **Diagnostics Bell & In-App Setup** — missing OCR language packs or incorrect display scaling caused silent runner failures without notification; added header Diagnostics Bell with 1-click OCR package installation and real-time status.
- `fix` **Lobby Auto-Recovery Navigation** — character could get stuck in lobby if dialog menus closed prematurely or templates shifted; added multi-anchor detection, relaxed matching tolerance (0.78), and proactive lobby reset.
- `fix` **Infinite Wave Limit & Match Stall Fallback** — runner could freeze indefinitely if victory/defeat banners were obscured during long runs; added timeout watchdog that safely leaves stage and advances queue.
- `fix` **Window Maximize & Fullscreen Layout** — maximizing window distorted Roblox coordinates or caused canvas stretching; fixed via Win32 `SW_MAXIMIZE`/`SW_RESTORE` preserving game viewport at (0, 44).
- `fix` **Multi-Key Hotkey Capture Glitch** — pressing `Alt` immediately locked the hotkey without waiting for the secondary key (e.g. `9` or `F5`); fixed by supporting modifier pending states (`Alt + ...`).
- `fix` **Recordings Drawer Roblox Occlusion** — embedded Roblox child window rendered on top of the F10 recordings drawer due to native HWND z-ordering; fixed by auto-hiding the game on drawer open and restoring it on close.
- `fix` **WASD Walk Recording Polish & Safe HUD** — floating recording HUD could remain on screen after screen switch; fixed with strict lifecycle cleanup and 1.8s idle auto-save to `Paths/`.
- `fix` **Dashboard Mini Queue Enabled Filtering** — upcoming queue on Dashboard showed disabled tasks and inflated count; now strictly filters `enabled !== false` with zebra striping and adaptive scrolling.
- `fix` **Thematic Modal Close Icons** — ambiguous or missing modal close buttons replaced with vector `#i-close` cross icons and danger hover states across all dialogs.
- `fix` **Seamless Roblox Docking & Window Protection** — embedded game window (1152×756) with auto-docking, smart un-docking on quit, resolution detection, and protection against UI overlap.
- `fix` **Elimination of Artificial Neon Glows & Native Dialogs** — replaced jarring oversaturated glow halos with natural frosted glass shadows and safe in-app confirmations that never hide behind native game windows.
- `fix` **Clean Layout Splitters** — removed non-functional tier resizers, keeping only high-precision column resizers with smooth pointer tracking.
- `fix` **Multi-Rank Fishing Rod Protection** — multi-layer verification protecting equipped fishing rods (Novice through Grandmaster) from accidental un-equipping during cycle transitions.

---

### How to update:
- **In-app:** Settings → "Check for Updates".
- **Direct download:** Download `Anime Expeditions Macro Setup.exe` from the release assets below.

> [!IMPORTANT]
> When updating manually from a `.zip` archive, make sure the `Assets` folder is placed next to the `.exe` file. The automatic installer updates all files preserving your settings.

## [1.1.10] - 2026-09-13

### Task Queue & Import
- `new` **Universal JSON Import in Tasks** — the Tasks screen now accepts any `.json` format: standalone macro templates (`Inf Summer.json`), exported template packs, single task objects without array wrappers, and raw CREAM share codes (`{"code": "..."}`). Tasks are automatically constructed, queued, and validated.
- `fix` **Task Auto-Transition Enforcement** — fixed edge cases where the macro could transition to the next task even when Auto Transition was disabled. Toggling Auto Transition Off now strictly repeats or terminates the current task safely.

### UI & Layout Scalability
- `new` **Horizontal Top Navigation Header** — moved screen navigation from the right vertical rail into a centered horizontal bar in the titlebar. Frees up 76px of width across all screens, completely eliminates navigation rail overlap, and compacts cleanly to icons on smaller screens.
- `new` **Dynamic Resolution Auto-Layout** — the embedded Roblox frame and game column dynamically scale to the selected game resolution (1152×768, 1024×768, 800×600), automatically reclaiming 130–350px of horizontal room on compact monitor setups.
- `fix` **Adaptive Controls & Overlap Protection** — Start, Pause, and Stop controls are positioned comfortably above Run History and dynamically adapt with container queries, stacking full-width on narrow panels so buttons are never clipped.

### Combat, Hotbar & Fishing Reliability
- `new` **Ironclad Multi-Rank Fishing Rod Verification** — multi-layer verification for equipped fishing rods supporting all ranks (Novice through Grandmaster) and low graphic settings via 11 reference templates and 2.5x OCR keyword parsing. Automatically draws slot 1 if missing.
- `fix` **Bottom Hotbar & Placeable Fish Safety** — eliminated automatic hotbar slot cycling and accidental clicks during matches. Prevents locking into unit placement/targeting mode when carrying placeable buff fish items.
- `fix` **Rod Unequip Prevention** — strictly checks if the rod is already active before interacting, preventing accidental un-equipping of fishing rods during cycle transitions.


## [1.1.9] - 2026-09-13

### New
- **Ironclad Fishing Rod Verification**: Multi-echelon verification of equipped fishing rod supporting all levels (Novice to Grandmaster) and low graphics via 11 templates and 2.5x OCR keyword parsing. Automatically equips slot 1 if missing and strictly protects held rods from accidental un-equipping (skipping slot 1 clicks/keys when already held).
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
