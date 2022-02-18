from typing import Optional
from gltfio import GltfData
from gltfio.types import GltfAccessorSlice
import pydear.imgui as ImGui
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
        ImGui.TextUnformatted(f'count: {self.view.get_count()}')
        flags = (
            ImGui.ImGuiTableFlags_.BordersV
            | ImGui.ImGuiTableFlags_.BordersOuterH
            | ImGui.ImGuiTableFlags_.Resizable
            | ImGui.ImGuiTableFlags_.RowBg
            | ImGui.ImGuiTableFlags_.NoBordersInBody
        )
        cols = self.view.element_count+1
        if self.key[-1] == 'WEIGHTS_0':
            cols += 1
        if ImGui.BeginTable("jsontree_table", cols, flags):
            # header
            # ImGui.TableSetupScrollFreeze(0, 1); // Make top row always visible
            ImGui.TableSetupColumn('index')
            for i in range(self.view.element_count):
                ImGui.TableSetupColumn(f'{i}')
            if self.key[-1] == 'WEIGHTS_0':
                ImGui.TableSetupColumn(f'sum')
            ImGui.TableHeadersRow()

            # body
            # ImGui._ImGuiListClipper clipper;

            it = iter(self.view.scalar_view)
            i = 0
            count = self.view.get_count()
            while i < count:
                ImGui.TableNextRow()
                # index
                ImGui.TableNextColumn()
                ImGui.TextUnformatted(f'{i:05}')
                #
                total = 0
                for j in range(self.view.element_count):
                    ImGui.TableNextColumn()
                    value = next(it)
                    total += value
                    ImGui.TextUnformatted(f'{value:.3f}')
                if self.key[-1] == 'WEIGHTS_0':
                    ImGui.TableNextColumn()

                    d = total-1
                    if d > THRESHOLD:
                        ImGui.PushStyleColor(
                            ImGui.ImGuiCol_.Text, color_32(255, 0, 0, 255))
                    elif d < -THRESHOLD:
                        ImGui.PushStyleColor(
                            ImGui.ImGuiCol_.Text, color_32(0, 0, 255, 255))
                    else:
                        ImGui.PushStyleColor(
                            ImGui.ImGuiCol_.Text, color_32(128, 128, 128, 255))
                    ImGui.TextUnformatted(f'{total:.3f}')
                    ImGui.PopStyleColor()
                i += 1

            ImGui.EndTable()
