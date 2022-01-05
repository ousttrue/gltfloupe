from typing import Optional
from gltfio import GltfData
from gltfio.types import GltfAccessorSlice
import pydear as imgui
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
            imgui.ImGuiTableFlags_.BordersV
            | imgui.ImGuiTableFlags_.BordersOuterH
            | imgui.ImGuiTableFlags_.Resizable
            | imgui.ImGuiTableFlags_.RowBg
            | imgui.ImGuiTableFlags_.NoBordersInBody
        )
        if imgui.BeginTable("jsontree_table", self.view.element_count+1, flags):
            # header
            # imgui.TableSetupScrollFreeze(0, 1); // Make top row always visible
            imgui.TableSetupColumn('index')
            for i in range(self.view.element_count):
                imgui.TableSetupColumn(f'{i}')
            imgui.TableHeadersRow()

            # body
            # imgui._ImGuiListClipper clipper;

            it = iter(self.view.scalar_view)
            i = 0
            count = self.view.get_count()
            while i < count:
                imgui.TableNextRow()
                # index
                imgui.TableNextColumn()
                imgui.TextUnformatted(f'{i:05}')
                #
                for j in range(self.view.element_count):
                    imgui.TableNextColumn()
                    imgui.TextUnformatted(f'{next(it):.3f}')
                i += 1

            imgui.EndTable()
