#pragma once
#include <hyprutils/math/Box.hpp>
#include <algorithm>
#include <vector>

namespace SpatialOverview::Placement {
using Hyprutils::Math::CBox;
using Hyprutils::Math::Vector2D;

// Prefer free space in the current viewport. Once it is full, grow a row
// to the right of the most visible window (rightmost window if none is visible).
inline CBox nearView(const CBox& view, const Vector2D& size, const std::vector<CBox>& boxes, double gap) {
    const auto area = [](const CBox& a, const CBox& b) {
        return std::max(0.0, std::min(a.x + a.width, b.x + b.width) - std::max(a.x, b.x)) *
               std::max(0.0, std::min(a.y + a.height, b.y + b.height) - std::max(a.y, b.y));
    };
    const auto clear = [&](const CBox& c) {
        return std::ranges::none_of(boxes, [&](CBox b) { b.expand(gap); return area(c, b) > 0.01; });
    };
    const CBox* anchor = nullptr;
    double visible = -1;
    for (const auto& b : boxes) {
        const double a = area(b, view);
        if (!anchor || a > visible || (a == visible && b.x + b.width > anchor->x + anchor->width)) {
            anchor = &b;
            visible = a;
        }
    }
    const Vector2D center = view.middle() - size / 2.0;
    std::vector<Vector2D> candidates;
    if (anchor) candidates.push_back({anchor->x + anchor->width + gap, anchor->y});
    candidates.push_back(center);
    std::vector<double> xs{view.x, view.x + view.width - size.x, center.x};
    std::vector<double> ys{view.y, view.y + view.height - size.y, center.y};
    for (const auto& b : boxes) {
        if (area(b, view) <= 0) continue;
        xs.insert(xs.end(), {b.x + b.width + gap, b.x - size.x - gap});
        ys.insert(ys.end(), {b.y, b.y + b.height + gap, b.y - size.y - gap});
    }
    for (double x : xs) for (double y : ys) candidates.push_back({x, y});
    CBox best{center, size};
    double bestArea = 0, bestDistance = 0;
    for (const auto& pos : candidates) {
        const CBox c{pos, size};
        if (!clear(c)) continue;
        const double a = area(c, view);
        const double dx = pos.x - center.x, dy = pos.y - center.y;
        const double distance = dx * dx + dy * dy;
        if (a > bestArea || (a > 0 && a == bestArea && distance < bestDistance)) {
            best = c; bestArea = a; bestDistance = distance;
        }
    }
    if (bestArea > 0) return best;
    CBox result{anchor ? Vector2D{anchor->x + anchor->width + gap, anchor->y} : center, size};
    // Every collision advances past an occupied right edge, so this terminates
    // without an arbitrary ring limit or an overlapping last-resort position.
    for (size_t pass = 0; pass <= boxes.size(); ++pass) {
        bool moved = false;
        for (auto b : boxes) {
            b.expand(gap);
            if (area(result, b) > 0.01) { result.x = b.x + b.width; moved = true; }
        }
        if (!moved) break;
    }
    return result;
}
}
