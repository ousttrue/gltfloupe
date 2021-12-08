from typing import Optional
import json
import io
import imgui
from gltfio.parser import GltfData
from ..gltf_loader import GltfLoader
from ..jsonutil import get_value, to_pretty

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
            value = get_value(self.data.gltf, self.key)
            self.value = to_pretty(value) + '\n'
            match self.key:
                case ('nodes', node_index, 'skin'):
                    self.value += node_debug(self.data, node_index, loader)
                case ('skins', skin_index):
                    from .. import skin_debug
                    self.value += skin_debug.get_debug_info(
                        self.data, skin_index, loader)

    def draw(self):
        if not self.data:
            imgui.text('not gltf')
            return

        imgui.text_unformatted(
            f'{self.key}')

        imgui.text_unformatted(self.value)
