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

    def print_tree(self):
        tree = DiskUsage.build_tree()
        self.treeWidget.setColumnCount(1)
        element = QTreeWidgetItem([tree.name])
        self.treeWidget.addTopLevelItem(element)

        def display_tree(el, catalog: DiskUsage.File):
            for file in catalog.files:
                file_item = QTreeWidgetItem([file.name])
                el.addChild(file_item)
            for folder in catalog.folders:
                folder_item = QTreeWidgetItem([folder.name])
                el.addChild(folder_item)
                display_tree(folder_item, folder)

        display_tree(element, tree)


app = QApplication(sys.argv)
main_window = MainWindow()
widget = QtWidgets.QStackedWidget()
widget.addWidget(main_window)
widget.setFixedHeight(850)
widget.setFixedWidth(1120)
widget.show()
try:
    sys.exit(app.exec_())
except:
    print('Exiting')