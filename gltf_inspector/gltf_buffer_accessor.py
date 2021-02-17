from OpenGL.GL import *
import ctypes


class GlbBuffer:
    def __init__(self, gltf: dict, bin: bytes):
        self.gltf = gltf
        self.bin = bytearray(bin)

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
