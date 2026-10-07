#include "../CanvasPlacement.hpp"
#include <cassert>
#include <iostream>
using namespace SpatialOverview::Placement;
int main() {
    const CBox view{0, 0, 1000, 600};
    auto p = nearView(view, {300, 200}, {}, 40);
    assert(p.x >= 0 && p.x + p.width <= 1000 && p.y >= 0 && p.y + p.height <= 600);
    std::vector<CBox> boxes{{0, 0, 1000, 600}};
    p = nearView(view, {300, 200}, boxes, 40);
    assert(p.x == 1040 && p.y == 0); // full viewport extends right, never down
    boxes.push_back({1040, 0, 600, 600});
    p = nearView(view, {300, 200}, boxes, 40);
    assert(p.x == 1680 && p.y == 0);
    boxes = {{-9000, -8000, 300, 200}, {0, 0, 400, 600}};
    p = nearView(view, {300, 200}, boxes, 40);
    assert(p.x >= 440 && p.x + p.width <= 1000 && p.y >= 0 && p.y + p.height <= 600);
    // Arbitrarily long rows still have a collision-free fallback.
    boxes.clear(); for (int i=0; i<80; ++i) boxes.push_back({i*1040.0, 0, 1000, 600});
    p = nearView(view, {300, 200}, boxes, 40);
    assert(p.x == 80*1040 && p.y == 0);
    // Negative canvas coordinates and non-integral zoom-sized viewports.
    p = nearView({-5000,-6000,2524,2840}, {800,600}, {},40);
    assert(p.x >= -5000 && p.x + p.width <= -2476 && p.y >= -6000 && p.y + p.height <= -3160);
    std::cout << "PASS: empty, visible gap, full viewport, blockers, long rows, negative camera\n";
}
