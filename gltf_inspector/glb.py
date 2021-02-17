import struct
from typing import Tuple


class Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def read_str(self, size):
        result = self.data[self.pos:self.pos + size]
        self.pos += size
        return result.strip()

    def read(self, size):
        result = self.data[self.pos:self.pos + size]
        self.pos += size
        return result

    def read_uint(self):
        result = struct.unpack('I', self.data[self.pos:self.pos + 4])[0]
        self.pos += 4
        return result


def parse_glb(data: bytes) -> Tuple[bytes, bytes]:
    reader = Reader(data)
    magic = reader.read_str(4)
    if magic != b'glTF':
        raise Exception(f'magic not found: #{magic}')

    version = reader.read_uint()
    if version != 2:
        raise Exception(f'version:#{version} is not 2')

    size = reader.read_uint()
    size -= 12

    glb_json = None
    glb_bin = None
    while size > 0:
        #print(size)

        chunk_size = reader.read_uint()
        size -= 4

        chunk_type = reader.read_str(4)
        size -= 4

        chunk_data = reader.read(chunk_size)
        size -= chunk_size

        if chunk_type == b'BIN\x00':
            glb_bin = chunk_data
        elif chunk_type == b'JSON':
            glb_json = chunk_data
        else:
            raise Exception(f'unknown chunk_type: {chunk_type}')

    if not glb_json:
        raise Exception('no json')
    if not glb_bin:
        raise Exception('no bin')

    return glb_json, glb_bin
