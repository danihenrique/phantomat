# Phantomat — Daniel Henrique’s personal fork

Maintained by [Daniel Henrique (@danihenrique)](https://github.com/danihenrique).
This is a customized fork of [kaolti/phantomat](https://github.com/kaolti/phantomat),
used as a daily desktop on Omarchy. The original history, credits and BSD 3-Clause
license are preserved. This fork is independently maintained and is not an
official release of the upstream project.

A zoomable, infinite-canvas window manager for Hyprland. Every window lives
on one endless plane instead of in workspaces. Press a key and the view pulls
back through a curved lens so you can see everything at once, then type a few
letters and fly straight to the window you want.

The name comes from Stanisław Lem's *Summa Technologiae*, where a phantomat
is a machine that builds a whole world around the person inside it.

<!-- Demo video: drag the recording into this spot in GitHub's editor. -->

Made on [Omarchy](https://omarchy.org) with Hyprland 0.56. Built on
[hyprland-scroll-overview](https://github.com/yayuuu/hyprland-scroll-overview)
by yayuuu (see [Credits](#credits)).

## What this fork adds

The fork starts from upstream commit
[`2e33ec1`](https://github.com/kaolti/phantomat/commit/2e33ec12e9d0a7699c61307c1e04909badb75e75).
The custom work focuses on mouse interaction, spatial groups, persistence and
multi-display focus. The canvas, lens, search, keyboard navigation, live tuner
and application support described below come from the original Phantomat.

| Customization | Behavior |
| --- | --- |
| **Resize from any edge or corner** | Drag a border with the primary mouse button, without a modifier. Sides resize one axis; corners resize both. Directional cursors show the grab area. Works at normal size and while zoomed out, without a separate Omarchy shell plugin. The original right-button resize remains available. |
| **Background right-click navigation** | Right-click empty desktop to open or close the navigator. Hold and drag to open and pan in one gesture; releasing after a drag keeps the overview open. |
| **Spatial window groups** | Ctrl+click selects members; Ctrl+G packs them together without resizing them. Move a group by dragging any member, or Shift+drag to adjust one member. Group framing fits the whole group into view. |
| **Focus without leaving the overview** | An optional primary-click mode focuses and raises a window or search result while preserving the camera. Enter still lands on it. |
| **Ctrl+click framing** | Outside the overview, an optional Ctrl+click frames a window or its whole group. |
| **Left+right button chord** | Outside the overview, pressing both buttons together can frame a window or group. The overlap timeout is configurable; ordinary clicks are forwarded when the chord does not complete. |
| **Persistent groups and cameras** | Save window geometry, group membership, per-screen camera, zoom and navigation state together. Plugin updates flush and restore the layout without repacking groups. |
| **Vertical focus regions** | Divide a selected output into vertical regions for stacked physical panels. Focus can target a fixed row or follow the window’s spatial position. Hardware-specific output names stay in user configuration. |
| **Shell popup rendering** | Layer-shell popups, such as tray menus, are rendered with their panel’s canvas transform and opacity. |

New interaction options default to **off** so users can choose the gestures they
want. To enable this fork’s mouse and group features, merge these fields into
the existing `plugin.spatialoverview` tables in
`~/.config/hypr/spatialoverview.lua`:

```lua
input = {
  background_right_click = true,
  ctrl_click_focus = true,
  button_chord_focus = true,
  button_chord_timeout = 120,
},
canvas = {
  border_resize = true,
  groups = true,
  remember_layout = true,
},
```

For focus-only clicks in the overview, also set
`navigator.click_to_focus = true`. Leave it off if clicking should fly into the
window. Do not replace your existing tables wholesale: retain the other canvas,
input and navigator settings. Apply with `hyprctl reload` and check
`hyprctl configerrors`.

For stacked displays, set `canvas.focus_monitor` to your output name,
`canvas.focus_rows` to the number of vertical regions, and `canvas.focus_row`
to `-1` for spatial selection or a zero-based fixed row. With the default empty
monitor name and one row, focus uses the normal monitor area.

### Upstream integration (2026-10-01)

The fork includes upstream through `d62ba67`: camera recovery after temporary
fullscreen windows and screensavers close, wallpaper/blur cache fixes, upright
HUD rendering on rotated monitors, and the live flight-speed slider with a 5%
default minimum zoom. The fork's mouse controls, groups, persistent layout,
vertical focus regions and native layer-popup input remain available.
Existing user configuration still takes precedence: a configured
`canvas.min_zoom = 0.15` stays at 15% until the user changes it.

The integration also preserves native wheel events over layer-shell popups.
Regression coverage includes temporary fullscreen exit with grouped windows
(`tests/fullscreen-groups-nested.py`) and the flight-speed slider's duration
conversion, persistence and reset (`tests/tuner-nested.py`).

### Validation and maintenance

This fork has been built and used with **Hyprland 0.56.2 on Omarchy**. The border
resize regression test covers all four edges and four corners at 100% and 50%
zoom, release handling, interior clicks, the existing right-button gesture and
runtime opt-out. The layer-popup test checks visibility before and during canvas
rendering. Both passed for the initial fork publication; border resize was also
confirmed in daily use. Other focused regression scripts cover groups, focus
regions, button chords and persistence; their presence is not a claim that the
entire suite was rerun for every publication.

Build a separate test binary and run tests in a disposable nested compositor:

```sh
make -j4 OUT=.build/dev/spatialoverview.so
python3 tests/border-resize-nested.py .build/dev/spatialoverview.so
python3 tests/layer-popup-nested.py .build/dev/spatialoverview.so
```

The test environment needs a running Wayland session, `foot`, and the relevant
helpers (`wtype`, `grim`, and Quickshell for the popup test). These tests operate
on the child compositor, not the active desktop. Hyprland’s plugin ABI changes;
rebuild after updating Hyprland. No workstation settings, saved window titles or
prebuilt plugin binaries are distributed in this repository.

Report issues with this customized version in
[this fork’s issue tracker](https://github.com/danihenrique/phantomat/issues).
Upstream remains [kaolti/phantomat](https://github.com/kaolti/phantomat); merging
future upstream changes is a separate maintenance step.

## What it does

- **One canvas for everything.** Windows float freely on a single 2D plane
  instead of in workspaces. Pan, zoom and place windows anywhere.
- **Your screens are one desk.** Side by side on the canvas as they stand on
  your desk, moving together: a window can sit across the seam, and dragging
  it from one screen to the other is one continuous move.
- **Type to find.** `SUPER + CTRL + G` zooms out with a search bar already
  listening. Type part of a title or app name and the camera glides to the
  best match; `Enter` lands on it at full size, `Esc` takes you back.
- **Keyboard first.** Jump to the nearest window in any direction, nudge
  windows around, bring a window to where you are, frame one or fit them all,
  tidy everything up by app, undo and redo.
- **Recent windows.** `ALT + TAB` flips between windows most recently used
  first; hold `ALT` to see the list.
- **Fill or go fullscreen.** `SUPER + T` makes a window fill its screen and puts
  it back. Fullscreen (`SUPER + F`, a video, a game) takes over just the screen
  the window is on; the other screens keep the canvas.
- **All your apps.** Wayland and X11 apps alike, games under Wine and Proton
  included: menus, drags, fullscreen and full frame rate work as on a normal
  desktop.
- **It remembers.** Windows return to their spots after a restart.
- **Tune it live.** `CTRL + ,` in the zoomed-out view opens a tuner for the
  lens, blur, grid, parallax, HUD size, type, colors and more, and you see
  each change as you make it.
- **Looks the part.** A barrel lens with optional edge blur, vignette and
  color fringe, a parallax wallpaper, a dotted grid, a minimap and a
  monospace HUD in the accent color of your choice.

## Install

You need Hyprland 0.56 or newer with its Lua config (`~/.config/hypr/hyprland.lua`,
which Omarchy uses), GCC 15 or newer, and Hyprland's development files. On
Arch or Omarchy:

```sh
sudo pacman -S --needed base-devel git hyprland hyprgraphics pango lua
git clone https://github.com/danihenrique/phantomat.git
cd phantomat
scripts/install.sh
```

The installer builds the plugin, puts it in `~/.local/share/spatial-overview/`,
copies the default settings to `~/.config/hypr/spatialoverview.lua` (it never
overwrites yours), adds two marked lines to your `hyprland.lua` (after making a
backup), and loads it right away. Then press `SUPER + CTRL + G`.

Phantomat used to be called Spatial Overview, and inside it still is: the
settings file, the `hl.plugin.spatialoverview` actions and the
`hyprctl spatialoverview` command keep that name, so configs from before the
rename keep working.

**After a Hyprland update**, the plugin has to be rebuilt for the new version.
Hyprland shows a notification when that is the case; run the installer again:

```sh
cd phantomat && git pull && scripts/install.sh
```

Updating never touches your `~/.config/hypr/spatialoverview.lua`, so keys added
in a new version are not in it yet: compare it with
[examples/spatialoverview.lua](examples/spatialoverview.lua) and copy what you
want (or move yours aside and run the installer for a fresh one).

**To uninstall**, run `scripts/uninstall.sh`. Windows go back to your normal
layout, the lines come out of `hyprland.lua`, and the plugin is deleted. Your
settings stay, in case you come back; `scripts/uninstall.sh --purge` deletes
them too.

## Keys

### Anywhere

| Keys | Action |
| --- | --- |
| `SUPER + CTRL + G` | Zoom out to the canvas (and back). |
| `ALT + TAB`, `ALT + SHIFT + TAB` | Recent windows. A tap flips to the previous one; hold `ALT` for the list, release to go. |
| `SUPER` + arrows | Focus the nearest window in that direction; the camera follows. |
| `SUPER + SHIFT` + arrows | Nudge the focused window one grid step; hold to keep moving. |
| `SUPER + T`, `SUPER + ALT + F` | Make the focused window fill its screen, with the usual gaps; again puts it back. |
| `SUPER + F`, or an app going fullscreen | Fullscreen on the screen the window is on; the other screens keep the canvas. `SUPER + CTRL + G` takes the screen back, going back to the window makes it fullscreen again. |
| `SUPER + O` | Pin the window to the screen: it stays put while the canvas moves; again puts it back on the canvas. |
| `SUPER + 1` … `0`, `SUPER + TAB` and the other workspace keys | Nothing, on the canvas (with `canvas.places`, experimental: places on the canvas). |
| `SUPER + J`, `P`, `L`, `Home`, `G`, `SHIFT + ALT + SUPER` + arrows | Tiling and grouping keys: nothing, on the canvas (every window floats). |
| Left-drag a border/corner | Resize from that edge when `canvas.border_resize = true` (default off). Works in navigation and direct-input modes; no modifier needed. |
| Middle-drag | Pan the canvas. |
| `CTRL` + wheel, pinch | Zoom. |
| `SUPER` + left-drag, right-drag | Move, resize a window. |

Border resize uses an 8 logical-pixel outside grab band and 2 pixels inside the window, independent of zoom. Corners resize both axes; sides resize only one. Popups, panels, pinned/fullscreen windows and modified clicks retain their existing behavior. The existing right-button resize is unchanged. No shell plugin is required.

### In the zoomed-out canvas

| Keys | Action |
| --- | --- |
| type | Search window titles and app names. Every word must appear as typed, letters together (`fas` finds `fastfetch`); case and accents are ignored. The camera and focus follow the best match. |
| `↑` `↓`, `Tab` `SHIFT + Tab` | Move through the results. With no search, `Tab` walks recent windows. |
| `CTRL + 1` … `CTRL + 9` | Go straight to that result. |
| `Enter` | Go to the selected window at full size. |
| `SHIFT + Enter` | Bring the selected window to where you are, then go there. |
| `Esc` | Clear the search, then go back to where you started. |
| `←` `→` `↑` `↓` | Select the nearest window in that direction. |
| `SHIFT` + arrows | Nudge the selected window. |
| `CTRL` + arrows | Pan. |
| `CTRL + =`, `CTRL + -` | Zoom in, out. |
| `CTRL + 0` | Fit every window (every match while searching). |
| `CTRL + F` | Frame the selected window. |
| `CTRL + A` | Tidy all windows up on the grid, by app. |
| `CTRL + Z`, `CTRL + SHIFT + Z` | Undo, redo moves and tidying. |
| `CTRL + ,` | Tune the look. |
| `F1` | Every key, on screen. |

With the mouse: click a window to go to it, drag a window to move it, drag the
empty canvas to pan, scroll to zoom, click the minimap to jump.

## Optional mouse controls and spatial groups

These controls are opt-in. Existing click and navigation behavior remains the
same unless enabled in `~/.config/hypr/spatialoverview.lua`:

```lua
-- Inside plugin.spatialoverview:
input = { background_right_click = true },
navigator = { click_to_focus = true },
canvas = { groups = true },
```

Merge these fields into the existing tables; do not replace your other settings.

- `input.background_right_click`: an unmodified physical right-click on empty
  desktop background toggles the navigator, including before the first canvas
  session. Hold the button and drag to pan immediately; dragging left reveals
  windows to the right. Releasing after a drag keeps the navigator open. A short
  right-click while navigating closes it and restores the view from before entering. Application windows, layer panels, popups and the lock screen are
  excluded. Right-clicking an app retains its normal behavior.
- `input.button_chord_focus` (default `false`): outside the overview, press left
  and right together over a window to focus and frame it or its group, in either
  order. Both presses must overlap within `input.button_chord_timeout` (default
  120 ms, range 30–300). The first press waits up to this interval so the app
  receives neither click when the chord succeeds. Releasing or starting a drag
  delivers an ordinary click immediately. Desktop-background gestures and
  modified clicks are excluded.
- `input.ctrl_click_focus` (default `false`): outside the overview, **Ctrl+primary-click**
  focuses and frames the window or its entire spatial group, respecting focus
  regions. The gesture is consumed instead of being sent to the app. Ordinary
  clicks and Ctrl+click selection inside the overview retain their behavior.
- `navigator.click_to_focus`: primary-click a window or search result to focus
  and raise it without moving the camera or leaving the overview. **Enter**
  still lands on the focused window. The primary button respects left-handed
  configuration. Leave this option disabled for primary-click to open the window.
- `canvas.groups`: **Ctrl+click** toggles selection of floating windows (or
  search results). **Ctrl+G** brings selected windows together in a compact
  grid, in selection order, preserving their sizes. Selecting an existing group
  member together with another window merges their entire groups. **Ctrl+Shift+G** dissolves
  groups containing the selection, or the focused window's group when no
  multi-selection is present. **Esc** clears multi-selection first.

Selected windows have a strong accent outline; grouped windows have a lighter
one. Drag a member to move the group; **Shift+drag** moves just that member.
Resize members independently. Landing on a member centers the bounding box of
all members, zooming out if needed within the configured minimum zoom. Group
framing respects the configured focus region, including spatial row selection.
Creating a group and moving it use the existing positional undo/redo history;
undo restores geometry, not group membership.

These are spatial associations, separate from Hyprland's tabbed groups. Pinned,
natively grouped and fullscreen windows cannot be added. Fullscreen temporarily
suspends group framing. Closed windows are removed automatically.

With `canvas.remember_layout = true`, groups, window positions and sizes, camera,
zoom and navigation mode are saved together in
`$XDG_STATE_HOME/spatial-overview/canvas-memory.tsv` (default
`~/.local/state/spatial-overview/canvas-memory.tsv`). Updates flush this state
before unloading and restore it without repacking groups. Stable window IDs
preserve identity across plugin reloads, including windows with identical titles.
After a new login, group membership is restored only for unambiguous app/title
matches; ambiguous or changed titles are not guessed. The existing app placement
fallback still applies to individual windows. Disabling `remember_layout` keeps
state in memory only. Version 1 layout files are read and upgraded on saving.

Script actions: `canvas("select")`, `canvas("clear-selection")`,
`canvas("group")`, `canvas("ungroup")`, `canvas("frame-group")`,
`canvas("save-memory")` (flush pending layout changes immediately).
`hyprctl spatialoverview` includes `selection` and `groups` arrays of window titles.

## Tuning

`CTRL + ,` in the zoomed-out canvas turns the search bar into a list of
settings. Type to filter (`blur`, `grid dot`, `accent`), `↑` `↓` to pick, `←`
`→` to adjust while you watch (`SHIFT` for fine steps, `CTRL` for big ones),
`Delete` to undo a change, `Esc` when done. The footer explains the selected
setting.

Changes are saved as you make them to `~/.config/hypr/spatialoverview-tuning.lua`,
which is applied after `spatialoverview.lua`, so a tuned value wins until you
delete its line there.

Everything can also be set in `~/.config/hypr/spatialoverview.lua` (then
`hyprctl reload`). The main settings, all under `plugin.spatialoverview`:

| Setting | Effect |
| --- | --- |
| `canvas.desktop_mode` | Enable the shared infinite-window desktop |
| `canvas.linked_screens` | Screens show adjacent parts of the canvas and move together (default); off: each screen is its own camera |
| `canvas.workspace_isolation` | Independent canvas per native workspace (off by default); filters windows, input, search, groups and undo; remembers each workspace camera. Overrides linked screens and places. |
| `canvas.places` | Experimental, off by default: the workspace keys go to places on the canvas and take windows there |
| `canvas.initial_zoom` | Camera zoom when desktop mode opens |
| `canvas.min_zoom` / `max_zoom` | Continuous camera zoom limits |
| `canvas.zoom_step` | Ctrl-wheel zoom strength |
| `canvas.space_pan` | Optional Space + left-drag panning; disabled by default so Space always reaches applications |
| `canvas.border_resize` | Primary-button border/corner resizing without modifiers (default off) |
| `canvas.direct_input` | Forward input into transformed Wayland windows |
| `canvas.hover_focus` | Activate a transformed window when the pointer enters it |
| `canvas.persistent` | Keep the canvas renderer active at 100% zoom instead of returning to workspace rendering |
| `canvas.minimap_*` | Configure the undistorted navigation-mode minimap size, margin, and opacity |
| `canvas.arrange_context_grouping` | Prefer shared local title/app context before falling back to app categories |
| `canvas.arrange_size_similarity` | Relative threshold for treating window sizes as equivalent |
| `canvas.arrange_resize_limit` | Maximum relative resize applied to any window by smart arrangement |
| `canvas.auto_float` | Detach existing and new app windows from tiling |
| `canvas.auto_place` | Place newly managed windows near the active camera |
| `canvas.placement_near_view` | Opt-in: use visible free space, then extend to the right without overlap. New launches ignore old remembered positions outside startup restoration. Default `false`; existing windows and reload restoration keep their positions. |
| `canvas.placement_gap` | Collision gap used by automatic placement |
| `input.pan_sensitivity` | Middle-drag camera sensitivity (and optional Space-drag sensitivity) |
| `input.drag_threshold` | Pixels before a click becomes a drag |
| `animation.enabled` | Enables overview camera animation |
| `animation.speed` | Camera animation speed |
| `animation.bezier` | Name of the Hyprland curve used for camera motion |
| `distortion.enabled` | The curved lens at all |
| `distortion.strength` | Signed lens curvature; `0` is flat |
| `distortion.shader_path` | A lens shader of your own; empty uses the one built into the plugin |
| `distortion.edge_scale` | Overscan that keeps curved corners filled |
| `distortion.feather` | Width of the soft screen-edge fade |
| `distortion.transition_power` | When the lens eases in during the zoom animation (1 follows the zoom) |
| `canvas.grid_*` | Shared snap/render spacing, width, opacity, line/dot style, and dot diameter |
| `canvas.background_dim` | Dark overlay behind the grid and windows in navigation mode |
| `canvas.snap_enabled` / `snap_size` | Snap free window placement to the canvas grid, and its step in pixels |
| `canvas.remember_layout` | Remember window positions and cameras across restarts and reopenings |
| `navigator.enabled` | Type-to-search palette in the zoomed-out canvas |
| `navigator.labels` | Window titles on the map |
| `navigator.dim_unmatched` | How far windows that do not match the search recede |
| `navigator.pointer` | Click lands, drag moves or pans, wheel zooms; off keeps direct app input while zoomed out |
| `navigator.accent` | HUD accent for the selected row, caret, key names and outlines: `#rrggbb`, a preset name (`orange`, `amber`, `yellow`, `lime`, `green`, `mint`, `teal`, `cyan`, `sky`, `blue`, `indigo`, `violet`, `purple`, `magenta`, `pink`, `red`, `white`), or `auto` to follow the active border |
| `navigator.mono_font` | The HUD's typeface (monospace, set in uppercase) |
| `wallpaper` / `blur` / `blur_strength` | Sharp-at-rest canvas backdrop and navigation-mode blur blend |
| `distortion.edge_blur` / `edge_blur_start` | Lens blur toward the screen edges, and where it begins (0 center, 1 corners) |
| `distortion.vignette` | Darkening toward the edges |
| `distortion.chromatic` | Red/blue fringe toward the edges |
| `parallax.enabled` / `strength` | The wallpaper follows the camera at this fraction of the windows' speed |
| `parallax.depth` | How much the wallpaper shrinks as you zoom out (0 keeps its size) |
| `parallax.desktop` | Also apply parallax when panning the full-size desktop |
| `navigator.hud_scale` | Size of the whole HUD |
| `navigator.width` / `top` / `rows` / `row_height` / `rounding` | Palette geometry |
| `navigator.panel_opacity` | Palette background opacity (lower is glassier) |
| `navigator.uppercase` / `letter_spacing` | Capitals or text as written, and tracking |
| `navigator.query_size` / `title_size` / `detail_size` / `corner_size` / `label_size` | Type sizes |
| `navigator.corner_labels` | Readouts in the screen corners |
| `navigator.search_height` / `search_border` / `search_border_opacity` / `search_border_color` / `search_glow` | The search field |
| `navigator.tuning_file` | Where the live tuner saves (default `$XDG_CONFIG_HOME/hypr/spatialoverview-tuning.lua`) |

`navigator.accent` takes `#rrggbb`, a preset name (`orange`, `amber`, `yellow`,
`lime`, `green`, `mint`, `teal`, `cyan`, `sky`, `blue`, `indigo`, `violet`,
`purple`, `magenta`, `pink`, `red`, `white`), or `auto` for your theme's border
color.

For scripts and bindings, `hl.plugin.spatialoverview.canvas(...)` takes
`search [text]`, `tune`, `fill`, `pin`, `go <place>|next|prev|back`,
`send <place> [stay]`, `switch next|prev`, `fit`, `summon`, `zoom in|out`,
`pan <dir>`, `nudge <dir>`, `undo`, `redo`, `arrange`, `frame`, `land`, `back`,
`noop` (for keys that do nothing on the canvas) and `refresh`.
`hyprctl spatialoverview` prints the canvases' state as JSON.

How each key behaves on the canvas, and what the tests check, is in
[docs/window-rules.md](docs/window-rules.md).

## Troubleshooting

- **"this build is for a different Hyprland version"**: Hyprland was updated.
  Run `scripts/install.sh` again.
- **Nothing happens on `SUPER + CTRL + G`**: check `hyprctl plugin list` and
  `hyprctl configerrors`. If you load the plugin in your own way, make sure
  `spatialoverview.lua` is loaded after it.
- **Something broke**: `scripts/uninstall.sh` puts your desktop back as it was.
  Please open an issue with your Hyprland version (`hyprctl version`).

This hooks deep into Hyprland internals, so a Hyprland update can break it
until it is updated too. It has been used daily on one setup (Omarchy,
Hyprland 0.56.2, NVIDIA, two monitors); other setups are less tested.

## Development

`make` builds `spatialoverview.so` in the checkout; `scripts/install-live.sh`
builds it and swaps it into the running session, keeping windows where they
are. The tests run a nested Hyprland in a window (`tests/*-nested.py`);
`make test-tools` builds the virtual mouse some of them use.

## Credits

This personal fork builds on [Phantomat by kaolti (Zsolt Kacso)](https://github.com/kaolti/phantomat).
Customizations in this repository are maintained by Daniel Henrique.

Phantomat began as a fork of
[hyprland-scroll-overview](https://github.com/yayuuu/hyprland-scroll-overview)
by yayuuu (Daniel Skorupa) and its contributors, which grew out of the plugin
work of Vaxry and the Hypr Development team. Their code and history are
kept in this repository. Neither project endorses this one.

## License

BSD 3-Clause; see [LICENSE](LICENSE).

### Desktop workspace wheel

Opt in with `input.background_workspace_scroll = true` (default off).
Roll the mouse wheel down on empty desktop for the next native workspace,
or up for the previous one. Switching preserves the cursor's screen position
and uses monitor-relative workspace ordering. A 250 ms cooldown prevents a
fast wheel burst from skipping several workspaces.

Works on the native desktop and the persistent canvas in direct-input mode
with `canvas.workspace_isolation = true`. The navigator keeps its normal zoom
and pan interactions. Windows, borders, panels, docks, menus and special
workspaces do not start the gesture. Modifiers, held mouse buttons, horizontal
scroll and touchpad scrolling retain their existing behavior. Left-dragging
is unchanged. Removing the plugin cancels queued switches.

### Independent workspace canvases

Set `canvas.workspace_isolation = true` in the plugin configuration, then close
and reopen the canvas (or reload the plugin). Each output shows only the windows
of its active native workspace, both at normal zoom and in the navigator. Bar
clicks and native workspace dispatchers use the same isolation boundary. Existing
`canvas_or("go ...", ...)` and `canvas_or("send ...", ...)` bindings fall back to
native workspace operations. Pinned windows intentionally remain screen-fixed
and visible across workspaces, as in Hyprland. Special workspaces keep their
existing native handling.

Camera position, zoom and navigation return view are retained per output and
workspace ID; with `remember_layout` they are also saved across plugin reloads.
Window positions remain world coordinates. An existing workspace without a saved
camera initially centers one of its windows; a new empty workspace starts at the
origin. Workspace ownership remains Hyprland's: automatic canvas reassignment to
the screen's workspace is disabled. Linked screens and experimental canvas places
are inactive in this mode. Sending a window uses the native workspace move; it
keeps its canvas position, so use the navigator to locate it if it is off camera.

Workspace switches cancel ongoing canvas drags/resizes and clear temporary group
selection and search. Undo journals are session-local and separate per workspace;
undo cannot retrieve a window that was explicitly moved to another workspace.
Groups spanning workspace boundaries operate only on members in the same
workspace as the selected window.

Regression: `python3 tests/workspaces-nested.py .build/workspaces/spatialoverview.so`
creates an isolated compositor and checks pixels, input, ownership, native
switching and camera restoration. `WORKSPACE_BASELINE=1` reproduces the shared
canvas visibility failure on the old build.
