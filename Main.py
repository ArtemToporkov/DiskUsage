import sys
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QTreeWidgetItem
import DiskUsage
from PyQt5.QtWidgets import QApplication, QMainWindow
import sys
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt


class QFileItem(QTreeWidgetItem):
    def __init__(self, file: DiskUsage.File):
        info = [
            file.name,
            str(file.size),
            file.creation_date.strftime('%H:%M:%S %d.%m.%y'),
            file.change_date.strftime('%H:%M:%S %d.%m.%y'),
            str(file.extension)
        ]
        super().__init__(info)
        self.file = file


class MainWindow(QDialog):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('diskUsage.ui', self)
        self.print_tree()
        self.treeWidget.header().resizeSection(0, 300)
        self.treeWidget.header().resizeSection(1, 50)
        self.treeWidget.itemClicked.connect(self.update_chart)
        self.chart.setRenderHint(QPainter.Antialiasing)
        series = QPieSeries()

    def print_tree(self):
        tree = DiskUsage.build_tree()
        element = QFileItem(tree)
        self.treeWidget.addTopLevelItem(element)
        element.setExpanded(True)

        def display_tree(el, catalog: DiskUsage.File):
            content = catalog.files + catalog.folders
            for item in content:
                tree_item = QFileItem(item)
                el.addChild(tree_item)
                if item.extension == '':
                    display_tree(tree_item, item)

        display_tree(element, tree)

    def update_chart(self):
        file = self.treeWidget.currentItem().file
        if file.extension != '':
            return
        series = QPieSeries()
        series.setPieSize(0.5)
        for child in file.files + file.folders:
            if child.size > 0:
                series.append(child.name, child.size)
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.addSeries(series)
        chart.legend().hide()
        self.chart.setChart(chart)
        series.hovered.connect(self.on_hovered)

    def on_hovered(self, slice: QPieSlice, state):
        if state:
            slice.setExploded(True)
            slice.setLabelVisible()
        else:
            slice.setExploded(False)
            slice.setLabelVisible(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    widget = QtWidgets.QStackedWidget()
    widget.addWidget(main_window)
    widget.setFixedHeight(850)
    widget.setFixedWidth(1400)
    widget.show()
    sys.exit(app.exec_())
