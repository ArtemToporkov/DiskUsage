import math
import os.path
import sys
import time
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path

import win32api
from PyQt5 import QtCore
from PyQt5.QtChart import QChart, QPieSeries, QPieSlice
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QMovie, QPainter
from PyQt5.QtWidgets import (QApplication, QPushButton, QSizePolicy,
                             QStackedWidget, QTreeWidgetItem)
from PyQt5.uic import loadUi

import disk_usage
import down_arrow  # noqa: F401
from enums import Filters, Grouping, Styles, TreeWidgetColumns


class QFileItem(QTreeWidgetItem):
    def __init__(self, file: disk_usage.File):
        info = [
            file.name,
            self.convert_bytes(file.size),
            (
                file.creation_date.strftime("%H:%M:%S %d.%m.%y")
                if file.extension != "protected system file"
                else "??:??:?? ??.??.????"
            ),
            (
                file.change_date.strftime("%H:%M:%S %d.%m.%y")
                if file.extension != "protected system file"
                else "??:??:?? ??.??.????"
            ),
            str(file.extension),
            file.owner,
        ]
        super().__init__(info)
        self.file = file

    def __lt__(self, other) -> bool:
        column = self.treeWidget().sortColumn()
        match column:
            case TreeWidgetColumns.FILE_OR_FOLDER_NAME:
                return self.file.name < other.file.name
            case TreeWidgetColumns.SIZE:
                return self.file.size < other.file.size
            case TreeWidgetColumns.CREATION_DATE:
                return self.file.creation_date < other.file.creation_date
            case TreeWidgetColumns.CHANGE_DATE:
                return self.file.change_date < other.file.change_date

    @staticmethod
    def convert_bytes(size) -> str:
        if size < 1024:
            return f"{size} b"
        elif 1024 <= size < 1024 ** 2:
            return f"{round(size / 1024, 1)} kb"
        elif 1024 ** 2 <= size < 1024 ** 3:
            return f"{round(size / 1024 ** 2, 1)} mb"
        else:
            return f"{round(size / 1024 ** 3, 1)} gb"


