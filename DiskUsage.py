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
            self.extension = self.get_file_extension(path)
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

    @staticmethod
    def get_file_extension(path):
        return os.path.splitext(path)[1] if os.path.isfile(path) else ''


class CalculatingFilesCount(QtCore.QThread):
    finished = QtCore.pyqtSignal(int)
    updated = QtCore.pyqtSignal(int)

    def __init__(self, disk):
        super(CalculatingFilesCount, self).__init__()
        self.disk = disk

    def run(self):
        count = self.get_files_count(self.disk)
        self.finished.emit(count)

    def get_files_count(self, directory):
        c = 0
        for root, dirs, files in os.walk(directory):
            c += len(dirs) + len(files)
            self.updated.emit(c)
        return c


class CalculatingMemoryUsage(QtCore.QThread):
    updated = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(File)
    running = False

    def __init__(self, disk, required_count):
        super(CalculatingMemoryUsage, self).__init__()
        self.disk = disk
        self.percent = 0
        self.running = True
        self.tree = None
        self.count = 0
        self.required_count = required_count

    def run(self):
        tree = self.build_tree()
        self.finished.emit(tree)

    def fill_disk_usage(self, path: str, current: File):
        try:
            for file in os.scandir(path):
                if os.path.isdir(file.path):
                    folder_instance = File(file.path)
                    current.folders.append(folder_instance)
                    folder_instance.parents.append(current)
                    for parent in current.parents:
                        folder_instance.parents.append(parent)
                else:
                    file_instance = File(file.path)
                    current.files.append(file_instance)
                    current.size += file_instance.size
                    for parent in current.parents:
                        parent.size += file_instance.size
        except PermissionError:
            pass
        self.count += len(current.folders) + len(current.files)
        self.updated.emit(self.count, self.required_count)
        for folder in current.folders:
            self.fill_disk_usage(os.path.join(path, folder.name), folder)

    def build_tree(self):
        start_time = time.time()
        self.tree = File(self.disk)
        self.fill_disk_usage(self.disk, self.tree)
        print("--- %s seconds ---" % (time.time() - start_time))
        print(self.count, self.required_count)
        return self.tree

    def stop(self):
        self.running = False

