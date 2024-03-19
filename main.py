import sys
import os
from PySide6 import *
from qt_material import *
import psutil
from PyQt5.QtWidgets import QMainWindow, QApplication, QGraphicsDropShadowEffect, QSizeGrip, QProgressBar
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable
from interfaceui import *


from multiprocessing import cpu_count
import datetime
import platform
import shutil
from time import sleep

platforms = {
    'linux' : 'Linux',
    'linux1' : 'Linux',
    'linux2' : 'Linux',
    'darwin' : 'OS X',
    'win32' : 'Windows'
}

class WorkerSignals(QObject):

    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker(QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self.__init__())

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        self.kwargs['process_callback'] = self.signals.progress

    #@Slot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()







class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        apply_stylesheet(app, theme='dark_cyan.xml')

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(50)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 94, 150, 200))

        self.ui.centralwidget.setGraphicsEffect(self.shadow)

        self.setWindowIcon(QtGui.QIcon(":/icon/icons/airplay.svg"))
        self.setWindowTitle("Monitoring-Dashboard")

        QSizeGrip(self.ui.size_grip)

        self.ui.minimize_window_button.clicked.connect(lambda: self.showMinimized())

        self.ui.close_window_button.clicked.connect(lambda: self.close())

        self.ui.restore_window_button.clicked.connect(lambda: self.restore_or_maximize_window())

        #navigate to CPU page
        self.ui.cpu_page_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.cpu_and_memory))

        #navigate to Battery page
        self.ui.battery_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.battery))

        #navigate to System Inf page
        self.ui.system_inf_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.system_information))

        #navigate to Activity page
        self.ui.activity_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.activities))

        #navigate to Storage page
        self.ui.storage_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.storage))

        #navigate to Sensors page
        self.ui.sensors_page_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.sensors))

        #navigate to Networks page
        self.ui.networks_page_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.networks))


        def moveWindow(e):
            if self.isMaximized() == False:
                if e.buttons() == Qt.LeftButton:
                    self.move(self.pos() + e.globalPos() - self.clickPosition)
                    self.clickPosition = e.globalPos()
                    e.accept()

        self.ui.header_frame.mouseMoveEvent = moveWindow

        self.ui.open_close_side_bar_btn.clicked.connect(lambda: self.slideLeftMenu())

        for w in self.ui.menu_frame.findChildren(QPushButton):
            w.clicked.connect(self.applyButtonStyle)



        self.threadpool = QThreadPool()

        self.show()


        #self.battery()
        #self.cpu_ram()
        self.system_info()
        self.processes()
        self.storage()
        self.sensors()
        self.networks()
        self.psutil_thread()

    def psutil_thread(self):
        worker = Worker(self.cpu_ram)

        #Start Worker
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)

        self.threadpool.start(worker)

        battery_worker = Worker(self.battery)

        battery_worker.signals.result.connect(self.print_output)
        battery_worker.signals.finished.connect(self.thread_complete)
        battery_worker.signals.progress.connect(self.progress_fn)

        self.threadpool.start(battery_worker)


    def print_output(self, s):
        print(s)

    def thread_complete(self):
        print("THREAD COMPLETE")

    def progress_fn(self, n):
        print("%d%% done" % n)

    def networks(self):
        #Net Stats
        for x in psutil.net_if_stats():
            z = psutil.net_if_stats()
            rowPosition = self.ui.net_stats_table.rowCount()
            self.ui.net_stats_table.insertRow(rowPosition)

            self.create_table_widget(rowPosition, 0, x, "net_stats_table")
            self.create_table_widget(rowPosition, 1, str(z[x].isup), "net_stats_table")
            self.create_table_widget(rowPosition, 2, str(z[x].duplex), "net_stats_table")
            self.create_table_widget(rowPosition, 3, str(z[x].speed), "net_stats_table")
            self.create_table_widget(rowPosition, 4, str(z[x].mtu), "net_stats_table")

        #Net IO Counters
        for x in psutil.net_io_counters(pernic=True):
            z = psutil.net_io_counters(pernic=True)
            rowPosition = self.ui.net_io_table.rowCount()
            self.ui.net_io_table.insertRow(rowPosition)

            self.create_table_widget(rowPosition, 0, x, "net_io_table")
            self.create_table_widget(rowPosition, 1, str(z[x].bytes_sent), "net_io_table")
            self.create_table_widget(rowPosition, 2, str(z[x].bytes_recv), "net_io_table")
            self.create_table_widget(rowPosition, 3, str(z[x].packets_sent), "net_io_table")
            self.create_table_widget(rowPosition, 4, str(z[x].packets_recv), "net_io_table")
            self.create_table_widget(rowPosition, 5, str(z[x].errin), "net_io_table")
            self.create_table_widget(rowPosition, 6, str(z[x].errout), "net_io_table")
            self.create_table_widget(rowPosition, 7, str(z[x].dropin), "net_io_table")
            self.create_table_widget(rowPosition, 8, str(z[x].dropout), "net_io_table")

        for x in psutil.net_if_addrs():
            z = psutil.net_if_addrs()
            for y in z[x]:
                rowPosition = self.ui.net_addresses_table.rowCount()
                self.ui.net_addresses_table.insertRow(rowPosition)

                self.create_table_widget(rowPosition, 0, str(x), "net_addresses_table")
                self.create_table_widget(rowPosition, 1, str(y.family), "net_addresses_table" )
                self.create_table_widget(rowPosition, 2, str(y.address), "net_addresses_table")
                self.create_table_widget(rowPosition, 3, str(y.netmask), "net_addresses_table")
                self.create_table_widget(rowPosition, 4, str(y.broadcast), "net_addresses_table")

        for x in psutil.net_connections():
            z = psutil.net_connections()
            rowPosition = self.ui.net_connections_table.rowCount()
            self.ui.net_connections_table.insertRow(rowPosition)

            self.create_table_widget(rowPosition, 0, str(x.fd), "net_connections_table")
            self.create_table_widget(rowPosition, 1, str(x.family), "net_connections_table")
            self.create_table_widget(rowPosition, 2, str(x.type), "net_connections_table")
            self.create_table_widget(rowPosition, 3, str(x.laddr), "net_connections_table")
            self.create_table_widget(rowPosition, 4, str(x.raddr), "net_connections_table")
            self.create_table_widget(rowPosition, 5, str(x.status), "net_connections_table")
            self.create_table_widget(rowPosition, 6, str(x.pid), "net_connections_table")




    def sensors(self):
        if sys.platform == 'linux' or sys.platform == 'linux1' or sys.platform == 'linux2':
            for x in psutil.sensors_temperatures():
                for y in psutil.sensors_temperatures()[x]:
                    rowPosition = self.ui.sensorTable.rowCount()
                    self.ui.sensorTable.insertRow(rowPosition)

                    self.create_table_widget(rowPosition, 0, x, "sensorTable")
                    self.create_table_widget(rowPosition, 1, y.label, "sensorTable")
                    self.create_table_widget(rowPosition, 2, str(y.current), "sensorTable")
                    self.create_table_widget(rowPosition, 3, str(y.high), "sensorTable")
                    self.create_table_widget(rowPosition, 4, str(y.critical), "sensorTable")

                    temp_per = (y.current / y.high) * 100

                    progressBar =  QProgressBar(self.ui.sensorTable)
                    progressBar.setOjectName(u"progressBar")
                    progressBar.setValue(temp_per)
                    self.ui.sensorTable.setCellWidget(rowPosition, 5, progressBar)

        else:
            global platforms
            rowPosition = self.ui.sensorTable.rowCount()
            self.ui.sensorTable.insertRow(rowPosition)

            self.create_table_widget(rowPosition, 0, "Function not supported on " + platforms[sys.platform], "sensorTable")
            self.create_table_widget(rowPosition, 1, "N/A", "sensorTable")
            self.create_table_widget(rowPosition, 2, "N/A", "sensorTable")
            self.create_table_widget(rowPosition, 3, "N/A", "sensorTable")
            self.create_table_widget(rowPosition, 4, "N/A", "sensorTable")
            self.create_table_widget(rowPosition, 5, "N/A", "sensorTable")

    def storage(self):
        global platforms
        storage_device = psutil.disk_partitions(all=False)
        z = 0
        for x in storage_device:
            rowPosition = self.ui.storageTable.rowCount()
            self.ui.storageTable.insertRow(rowPosition)

            self.create_table_widget(rowPosition, 0, x.device, "storageTable")
            self.create_table_widget(rowPosition, 1, x.mountpoint, "storageTable")
            self.create_table_widget(rowPosition, 2, x.fstype, "storageTable")
            self.create_table_widget(rowPosition, 3, x.opts, "storageTable")


            if sys.platform == 'linux' or sys.platform == 'linux1' or sys.platform == 'linux2':
                self.create_table_widget(rowPosition, 4, str(x.maxfile), "storageTable")
                self.create_table_widget(rowPosition, 5, str(x.maxpath), "storageTable")
            else:
                self.create_table_widget(rowPosition, 4, "Function not available on " + platforms[sys.platform], "storageTable")
                self.create_table_widget(rowPosition, 5, "Function not available on " + platforms[sys.platform], "storageTable")

            disk_usage =shutil.disk_usage(x.mountpoint)
            self.create_table_widget(rowPosition, 6, str((disk_usage.total / (1024 * 1024 * 1024))) + " GB", "storageTable")
            self.create_table_widget(rowPosition, 7, str((disk_usage.free / (1024 * 1024 * 1024))) + " GB", "storageTable")
            self.create_table_widget(rowPosition, 8, str((disk_usage.used / (1024 * 1024 * 1024))) + " GB", storageTable)

            full_disk = (disk_usage.used / disk_usage.total) * 100
            progressBar = QProgressBar(self.ui.storageTable)
            progressBar.setOjectName(u"progressBar")
            progressBar.setValue(full_disk)
            self.ui.storageTable.setCellWidget(rowPosition, 9, progressBar)



    def create_table_widget(self, rowPosition, columnPosition, text, tableName):
        qTableWidgetItem = QTableWidgetItem()
        getattr(self.ui.tableName).setItem(rowPosition, columnPosition, qTableWidgetItem)
        qTableWidgetItem = getattr(self.ui.tableName).item(rowPosition, columnPosition)

        qTableWidgetItem.setText(text)

    def processes(self):
        for x in psutil.pids():
            rowPosition = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(rowPosition)

            try:
                process = psutil.Process(x)

                self.create_table_widget(rowPosition, 0, str(process.pid), "tableWidget")
                self.create_table_widget(rowPosition, 1, process.name(), "tableWidget")
                self.create_table_widget(rowPosition, 2, process.status(), "tableWidget")
                self.create_table_widget(rowPosition, 3, str(datetime.datetime.utcfromtimestamp(process.create_time()).strftime('%Y-%m-%d-%H-%M-%S')), "tableWidget")


                suspend_btn = QPushButton(self.ui.tableWidget)
                suspend_btn.setText('Suspend')
                suspend_btn.setStylesheet("color: brown")
                self.ui.tableWidget.setCellWidget(rowPosition, 4, suspend_btn)

                resume_btn = QPushButton(self.ui.tableWidget)
                resume_btn.setText('Resume')
                resume_btn.setStylesheet("color: green")
                self.ui.tableWidget.setCellWidget(rowPosition, 5, resume_btn)

                terminate_btn = QPushButton(self.ui.tableWidget)
                terminate_btn.setText('Terminate')
                terminate_btn.setStylesheet("color: orange")
                self.ui.tableWidget.setCellWidget(rowPosition, 6, terminate_btn)

                kill_btn = QPushButton(self.ui.tableWidget)
                kill_btn.setText('Kill')
                kill_btn.setStylesheet("color: red")
                self.ui.tableWidget.setCellWidget(rowPosition, 7, kill_btn)
            except Exception as e:
                print(e)

        self.ui.activity_search.textChanged.connect(self.findName)

    def findName(self):
        name = self.ui.activity_search.text().lower()
        for row in range(self.ui.tableWidget.rowCount()):
            item = self.ui.tableWidget.item(row, 1)
            self.ui.tableWidget.setRowHidden(row, name not in item.text().lower())

    def system_info(self):
        time = datetime.datetime.now().strftime("%I:%M:%S %p")
        self.ui.system_date.setText(str(time))
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.ui.system_time.setText(str(date))

        self.ui.system_machine.setText(platform.machine())
        self.ui.system_version.setText(platform.version())
        self.ui.system_platform.setText(platform.platform())
        self.ui.system_system.setText(platform.system())
        self.ui.system_processor.setText(platform.processor())


    def cpu_ram(self, progress_callback):
        while True:
            totalRam = 1.0
            totalRam = psutil.virtual_memory()[0] * totalRam
            totalRam = totalRam / (1024 * 1024 * 1024)
            self.ui.total_ram.setText(str("{:.4f}".format(totalRam) + ' GB'))

            availRam = 1.0
            availRam = psutil.virtual_memory()[1] * availRam
            availRam = availRam / (1024 * 1024 * 1024)
            self.ui.available_ram.setText(str("{:.4f}".format(availRam) + ' GB'))

            ramUsed = 1.0
            ramUsed = psutil.virtual_memory()[3] * ramUsed
            ramUsed = ramUsed / (1024 * 1024 * 1024)
            self.ui.used_ram.setText(str("{:.4f}".format(ramUsed) + ' GB'))

            ramFree = 1.0
            ramFree = psutil.virtual_memory()[4] * ramFree
            ramFree = ramFree / (1024 * 1024 * 1024)
            self.ui.free_ram.setText(str("{:.4f}".format(ramFree) + ' GB'))

            ramUsages = str(psutil.virtual_memory()[2]) + '%'
            self.ui.ram_usage.setText(str("{:.4f}".format(totalRam) + ' GB'))

            core = cpu_count()
            self.ui.cpu_count.setText(str(core))

            cpuPer = psutil.cpu_percent()
            self.ui.cpu_per.setText(str(cpuPer) + " %")

            cpuMainCore = psutil.cpu_count(logical=False)
            self.ui.cpu_main_core.setText(str(cpuMainCore))

            self.ui.cpu_percentage.rpb_setMaximum(100)
            self.ui.cpu_percentage.rpb_setValue(cpuPer)
            self.ui.cpu_percentage.rpb_setBarStyle('Hybrid2')
            self.ui.cpu_percentage.rpb-setLineColor((255, 30, 99))
            self.ui.cpu_percentage.rpb_setPieColor((45, 75, 83))
            self.ui.cpu_percentage.rpb_setTextColor((255, 255, 255))
            self.ui.cpu_percentage.rpb_setInittialPos('West')
            self.ui.cpu_percentage.rpb_setTextFormat('Percentage')
            self.ui.cpu_percentage.rpb_setTextFormat('Arial')
            self.ui.cpu_percentage.rpb_setLineWidth(15)
            self.ui.cpu_percentage.rpb_setPatWidth(15)
            self.ui.cpu_percentage.rpb_setLineCap('RoundCap')
            self.ui.ram_percentage.spb_setMinimum((0, 0, 0))
            self.ui.ram_percentage.spb_setMaximum((totalRam, totalRam, totalRam))
            self.ui.ram_percentage.spb_setValue((availRam, ramUsed, ramFree))
            self.ui.ram_percentage.spb_lineColor(((6, 233, 38), (6, 201, 233), (233, 6, 201)))
            self.ui.ram_percentage.spb_setInitialPos(('West', 'West', 'West'))
            self.ui.ram_percentage.spb_lineWidth(15)
            self.ui.ram_percentage.spb_lineStyle(('SolidLine', 'SolidLine', 'SolidLine'))
            self.ui.ram_percentage.spb_lineCap(('RoundCap', 'RoundCap', 'RoundCap'))
            self.ui.ram_percentage.spb_setPathHidden(True)

            sleep(1)



    def secs2hours(self, secs):
        mm, ss = divmod(secs, 60)
        hh, mm = divmod(mm, 60)
        return "%d:%02d:%02d (H:M:S)" % (hh, mm, ss)

    def battery(self, progress_callback):
        while True:
            batt = psutil.sensors_battery()

            if not hasattr(psutil, "sensors_battery"):
                self.ui.battery_status.setText("Platform not supported")
            if batt is None:
                self.ui.battery_status.setText("No battery installed")

            if batt.power_plugged:
                self.ui.battery_charge.setText(str(round(batt.percent, 2))+"%")
                self.ui.battery_time_left.setText("N/A")
                if batt.percent < 100:
                    self.ui.battery_status.setText("Charging")
                else:
                    self.ui.battery_status.setText("Fully Charged")
                self.ui.battery_plugged.setText("Yes")
            else:
                self.ui.battery_charge.setText(str(round(batt.percent, 2))+"%")
                self.ui.battery_time_left.setText(self.secs2hours(batt.secsleft))
                if batt.percent < 100:
                    self.ui.battery_status.setText("Discharging")
                else:
                    self.ui.battery_status.setText("Fully Charged")
                self.ui.battery_plugged.setText("No")

            self.ui.battery_usage.rpb_setMaximum(100)
            self.ui.battery_usage.rpb_setValue(batt.percent)
            self.ui.battery_usage.rpb_setBarStyle('Hybrid2')
            self.ui.battery_usage.rpb_setLineColor((255, 30, 99))
            self.ui.battery_usage.rpb_setPieColor((45, 74, 83))
            self.ui.battery_usage.rpb_setTextColor((255, 255, 255))
            self.ui.battery_usage.rpb_setInititalPos('West')
            self.ui.battery_usage.rpb_setTextFormat('Percentage')
            self.ui.battery_usage.rpb_setLineWidth(15)
            self.ui.battery_usage.rpb_setPatWidth(15)
            self.ui.battery_usage.rpb_setLineCap('RoundCap')

            sleep(1)

    def applyButtonStyle(self):
        for w in self.ui.menu_frame.findChildren(QPushButton):
            if w.objectName() != self.sender().objectName():
                w.setStyleSheet("border-bottom: none;")

        self.sender().setStyleSheet("border-bottom: 2px solid;")
        return



    def slideLeftMenu(self):
        width = self.ui.left_menu_cont_frame.width()

        if width == 40:
            newWidth = 200
        else:
            newWidth = 40

        self.animation = QPropertyAnimation(self.ui.left_menu_cont_frame, b"miniumWidth")
        self.animation.setDuration(250)
        self.animation.setStartValue(width)
        self.animation.setEndValue(newWidth)
        self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
        self.animation.start()

    def mousePressEvent(self, event):
        self.clickPosition = event.globalPos()



    def restore_or_maximize_window(self):
        if self.isMaximized():
            self.showNormal()
            self.ui.restore_window_button.setIcon(QtGui.QIcon((":/icon/icons/restore.png")))
        else:
            self.showMaximized()
            self.ui.restore_window_button.setIcon(QtGui.QIcon(":/icon/icons/maximize.svg"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
