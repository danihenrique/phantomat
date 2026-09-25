#define WLR_USE_UNSTABLE

#include "Memory.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>

#include <hyprland/src/desktop/state/WindowState.hpp>
#include <hyprland/src/desktop/view/Window.hpp>

#include "Navigator.hpp"
#include "CanvasGroups.hpp"
#include "Config.hpp"
#include <unordered_set>

namespace SpatialOverview::Memory {
    namespace {
        struct SEntry {
            std::string klass;
            std::string title;
            CBox        box;
            int64_t     seen   = 0;
            uint64_t    window = 0; // claimed by this open window
            uint64_t    savedWindow = 0; // identity across plugin reloads in one compositor
            uint64_t    group = 0;
        };

        constexpr size_t MAX_ENTRIES = 96;

        bool                                      g_loaded = false;
        std::vector<SEntry>                       g_entries;
        std::unordered_map<std::string, SCamera> g_cameras;
        bool g_sameSession = false;
        uint64_t g_nextGroup = 1;

        std::string session() {
            const char* value = std::getenv("HYPRLAND_INSTANCE_SIGNATURE");
            return value ? value : "";
        }

        void restoreGroup(uint64_t id) {
            if (!id || !ScrollOverview::Config::getCanvasGroups())
                return;
            CanvasGroups::Members members;
            for (const auto& entry : g_entries) {
                if (entry.group != id || !entry.window)
                    continue;
                for (const auto& w : Desktop::windowState()->windows())
                    if (w && w->m_stableID == entry.window && CanvasGroups::eligible(w))
                        members.emplace_back(w);
            }
            if (members.size() < 2)
                return;
            // A later-starting member extends its restored group. Never compact
            // or move windows when restoring associations.
            for (auto& group : CanvasGroups::groups) {
                if (std::ranges::any_of(members, [&](const auto& ref) { return CanvasGroups::contains(group, ref.lock()); })) {
                    for (const auto& ref : members)
                        if (!CanvasGroups::contains(group, ref.lock()))
                            group.push_back(ref);
                    return;
                }
            }
            CanvasGroups::groups.push_back(members);
        }

        // Hand-edited or damaged files must never feed NaN, infinity or
        // absurd sizes into window geometry or the camera.
        bool sane(double value, double limit) {
            return std::isfinite(value) && std::abs(value) <= limit;
        }

        bool saneBox(const CBox& box) {
            return sane(box.x, 1e6) && sane(box.y, 1e6) && sane(box.width, 16384) && sane(box.height, 16384) && box.width >= 1 && box.height >= 1;
        }

        std::string clean(std::string value) {
            std::ranges::replace(value, '\t', ' ');
            std::ranges::replace(value, '\n', ' ');
            std::ranges::replace(value, '\r', ' ');
            return value;
        }

        void load() {
            if (g_loaded)
                return;
            g_loaded = true;

            std::ifstream in{path()};
            std::string   line;
            while (in && std::getline(in, line)) {
                std::vector<std::string> fields;
                std::string              field;
                std::istringstream       stream{line};
                while (std::getline(stream, field, '\t'))
                    fields.push_back(field);
                try {
                    if (fields.size() == 2 && fields[0] == "session") {
                        g_sameSession = !session().empty() && fields[1] == session();
                    } else if ((fields.size() == 4 || fields.size() == 9) && fields[0] == "camera") {
                        SCamera camera{.offset = {std::stod(fields[2]), std::stod(fields[3])}};
                        camera.returnOffset = camera.offset;
                        if (fields.size() == 9) {
                            camera.zoom = std::stof(fields[4]);
                            camera.navigating = fields[5] == "1";
                            camera.returnOffset = {std::stod(fields[6]), std::stod(fields[7])};
                            camera.returnZoom = std::stof(fields[8]);
                        }
                        if (sane(camera.offset.x, 1e6) && sane(camera.offset.y, 1e6) && sane(camera.returnOffset.x, 1e6) && sane(camera.returnOffset.y, 1e6) &&
                            sane(camera.zoom, 100) && camera.zoom >= .01F && sane(camera.returnZoom, 100) && camera.returnZoom >= .01F)
                            g_cameras[fields[1]] = camera;
                    } else if ((fields.size() == 8 || fields.size() == 10) && fields[0] == "window" && g_entries.size() < MAX_ENTRIES) {
                        const CBox BOX{std::stod(fields[3]), std::stod(fields[4]), std::stod(fields[5]), std::stod(fields[6])};
                        if (saneBox(BOX)) {
                            SEntry entry{.klass = fields[1], .title = fields[2], .box = BOX, .seen = std::stoll(fields[7])};
                            if (fields.size() == 10) {
                                entry.savedWindow = g_sameSession ? std::stoull(fields[8]) : 0;
                                entry.group = std::stoull(fields[9]);
                                if (entry.group > 1000000000ULL) entry.group = 0;
                            }
                            g_nextGroup = std::max(g_nextGroup, entry.group + 1);
                            g_entries.push_back(entry);
                        }
                    }
                } catch (...) {
                    // A damaged line only costs that one window its memory.
                }
            }
        }
    }

