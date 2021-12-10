import logging
from typing import Optional, List, NamedTuple, Union
import dataclasses
import json
import io
import imgui
from gltfio.parser import GltfData
from ..gltf_loader import GltfLoader
from ..jsonutil import get_value, to_pretty
from .accessor_table import AccessorTable, get_accessor


logger = logging.getLogger(__name__)


def node_debug(data: GltfData, node_index, loader: GltfLoader) -> str:
    node = data.nodes[node_index]

    if node.mesh and node.skin:
        used_joints = set()
        for i, prim in enumerate(node.mesh.primitives):
            if not prim.weights:
                raise RuntimeError()
            if not prim.joints:
                raise RuntimeError()
            for w4, j4 in zip(prim.weights, prim.joints):
                for k in range(4):
                    if w4[k] > 0:
                        used_joints.add(j4[k])

        w = io.StringIO()
        if node.skin.inverse_bind_matrices:
            for i, m in enumerate(node.skin.inverse_bind_matrices):
                if i in used_joints:
                    w.write(f'[{i}]{data.nodes[i].name}: ')
                    w.write(f'({m[12]:.3f}, {m[13]:.3f}. {m[14]:.3f})')
                    scene_node = loader.nodes[node.skin.joints[i].index]
                    wm = scene_node.world_matrix
                    w.write(f', ({wm._41:.3f}, {wm._42:.3f}. {wm._43:.3f})')
                    w.write('\n')

        return w.getvalue()

    else:
        return json.dumps(node, indent=2)


class TextContent(NamedTuple):
    content: str

    def draw(self):
        imgui.text_unformatted(self.content)


class JumpContent(NamedTuple):
    keys: tuple

    def draw(self):
        if imgui.button(str(self.keys)):
            return self.keys


@dataclasses.dataclass
class Item:
    name: str
    content: Union[TextContent, JumpContent, AccessorTable]
    visible = True

    def draw(self):
        imgui.set_next_item_open(True, imgui.ONCE)
        expanded, self.visible = imgui.collapsing_header(
            self.name, self.visible)
        if expanded:
            return self.content.draw()


class Prop:
    def __init__(self) -> None:
        self.data: Optional[GltfData] = None
        self.key = ()
        self.contents: List[Item] = []

    def set(self, data: Optional[GltfData], key: tuple, loader: Optional[GltfLoader]):
        if self.data == data and self.key == key:
            return

        self.data = data
        self.key = key
        self.contents.clear()

        if self.data and loader:
            value = get_value(self.data.gltf, self.key)
            self.contents.append(Item('json', TextContent(to_pretty(value))))

            match self.key:
                case ('nodes', node_index):
                    node = self.data.nodes[node_index]
                    if node.mesh:
                        self.contents.append(
                            Item('ref to', JumpContent(('meshes', node.mesh.index))))
                    if node.skin:
                        self.contents.append(
                            Item('ref to', JumpContent(('skins', node.skin.index))))

                case ('nodes', node_index, 'skin'):
                    self.contents.append(Item('node_debug', TextContent(node_debug(
                        self.data, node_index, loader))))

                case ('skins', skin_index):
                    # ref from
                    for node in self.data.nodes:
                        if node.skin and node.skin.index == skin_index:
                            self.contents.append(
                                Item('ref from', JumpContent(('nodes', node.index))))

                    from .. import skin_debug
                    self.contents.append(Item('skin_debug', TextContent(skin_debug.get_debug_info(
                        self.data, skin_index, loader))))

            match get_accessor(self.data, key):
                case int() as accessor_index:
                    accessor = self.data.buffer_reader.read_accessor(
                        accessor_index)
                    self.contents.append(
                        Item('accessor', AccessorTable(key, accessor)))

    def draw(self) -> Optional[tuple]:
        '''
        return selected keys
        '''
        if not self.data:
            imgui.text('not gltf')
            return

        imgui.text_unformatted(str(self.key))

        selected = None
        for item in self.contents:
            current = item.draw()
            if current:
                selected = current

        return selected
