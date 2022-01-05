import logging

logger = logging.getLogger(__name__)


def run():
    logging.basicConfig(level=logging.DEBUG)

    from . import config
    ini, window_config = config.load()

    logger.debug(f'{window_config}')

    from .gui.gui import GUI
    controller = GUI(ini)
    import sys
    if len(sys.argv) > 1:
        import pathlib
        controller.open(pathlib.Path(sys.argv[1]))

    import glglue.glfw
    loop = glglue.glfw.LoopManager(controller,
                                   title='glfw loupe',
                                   config=window_config)

    def close():
        import glfw
        glfw.set_window_should_close(loop.window, True)
    controller.close_callback = close

    lastCount = 0
    while True:
        count = loop.begin_frame()
        if not count:
            window_config = loop.get_config()
            break
        d = count - lastCount
        lastCount = count
        if d > 0:
            controller.onUpdate(d)
            controller.draw()
            loop.end_frame()

    ini = controller.save_ini()
    config.save(ini, window_config)  # type: ignore
