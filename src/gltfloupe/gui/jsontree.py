import logging
import ctypes
from typing import Union, Optional, Any, Tuple, List
import pydear as imgui
import fontawesome47.icons_str as ICONS_FA
logger = logging.getLogger(__name__)


def can_jump(keys: tuple, value):
    match keys:
        case ('nodes', node_index, 'children', child_index):
            return ('nodes', value)
        case ('scenes', scene_index, 'nodes', node_index):
            return ('nodes', value)
        case ('skins', skin_index, 'skeleton'):
            return ('nodes', value)
        case ('skins', skin_index, 'joints', joint_index):
            return ('nodes', value)

    return False


def is_scene(keys: tuple):
    match keys:
        case ('scene',):
            return True
        case ('scenes',):
            return True
        case ('scenes', scene_index):
            return True


def is_node(keys: tuple):
    '''
    array of node, the node, node index
    '''
    match keys:
        case  ('nodes',):
            return True
        case ('nodes', node_index):
            return True
        case ('nodes', node_index, 'children'):
            return True
        case ('nodes', node_index, 'children', child_index):
            return True
        case ('scenes', scene_index, 'nodes'):
            return True
        case ('scenes', scene_index, 'nodes', node_index):
            return True
        case ('skins', skin_index, 'skeleton'):
            return True
        case ('skins', skin_index, 'joints'):
            return True
        case ('skins', skin_index, 'joints', joint_index):
            return True


def is_mesh(keys: tuple):
    match keys:
        case ('meshes',):
            return True
        case ('meshes', mesh_index):
            return True
        case ('meshes', mesh_index, 'primitives'):
            return True
        case ('meshes', mesh_index, 'primitives', prim_index):
            return True
        case ('nodes', node_index, 'mesh'):
            return True


def is_skin(keys: tuple):
    match keys:
        case ('skins',):
            return True
        case ('skins', skin_index):
            return True
        case ('nodes', node_index, 'skin'):
            return True


def is_material(keys: tuple):
    match keys:
        case ('materials', ):
            return True
        case ('materials', material_index):
            return True
        case ('textures',):
            return True
        case ('textures', texture_index):
            return True
        case ('images',):
            return True
        case ('images', image_index):
            return True
        case ('samplers', ):
            return True
        case ('samplers', sampler_index):
            return True
        case ('meshes', meshes_index, 'primitives', prim_index, 'material'):
            return True


def is_animation(keys: tuple):
    match keys:
        case ('animations',):
            return True
        case ('animations', animation_index):
            return True


def is_buffer(keys: tuple):
    match keys:
        case ('buffers', ):
            return True
        case ('buffers', buffer_index):
            return True
        case ('bufferViews', ):
            return True
        case ('bufferViews', bufferView_index):
            return True
        case ('bufferViews', bufferView_index, 'buffer'):
            return True
        case ('accessors', ):
            return True
        case ('accessors', accessor_index):
            return True
        case ('accessors', accessor_index, 'bufferView'):
            return True
        case ('meshes', meshes_index, 'primitives', prim_index, 'indices'):
            return True
        case ('meshes', meshes_index, 'primitives', prim_index, 'attributes', attribute):
            return True
        case ('skins', skin_index, 'inverseBindMatrices'):
            return True


def get_icon(keys: tuple) -> str:
    if is_scene(keys):
        return ICONS_FA.FOLDER

    if is_node(keys):
        return ICONS_FA.SITEMAP

    if is_mesh(keys):
        return ICONS_FA.CUBE

    if is_skin(keys):
        return ICONS_FA.CHILD

    if is_material(keys):
        return ICONS_FA.DIAMOND

    if is_buffer(keys):
        return ICONS_FA.DATABASE

    if is_animation(keys):
        return ICONS_FA.PLAY

    if can_jump(keys, None):
        return ICONS_FA.SHARE

    return ''


def tuple_status_with(current, target) -> bool:
    if len(current) > len(target):
        return False

    for l, r in zip(current, target):
        if l != r:
            return False
    return True


class JsonTree:
    def __init__(self) -> None:
        self.root = None
        self._history: List[tuple] = []
        self._history_pos = -1

    def get_selected(self) -> tuple:
        if len(self._history) == 0:
            return ()
        return self._history[self._history_pos]

    def push(self, keys: tuple):
        if self.get_selected() == keys:
            return

        if self._history:
            # empty
            while(self._history_pos+1 < len(self._history)):
                self._history.pop()

        self._history.append(keys)
        self._history_pos += 1
        logger.debug(
            f'{self._history_pos}/{len(self._history)}: {self._history[-1]}')

    def back(self):
        if self._history_pos > 0:
            self._history_pos -= 1
            logger.debug(f'{self._history_pos}/{len(self._history)}')

    def forward(self):
        if (self._history_pos+1) < len(self._history):
            self._history_pos += 1
            logger.debug(f'{self._history_pos}/{len(self._history)}')

    def _traverse(self, node: Union[list, dict, Any], *keys: Union[str, int]):
        flag = 0  # const.ImGuiTreeNodeFlags_.SpanFullWidth
        match node:
            case list():
                value = f'({len(node)})'
            case dict():
                value = node.get('name', '')
            case _:
                flag |= imgui.ImGuiTreeNodeFlags_.Leaf
                flag |= imgui.ImGuiTreeNodeFlags_.Bullet
                # flag |= imgui.TREE_NODE_NO_TREE_PUSH_ON_OPEN
                value = f'{node}'
        selected = self.get_selected()
        if tuple_status_with(keys, selected):
            if len(keys) < len(selected):
                imgui.SetNextItemOpen(True, imgui.ImGuiCond_.Once)
        imgui.TableNextRow()
        # col 0
        imgui.TableNextColumn()
        open = imgui.TreeNodeEx(f'{get_icon(keys)} {keys[-1]}', flag)
        imgui.SetItemAllowOverlap()
        # col 1
        imgui.TableNextColumn()
        selected = imgui.Selectable(
            f'{value}##{keys}', keys == self.get_selected(), imgui.ImGuiSelectableFlags_.SpanAllColumns)
        if imgui.IsMouseDoubleClicked(0) and imgui.IsItemClicked():
            # update selectable
            dst = can_jump(keys, node)
            if dst:
                logger.debug('double clicked')
                self.push(dst)
        elif imgui.IsItemClicked():
            # update selectable
            logger.debug('clicked')
            self.push(keys)
        # elif selected:
        #     # update selectable
        #     logger.debug('selected')
        #     self.push(keys)

        if open:
            match node:
                case list():
                    for i, v in enumerate(node):
                        self._traverse(v, *keys, i)
                case dict():
                    for k, v in node.items():
                        self._traverse(v, *keys, k)
            imgui.TreePop()

    def draw(self, p_open: ctypes.Array):
        if imgui.Begin('json', p_open):
            if not self.root:
                return
            flags = (
                imgui.ImGuiTableFlags_.BordersV
                | imgui.ImGuiTableFlags_.BordersOuterH
                | imgui.ImGuiTableFlags_.Resizable
                | imgui.ImGuiTableFlags_.RowBg
                | imgui.ImGuiTableFlags_.NoBordersInBody
            )
            if imgui.BeginTable("jsontree_table", 2, flags):
                # header
                imgui.TableSetupColumn("key")
                imgui.TableSetupColumn("value")
                imgui.TableHeadersRow()

                # body
                for k, v in self.root.items():
                    self._traverse(v, k)

                imgui.EndTable()
        imgui.End()
