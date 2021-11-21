from OpenGL.GL import *
import ctypes


class Node:
    def __init__(self, node: dict) -> None:
        self.name = node.get('name', '')
        self.local_position = node.get('translation', [0, 0, 0])
        self.world_position = self.local_position
        self.children = []
        self.parent = None

    def add_child(self, child: 'Node'):
        child.parent = self
        self.children.append(child)

    def update_world_position(self, parent_position, level=0):
        self.world_position = [
            parent_position[0] + self.local_position[0],
            parent_position[1] + self.local_position[1],
            parent_position[2] + self.local_position[2]
        ]
        indent = '  ' * level
        print(
            f'{indent}{self.name}: [{self.world_position[0]:.2f}, {self.world_position[1]:.2f}, {self.world_position[2]:.2f}]'
        )

        for child in self.children:
            child.update_world_position(self.world_position, level + 1)


class GlbBuffer:
    def __init__(self, gltf: dict, bin: bytes):
        self.gltf = gltf
        self.bin = bytearray(bin)
        self.nodes = []
        for gltf_node in gltf['nodes']:
            self.nodes.append(Node(gltf_node))
        # build tree
        for i, gltf_node in enumerate(gltf['nodes']):
            node = self.nodes[i]
            for j in gltf_node.get('children', []):
                node.add_child(self.nodes[j])

        for node in self.nodes:
            if not node.parent:
                node.update_world_position([0, 0, 0])

    def get_accessor(self, index: int):
        accessor = self.gltf['accessors'][index]
        bufferView_index = accessor['bufferView']
        bufferView = self.gltf['bufferViews'][bufferView_index]
        buffer_index = bufferView['buffer']
        buffer = self.gltf['buffers'][buffer_index]
        if buffer['byteLength'] != len(self.bin):
            raise Exception()
        byteOffset = bufferView['byteOffset']
        byteLength = bufferView['byteLength']
        bufferView_bytes = self.bin[byteOffset:byteOffset + byteLength]

        if accessor['componentType'] == GL_FLOAT and accessor['type'] == 'MAT4':
            # float16
            array_type = (ctypes.c_float * 16 * accessor['count'])
            accessor_byteOffset = accessor.get('byteOffset', 0)
            buffer = array_type.from_buffer(bufferView_bytes,
                                            accessor_byteOffset)
            return buffer
        else:
            raise NotImplementedError()
