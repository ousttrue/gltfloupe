import imgui
import json


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
        self.root = {}
        self.key = ()
        self.value = ''

    def set(self, root: dict, key: tuple):
        if self.root == root and self.key == key:
            return
        self.root = root
        self.key = key
        value = get_value(self.root, self.key)
        self.value = json.dumps(value, indent=2)

    def draw(self):
        if not self.root:
            imgui.text('not selected')
            return

        imgui.text_unformatted(
            f'{self.key}')

        imgui.text_unformatted(self.value)
