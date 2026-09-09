# Portals

Single reference for the Portals feature (Summer Siege / Sky Ruins /
Lightning God / Sovereign portal runs), added in 0.21 and promoted to a
task mode in 0.22.

## What Portals ship as

There are two ways to run one.

**As a task (0.22).** Pick **Portals** in the Task Builder's Mode
dropdown. The task drives the whole cycle -- in, through the run, and
into the next one -- so it needs no portal template; a Macro Operation
on a Portals task is only for placing units in battle.

Set two things on the task:

- **Portals Then Exit** -- how many portals to run. `0` means keep
  going until you stop the task. This replaces Repeat for this mode.
- **Portal in lobby** and **Portal in chooser** -- the two click
  points, both required, each with a Pick button that captures the live
  Roblox window.
  Navigate the game to the matching screen before picking: the Items >
  Portals inventory for the lobby one, a post-run chooser for the other.
  Both are stored on the task, so two queued Portals tasks can farm two
  different portals.

You never choose *which* of those two gets used. The runner looks: if
the post-run chooser is on screen (`portal_offer` / `portal_win`, see
`_portal_chooser_showing`) it picks from the chooser and goes straight
into the next run; otherwise it walks the lobby route -- Items ->
Portals tab -> your lobby slot -> Activate -> Start. The post-run route
is middle of screen (to clear the result panel) -> Select -> your
chooser slot -> Activate -> Start. Both live in
`_reach_portal_activated`.

Activate is not the last click: it opens a **party screen** with its own
green Start button, and nothing teleports until that is pressed. A run that ends anywhere
unexpected therefore re-enters from the lobby on its own.

Portals has no Select Stage screen, no Start button, and no Repeat /
Leave Stage after a run -- Activate teleports you straight in, and the
chooser replaces the result buttons. So it is the one mode that skips
the shared confirm/Solo/Matchmaking tail, and `_handle_portal_result`
stands in for `_handle_match_result`'s repeat/leave branch. There is no
Solo/Matchmaking toggle for the same reason: a portal is always entered
solo from your own inventory.

Teleport-in is confirmed by any of several things that only render once
you are inside a run, checked in this order: the **"Start Game?" prompt**,
the **Start Game button**, the **Auto Play button**, then
**`nav_unitmanager`**. The prompt is the most reliable of them but only
appears when auto-start is off, which is why the HUD buttons back it up.
More than one witness is needed because `nav_unitmanager` is a single crop
of a single HUD button, and when it doesn't match a particular setup the
macro decides a run that loaded fine never started -- then leaves the match
it is already in. The lobby-resync and disconnect checks still take
priority over all of them.

All of this art is cut from a frame the macro itself saved
(`debug/region_teleport_timeout.png`), which is already in the normalised
1152x756 space the matcher works in. Art cropped from a screenshot at some
other scale may never match -- that is what made the first two attempts at
this fix fail.

A Portals task pairs naturally with **Plays The Map: Auto Play** (the
toggle beside Play Mode on every task): the game clears the portal
while the task's Macro Operation is free to do something else with its
Battle and Loop blocks. The Macro Operation picker stays available --
choosing Auto Play does not replace the template, it just changes who
is fighting. See `_ensure_autoplay`, which reads the button's state
before touching it and switches it back off for a Macro task.

Auto Play is only checked on a **lobby** entry. It survives from one
portal into the next through the chooser and is reset only by returning
to the lobby, so clicking it on a chooser entry would toggle it off
mid-chain. The runner records which route it took in
`_portal_entered_from`.

Pointing a Portals task at one of the bundled portal templates is safe:
those templates' "wait for Activate" and post-run Select blocks carry
`"skip_modes": ["portals"]` and are skipped (taking their ELSE branch)
when a Portals task is running, so they can't race the task for the
same buttons. `skip_modes` is generic -- any Pre Start, Battle or Loop
block in any template can list task modes it should sit out.

**As a template (0.21).** At the runner level, Portals are template-driven -- three bundled
examples under `Templates/examples/` (`Portals - single portal (exit to
lobby)`, `Portals - N portals then exit`, `Portals - continuous`) drive
the entire run using generic Detect + Click blocks. Every anchor image
lives under `Assets/ui/portal_*/` and every click point comes from
`MACRO_COORD_DEFAULTS` in `main.py` (Settings > Debug > Macro
Coordinates), so a user picks each point once and every template
respects it -- the same "override story" the rest of the runner uses
for `matchmaking_region_*`, `story_click_x/y`, etc.

