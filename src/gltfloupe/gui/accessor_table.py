from typing import Optional
from gltfio import GltfData
from ..gltf_loader import GltfLoader
import imgui
from ..jsonutil import get_value


class AccessorTable:
    def __init__(self) -> None:
        self.data = None
        self.key = None
        self.view = None

    def draw(self):
        imgui.text_unformatted(str(self.key))
        if not self.view:
            return

        flags = (
            imgui.TABLE_BORDERS_VERTICAL
            | imgui.TABLE_BORDERS_OUTER_HORIZONTAL
            | imgui.TABLE_RESIZABLE
            | imgui.TABLE_ROW_BACKGROUND
            | imgui.TABLE_NO_BORDERS_IN_BODY
        )
        if imgui.begin_table("jsontree_table", self.view.element_count+1, flags):
            # header
            # imgui.TableSetupScrollFreeze(0, 1); // Make top row always visible
            imgui.table_setup_column('index')
            for i in range(self.view.element_count):
                imgui.table_setup_column(f'{i}')
            imgui.table_headers_row()

            # body
            # imgui._ImGuiListClipper clipper;

            it = iter(self.view.scalar_view)
            i = 0
            count = self.view.get_count()
            while i < count:
                imgui.table_next_row()
                # index
                imgui.table_next_column()
                imgui.text_unformatted(f'{i:05}')
                #
                for j in range(self.view.element_count):
                    imgui.table_next_column()
                    imgui.text_unformatted(f'{next(it):.3f}')
                i += 1

            imgui.end_table()

    def set(self, data: Optional[GltfData], key: tuple, loader: Optional[GltfLoader]):
        if self.data == data and self.key == key:
            return

        if data and loader:
            accessor_index = None
            match key:
                case ('meshes', mesh_index, 'primitives', prim_index, 'indices'):
                    accessor_index = get_value(data.gltf, key)

                case ('meshes', mesh_index, 'primitives', prim_index, 'attributes', attribute):
                    accessor_index = get_value(data.gltf, key)

                case ('skins', skin_index, 'inverseBindMatrices'):
                    accessor_index = get_value(data.gltf, key)

                case ('accessors', accessor_index):
                    pass

                case _:
                    return

            self.data = data
            self.key = key
            self.view = data.buffer_reader.read_accessor(accessor_index)
