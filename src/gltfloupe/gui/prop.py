from typing import Optional
import json
import imgui
from gltfio.parser import GltfData
from ..gltf_loader import GltfLoader


def get_value(json, key):
    current = json
    for k in key:
        match current:
            case list():
                current = current[int(k)]
            case dict():
                current = current[k]
            case _:
                raise RuntimeError()
    return current


class Prop:
    def __init__(self) -> None:
        self.data: Optional[GltfData] = None
        self.key = ()
        self.value = ''

    def set(self, data: Optional[GltfData], key: tuple, loader: Optional[GltfLoader]):
        if self.data == data and self.key == key:
            return
        self.data = data
        self.key = key

        if self.data and loader:
            match self.key:
                case ('skins', skin_index):
                    from .. import skin_debug
                    self.value = skin_debug.get_debug_info(
                        self.data, int(skin_index), loader)
                case _:
                    value = get_value(self.data.gltf, self.key)
                    self.value = json.dumps(value, indent=2)

    def draw(self):
        if not self.data:
            imgui.text('not gltf')
            return

        imgui.text_unformatted(
            f'{self.key}')

        imgui.text_unformatted(self.value)