## Detect names (`Assets/ui/<name>/`)

Every entry is a folder; the macro's Detect block matches by folder
name, and every `*.png` inside is tried as an interchangeable variant.
Naming follows the pristine short-prefix convention (`portal_*`, same
shape as `exp_*`, `chal_*`, `craft_*`, `fuel_*`, `shop_*`).

### Navigation into the event

The art below still ships, but **nothing in the Portals route uses it any
more** -- since 0.22 a portal is opened straight out of the inventory. It
is kept for templates that navigate the event menu themselves, and as
reference for anyone building one.

- `portal_event_bar` -- bottom bar in the event lobby (Shop / Gamemode / Quests).
- `portal_event_open` -- the Tidal Siege event card that opens the mode picker.
- `portal_mode_tile` -- the Portal Mode tile inside the picker.
- `event_mode_tile` -- the Event Mode tile alongside Portal Mode.

### Portal inventory flow (from lobby)

- `portal_tab_selected` -- the Portals tab in its SELECTED (blue) state, used to
  verify the tab click landed. Distinct from `portal_tab`, which is the
  unselected state -- the two never match at once, which is what makes it a
  reliable proof.

- `nav_items` -- Items button on the main lobby HUD.
- `portal_tab` -- Portals sub-tab inside the Items panel.
- `portal_inventory` -- Portal Inventory screen (idle + post-win alt).
- `portal_selected` -- highlighted state when a portal is currently selected.
- `portal_activate` -- confirmation screen after clicking a portal.
- `portal_party` -- the party screen Activate opens. Cropped to the "Public
  Party" band, NOT the header: the header carries the portal's name and tier
  and would only ever match one portal. Detection only, never clicked.
- `portal_start` -- the green Start button on that party screen.

### In-inventory tier icons

- `portal_tier_1` .. `portal_tier_5` -- Summer Portal tier icons (icon + name-label alt).
- `sky_ruins_portal_tier_5` -- Sky Ruins T5 icon (T1--T4 not shot yet).

### Post-run portal chooser + exit

- `portal_win` -- victory screen with the 3-portal offer.
- `portal_offer` -- the "choose your next portal" screen (T1..T5 variants as alts).
- `portal_select` -- gold Select button on that screen (three states as alts).
- `portal_exit` -- Exit to Lobby button (idle + selected).

## Click coord keys (`MACRO_COORD_DEFAULTS`)

