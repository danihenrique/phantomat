#pragma once

#include <algorithm>
#include <optional>
#include <vector>
#include <hyprland/src/desktop/view/Window.hpp>
#include <hyprland/src/managers/fullscreen/FullscreenController.hpp>

// Canvas-only groups never touch Hyprland's native tabbed groups. Weak refs
// avoid keeping closed windows alive. State lasts until plugin unload.
namespace SpatialOverview::CanvasGroups {
    using Members = std::vector<PHLWINDOWREF>;
    inline Members              selection;
    inline std::vector<Members> groups;

    inline bool                 eligible(const PHLWINDOW& w) {
        return w && w->m_isMapped && !w->m_pinned && !w->m_group && w->m_isFloating && !Fullscreen::controller()->isFullscreen(w);
    }
    inline bool contains(const Members& set, const PHLWINDOW& w) {
        return std::ranges::any_of(set, [&](const auto& ref) { return ref.lock() == w; });
    }
    inline void prune() {
        const auto dead = [](const auto& ref) {
            const auto w = ref.lock();
            return !w || !w->m_isMapped || w->m_pinned || w->m_group;
        };
        std::erase_if(selection, [](const auto& ref) { return !eligible(ref.lock()); });
        for (auto& group : groups)
            std::erase_if(group, dead);
        std::erase_if(groups, [](const auto& group) { return group.size() < 2; });
    }
    inline Members members(const PHLWINDOW& w) {
        prune();
        for (const auto& group : groups)
            if (contains(group, w))
                return group;
        return {};
    }
    inline void toggle(const PHLWINDOW& w) {
        prune();
        if (!eligible(w))
            return;
        if (contains(selection, w))
            std::erase_if(selection, [&](const auto& ref) { return ref.lock() == w; });
        else
            selection.emplace_back(w);
    }
    // Adding a selected window to an existing group merges the whole group.
    // Use the same member set for layout and membership, without duplicates.
    inline Members groupingMembers() {
        prune();
        Members result = selection;
        for (const auto& group : groups)
            if (std::ranges::any_of(selection, [&](const auto& ref) { return contains(group, ref.lock()); }))
                for (const auto& ref : group)
                    if (!contains(result, ref.lock()))
                        result.push_back(ref);
        return result;
    }
    inline bool create() {
        const auto picked = groupingMembers();
        if (selection.size() < 2 || std::ranges::any_of(picked, [](const auto& ref) { return !eligible(ref.lock()); }))
            return false;
        std::erase_if(groups, [&](const auto& group) {
            return std::ranges::any_of(picked, [&](const auto& ref) { return contains(group, ref.lock()); });
        });
        groups.push_back(picked);
        selection.clear();
        return true;
    }
    inline bool dissolve(const PHLWINDOW& focused) {
        prune();
        const auto old = groups.size();
        std::erase_if(groups, [&](const auto& group) {
            if (selection.empty())
                return contains(group, focused);
            return std::ranges::any_of(selection, [&](const auto& ref) { return contains(group, ref.lock()); });
        });
        selection.clear();
        return groups.size() != old;
    }
    inline std::optional<CBox> bounds(const PHLWINDOW& w) {
        std::optional<CBox> box;
        const auto          group = members(w);
        if (std::ranges::any_of(group, [](const auto& ref) { return !eligible(ref.lock()); }))
            return std::nullopt; // fullscreen suspends group framing without destroying membership
        for (const auto& ref : group) {
            const auto member = ref.lock();
            if (!member)
                continue;
            const auto b = member->geometricBox(Desktop::View::IGeometric::GEOMETRIC_CURRENT);
            if (!box)
                box = b;
            else {
                const double x = std::min(box->x, b.x), y = std::min(box->y, b.y);
                const double r = std::max(box->x + box->width, b.x + b.width), bottom = std::max(box->y + box->height, b.y + b.height);
                box = CBox{x, y, r - x, bottom - y};
            }
        }
        return box;
    }
    inline void clear() {
        selection.clear();
        groups.clear();
    }
}
