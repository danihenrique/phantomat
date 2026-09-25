# Shared by install.sh, install-live.sh and uninstall.sh. Source it after
# setting project_dir.

hyprland_session() {
  [[ -n ${HYPRLAND_INSTANCE_SIGNATURE:-} ]] && hyprctl instances >/dev/null 2>&1
}

spatialoverview_loaded() {
  hyprctl plugin list 2>/dev/null | grep -q '^Plugin spatialoverview '
}

# Unloading the plugin returns every window to its normal layout. Writing the
# canvas positions to the layout memory first lets the next load put each
# window back where it was (canvas.remember_layout).
remember_canvas_layout() {
  local state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/spatial-overview"
  mkdir -p "$state_dir"
  python3 - "$state_dir/canvas-memory.tsv" <<'EOF'
import json, os, pathlib, shutil, subprocess, sys, time

state = json.loads(subprocess.check_output(["hyprctl", "spatialoverview"]))
if state.get("memory_version", 0) >= 2:
    saved = subprocess.run(["hyprctl", "dispatch", 'hl.plugin.spatialoverview.canvas("save-memory")'], capture_output=True, text=True)
    if saved.returncode or saved.stdout.strip() != "ok":
        raise SystemExit("Cannot save canvas state; update stopped: " + saved.stdout + saved.stderr)
    print("Saved canvas windows, groups and cameras through the running plugin.")
    raise SystemExit(0)

# One-time upgrade from builds without native group persistence. Stable IDs
# identify live windows even when titles change or applications have siblings.
clients = json.loads(subprocess.check_output(["hyprctl", "clients", "-j"]))
monitors = json.loads(subprocess.check_output(["hyprctl", "monitors", "-j"]))
now = int(time.time())
clean = lambda s: s.replace("\t", " ").replace("\n", " ").replace("\r", " ")
path = pathlib.Path(sys.argv[1])
lines = ["# spatial-overview canvas memory v2", "session\t" + clean(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", ""))]
by_title = {}
for c in clients:
    if c.get("mapped"):
        by_title.setdefault(c.get("title", ""), []).append(c)
groups = {}
for index, group in enumerate(state.get("groups", []), 1):
    for title in group:
        matches = by_title.get(title, [])
        if len(matches) != 1:
            raise SystemExit("Cannot safely migrate an ambiguous group member; existing plugin and state kept.")
        groups[matches[0]["address"]] = index
for monitor in monitors:
    screen = next((s for s in state.get("screens", []) if s.get("name") == monitor["name"] or s.get("monitor") == monitor["name"]), None)
    if not screen:
        continue
    x, y, w, h = screen["view"]
    width, height = monitor["width"] / monitor["scale"], monitor["height"] / monitor["scale"]
    cx, cy = x + w/2 - monitor["x"] - width/2, y + h/2 - monitor["y"] - height/2
    zoom = screen["zoom"]
    lines.append(f"camera\t{clean(monitor['name'])}\t{cx:.6f}\t{cy:.6f}\t{zoom:.6f}\t{int(screen['navigating'])}\t{cx:.6f}\t{cy:.6f}\t{zoom:.6f}")
for c in clients:
    if not c.get("mapped") or not c.get("floating") or c["workspace"]["id"] <= 0 or c.get("pinned"):
        continue
    klass = clean(c.get("class") or c.get("initialClass") or "")
    title = clean(c.get("title") or c.get("initialTitle") or klass)
    if klass:
        x, y = c["at"]
        w, h = c["size"]
        stable = int(c.get("stableId", "0"), 16)
        lines.append(f"window\t{klass}\t{title}\t{x:.6f}\t{y:.6f}\t{w:.6f}\t{h:.6f}\t{now}\t{stable}\t{groups.get(c['address'], 0)}")
if path.exists():
    shutil.copy2(path, str(path) + ".pre-v2")
temporary = path.with_name(path.name + ".next")
temporary.write_text("\n".join(lines) + "\n")
os.replace(temporary, path)
print(f"Migrated {len(groups)} grouped windows and their layout without rearranging them.")
EOF
}

# Unloads the running build through a small helper plugin
# (scripts/safe-unload.cpp) that first repairs window layout state older
# builds could leave inconsistent; re-tiling such a window crashed Hyprland.
# Returns non-zero, having unloaded nothing, if that is not safe.
safe_unload() {
  make -C "$project_dir" --no-print-directory -s safe-unload
  local helper="$project_dir/.build/safe-unload.so"
  local report="${XDG_RUNTIME_DIR:-/tmp}/spatialoverview-safe-unload.${HYPRLAND_INSTANCE_SIGNATURE:?not inside Hyprland}"
  rm -f "$report"
  hyprctl plugin load "$helper" >/dev/null
  for _ in $(seq 50); do
    grep -q '^unloaded ' "$report" 2>/dev/null && break
    sleep 0.1
  done
  hyprctl plugin unload "$helper" >/dev/null || true

  if ! grep -q '^unloaded 1' "$report" 2>/dev/null; then
    echo "Could not unload the running Phantomat safely; nothing was changed." >&2
    [[ -f "$report" ]] && sed 's/^/  /' "$report" >&2
    rm -f "$report"
    return 1
  fi
  local checked repaired repaired_after unresolved
  read -r _ checked repaired _ < <(grep '^before ' "$report")
  read -r _ _ repaired_after unresolved < <(grep '^after ' "$report")
  echo "Unloaded the running Phantomat ($checked windows checked, $((repaired + repaired_after)) layouts repaired)."
  if (( unresolved > 0 )); then
    echo "Warning: $unresolved window layouts could not be repaired; avoid toggling floating on them until you log out and back in." >&2
  fi
  rm -f "$report"
}
