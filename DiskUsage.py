import os, datetime
import xml.etree.ElementTree as ET
from PyQt5.QtChart import QChartView
import time
import PyQt5
from PyQt5 import QtCore


class File:
    def __init__(self, path: str):
        try:
            self.name = os.path.basename(path)
            self.location = path
            self.size = 0 if os.path.isdir(path) else os.path.getsize(path)
            self.creation_date = datetime.datetime.fromtimestamp(os.path.getctime(path))
            self.change_date = datetime.datetime.fromtimestamp(os.path.getmtime(path))
            self.extension = os.path.splitext(path)[1]
            self.files = []
            self.folders = []
            self.parents = []
        except FileNotFoundError:
            self.name = os.path.basename(path)
            self.location = path
            self.extension = 'protected system file'
            self.size = 0
            self.files = []
            self.folders = []
            self.parents = []

CURRENT = None
COUNT = 0


class CalculatingMemoryUsage(QtCore.QThread):
    updated = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(File)
    running = False

    def __init__(self, disk):
        super(CalculatingMemoryUsage, self).__init__()
        self.disk = disk
        self.percent = 0
        self.running = True

    def run(self):
        tree = build_tree(self.disk)
        self.finished.emit(tree)

    def stop(self):
        self.running = False


def fill_disk_usage(path: str, current: File):
    global COUNT
    try:
        for file in os.scandir(path):
            if os.path.isdir(file.path):
                folder_instance = File(file.path)
                current.folders.append(folder_instance)
                folder_instance.parents.append(current)
            else:
                file_instance = File(file.path)
                current.files.append(file_instance)
                current.size += file_instance.size
                for parent in current.parents:
                    parent.size += file_instance.size
    except PermissionError:
        pass
    COUNT += len(current.folders) + len(current.files)
    for folder in current.folders:
        fill_disk_usage(os.path.join(path, folder.name), folder)


def get_files_count(directory):
    c = 0
    for root, dirs, files in os.walk(directory):
        c += len(dirs) + len(files)
    return c


def build_tree(directory):
    start_time = time.time()
    CURRENT = File(directory)
    fill_disk_usage(directory, CURRENT)
    print("--- %s seconds ---" % (time.time() - start_time))
    print(COUNT, get_files_count(directory))
    return CURRENT

