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
    background-color: rgb(255, 200, 179);
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
        self.startButton.clicked.connect(self.calculate_files_count)
        self.filesTreeWidget.header().resizeSection(0, 300)
        self.filesTreeWidget.header().resizeSection(1, 50)
        self.filesTreeWidget.itemClicked.connect(partial(self.update_chart, None))
        self.chart.setRenderHint(QPainter.Antialiasing)
        self.customPathEdit.textChanged.connect(self.on_text_changed)
        for disk in self.get_disks():
            disk_button = QPushButton(disk)
            disk_button.setFixedHeight(80)
            disk_button.setStyleSheet(ButtonStyles.BUTTON_STYLE_SHEET)
            disk_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            disk_button.setFont(QFont('Montserrat bold', 20))
            disk_button.clicked.connect(partial(self.set_directory, disk_button))
            self.disksLayout.addWidget(disk_button)

    def set_directory(self, disk_button):
        print(self.size())
        print(self.startButton.size())
        print(self.currentWidget())
        self.processed_disk = disk_button.text() + ':\\'
        disk_button.setStyleSheet(ButtonStyles.SELECTED_BUTTON_STYLE_SHEET)
        for button in (self.disksLayout.itemAt(i).widget() for i in range(self.disksLayout.count())):
            button.setStyleSheet(ButtonStyles.BUTTON_STYLE_SHEET
                                 if button != disk_button
                                 else ButtonStyles.SELECTED_BUTTON_STYLE_SHEET)

    def calculate_files_count(self):
        self.setCurrentIndex(1)
        movie = QMovie('searching.gif')
        self.label_3.setMovie(movie)
        movie.start()
        if self.customPathEdit.text():
            self.processed_disk = self.customPathEdit.text()
        self.calculating_task = DiskUsage.CalculatingFilesCount(self.processed_disk)
        self.calculating_task.finished.connect(self.on_calculating_files_count_finished)
        self.calculating_task.updated.connect(self.on_preparing)
        self.progressBar.setValue(0)
        self.calculating_task.start()

    def on_preparing(self, prepared_files_count):
        self.progressBar.setFormat(f'{prepared_files_count} files found...')

    def on_calculating_files_count_finished(self, required_files_count):
        movie = QMovie(f'loading.gif')
        self.label_3.setMovie(movie)
        movie.start()
        self.processing_files_task = DiskUsage.CalculatingMemoryUsage(self.processed_disk, required_files_count)
        self.processing_files_task.updated.connect(self.on_update)
        self.processing_files_task.finished.connect(self.on_preparing_files_finished)
        self.processing_files_task.start()

    def on_preparing_files_finished(self, tree: DiskUsage.File, required_files_count: int):
        self.updating_size_task = DiskUsage.UpdatingFoldersSize(tree, required_files_count)
        self.updating_size_task.updated.connect(self.on_update)
        self.updating_size_task.finished.connect(self.start_building_widget_on_finish_calculating)
        self.updating_size_task.start()


    def on_update(self, count, req_count):
        progress = int(count / req_count * 100)
        self.progressBar.setFormat(f'{progress}% ({count}/{req_count} files processed)')
        self.progressBar.setValue(progress)

    def on_text_changed(self):
        for button in (self.disksLayout.itemAt(i).widget() for i in range(self.disksLayout.count())):
            button.setEnabled(not self.customPathEdit.text())
            button.setStyleSheet(ButtonStyles.BUTTON_STYLE_SHEET)

    def start_building_widget_on_finish_calculating(self, tree):
        element = QFileItem(tree)
        self.filesTreeWidget.addTopLevelItem(element)
        element.setExpanded(True)
        element.setSelected(True)

        def display_tree(el, catalog: DiskUsage.File):
            content = catalog.files + catalog.folders
            for item in content:
                tree_item = QFileItem(item)
                el.addChild(tree_item)
                if item.extension == '':
                    display_tree(tree_item, item)

        start_time = time.time()
        display_tree(element, tree)
        self.update_chart(tree)
        self.current_selected_folder = element
        print("--- %s seconds ---" % (time.time() - start_time))
        self.setCurrentIndex(2)

    def update_chart(self, item):
        self.current_selected_folder = self.filesTreeWidget.currentItem()
        file = self.current_selected_folder.file if item is None else item
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
        self.chart.setChart(chart)
        series.hovered.connect(self.on_hovered)
        series.clicked.connect(self.on_clicked)

    def on_hovered(self, slice: QPieSlice, state):
        if state:
            slice.setExploded(True)
            slice.setLabelVisible()
        else:
            slice.setExploded(False)
            slice.setLabelVisible(False)

    def on_clicked(self, slice: QPieSlice):
        file_name = slice.label().title().lower()
        print(file_name)
        for child in (self.current_selected_folder.child(i) for i in range(self.current_selected_folder.childCount())):
            if file_name == child.file.name.lower():
                child.setSelected(True)
            else:
                child.setSelected(False)

    @staticmethod
    def get_disks():
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        drives = [drive.split(':')[0] for drive in drives]
        return drives


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.resize(1400, 850)
    main_window.show()
    sys.exit(app.exec_())
