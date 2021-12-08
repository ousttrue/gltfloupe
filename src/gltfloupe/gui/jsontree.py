import logging
from typing import Union, Optional, Any, Tuple
import imgui
logger = logging.getLogger(__name__)


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
        open = imgui.tree_node(str(keys[-1]), flag)
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
