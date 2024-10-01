import unittest
from unittest.mock import MagicMock, patch

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

import main
from disk_usage import File
from enums import Filters, Grouping, TreeWidgetColumns
from main import MainWindow, QFileItem


class TestMainWindow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    def setUp(self):
        self.main_window = MainWindow()

    def test_init(self):
        self.assertIsNotNone(self.main_window.filesTreeWidget)
        self.assertIsNotNone(self.main_window.chart)
        self.assertEqual(self.main_window.sorting_order, Qt.SortOrder.DescendingOrder)
        self.assertEqual(self.main_window.sorting_by, TreeWidgetColumns.FILE_OR_FOLDER_NAME)

    def test_connect_functions(self):
        self.main_window.connect_functions()
        self.assertTrue(self.main_window.groupingComboBox.currentTextChanged.connect)
        self.assertTrue(self.main_window.filterComboBox.currentTextChanged.connect)
        self.assertTrue(self.main_window.sortingComboBox.currentTextChanged.connect)
        self.assertTrue(self.main_window.startButton.clicked.connect)
        self.assertTrue(self.main_window.filesTreeWidget.itemClicked.connect)
        self.assertTrue(self.main_window.customPathEdit.textChanged.connect)
        self.assertTrue(self.main_window.descendingRadioButton.toggled.connect)

    def test_resize_tree_sections(self):
        self.main_window.resize_tree_sections()
        self.assertEqual(self.main_window.filesTreeWidget.header().sectionSize(0), 300)
        self.assertEqual(self.main_window.filesTreeWidget.header().sectionSize(1), 50)
        self.assertEqual(self.main_window.filesTreeWidget.header().sectionSize(4), 100)

    def test_add_disk_buttons(self):
        layout = self.main_window.disksLayout
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)
        with patch('main.MainWindow.get_disks', return_value=['1st disk', '2nd disk', '3rd disk']):
            self.main_window.add_disk_buttons()
            self.assertEqual(self.main_window.disksLayout.count(), 3)
            disks = []
            for child in (layout.itemAt(i).widget() for i in range(layout.count())):
                disks.append(child.text())
            self.assertEqual(disks, ['1st disk', '2nd disk', '3rd disk'])

    def test_change_sort_settings(self):
        with patch('main.MainWindow.sort_items'):
            self.main_window.change_sort_settings("name")
            self.assertEqual(self.main_window.sorting_by, TreeWidgetColumns.FILE_OR_FOLDER_NAME)
            self.main_window.change_sort_settings("size")
            self.assertEqual(self.main_window.sorting_by, TreeWidgetColumns.SIZE)

    def test_sort_items(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.main_window.current_selected_folder = item
        self.main_window.sort_items()

    def test_on_order_radiobutton_toggled(self):
        with patch('main.MainWindow.sort_items'):
            self.main_window.descendingRadioButton.setChecked(True)
            self.main_window.on_order_radiobutton_toggled()
            self.assertEqual(self.main_window.sorting_order, Qt.SortOrder.DescendingOrder)
            self.assertEqual(self.main_window.ascendingRadioButton.isChecked(), False)
            self.main_window.ascendingRadioButton.setChecked(True)
            self.main_window.on_order_radiobutton_toggled()
            self.assertEqual(self.main_window.sorting_order, Qt.SortOrder.AscendingOrder)
            self.assertEqual(self.main_window.descendingRadioButton.isChecked(), False)

    def test_on_filter_settings_changed(self):
        with patch('main.MainWindow.filter_file_items'):
            self.main_window.on_filter_settings_changed(Filters.FOLDERS)
            self.assertEqual(self.main_window.filter_settings, "")
            self.main_window.on_filter_settings_changed('.exe')
            self.assertEqual(self.main_window.filter_settings, '.exe')

    def test_filter_file_items(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.main_window.current_selected_folder = item
        self.main_window.filter_settings = Filters.FOLDERS
        self.main_window.filter_file_items()


    def test_set_groups(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.main_window.current_selected_folder = item
        self.main_window.set_groups(Grouping.NAME)

    def test_group_by_specific_data(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.main_window.current_selected_folder = item
        self.main_window.group_by_specific_data(lambda x: x.file.extension, lambda x: not x.file.extension)

    def test_get_specific_file_date(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.assertEqual(self.main_window.get_specific_file_date(item, "creation date"), file.creation_date.date())
        self.assertEqual(self.main_window.get_specific_file_date(item, "change date"), file.change_date.date())

    def test_group_by(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.main_window.current_selected_folder = item
        self.main_window.group_by([("test", 0, 1)], lambda x: x.file.size, lambda x: False)

    def test_ungroup(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.main_window.current_selected_folder = item
        self.main_window.ungroup()

    def test_set_directory(self):
        disk_button = MagicMock()
        disk_button.text.return_value = "C"
        self.main_window.set_directory(disk_button)
        self.assertEqual(self.main_window.processed_disk, "C:\\")

    def test_calculate_files_count(self):
        with patch('main.disk_usage.CalculatingFilesCount') as mock_task:
            self.main_window.calculate_files_count()
            mock_task.assert_called_once()

    def test_on_preparing(self):
        self.main_window.on_preparing(10)
        self.assertEqual(self.main_window.progressBar.format(), "10 files found...")

    def test_start_preparing_files_on_calculating_files_count_finished(self):
        with patch('main.disk_usage.CalculatingMemoryUsage') as mock_task:
            self.main_window.start_preparing_files_on_calculating_files_count_finished(10)
            mock_task.assert_called_once()

    def test_update_files_size_on_preparing_files_finished(self):
        with patch('main.disk_usage.UpdatingFoldersSize') as mock_task:
            self.main_window.update_files_size_on_preparing_files_finished(File("test.txt"), 10)
            mock_task.assert_called_once()

    def test_build_widget_on_size_updating_finished(self):
        with patch('main.BuildingTreeWidget') as mock_task:
            self.main_window.build_widget_on_size_updating_finished(File("test.txt"), 10)
            mock_task.assert_called_once()

    def test_display_tree_on_widget_building_finished(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.main_window.display_tree_on_widget_building_finished(item)
        self.assertEqual(self.main_window.filesTreeWidget.topLevelItemCount(), 1)

    def test_on_update(self):
        self.main_window.on_update(5, 10)
        self.assertEqual(self.main_window.progressBar.format(), "50% (5/10 )")

    def test_on_text_changed(self):
        self.main_window.customPathEdit.setText("C:\\")
        self.main_window.on_text_changed()
        self.assertFalse(self.main_window.disksLayout.itemAt(0).widget().isEnabled())

    def test_on_selection_new_item(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.main_window.on_selection_new_item(item)

    def test_on_file_selected(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.main_window.on_file_selected(item)

    def test_on_group_selected(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.main_window.on_group_selected(item)

    def test_update_chart(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.main_window.current_selected_folder = item
        self.main_window.update_chart()

    def test_update_filters(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.main_window.current_selected_folder = item
        self.main_window.update_filters()

    def test_on_hovered(self):
        slice = MagicMock()
        self.main_window.on_hovered(slice, True)
        slice.setExploded.assert_called_once_with(True)
        slice.setLabelVisible.assert_called_once_with()

    def test_remove_children_and_temporarily_save_them(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.main_window.remove_children_and_temporarily_save_them(item)

    def test_get_disks(self):
        with patch('main.win32api.GetLogicalDriveStrings', return_value="C:\\\0D:\\\0"):
            self.assertEqual(self.main_window.get_disks(), ["C", "D"])

    def test_get_children(self):
        file = File("test.txt")
        item = QFileItem(file)
        self.assertEqual(list(self.main_window.get_children(item)), [])

    def test_convert_bytes(self):
        b = 782634
        converted = "764.3 kb"
        self.assertEqual(main.QFileItem.convert_bytes(b), converted)


if __name__ == '__main__':
    unittest.main()