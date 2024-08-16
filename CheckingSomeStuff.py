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
from random import randint

class CreatingButton(QtCore.QThread):
    finished = QtCore.pyqtSignal(QPushButton)

    def __init__(self):
        super(CreatingButton, self).__init__()

    def run(self):
        button = QPushButton()
        self.finished.emit(button)

class MainWindow(QStackedWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.task = CreatingButton()
        self.task.finished.connect(self.on_created)
        self.task.start()
    
    def on_created(self, button):
        self.addWidget(button)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