Every Click block in the bundled templates passes a `coord_key` param
instead of a hardcoded x/y. The runner's `_run_click_block` (see
`core/runner_blocks.py`, extended in 0.21) reads `<key>_x` and
`<key>_y` from the runner's coords map -- populated from
`MACRO_COORD_DEFAULTS` in `main.py` and overridable per user in
Settings > Debug > Macro Coordinates. An unset coord logs
`coord_key '<key>' not set in Settings > Debug > Macro Coordinates
-- skipping` and no click happens (identical to the old "no position
set -- skipping" behavior for a forgotten Set picker).

The seven points the route uses, in route order:

- `nav_items` -- Items button on the lobby HUD.
- `portal_tab` -- Portals sub-tab inside the Items panel.
- `portal_activate` -- Activate button on the portal confirmation screen.
- `portal_start` -- Start button on the party screen Activate opens (fallback only).
- `portal_select` -- Select button on the post-run screen, which opens the chooser.
- `portal_exit` -- Exit to Lobby button, used after the last portal.

The post-run route also clicks the shared `screen_middle` point first, to
dismiss the result panel sitting over those buttons.

One more point is not part of the route at all:

- `portal_panel_close` -- the lobby's close button, top-left. Clicked
  before every retry and on every back-out, to shut an Items/Portals
  panel a failed attempt left open. Without it the next attempt clicks
  "Items" at a point that is now something else. Unset is fine: it is
  logged and skipped rather than failing anything.

Every step of both routes is image-first with its coordinate as the
fallback, so stale reference art degrades to coordinate clicking rather
than stopping the task.

Each step also **verifies itself** (`_portal_step`). It names the art
that proves its click worked -- Items expects the Portals tab or the
inventory, the Portals tab expects the inventory, a portal slot expects
the Activate screen -- and re-clicks up to three times if that art
doesn't appear. This exists because a Roblox click can land on the
right pixel and still not register; without the check, the route
marched on and every later step failed against a screen that had never
changed. A step also skips its click when it is *already* where it was
trying to get to, so a retry that starts with the panel still open
can't toggle it shut.

Pick verification anchors that change **because of the click**: the
Portals tab is proven by the tab turning blue (`portal_tab_selected`),
not by the inventory art, which drifts as the game is updated. A stale
anchor turns a working step into a failing one, which is worse than no
check at all. Portal clicks therefore also assert window focus and hover in
before clicking (`_hover_click` / `click_match(shuffle=True)`), the same
treatment the lobby Event button and the Start Game click already
needed.

One rule when adding art to any of these folders: **every variant must
be safe to click.** `template_variant_paths` tries `<name>.png` first
and then the rest alphabetically, the first variant over threshold
wins, and what gets clicked is the *centre of that match*. A crop of a
whole panel will therefore click the middle of the panel rather than
the button inside it -- which is exactly why 0.22 moved the old
231x378 `portal_activate.png` out to `Assets/ui/_unused/`. Crop to the
button, not to the screen it lives on.

Nothing from the Event menu is here any more. Through 0.21 the route
entered via the event card and the Portal Mode tile; opening a portal
straight out of the inventory works from the lobby regardless of what
else is on screen, so `nav_event`, `portal_event_open` and
`portal_mode_tile` were dropped along with those two screens.

There is deliberately **no "which portal" point here, not even a
fallback**. Which portal to run is per-player *and* per-task -- two
queued tasks can farm two different portals out of one inventory -- so a
shared default could only ever be right for one of them, and a task
quietly opening someone else's portal is worse than a task that says
what it needs. A Portals task carries both points and will not run
without them.

## Bundled example templates

Load any from **Load Example...** in the block editor.

### `Portals - single portal (exit to lobby).json`

One portal, then exit. Prestart navigates in and starts a portal;
Battle plays it; Loop A watches for the exit screen and clicks Exit
to Lobby the moment it appears. Use for gold-mine / drill refill
loops.

### `Portals - N portals then exit.json`

Runs a set number of portals and then exits. Loop A wraps the Select
click in a `mode: "counter"` Detect (default `limit: 3`): the THEN
branch clicks Select while count <= limit and the ELSE branch clicks
Exit to Lobby once the counter passes it.

Since 0.22 that Detect also carries `"limit_from_task":
"extract_after"`. Run the template from a **Portals task** and the
limit comes from that task's *Portals Then Exit* field automatically
(`0` = infinite), so one template serves every count without being
edited. Run it from the Macro Manager with no task and it falls back
to the `limit` baked into the block (default `3`) and logs that it did
-- edit that for any positive integer, or set it to `""` for infinite.
The fallback also covers a task whose field is missing or holds
something unparseable, so a hand-edited task file can never make the
counter exit on its first pass.

### `Portals - continuous.json`

Loops portals forever until fuel runs out or you press Stop.

## First-run defaults

0.21.0 shipped every entry above as `None`; 0.21.2 replaced them with
real values picked from a live 1152x756 window, and 0.22 added the two
`*_pick` points the same way. Per-user overrides in `settings.json`
always win, so a game update that shifts a point is a picker click in
Settings > Debug > Macro Coordinates rather than a release. The
`*_pick` points are the two most worth re-picking on a fresh install
-- everything else is a fixed piece of UI, those two are your own
inventory.

## What still needs a shot

`Assets/ui/` folders that would round out the pack but aren't
strictly required to run:

- `portal_activate_button` -- tight crop of just the Activate / Start button on the portal-activate screen.
- `sky_ruins_portal_tier_1` .. `sky_ruins_portal_tier_4` -- Sky Ruins tier icons (T5 shipped).
- `portal_insufficient_fuel` -- the "not enough fuel" popup, if it has its own art.

Drop any of those into an `Assets/ui/<name>/` folder and the runner
picks them up automatically.

## Where the full "Portals as a UI tab" mode is

0.22 delivered the task-queue half of this: Portals is a mode in the
Task Builder, with its own portal-type dropdown and run counter (see
"As a task" above). What is still outstanding is the *settings tab*
alongside Auto Challenge / Auto Bounty -- tier picker, per-tier macro
binding, health check, `setup_ready` gate -- it needs a
new panel in `ui/index.html` + `ui/app.js` mirrored from the Auto
Challenge panel, and a `core/runner_portals.py` mixin styled after
`core/runner_challenge.py` -- 500+ lines across three files, which is
why it stayed out of 0.22 as well. The task path added in 0.22 covers
the "just run portals from the queue" case that panel would mostly
serve; the panel is what a per-tier setup would need.
