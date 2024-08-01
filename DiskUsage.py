import os, datetime
import xml.etree.ElementTree as ET
from PyQt5.QtChart import QChartView
import time


class File:
    def __init__(self, path: str):
        self.name = os.path.basename(path)
        self.location = path
        self.size = 0 if os.path.isdir(path) else os.path.getsize(path)
        self.creation_date = datetime.datetime.fromtimestamp(os.path.getctime(path))
        self.change_date = datetime.datetime.fromtimestamp(os.path.getmtime(path))
        self.extension = os.path.splitext(path)[1]
        self.files = []
        self.folders = []
        self.parents = []


# DIRECTORY = 'C:\\Users\\topor\OneDrive\\Рабочий стол\\check'
DIRECTORY = 'D:\\'
CURRENT = File(DIRECTORY)


def fill_disk_usage(path: str, current: File):
    try:
        for file in os.listdir(path):
            if os.path.isdir(os.path.join(path, file)):
                folder_instance = File(os.path.join(path, file))
                current.folders.append(folder_instance)
                folder_instance.parents.append(current)
            else:
                file_instance = File(os.path.join(path, file))
                current.files.append(file_instance)
                current.size += file_instance.size
                for parent in current.parents:
                    parent.size += file_instance.size
    except PermissionError:
        pass
    for folder in current.folders:
        fill_disk_usage(os.path.join(path, folder.name), folder)


def build_tree():
    start_time = time.time()
    fill_disk_usage(DIRECTORY, CURRENT)
    print("--- %s seconds ---" % (time.time() - start_time))
    return CURRENT