    std::string path() {
        std::filesystem::path base;
        if (const char* state = std::getenv("XDG_STATE_HOME"); state && *state)
            base = state;
        else
            base = std::filesystem::path{std::getenv("HOME") ? std::getenv("HOME") : "/tmp"} / ".local" / "state";
        return (base / "spatial-overview" / "canvas-memory.tsv").string();
    }

    std::optional<CBox> claim(const PHLWINDOW& window, bool restoring) {
        if (!window)
            return std::nullopt;
        load();

        const auto KLASS = clean(window->m_class.empty() ? window->m_initialClass : window->m_class);
        const auto TITLE = clean(Navigator::displayTitle(window));
        if (KLASS.empty())
            return std::nullopt;

        SEntry* best = nullptr;
        if (g_sameSession)
            for (auto& entry : g_entries)
                if (!entry.window && entry.savedWindow == window->m_stableID) {
                    best = &entry;
                    break;
                }
        const bool identityMatch = best != nullptr;
        for (auto& entry : g_entries) {
            if (identityMatch)
                break;
            // Never steal the placement of another live window in this session.
            if (g_sameSession && entry.savedWindow && std::ranges::any_of(Desktop::windowState()->windows(), [&](const auto& w) {
                    return w && w->m_isMapped && w->m_stableID == entry.savedWindow;
                }))
                continue;
            if (entry.window || entry.klass != KLASS)
                continue;
            if (entry.title == TITLE && (!best || best->title != TITLE || entry.seen > best->seen))
                best = &entry;
            else if (restoring && (!best || (best->title != TITLE && entry.seen > best->seen)))
                best = &entry;
        }
        if (!best)
            return std::nullopt;

        if (!restoring && !identityMatch) {
            // Outside a restore, only a lone app returning to its own spot:
            // a second terminal belongs next to you, not in the first one's
            // old place.
            if (best->title != TITLE)
                return std::nullopt;
            const auto& WINDOWS = Desktop::windowState()->windows();
            const bool  SIBLING = std::ranges::any_of(WINDOWS, [&](const PHLWINDOW& other) {
                return other && other != window && other->m_isMapped && clean(other->m_class) == KLASS;
            });
            if (SIBLING)
                return std::nullopt;
        }

        // Across logins, restore group membership only for an unambiguous
        // app/title match. Stable IDs are meaningful only within one compositor.
        if (!identityMatch && best->group) {
            const auto matches = [&](const auto& entry) { return entry.klass == KLASS && entry.title == TITLE; };
            const auto liveMatches = std::ranges::count_if(Desktop::windowState()->windows(), [&](const auto& w) {
                return w && w->m_isMapped && clean(w->m_class.empty() ? w->m_initialClass : w->m_class) == KLASS && clean(Navigator::displayTitle(w)) == TITLE;
            });
            if (best->title != TITLE || std::ranges::count_if(g_entries, matches) != 1 || liveMatches != 1)
                best->group = 0;
        }
        best->window = window->m_stableID;
        restoreGroup(best->group);
        return best->box;
    }

