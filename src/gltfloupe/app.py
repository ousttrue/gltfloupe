import sys
import pathlib
import logging

logger = logging.getLogger(__name__)


def run():
    logging.basicConfig(level=logging.DEBUG)

    from . import config
    ini, window_status = config.load()

    logger.debug(f'{window_status}')

    from .gui.gui import GUI
    controller = GUI(ini)
    if len(sys.argv) > 1:
        controller.open(pathlib.Path(sys.argv[1]))

    import glglue.glfw
    loop = glglue.glfw.LoopManager(controller,
                                   title='glfw loupe',
                                   width=window_status.width if window_status else 1280,
                                   height=window_status.height if window_status else 720,
                                   is_maximized=window_status.is_maximized if window_status else False)

    def close():
        import glfw
        glfw.set_window_should_close(loop.window, True)
    controller.close_callback = close

    lastCount = 0
    while True:
        count = loop.begin_frame()
        if not count:
            window_status = loop.get_status()
            break
        d = count - lastCount
        lastCount = count
        if d > 0:
            controller.onUpdate(d)
            controller.draw()
            loop.end_frame()

    ini = controller.save_ini()
    config.save(ini.decode('utf-8'), window_status)  # type: ignore
