import math
from typing import Tuple
from gltfio.types import GltfNode
from gltfio.parser import GltfData
from .gltf_loader import GltfLoader


def tuple_3f(x, y, z):
    return f'({x:.3f}, {y:.3f}, {z:.3f})'


def get_debug_info(data: GltfData, skin_index: int, loader: GltfLoader):
    skin = data.gltf['skins'][skin_index]
    joints = skin['joints']

    matrices_index = skin['inverseBindMatrices']
    matrices = data.buffer_reader.read_accessor(matrices_index)
    if matrices.get_count() != len(joints):
        raise Exception()

    text = ''
    for i, joint in enumerate(joints):
        matrix = matrices.get_item(i)

        node = loader.nodes[joint]
        world = node.world_matrix
        mp = (matrix[12], matrix[13], matrix[14])
        wp = (world._41, world._42, world._43)

        validation = ''
        EPS = 1e-5
        if math.fabs(mp[0] + wp[0]) > EPS:
            validation += 'X'
        if math.fabs(mp[1] + wp[1]) > EPS:
            validation += 'Y'
        if math.fabs(mp[2] + wp[2]) > EPS:
            validation += 'Z'

        text += f'[{joint}:{node.name}] {tuple_3f(*mp)}, {tuple_3f(*wp)}{validation}\n'
    return text