    std::optional<SCamera> camera(const std::string& monitor) {
        load();
        if (const auto IT = g_cameras.find(monitor); IT != g_cameras.end())
            return IT->second;
        return std::nullopt;
    }

    bool save(const std::vector<SWindowPlacement>& windows, const std::unordered_map<std::string, SCamera>& cameras) {
        load();
        const int64_t NOW = std::time(nullptr);

        CanvasGroups::prune();
        std::unordered_map<uint64_t, uint64_t> memberships;
        std::unordered_set<uint64_t> usedGroups;
        if (ScrollOverview::Config::getCanvasGroups()) {
            for (const auto& group : CanvasGroups::groups) {
                uint64_t id = 0;
                for (const auto& ref : group)
                    if (const auto w = ref.lock())
                        for (const auto& entry : g_entries)
                            if (entry.window == w->m_stableID && entry.group && !usedGroups.contains(entry.group))
                                id = entry.group;
                if (!id) id = g_nextGroup++;
                usedGroups.insert(id);
                for (const auto& ref : group)
                    if (const auto w = ref.lock())
                        memberships[w->m_stableID] = id;
            }
        }
        std::vector<SEntry> next;
        next.reserve(windows.size() + g_entries.size());
        for (const auto& placement : windows) {
            if (!placement.window || !saneBox(placement.box))
                continue;
            const auto KLASS = clean(placement.window->m_class.empty() ? placement.window->m_initialClass : placement.window->m_class);
            if (KLASS.empty())
                continue;
            next.push_back({.klass = KLASS, .title = clean(Navigator::displayTitle(placement.window)), .box = placement.box, .seen = NOW,
                            .window = placement.window->m_stableID, .savedWindow = placement.window->m_stableID, .group = memberships[placement.window->m_stableID]});
        }

        // Entries describing a window that is still open are superseded by
        // the lines above; a window that has closed keeps its last home.
        for (auto entry : g_entries) {
            if (entry.window && std::ranges::any_of(windows, [&entry](const SWindowPlacement& placement) {
                    return placement.window && placement.window->m_stableID == entry.window;
                }))
                continue;
            entry.window = 0;
            const bool DUPLICATE = std::ranges::any_of(next, [&entry](const SEntry& current) {
                return current.klass == entry.klass && current.title == entry.title && current.box == entry.box;
            });
            if (!DUPLICATE)
                next.push_back(entry);
        }

        std::ranges::stable_sort(next, [](const SEntry& a, const SEntry& b) { return a.seen > b.seen; });
        if (next.size() > MAX_ENTRIES)
            next.resize(MAX_ENTRIES);
        g_entries = std::move(next);
        for (const auto& [monitor, camera] : cameras) {
            if (sane(camera.offset.x, 1e6) && sane(camera.offset.y, 1e6))
                g_cameras[monitor] = camera;
        }

        std::error_code error;
        std::filesystem::create_directories(std::filesystem::path{path()}.parent_path(), error);
        const auto    TEMPORARY = path() + ".next";
        std::ofstream out{TEMPORARY, std::ios::trunc};
        if (!out)
            return false;
        out << std::fixed << std::setprecision(6) << "# spatial-overview canvas memory v2\n";
        out << "session\t" << clean(session()) << '\n';
        for (const auto& [monitor, camera] : g_cameras)
            out << "camera\t" << clean(monitor) << '\t' << camera.offset.x << '\t' << camera.offset.y << '\t' << camera.zoom << '\t' << camera.navigating
                << '\t' << camera.returnOffset.x << '\t' << camera.returnOffset.y << '\t' << camera.returnZoom << '\n';
        for (const auto& entry : g_entries)
            out << "window\t" << entry.klass << '\t' << entry.title << '\t' << entry.box.x << '\t' << entry.box.y << '\t' << entry.box.width << '\t' << entry.box.height
                << '\t' << entry.seen << '\t' << entry.savedWindow << '\t' << entry.group << '\n';
        out.close();
        if (!out)
            return false;
        std::filesystem::rename(TEMPORARY, path(), error);
        return !error;
    }
}
