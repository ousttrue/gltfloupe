import contextlib
import imgui
'''
https://gist.github.com/rmitton/f80cbb028fca4495ab1859a155db4cd8
'''

TOOLBAR_SIZE = 50


def _dockspace(name: str):
    flags = (imgui.WINDOW_MENU_BAR
             | imgui.WINDOW_NO_DOCKING
             | imgui.WINDOW_NO_BACKGROUND
             | imgui.WINDOW_NO_TITLE_BAR
             | imgui.WINDOW_NO_COLLAPSE
             | imgui.WINDOW_NO_RESIZE
             | imgui.WINDOW_NO_MOVE
             | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
             | imgui.WINDOW_NO_NAV_FOCUS
             )

    viewport = imgui.get_main_viewport()
    x, y = viewport.pos
    y += TOOLBAR_SIZE
    w, h = viewport.size
    h -= TOOLBAR_SIZE

    imgui.set_next_window_position(x, y)
    imgui.set_next_window_size(w, h)
    # imgui.set_next_window_viewport(viewport.id)
    imgui.push_style_var(imgui.STYLE_WINDOW_BORDERSIZE, 0.0)
    imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 0.0)

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
    imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, (0, 0))
    imgui.begin(name, None, flags)
    imgui.pop_style_var()
    imgui.pop_style_var(2)

    # Save off menu bar height for later.
    menubar_height = imgui.internal.get_current_window().menu_bar_height()

    # DockSpace
    dockspace_id = imgui.get_id(name)
    imgui.dockspace(dockspace_id, (0, 0), imgui.DOCKNODE_PASSTHRU_CENTRAL_NODE)

    imgui.end()

    return menubar_height


@contextlib.contextmanager
def dockspace(name: str):
    menubar_height = _dockspace(name)

    # toolbar
    viewport: imgui._ImGuiViewport = imgui.get_main_viewport()
    imgui.set_next_window_position(
        viewport.pos.x, viewport.pos.y + menubar_height)
    imgui.set_next_window_size(viewport.size.x, TOOLBAR_SIZE)
    # imgui.SetNextWindowViewport(viewport -> ID);

    window_flags = (0
                    | imgui.WINDOW_NO_DOCKING
                    | imgui.WINDOW_NO_TITLE_BAR
                    | imgui.WINDOW_NO_RESIZE
                    | imgui.WINDOW_NO_MOVE
                    | imgui.WINDOW_NO_SCROLLBAR
                    | imgui.WINDOW_NO_SAVED_SETTINGS
                    )
    imgui.push_style_var(imgui.STYLE_WINDOW_BORDERSIZE, 0)
    imgui.begin("TOOLBAR", None, window_flags)
    imgui.pop_style_var()

    yield

    imgui.end()
