from .gltf_buffer_accessor import GlbBuffer
import math


def translation(t) -> str:
    return f'position [{t[0]:.2f}, {t[1]:.2f}, {t[2]:.2f}]'


def inverseMatrix(m) -> str:
    return f'[{m[12]:.2f}, {m[13]:.2f}, {m[14]:.2f}, {m[15]:.2f}]'


def info(bin: GlbBuffer, gltf: dict, skin_index: int):
    skin = gltf['skins'][skin_index]
    joints = skin['joints']

    matrices_index = skin['inverseBindMatrices']
    matrices = bin.get_accessor(matrices_index)
    if len(matrices) != len(joints):
        raise Exception()

    text = ''
    for i, joint in enumerate(joints):
        # node = gltf['nodes'][joint]
        node = bin.nodes[joint]
        matrix = matrices[i]

        validation = ''
        EPS = 1e-5
        if math.fabs(node.world_position[0] + matrix[12]) > EPS:
            validation += 'X'
        if math.fabs(node.world_position[1] + matrix[13]) > EPS:
            validation += 'Y'
        if math.fabs(node.world_position[2] + matrix[14]) > EPS:
            validation += 'Z'

        text += f'{joint}: {translation(node.world_position)}, {inverseMatrix(matrix)}{validation}\n'
    return text
