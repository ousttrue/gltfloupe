import logging
from typing import Union, Optional, Any, Tuple
import imgui
import fontawesome47.icons_str as ICONS_FA
logger = logging.getLogger(__name__)


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
    if is_node(keys):
        return ICONS_FA.ARROWS

    if is_mesh(keys):
        return ICONS_FA.CUBE

    if is_skin(keys):
        return ICONS_FA.MALE

    if is_material(keys):
        return ICONS_FA.DIAMOND

    if is_buffer(keys):
        return ICONS_FA.DATABASE

    if is_animation(keys):
        return ICONS_FA.PLAY

    return ''


class JsonTree:
    def __init__(self) -> None:
        self.selected: Tuple[Union[str, int], ...] = ()
        self.root = None

    def _traverse(self, node: Union[list, dict, Any], *keys: Union[str, int]):
        flag = 0  # const.ImGuiTreeNodeFlags_.SpanFullWidth
        match node:
            case list():
                value = f'({len(node)})'
            case dict():
                value = node.get('name', '')
            case _:
                flag |= imgui.TREE_NODE_LEAF
                flag |= imgui.TREE_NODE_BULLET
                # flag |= imgui.TREE_NODE_NO_TREE_PUSH_ON_OPEN
                value = f'{node}'
        imgui.table_next_row()
        # col 0
        imgui.table_next_column()
        open = imgui.tree_node(f'{get_icon(keys)} {keys[-1]}', flag)
        imgui.set_item_allow_overlap()
        # col 1
        imgui.table_next_column()
        _, selected = imgui.selectable(
            value, keys == self.selected, imgui.SELECTABLE_SPAN_ALL_COLUMNS)
        if selected:
            # update selctable
            self.selected = keys
        if imgui.is_item_clicked():
            # update selctable
            self.selected = keys
        if open:
            match node:
                case list():
                    for i, v in enumerate(node):
                        self._traverse(v, *keys, i)
                case dict():
                    for k, v in node.items():
                        self._traverse(v, *keys, k)
            imgui.tree_pop()

    def draw(self):
        if not self.root:
            return
        flags = (
            imgui.TABLE_BORDERS_VERTICAL
            | imgui.TABLE_BORDERS_OUTER_HORIZONTAL
            | imgui.TABLE_RESIZABLE
            | imgui.TABLE_ROW_BACKGROUND
            | imgui.TABLE_NO_BORDERS_IN_BODY
        )
        if imgui.begin_table("jsontree_table", 2, flags):
            # header
            imgui.table_setup_column("key")
            imgui.table_setup_column("value")
            imgui.table_headers_row()

            # body
            # imgui.set_next_item_open(True, imgui.ONCE)

            old = self.selected

            for k, v in self.root.items():
                self._traverse(v, k)

            imgui.end_table()
