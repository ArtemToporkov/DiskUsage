import sys
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QDialog, QApplication, QTreeWidgetItem, QPushButton
import DiskUsage
from PyQt5.QtWidgets import QApplication, QMainWindow
import sys
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
from PyQt5.QtCore import Qt, pyqtSignal
import win32api
from functools import partial
import time


class QFileItem(QTreeWidgetItem):
    def __init__(self, file: DiskUsage.File):
        info = [
            file.name,
            str(file.size),
            file.creation_date.strftime('%H:%M:%S %d.%m.%y') if file.extension != 'protected system file' else '??:??:?? ??.??.????',
            file.change_date.strftime('%H:%M:%S %d.%m.%y') if file.extension != 'protected system file' else '??:??:?? ??.??.????',
            str(file.extension)
        ]
        super().__init__(info)
        self.file = file


class MainWindow(QDialog):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('diskUsage.ui', self)
        self.processed_disk = ''
        self.startButton.clicked.connect(self.start_building_tree)
        self.treeWidget.header().resizeSection(0, 300)
        self.treeWidget.header().resizeSection(1, 50)
        self.treeWidget.itemClicked.connect(self.update_chart)
        self.chart.setRenderHint(QPainter.Antialiasing)
        for disk in self.get_disks():
            disk_button = QPushButton(disk)
            disk_button.setFixedHeight(80)
            disk_button.setFont(QFont('Montserrat bold', 20))
            disk_button.clicked.connect(partial(self.set_directory, disk_button.text()))
            self.horizontalLayout.addWidget(disk_button)

    def set_directory(self, text):
        self.processed_disk = text + ':\\'

    def get_disks(self):
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        drives = [drive.split(':')[0] for drive in drives]
        return drives

    def start_building_tree(self):
        self.stackedWidget.setCurrentIndex(1)
        if self.lineEdit.text():
            self.processed_disk = self.lineEdit.text()
        self.task = DiskUsage.CalculatingMemoryUsage(self.processed_disk)
        self.task.updated.connect(self.on_update)
        self.task.finished.connect(self.start_building_widget_on_finish_calculating)
        self.task.start()

    def on_update(self, data):
        self.progressBar.setValue(int(data))

    def start_building_widget_on_finish_calculating(self, tree):
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

        start_time = time.time()
        display_tree(element, tree)
        print("--- %s seconds ---" % (time.time() - start_time))
        self.stackedWidget.setCurrentIndex(2)

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
