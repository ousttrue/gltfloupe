import math
from typing import Tuple
import glglue.gltf


def translation(t) -> str:
    return f'position [{t[0]:.2f}, {t[1]:.2f}, {t[2]:.2f}]'


def inverseMatrix(m) -> str:
    return f'[{m[12]:.2f}, {m[13]:.2f}, {m[14]:.2f}, {m[15]:.2f}]'


def get_world_position(data: glglue.gltf.GltfData, node: glglue.gltf.GltfNode) -> Tuple[float, float, float]:
    # TODO:
    return 0, 0, 0


def info(data: glglue.gltf.GltfData, skin_index: int):
    skin = data.gltf['skins'][skin_index]
    joints = skin['joints']

    matrices_index = skin['inverseBindMatrices']
    matrices = data.buffer_reader.read_accessor(matrices_index)
    if matrices.get_count() != len(joints):
        raise Exception()

    text = ''
    for i, joint in enumerate(joints):
        # node = gltf['nodes'][joint]
        node = data.nodes[joint]
        matrix = matrices.get_item(i)

        validation = ''
        EPS = 1e-5
        world_position = get_world_position(data, node)
        if math.fabs(world_position[0] + matrix[12]) > EPS:
            validation += 'X'
        if math.fabs(world_position[1] + matrix[13]) > EPS:
            validation += 'Y'
        if math.fabs(world_position[2] + matrix[14]) > EPS:
            validation += 'Z'

        text += f'{joint}: {translation(world_position)}, {inverseMatrix(matrix)}{validation}\n'
    return text
