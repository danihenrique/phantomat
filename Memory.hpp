#pragma once

#include "globals.hpp"

#include <hyprland/src/desktop/DesktopTypes.hpp>
#include <hyprland/src/helpers/math/Math.hpp>

#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

// Where windows live on the canvas, remembered across restarts. Entries are
// keyed by compositor session/stable ID, with app/title fallback after login.
// A closed window keeps its entry so it can come home when opened again.
namespace SpatialOverview::Memory {

    struct SWindowPlacement {
        PHLWINDOW window;
        CBox      box;
    };

    struct SCamera {
        Vector2D offset;
        float zoom = 1.F;
        bool navigating = false;
        Vector2D returnOffset;
        float returnZoom = 1.F;
    };

    // restoring: true while a fresh canvas is being populated (login, first
    // open). Then any window of a remembered app may take that app's most
    // recent free spot; afterwards only an exact title match of an app with
    // no other open window comes home.
    std::optional<CBox>     claim(const PHLWINDOW& window, bool restoring);
    std::optional<SCamera> camera(const std::string& monitor);
    bool                    save(const std::vector<SWindowPlacement>& windows, const std::unordered_map<std::string, SCamera>& cameras);
    std::string             path();
}
