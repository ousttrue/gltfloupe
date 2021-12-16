import contextlib
import cydeer as imgui
'''
https://gist.github.com/rmitton/f80cbb028fca4495ab1859a155db4cd8
'''

TOOLBAR_SIZE = 50


def _dockspace(name: str):
    flags = (imgui.ImGuiWindowFlags_.MenuBar
             | imgui.ImGuiWindowFlags_.NoDocking
             | imgui.ImGuiWindowFlags_.NoBackground
             | imgui.ImGuiWindowFlags_.NoTitleBar
             | imgui.ImGuiWindowFlags_.NoCollapse
             | imgui.ImGuiWindowFlags_.NoResize
             | imgui.ImGuiWindowFlags_.NoMove
             | imgui.ImGuiWindowFlags_.NoBringToFrontOnFocus
             | imgui.ImGuiWindowFlags_.NoNavFocus
             )

    viewport = imgui.GetMainViewport()
    x, y = viewport.Pos
    y += TOOLBAR_SIZE
    w, h = viewport.Size
    h -= TOOLBAR_SIZE

    imgui.SetNextWindowPos((x, y))
    imgui.SetNextWindowSize((w, h))
    # imgui.set_next_window_viewport(viewport.id)
    imgui.PushStyleVar(imgui.ImGuiStyleVar_.WindowBorderSize, 0.0)
    imgui.PushStyleVar(imgui.ImGuiStyleVar_.WindowRounding, 0.0)

    # When using ImGuiDockNodeFlags_PassthruCentralNode, DockSpace() will render our background and handle the pass-thru hole, so we ask Begin() to not render a background.
    # local window_flags = self.window_flags
    # if bit.band(self.dockspace_flags, ) ~= 0 then
    #     window_flags = bit.bor(window_flags, const.ImGuiWindowFlags_.NoBackground)
    # end

    # Important: note that we proceed even if Begin() returns false (aka window is collapsed).
    # This is because we want to keep our DockSpace() active. If a DockSpace() is inactive,
    # all active windows docked into it will lose their parent and become undocked.
    # We cannot preserve the docking relationship between an active window and an inactive docking, otherwise
    # any change of dockspace/settings would lead to windows being stuck in limbo and never being visible.
    imgui.PushStyleVar_2(imgui.ImGuiStyleVar_.WindowPadding, (0, 0))
    imgui.Begin(name, None, flags)
    imgui.PopStyleVar()
    imgui.PopStyleVar(2)

    # TODO:
    # Save off menu bar height for later.
    # menubar_height = imgui.internal.get_current_window().menu_bar_height()
    menubar_height = 30

    # DockSpace
    dockspace_id = imgui.GetID(name)
    imgui.DockSpace(dockspace_id, (0, 0),
                    imgui.ImGuiDockNodeFlags_.PassthruCentralNode)

    imgui.End()

    return menubar_height


@contextlib.contextmanager
def dockspace(name: str):
    menubar_height = _dockspace(name)

    # toolbar
    viewport: imgui.ImGuiViewport = imgui.GetMainViewport()
    imgui.SetNextWindowPos((viewport.Pos.x, viewport.Pos.y + menubar_height))
    imgui.SetNextWindowSize((viewport.Size.x, TOOLBAR_SIZE))
    # imgui.SetNextWindowViewport(viewport -> ID);

    window_flags = (0
                    | imgui.ImGuiWindowFlags_.NoDocking
                    | imgui.ImGuiWindowFlags_.NoTitleBar
                    | imgui.ImGuiWindowFlags_.NoResize
                    | imgui.ImGuiWindowFlags_.NoMove
                    | imgui.ImGuiWindowFlags_.NoScrollbar
                    | imgui.ImGuiWindowFlags_.NoSavedSettings
                    )
    imgui.PushStyleVar(imgui.ImGuiStyleVar_.WindowBorderSize, 0)
    imgui.Begin("TOOLBAR", None, window_flags)
    imgui.PopStyleVar()

    yield

    imgui.End()