class MainWindow(QStackedWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        current_dir = Path(__file__).parent
        loadUi(current_dir / 'ui' / 'diskUsage.ui', self)

        self.current_processing_phrase = ""

        self.connect_functions()
        self.resize_tree_sections()

        self.processed_disk = ""

        self.current_selected_folder = None
        self.current_selected_group = None
        self.filtered_items = []

        self.chart.setRenderHint(QPainter.Antialiasing)

        self.filter_settings = Filters.NO_FILTER
        self.group_settings = Grouping.NO_GROUPING
        self.sorting_order = Qt.SortOrder.DescendingOrder
        self.sorting_by = TreeWidgetColumns.FILE_OR_FOLDER_NAME

        self.add_disk_buttons()

    def connect_functions(self):
        self.groupingComboBox.currentTextChanged.connect(self.set_groups)
        self.filterComboBox.currentTextChanged.connect(self.on_filter_settings_changed)
        self.sortingComboBox.currentTextChanged.connect(self.change_sort_settings)
        self.startButton.clicked.connect(self.on_start_button_pressed)
        self.filesTreeWidget.itemClicked.connect(self.on_selection_new_item)
        self.customPathEdit.textChanged.connect(self.on_text_changed)
        self.descendingRadioButton.toggled.connect(self.on_order_radiobutton_toggled)

    def resize_tree_sections(self):
        self.filesTreeWidget.header().resizeSection(0, 300)
        self.filesTreeWidget.header().resizeSection(1, 50)
        self.filesTreeWidget.header().resizeSection(4, 100)

    def add_disk_buttons(self):
        for disk in self.get_disks():
            disk_button = QPushButton(disk)
            disk_button.setFixedHeight(80)
            disk_button.setStyleSheet(Styles.BUTTON_STYLE_SHEET)
            disk_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            disk_button.setFont(QFont("Montserrat bold", 20))
            disk_button.clicked.connect(partial(self.set_directory, disk_button))
            self.disksLayout.addWidget(disk_button)

    def change_sort_settings(self, sort_settings):
        match sort_settings:
            case "name":
                self.sorting_by = TreeWidgetColumns.FILE_OR_FOLDER_NAME
            case "size":
                self.sorting_by = TreeWidgetColumns.SIZE
            case "creation date":
                self.sorting_by = TreeWidgetColumns.CREATION_DATE
            case "change date":
                self.sorting_by = TreeWidgetColumns.CHANGE_DATE
        self.sort_items()

    def sort_items(self, item=None):
        sorting_item = item if item else self.current_selected_folder
        if sorting_item.file.grouped:
            for child in self.get_children(sorting_item):
                child.sortChildren(self.sorting_by, self.sorting_order)
        else:
            sorting_item.sortChildren(self.sorting_by, self.sorting_order)

    def on_order_radiobutton_toggled(self):
        if self.descendingRadioButton.isChecked():
            self.sorting_order = Qt.SortOrder.DescendingOrder
        else:
            self.sorting_order = Qt.SortOrder.AscendingOrder
        self.sort_items()

    def on_filter_settings_changed(self, filter_settings):
        self.filter_settings = "" if filter_settings == Filters.FOLDERS else filter_settings
        self.filter_file_items()

    def filter_file_items(self):
        if self.current_selected_folder.file.grouped:
            self.ungroup()
        if self.filter_settings == Filters.NO_FILTER:
            if self.current_selected_folder.file.filtered:
                self.undo_filter()
            self.set_groups(self.group_settings)
            return
        if self.current_selected_folder.file.filtered:
            self.undo_filter()
        children = self.remove_children_and_temporarily_save_them(self.current_selected_folder)
        for child in children:
            if child.file.extension == self.filter_settings:
                self.current_selected_folder.addChild(child)
            else:
                self.filtered_items.append(child)
        self.set_groups(self.group_settings)
        self.current_selected_folder.file.filtered = True
        self.sort_items()

    def undo_filter(self):
        for filtered_item in self.filtered_items:
            self.current_selected_folder.addChild(filtered_item)
        self.filtered_items.clear()
        self.current_selected_folder.file.filtered = False
        self.sort_items()

    def set_groups(self, group):
        self.group_settings = group
        if self.current_selected_folder.file.grouped:
            self.ungroup()
        match group:
            case Grouping.NAME:
                self.group_by(
                    [("A-H", "a", "h"), ("I-P", "i", "p"), ("Q-Z", "q", "z")],
                    lambda file_item: file_item.file.name[0].lower(),
                    lambda file_item: not file_item.file.name[0].isalpha(),
                )
            case Grouping.SIZE:
                self.group_by(
                    [
                        ("huge (more than 10 gb)", 10737418240, math.inf),
                        ("large (1 - 10 gb)", 1073741824, 10737418239),
                        ("big (257-1023 mb)", 269484032, 1073741823),
                        ("medium (1-256 mb)", 1048576, 269484031),
                        ("small (16-1023 kb)", 17404, 1048575),
                        ("tiny (1-16 kb)", 1, 17403),
                        ("no size", 0, 0),
                    ],
                    lambda file_item: file_item.file.size,
                    lambda file_item: False,
                )
            case Grouping.EXTENSION:
                self.group_by_specific_data(
                    lambda item: item.file.extension,
                    lambda item: not item.file.extension,
                )
            case Grouping.OWNER:
                self.group_by_specific_data(
                    lambda item: item.file.owner, lambda item: not item.file.owner
                )
            case Grouping.CREATION_DATE | Grouping.CHANGE_DATE:
                today = datetime.today().date()
                self.group_by(
                    [
                        ('today', today, today),
                        ('last week', today - timedelta(days=7), today - timedelta(days=1)),
                        ('last month', today - timedelta(days=30), today - timedelta(days=8)),
                        ('this year', today - timedelta(days=365), today - timedelta(days=31)),
                        ('last year', today - timedelta(days=730), today - timedelta(days=366)),
                        ('waaaay too long ago', datetime.min.date(), today - timedelta(days=731))
                    ],
                    lambda file_item: self.get_specific_file_date(file_item, group),
                    lambda file_item: not self.get_specific_file_date(file_item, group))
        self.sort_items()

    def group_by_specific_data(self, get_specific_data: callable, function_for_other: callable):
        data = set()
        for child in self.get_children(self.current_selected_folder):
            data_piece = get_specific_data(child)
            if data_piece:
                data.add(data_piece)
        self.group_by(
            [(data_piece, data_piece, data_piece) for data_piece in data],
            lambda file_item: get_specific_data(file_item),
            lambda file_item: function_for_other(file_item),
        )

    @staticmethod
    def get_specific_file_date(item, date_name):
        return (
            item.file.creation_date.date()
            if date_name == "creation date"
            else item.file.change_date.date()
        )

    def group_by(self, groups: list[tuple], comparison_function: callable, function_for_other: callable):
        temp = self.remove_children_and_temporarily_save_them(self.current_selected_folder)
        for group in groups:
            group_item = QTreeWidgetItem([group[0], "", "", "", "", ""])
            self.current_selected_folder.addChild(group_item)
            group_item.setExpanded(True)
            self.change_color_of_item(group_item, QColor(255, 239, 232))
            files_that_match_group = [file for file in temp if group[1] <= comparison_function(file) <= group[2]]
            if files_that_match_group:
                group_item.addChildren(files_that_match_group)
            else:
                self.current_selected_folder.removeChild(group_item)
        doesnt_match_any_group = [file for file in temp if function_for_other(file) and not file.parent()]
        if doesnt_match_any_group:
            other = QTreeWidgetItem(["other", "", "", "", "", ""])
            self.current_selected_folder.addChild(other)
            other.addChildren(doesnt_match_any_group)
            self.change_color_of_item(other, QColor(255, 239, 232))
            other.setExpanded(True)
        self.current_selected_folder.file.grouped = True

    def ungroup(self):
        temp = []
        for child in self.get_children(self.current_selected_folder, reversed_flag=True):
            for group_child in self.get_children(child, reversed_flag=True):
                temp.append(group_child)
                child.removeChild(group_child)
            self.current_selected_folder.removeChild(child)
        self.current_selected_folder.addChildren(temp)
        self.current_selected_folder.file.grouped = False

    def set_directory(self, disk_button):
        self.processed_disk = disk_button.text() + ":\\"
        disk_button.setStyleSheet(Styles.SELECTED_BUTTON_STYLE_SHEET)
        for button in (self.disksLayout.itemAt(i).widget() for i in range(self.disksLayout.count())):
            button.setStyleSheet(Styles.BUTTON_STYLE_SHEET
                                 if button != disk_button
                                 else Styles.SELECTED_BUTTON_STYLE_SHEET)

    def on_start_button_pressed(self):
        if self.customPathEdit.text():
            self.processed_disk = self.customPathEdit.text()
        if not os.path.isdir(self.processed_disk):
            self.errorLabel.setText("Path does not exist or it's not a directory!")
            QTimer.singleShot(2000, lambda: self.errorLabel.setText(""))
            return
        else:
            self.calculate_files_count()

    def calculate_files_count(self):
        self.setCurrentIndex(1)
        movie = QMovie("assets/gifs/searching.gif")
        self.label_3.setMovie(movie)
        movie.start()
        if self.customPathEdit.text():
            self.processed_disk = self.customPathEdit.text()
        self.calculating_task = disk_usage.CalculatingFilesCount(self.processed_disk)
        self.calculating_task.finished.connect(self.start_preparing_files_on_calculating_files_count_finished)
        self.calculating_task.updated.connect(self.on_preparing)
        self.progressBar.setValue(0)
        self.calculating_task.start()

    def on_preparing(self, prepared_files_count):
        self.progressBar.setFormat(f"{prepared_files_count} files found...")

    def start_preparing_files_on_calculating_files_count_finished(self, required_files_count):
        self.current_processing_phrase = "files prepared"
        movie = QMovie(f'assets/gifs/preparing_files.gif')
        self.label_3.setMovie(movie)
        movie.start()
        self.processing_files_task = disk_usage.CalculatingMemoryUsage(self.processed_disk, required_files_count)
        self.processing_files_task.updated.connect(self.on_update)
        self.processing_files_task.finished.connect(self.update_files_size_on_preparing_files_finished)
        self.processing_files_task.start()

    def update_files_size_on_preparing_files_finished(self, tree: disk_usage.File, required_files_count: int):
        self.current_processing_phrase = "files sizes updated"
        movie = QMovie(f'assets/gifs/updating_size.gif')
        self.label_3.setMovie(movie)
        movie.start()
        self.updating_size_task = disk_usage.UpdatingFoldersSize(tree, required_files_count)
        self.updating_size_task.updated.connect(self.on_update)
        self.updating_size_task.finished.connect(self.build_widget_on_size_updating_finished)
        self.updating_size_task.start()

    def build_widget_on_size_updating_finished(self, tree: disk_usage.File, required_count: int):
        self.current_processing_phrase = "files in widget built"
        movie = QMovie(f'assets/gifs/building_widget.gif')
        self.label_3.setMovie(movie)
        movie.start()
        self.building_widget_task = BuildingTreeWidget(tree, required_count)
        self.building_widget_task.updated.connect(self.on_update)
        self.building_widget_task.finished.connect(self.display_tree_on_widget_building_finished)
        self.building_widget_task.start()

    def display_tree_on_widget_building_finished(self, element: QFileItem):
        self.filesTreeWidget.addTopLevelItem(element)
        element.setExpanded(True)
        element.setSelected(True)
        self.current_selected_folder = element
        self.on_selection_new_item(element)
        self.setCurrentIndex(2)

    def on_update(self, count, req_count):
        progress = int(count / req_count * 100)
        self.progressBar.setFormat(f"{progress}% ({count}/{req_count} {self.current_processing_phrase})")
        self.progressBar.setValue(progress)

    def on_text_changed(self):
        for button in (self.disksLayout.itemAt(i).widget() for i in range(self.disksLayout.count())):
            button.setEnabled(not self.customPathEdit.text())
            button.setStyleSheet(Styles.BUTTON_STYLE_SHEET)

    def on_selection_new_item(self, item):
        if type(item) is QTreeWidgetItem:
            self.on_group_selected(item)
        else:
            self.on_file_selected(item)

    def on_file_selected(self, item):
        self.groupWidget.setEnabled(True)
        self.filterWidget.setEnabled(True)
        if item.file.extension != "":
            return
        if self.current_selected_folder.file.grouped:
            self.ungroup()
        if self.current_selected_folder.file.filtered:
            self.undo_filter()
        self.filesTreeWidget.setCurrentItem(item)
        item.setExpanded(True)
        self.current_selected_folder = self.filesTreeWidget.currentItem()
        self.update_chart()
        self.update_filters()
        self.sort_items()
        self.set_groups(self.group_settings)

    def on_group_selected(self, item):
        self.current_selected_group = item
        self.groupWidget.setEnabled(False)
        self.filterWidget.setEnabled(False)
        series = QPieSeries()
        series.setPieSize(0.5)
        for child in self.get_children(item):
            if child.file.size > 0:
                series.append(child.file.name, child.file.size)
        chart = QChart()
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.addSeries(series)
        self.chart.setChart(chart)
        series.hovered.connect(self.on_hovered)
        series.clicked.connect(self.on_group_clicked)

    def update_chart(self):
        file = self.current_selected_folder.file
        if file.extension != "":
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
        series.clicked.connect(self.on_clicked)

    def update_filters(self, item=None):
        self.filterComboBox.setCurrentIndex(0)
        for i in reversed(range(1, self.filterComboBox.count())):
            self.filterComboBox.removeItem(i)
        selected_item = self.current_selected_folder if not item else item
        extensions = {file.extension for file in selected_item.file.files if file.extension}
        if selected_item.file.folders:
            extensions.add("folders")
        self.filterComboBox.addItems(extensions)

    def on_hovered(self, slice: QPieSlice, state):
        if state:
            slice.setExploded(True)
            slice.setLabelVisible()
        else:
            slice.setExploded(False)
            slice.setLabelVisible(False)

    def on_clicked(self, slice: QPieSlice):
        file_name = slice.label()
        if self.current_selected_folder.file.grouped:
            for group in self.get_children(self.current_selected_folder):
                for child in self.get_children(group):
                    if child.file.name == file_name:
                        child.setSelected(True)
                    else:
                        child.setSelected(False)
        else:
            for child in self.get_children(self.current_selected_folder):
                if file_name == child.file.name:
                    child.setSelected(True)
                else:
                    child.setSelected(False)

    def on_group_clicked(self, pie_slice: QPieSlice):
        file_name = pie_slice.label()
        for child in self.get_children(self.current_selected_group):
            if file_name == child.file.name:
                child.setSelected(True)
            else:
                child.setSelected(False)

    @staticmethod
    def remove_children_and_temporarily_save_them(item):
        temp = []
        for child in MainWindow.get_children(item, reversed_flag=True):
            temp.append(child)
            item.removeChild(child)
        return temp

    @staticmethod
    def get_disks():
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split("\000")[:-1]
        drives = [drive.split(":")[0] for drive in drives]
        return drives

    @staticmethod
    def change_color_of_item(item, color: QColor):
        for i in range(item.columnCount()):
            item.setBackground(i, color)

    @staticmethod
    def get_children(item, reversed_flag=False):
        if not reversed_flag:
            for child in (item.child(i) for i in range(item.childCount())):
                yield child
        else:
            for child in (item.child(i) for i in reversed(range(item.childCount()))):
                yield child


class BuildingTreeWidget(QtCore.QThread):
    updated = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(QFileItem)
    running = False

    def __init__(self, tree: disk_usage.File, required_files_count: int):
        super(BuildingTreeWidget, self).__init__()
        self.tree = tree
        self.count = 0
        self.required_files_count = required_files_count

    def run(self):
        element = QFileItem(self.tree)
        element.setSelected(True)
        element.setExpanded(True)
        self.display_tree(element, self.tree)
        self.finished.emit(element)

    def display_tree(self, el, catalog: disk_usage.File):
        content = catalog.files + catalog.folders
        self.count += len(catalog.files) + len(catalog.folders)
        self.updated.emit(self.count, self.required_files_count)
        time.sleep(0.00001)
        for item in content:
            tree_item = QFileItem(item)
            el.addChild(tree_item)
            if item.extension == "":
                self.display_tree(tree_item, item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.setWindowTitle("Disk Usage")
    main_window.setWindowIcon(QIcon("assets/icons/window_icon.png"))
    main_window.resize(1400, 850)
    main_window.show()
    sys.exit(app.exec_())
