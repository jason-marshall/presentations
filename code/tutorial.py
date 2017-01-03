from PyQt4 import QtGui,QtCore
import sys, serial, io
import plotter
import numpy as np
import pylab
import time
import pyqtgraph
from datetime import datetime
from Tkinter import Tk
from tkFileDialog import asksaveasfile
from tkMessageBox import showerror
#from Tkinter.filedialog import asksaveasfile
#from Tkinter.messagebox import showerror
from random import randint
from collections import deque

class ExampleApp(QtGui.QMainWindow, plotter.Ui_TeledynePlotter):
    
    def __init__(self, parent=None):
    
        self.port = "/dev/ttyUSB0"
        self.baudrate = 115200
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.bytesize = serial.EIGHTBITS
        self.timeout = 1
        self.ser = None
        
        self.connect()

        pyqtgraph.setConfigOption('background', 'w') #before loading widget
        super(ExampleApp, self).__init__(parent)
        self.setupUi(self)
        self.startButton.clicked.connect(self.start_test)
        self.stopButton.clicked.connect(self.stop_test)
        self.newButton.clicked.connect(self.new_test)
        
        self.graphicsView.plotItem.showGrid(True, True, 0.7)
        self.color = pyqtgraph.hsvColor(0.38,0.92,0.47,alpha=.5)
        self.pen = pyqtgraph.mkPen(color=self.color,width=10)
        self.num_points = 100
        self.X = np.arange(self.num_points)
        self.Y = deque([0.0]*self.num_points)
        self.filename = None
        self.plainTextEdit.appendPlainText('No filename')
        
        self.test = False

    def connect(self):
        print("Reading from serial port {} ...".format(self.port))
        num_attempts = 7
        for i in range(1, num_attempts):
            if i is num_attempts-1:
                print('Failed too many times.  Exiting')
                exit()
            try:
                self.ser = serial.Serial(port = self.port,
                                         baudrate = self.baudrate,
                                         parity = self.parity,
                                         stopbits = self.stopbits,
                                         bytesize = self.bytesize,
                                         timeout = self.timeout)
                self.ser.flush()
                print('Success.')
                break
            except ValueError:
                print("Attempt {}: Parameters out of range, e.g. baud rate, data bits. Retrying ...".format(i))
                time.sleep(2)
            except serial.SerialException:
                print("Attempt {}: Device can not be found or can not be configured. Retrying ...".format(i))
                time.sleep(2)

    def file_header(self):
        header = 'Hour, Minute, Second, Pressure (psi)\n'
        return header

    def new_test(self):
        if self.test is True:
            showerror("New Test", "Test currently running!")
            return
        if self.filename is not None:
            self.filename.close()
            self.filename = None
            
        self.filename = asksaveasfile(mode='w',
                                      defaultextension=".txt")
        if self.filename is None:
            return
        
        self.filename.write(self.file_header())
        self.filename.flush()
        self.show_filename()

    def show_filename(self):
        if self.filename is None:
            self.plainTextEdit.appendPlainText('No filename')
            return
        self.plainTextEdit.appendPlainText(self.filename.name)

    def start_test(self):
        if self.filename is None:
            showerror("Start Test", "Need to select new test first!")
            return
        if self.test is True:
            showerror("Start Test", "A test is running!")
            return
        self.Y = deque([0.0]*self.num_points)
        self.test = True
        self.ser.flush()
        self.update()

    def stop_test(self):
        if self.test is False:
            showerror("Stop Test", "No test running")
            return
        self.test = False
        self.filename.close()
        self.filename = None
        self.show_filename()

    def get_data(self):
        line = self.read_line()

        if line is '':
            self.filename.write('-9999\n')
            print('Possible read error:\n')
            print(line)
        else:
            self.filename.write(line+'\n')
        self.filename.flush()
        dummy = self.Y.pop()
        try:
            self.Y.appendleft(float(line))
        except ValueError:
            self.Y.appendleft(dummy)

    def read_line(self):
        # return ead 
        line = bytearray()
        for i in range(0,33):
            c = self.ser.read(1)
            if c:
                if c >= '0' and c <= '9': 
                    line += c
                if c is ' ' or c is '\0':
                    break
            else:
                break
        time.sleep(0.25)
        self.ser.flushInput()
        return str(line)


    def update(self):
        if self.test is True:
            t1=datetime.now().strftime("%H, %M, %S.%f, ")
            self.filename.write(t1)
            self.get_data()
            self.graphicsView.plot(self.X,self.Y,pen=self.pen,clear=True)
            QtCore.QTimer.singleShot(1, self.update) # QUICKLY repeat

    def close_connection(self):
        self.ser.close()

if __name__=="__main__":
    Tk().withdraw()
    app = QtGui.QApplication(sys.argv)
    form = ExampleApp()
    form.show()
    app.exec_()
    #app.close_connection()
    print("DONE")
    exit()
