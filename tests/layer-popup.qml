import QtQuick
import Quickshell
import Quickshell.Io
ShellRoot {
  id: root
  property int clicks: 0
  property int wheelDelta: 0
  IpcHandler {
    target: "test"
    function clicks(): int { return root.clicks }
    function wheelDelta(): int { return root.wheelDelta }
  }
  PanelWindow {
    id: bar
    anchors { top: true; left: true; right: true }
    implicitHeight: 30
    color: "#00ffff"
    Rectangle { id: button; x: 100; width: 30; height: 30; color: "white" }
    PopupWindow {
      visible: true
      anchor.window: bar
      anchor.rect.x: 100
      anchor.rect.y: 40
      implicitWidth: 160
      implicitHeight: 120
      color: "#ff00ff"
      MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: root.clicks++
        onWheel: event => { root.wheelDelta += event.angleDelta.y; event.accepted = true }
      }
    }
  }
}
