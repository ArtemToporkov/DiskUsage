import sys
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QTreeWidgetItem
import DiskUsage


class MainWindow(QDialog):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('diskUsage.ui', self)
        self.print_tree()
        self.treeWidget.header().resizeSection(0, 300)
        self.treeWidget.header().resizeSection(1, 50)

    def print_tree(self):
        tree = DiskUsage.build_tree()
        element = QTreeWidgetItem([tree.name])
        self.treeWidget.addTopLevelItem(element)
        element.setExpanded(True)

        def display_tree(el, catalog: DiskUsage.File):
            content = catalog.files + catalog.folders
            for item in content:
                info = [
                    item.name,
                    str(item.size),
                    item.creation_date.strftime('%H:%M:%S %d.%m.%y'),
                    item.change_date.strftime('%H:%M:%S %d.%m.%y'),
                    str(item.extension)
                ]
                tree_item = QTreeWidgetItem(info)
                el.addChild(tree_item)
                if item.extension == '':
                    display_tree(tree_item, item)

        display_tree(element, tree)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    widget = QtWidgets.QStackedWidget()
    widget.addWidget(main_window)
    widget.setFixedHeight(850)
    widget.setFixedWidth(1120)
    widget.show()
    sys.exit(app.exec_())
