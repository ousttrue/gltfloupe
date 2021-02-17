from .gltf_buffer_accessor import GlbBuffer


def translation(node: dict) -> str:
    t = node.get('translation', [0, 0, 0])
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
        node = gltf['nodes'][joint]
        matrix = matrices[i]
        text += f'{joint}: {translation(node)}, {inverseMatrix(matrix)}\n'
    return text
