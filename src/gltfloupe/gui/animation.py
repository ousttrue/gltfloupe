from typing import Optional
import ctypes
import pydear as ImGui


class Playback:
    def __init__(self) -> None:
        self.time = 0.0
        self.pos = (ctypes.c_float * 1)()

    def draw(self, p_open: ctypes.Array):
        if ImGui.Begin('playback', p_open):
            # ImGui.TextUnformatted(f'{self.pos[0]} / {self.time}')
            ImGui.SliderFloat('pos', self.pos, 0.0, self.time)
        ImGui.End()
