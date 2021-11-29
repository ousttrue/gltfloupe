from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex
from typing import Optional


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

    def json_path(self) -> str:
        path = [f'/{x.name}' for x in self.get_ancestors()][:-1]
        return ''.join(reversed(path))


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


class TreeModel(QAbstractItemModel):
    def __init__(self, root: dict, parent=None):
        super(TreeModel, self).__init__(parent)
        self.rootItem = build(root)
        # self.layoutChanged.emit()

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):

        if not index.isValid():
            return None
        if role != Qt.DisplayRole:
            return None
        item = index.internalPointer()
        return item.data(index.column())

    def flags(self, index):

        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            # return self.rootItem.data(section)
            if section == 0:
                return 'property'
            elif section == 1:
                return 'value'
            else:
                raise Exception()

        return None

    def index(self, row, column, parent):

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:

        if not index.isValid():
            return QModelIndex()
        childItem = index.internalPointer()
        parentItem = childItem.parent()
        if parentItem == self.rootItem:
            return QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):

        if parent.column() > 0:
            return 0
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        return parentItem.childCount()
