import unittest
from enums import Styles, Grouping, Sorting, Filters, TreeWidgetColumns


class TestEnums(unittest.TestCase):

    def test_styles(self):
        self.assertIsInstance(Styles.BUTTON_STYLE_SHEET, str)
        self.assertIsInstance(Styles.SELECTED_BUTTON_STYLE_SHEET, str)
        self.assertIsInstance(Styles.GROUP_STYLE, str)

    def test_grouping(self):
        self.assertIsInstance(Grouping.NO_GROUPING, str)
        self.assertIsInstance(Grouping.NAME, str)
        self.assertIsInstance(Grouping.SIZE, str)
        self.assertIsInstance(Grouping.EXTENSION, str)
        self.assertIsInstance(Grouping.CHANGE_DATE, str)
        self.assertIsInstance(Grouping.CREATION_DATE, str)
        self.assertIsInstance(Grouping.OWNER, str)

    def test_sorting(self):
        self.assertIsInstance(Sorting.NAME, str)
        self.assertIsInstance(Sorting.SIZE, str)
        self.assertIsInstance(Sorting.CREATION_DATE, str)
        self.assertIsInstance(Sorting.CHANGE_DATE, str)

    def test_filters(self):
        self.assertIsInstance(Filters.NO_FILTER, str)
        self.assertIsInstance(Filters.FOLDERS, str)

    def test_tree_widget_columns(self):
        self.assertIsInstance(TreeWidgetColumns.FILE_OR_FOLDER_NAME, int)
        self.assertIsInstance(TreeWidgetColumns.SIZE, int)
        self.assertIsInstance(TreeWidgetColumns.CREATION_DATE, int)
        self.assertIsInstance(TreeWidgetColumns.CHANGE_DATE, int)
        self.assertIsInstance(TreeWidgetColumns.EXTENSION, int)
        self.assertIsInstance(TreeWidgetColumns.OWNER, int)


if __name__ == '__main__':
    unittest.main()