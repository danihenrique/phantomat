import QtQuick
import Quickshell
FloatingWindow { visible: true; width: 900; height: 600; title: "Scroll probe"; color: "#283040"
MouseArea { anchors.fill: parent; onWheel: event => console.log("SCROLL", event.pixelDelta.x, event.pixelDelta.y, event.phase) }
Text { anchors.centerIn: parent; text: "Isolated scroll test"; color: "white" }
}
