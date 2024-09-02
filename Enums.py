from enum import IntEnum, StrEnum


class Styles(StrEnum):
    BUTTON_STYLE_SHEET = """QPushButton {
    background-color: rgb(255, 255, 255);
    border-style: solid;
    border-radius: 15px;
    }

    QPushButton:hover {
    background-color: rgb(255, 246, 242);
    }"""
    SELECTED_BUTTON_STYLE_SHEET = """QPushButton {
    background-color: rgb(255, 186, 158); 
    border-style: solid;
    border-radius: 15px;
    }

    QPushButton:hover {
    background-color: rgb(255, 200, 179);
    }"""
    GROUP_STYLE = """QTreeWidgetItem {
        background-color: rgb(255, 239, 232);
    }"""


class Grouping(StrEnum):
    NO_GROUPING = "no grouping"
    NAME = "name"
    SIZE = "size"
    EXTENSION = "extension"
    CHANGE_DATE = "change date"
    CREATION_DATE = "creation date"
    OWNER = "owner"


class Sorting(StrEnum):
    NAME = "name"
    SIZE = "size"
    CREATION_DATE = "creation date"
    CHANGE_DATE = "change date"


class Filters(StrEnum):
    NO_FILTER = "no filter"
    FOLDERS = "folders"


class TreeWidgetColumns(IntEnum):
    FILE_OR_FOLDER_NAME = 0
    SIZE = 1
    CREATION_DATE = 2
    CHANGE_DATE = 3
    EXTENSION = 4
    OWNER = 5
