import sys
import time
from PyQt5 import QtCore, QtWidgets

class SlowTask(QtCore.QThread):
    updated = QtCore.pyqtSignal(int)
    running = False

    def __init__(self, *args, **kwargs):
        super(SlowTask, self).__init__(*args, **kwargs)
        self.percent = 0
        self.running = True

    def run(self):
        while self.running:
            self.percent += 10
            self.percent %= 100
            self.updated.emit(int(self.percent))
            time.sleep(0.1)

    def stop(self):
        self.running = False


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle('Test')
        self.resize(446, 207)

        self.progressbar = QtWidgets.QProgressBar(self)
        self.progressbar.setGeometry(QtCore.QRect(40, 70, 381, 23))
        self.progressbar.setProperty('value', 0)

        self.btn_start = QtWidgets.QPushButton('Start', self)
        self.btn_start.setGeometry(QtCore.QRect(110, 110, 75, 23))
        self.btn_start.setEnabled(True)
        self.btn_start.clicked.connect(self.on_start)

        self.btn_stop = QtWidgets.QPushButton('Stop', self)
        self.btn_stop.setGeometry(QtCore.QRect(260, 110, 75, 23))
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.on_stop)

    def toggle_buttons(self):
        self.btn_start.setEnabled(not self.btn_start.isEnabled())
        self.btn_stop.setEnabled(not self.btn_stop.isEnabled())

    def on_update(self, data):
        self.progressbar.setValue(data)
        if data == 90:
            self.on_stop()

    def on_start(self):
        self.toggle_buttons()
        self.task = SlowTask(self)
        self.task.updated.connect(self.on_update)
        self.task.start()

    def on_stop(self):
        self.task.stop()
        self.progressbar.setValue(0)
        self.toggle_buttons()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())