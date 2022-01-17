from typing import Optional
from gltfio import GltfData
from gltfio.types import GltfAccessorSlice
import pydear as imgui
from ..jsonutil import get_value

THRESHOLD = 1e-5


def color_32(r, g, b, a):
    return r + (g << 8) + (b << 16) + (a << 24)


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
        imgui.TextUnformatted(f'count: {self.view.get_count()}')
        flags = (
            imgui.ImGuiTableFlags_.BordersV
            | imgui.ImGuiTableFlags_.BordersOuterH
            | imgui.ImGuiTableFlags_.Resizable
            | imgui.ImGuiTableFlags_.RowBg
            | imgui.ImGuiTableFlags_.NoBordersInBody
        )
        cols = self.view.element_count+1
        if self.key[-1] == 'WEIGHTS_0':
            cols += 1
        if imgui.BeginTable("jsontree_table", cols, flags):
            # header
            # imgui.TableSetupScrollFreeze(0, 1); // Make top row always visible
            imgui.TableSetupColumn('index')
            for i in range(self.view.element_count):
                imgui.TableSetupColumn(f'{i}')
            if self.key[-1] == 'WEIGHTS_0':
                imgui.TableSetupColumn(f'sum')
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
                total = 0
                for j in range(self.view.element_count):
                    imgui.TableNextColumn()
                    value = next(it)
                    total += value
                    imgui.TextUnformatted(f'{value:.3f}')
                if self.key[-1] == 'WEIGHTS_0':
                    imgui.TableNextColumn()

                    d = total-1
                    if d > THRESHOLD:
                        imgui.PushStyleColor(
                            imgui.ImGuiCol_.Text, color_32(255, 0, 0, 255))
                    elif d < -THRESHOLD:
                        imgui.PushStyleColor(
                            imgui.ImGuiCol_.Text, color_32(0, 0, 255, 255))
                    else:
                        imgui.PushStyleColor(
                            imgui.ImGuiCol_.Text, color_32(128, 128, 128, 255))
                    imgui.TextUnformatted(f'{total:.3f}')
                    imgui.PopStyleColor()
                i += 1

            imgui.EndTable()
