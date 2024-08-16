import sys
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QDialog, QApplication, QTreeWidgetItem, QPushButton, QSizePolicy, QStackedWidget
import DiskUsage
from PyQt5.QtWidgets import QApplication, QMainWindow
import sys
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QMovie
from PyQt5.QtCore import Qt, pyqtSignal
import win32api
from functools import partial
import time
from enum import StrEnum


class ButtonStyles(StrEnum):
    BUTTON_STYLE_SHEET = '''QPushButton {
    background-color: rgb(255, 255, 255);
    border-style: solid;
    border-radius: 15px;
    }

    QPushButton:hover {
    background-color: rgb(255, 246, 242);
    }'''

    SELECTED_BUTTON_STYLE_SHEET = '''QPushButton {
    background-color: rgb(255, 186, 158);
    border-style: solid;
    border-radius: 15px;
    }
    
    QPushButton:hover {
    background-color: rgb(255, 149, 107);
    }'''


class QFileItem(QTreeWidgetItem):
    def __init__(self, file: DiskUsage.File):
        info = [
            file.name,
            str(file.size),
            file.creation_date.strftime('%H:%M:%S %d.%m.%y')
            if file.extension != 'protected system file'
            else '??:??:?? ??.??.????',
            file.change_date.strftime('%H:%M:%S %d.%m.%y')
            if file.extension != 'protected system file'
            else '??:??:?? ??.??.????',
            str(file.extension)
        ]
        super().__init__(info)
        self.file = file


class MainWindow(QStackedWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('diskUsage.ui', self)
        self.processed_disk = ''
        self.startButton.clicked.connect(self.start_building_tree)
        self.treeWidget.header().resizeSection(0, 300)
        self.treeWidget.header().resizeSection(1, 50)
        self.treeWidget.itemClicked.connect(self.update_chart)
        self.chart.setRenderHint(QPainter.Antialiasing)
        self.lineEdit.textChanged.connect(self.on_text_changed)
        for disk in self.get_disks():
            disk_button = QPushButton(disk)
            disk_button.setFixedHeight(80)
            disk_button.setStyleSheet(ButtonStyles.BUTTON_STYLE_SHEET)
            disk_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            disk_button.setFont(QFont('Montserrat bold', 20))
            disk_button.clicked.connect(partial(self.set_directory, disk_button))
            self.horizontalLayout.addWidget(disk_button)

    def set_directory(self, disk_button):
        print(self.size())
        print(self.startButton.size())
        print(self.currentWidget())
        self.processed_disk = disk_button.text() + ':\\'
        disk_button.setStyleSheet(ButtonStyles.SELECTED_BUTTON_STYLE_SHEET)
        for button in (self.horizontalLayout.itemAt(i).widget() for i in range(self.horizontalLayout.count())):
            button.setStyleSheet(ButtonStyles.BUTTON_STYLE_SHEET
                                 if button != disk_button
                                 else ButtonStyles.SELECTED_BUTTON_STYLE_SHEET)



    def get_disks(self):
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        drives = [drive.split(':')[0] for drive in drives]
        return drives

    def start_building_tree(self):
        self.setCurrentIndex(1)
        movie = QMovie('loading.gif')
        self.label_3.setMovie(movie)
        movie.start()
        if self.lineEdit.text():
            self.processed_disk = self.lineEdit.text()
        required_files_count = DiskUsage.get_files_count(self.processed_disk)
        self.task = DiskUsage.CalculatingMemoryUsage(self.processed_disk, required_files_count)
        self.task.updated.connect(self.on_update)
        self.task.finished.connect(self.start_building_widget_on_finish_calculating)
        self.task.start()

    def on_update(self, count, req_count):
        progress = int(count / req_count * 100)
        self.progressBar.setFormat(f'{progress}% ({count}/{req_count} files processed)')
        self.progressBar.setValue(progress)

    def on_text_changed(self):
        for button in (self.horizontalLayout.itemAt(i).widget() for i in range(self.horizontalLayout.count())):
            button.setEnabled(not self.lineEdit.text())
            button.setStyleSheet(ButtonStyles.BUTTON_STYLE_SHEET)

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
        self.setCurrentIndex(2)

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
    main_window.resize(1400, 850)
    main_window.show()
    sys.exit(app.exec_())
