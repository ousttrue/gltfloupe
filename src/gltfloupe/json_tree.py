from PySide6 import QtCore, QtGui, QtWidgets
from typing import Optional, Dict


class Item:
    def __init__(self, value=None):
        self.name = ''
        self.value = value
        self.parentItem: Optional['Item'] = None
        self.children = []

    def columnCount(self) -> int:
        return 2

    def add_child(self, child):
        self.children.append(child)
        child.parentItem = self

    def childCount(self) -> int:
        return len(self.children)

    def child(self, row):
        return self.children[row]

    def data(self, column):
        if column == 0:
            return self.name
        elif column == 1:
            return self.value
        else:
            raise Exception()

    def parent(self):
        return self.parentItem

    def row(self):
        if isinstance(self.parentItem, Item):
            return self.parentItem.children.index(self)
        return 0

    def get_ancestors(self):
        yield self
        if self.parentItem:
            for x in self.parentItem.get_ancestors():
                yield x

    def get_ancestors_reverse(self):
        if self.parentItem:
            for x in self.parentItem.get_ancestors_reverse():
                yield x
        yield self

    def json_path(self) -> tuple:
        path = tuple(x.name for x in self.get_ancestors_reverse())
        return path[1:]


def build(value):
    if isinstance(value, dict):
        node = Item()
        for k, v in value.items():
            child = build(v)
            node.add_child(child)
            child.name = k
        return node

    elif isinstance(value, list):
        node = Item()
        for i, v in enumerate(value):
            child = build(v)
            node.add_child(child)
            child.name = f'{i}'
        return node

    else:
        node = Item(value)
        return node


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, root: dict, icon_map: Dict[str, QtGui.QIcon], parent=None):
        super(TreeModel, self).__init__(parent)
        self.rootItem = build(root)
        self.icon_map = icon_map

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == 0:
                return 'property'
            elif section == 1:
                return 'value'
            else:
                raise Exception()

        return None

    def rowCount(self, parent):

        if parent.column() > 0:
            return 0
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        return parentItem.childCount()

    def index(self, row, column, parent):

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        if not index.isValid():
            return QtCore.QModelIndex()
        childItem = index.internalPointer()
        parentItem = childItem.parent()  # type: ignore
        if parentItem == self.rootItem:
            return QtCore.QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

    def data(self, index, role):

        if not index.isValid():
            return None

        item: Item = index.internalPointer()
        match role:
            case QtCore.Qt.DisplayRole:
                # name, value
                if index.column() == 1:
                    match item.json_path():
                        case (x, i) if i.isdigit():
                            found = [
                                child.value for child in item.children if child.name == 'name']
                            if found:
                                return found[0]

                return item.data(index.column())

            case QtCore.Qt.DecorationRole:
                # icon
                if index.column() == 0:
                    match item.json_path():
                        case ('nodes',) | ('scenes',) | ('scene',):
                            return self.icon_map['node']

                        case ('buffers',) | ('bufferViews',) | ('accessors',):
                            return self.icon_map['buffer']

                        case ('materials',) | ('textures',) | ('images',) | ('samplers',):
                            return self.icon_map['material']

                        case ('meshes',) | ('skins',):
                            return self.icon_map['mesh']

                    if item.children:
                        return self.icon_map['folder']

    def flags(self, index):

        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
