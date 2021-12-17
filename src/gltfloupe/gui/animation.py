from typing import Optional
import ctypes
import cydeer as ImGui


class Playback:
    def __init__(self) -> None:
        self.time = 0.0
        self.pos = (ctypes.c_float * 1)()

    def draw(self) -> Optional[tuple]:
        # ImGui.TextUnformatted(f'{self.pos[0]} / {self.time}')
        ImGui.SliderFloat('pos', self.pos, 0.0, self.time)
