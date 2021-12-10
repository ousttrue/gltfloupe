from typing import Optional
from gltfio import GltfData
from gltfio.types import GltfAccessorSlice
import imgui
from ..jsonutil import get_value


def get_accessor(data: GltfData, keys: tuple) -> Optional[int]:
    match keys:
        case ('meshes', mesh_index, 'primitives', prim_index, 'indices'):
            return get_value(data.gltf, keys)

        case ('meshes', mesh_index, 'primitives', prim_index, 'attributes', attribute):
            return get_value(data.gltf, keys)

        case ('skins', skin_index, 'inverseBindMatrices'):
            return get_value(data.gltf, keys)

        case ('accessors', accessor_index):
            return accessor_index


class AccessorTable:
    def __init__(self, keys: tuple, view: GltfAccessorSlice) -> None:
        self.key = keys
        self.view = view

    def draw(self):
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
