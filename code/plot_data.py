#!/usr/bin/env python

import serial, sys, io
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from mpl_toolkits.axes_grid1 import host_subplot

from time import sleep
from time import time
from datetime import datetime
from collections import deque

# main function
# plot class
class LivePlot:
  
  # constr
  def __init__(self, strPort, maxLen):

    # count of number of data timesteps taken
    self.count = -1

    # continuously logging data file name
    self.dataFileName = 'streaming'
    self.dataFileCount = 0
    self.dataFile = open(self.dataFileName+'{0:04d}'.format(self.dataFileCount)+'.data','a+')

    # test data file name
    self.testFileName = 'test'
    self.testFileCount = 0
    self.testFile = open('initial_test.data','a+')

    # plot attributes
    title_font_size = 72
    ylabel_font_size = 48
    tick_font_size = 48
    legend_font_size = 32
    image_height = 15.0
    image_width = 10.0
    plot_line_width = 5
    self.filterLen = 10
    self.data_x = np.linspace(0.0,1.50,maxLen)
    self.length_data = 25
    
    # initialize data
    self.maxLen = maxLen
    self.data_displacement_actual = deque([0.0]*maxLen)
    self.data_displacement = deque([0.0]*maxLen)
    self.data_displacement_avg = deque([0.0]*self.filterLen)
    self.data_gravity = deque([0.0]*maxLen)
    self.data_gravity_x = deque([0.0]*maxLen)
    self.data_gravity_y = deque([0.0]*maxLen)
    self.data_gravity_z = deque([1.0]*maxLen)
    self.data_load_cell_actual = deque([1.0]*maxLen) 
    self.data_load_cell = deque([0.0]*maxLen)
    self.data_load_cell_avg = deque([0.0]*self.filterLen)
    self.data_inner_warning = deque([0.0]*maxLen)
    self.data_outer_warning = deque([0.0]*maxLen)
    self.data_auto_start = deque([0.0]*maxLen)

    # setup figure
    plt.ion()
    self.fig = plt.figure(figsize=(image_height,image_width))
    self.fig.suptitle("0g Real Time Experimental Data", fontsize=title_font_size)
    self.fig.set_size_inches(image_height,image_width,forward=True)
    self.fig.set_facecolor('w')

    # setup axis 1
    self.ax1 = self.fig.add_subplot(411)
    self.ax1.grid(color='0.5', which='major', axis='both')
    self.ax1.set_xlim(0.0,1.50)
    self.ax1.set_ylim(-5,30)
    self.ax1.set_ylabel("Displacement (mm)", fontsize=ylabel_font_size)
    self.line1, = self.ax1.plot(self.data_x,
                                self.data_displacement,
                                label='Displacement Avg (mm)',
                                linewidth=plot_line_width,
                                color='b')
    self.line_disp_act, = self.ax1.plot(self.data_x,
                                self.data_displacement_actual,
                                label='Displacement (mm)',
                                linewidth=plot_line_width,
                                color='g')
    for tick in self.ax1.xaxis.get_major_ticks():
      tick.label.set_fontsize(tick_font_size)

    for tick in self.ax1.yaxis.get_major_ticks():
      tick.label.set_fontsize(tick_font_size)
    self.ax1.legend(fontsize=legend_font_size)

    # setup axis 2
    self.ax2 = self.fig.add_subplot(412)
    self.ax2.grid(color='0.5', which='major', axis='both')
    self.ax2.set_xlim(0.0,1.50)
    self.ax2.set_ylim(0.0,2.0)
    self.ax2.set_ylabel("Gravity", fontsize=ylabel_font_size)
    self.line4, = self.ax2.plot(self.data_x,
                                self.data_gravity_x,
                                label='Gravity (X)',
                                linewidth=plot_line_width,
                                color='b')
    self.line5, = self.ax2.plot(self.data_x,
                                self.data_gravity_y,
                                label='Gravity (Y)',
                                linewidth=plot_line_width,
                                color='r')
    self.line6, = self.ax2.plot(self.data_x,
                                self.data_gravity_z,
                                label='Gravity (Z)',
                                linewidth=plot_line_width,
                                color='c')
    self.line2, = self.ax2.plot(self.data_x,
                                self.data_gravity,
                                label='Gravity Magnitude',
                                linewidth=plot_line_width,
                                color='g')
    for tick in self.ax2.xaxis.get_major_ticks():
      tick.label.set_fontsize(tick_font_size)

    for tick in self.ax2.yaxis.get_major_ticks():
      tick.label.set_fontsize(tick_font_size)
    self.ax2.legend(fontsize=legend_font_size)

    # setup axis 3
    self.ax3 = self.fig.add_subplot(413)
    self.ax3.grid(color='0.5', which='major', axis='both')
    self.ax3.set_xlim(0.0,1.50)
    self.ax3.set_ylim(-200.0,100.0)
    self.ax3.set_ylabel("Load (N)", fontsize=ylabel_font_size)
    self.ax3.set_xlabel("Time", fontsize=ylabel_font_size)
    self.line3, = self.ax3.plot(self.data_x,
                                self.data_load_cell,
                                label='Load Avg (N)',
                                linewidth=plot_line_width,
                                color='c')
    self.line_load_act, = self.ax3.plot(self.data_x,
                                self.data_load_cell_actual,
                                label='Load (N)',
                                linewidth=plot_line_width,
                                color='g')
    for tick in self.ax3.xaxis.get_major_ticks():
      tick.label.set_fontsize(tick_font_size)

    for tick in self.ax3.yaxis.get_major_ticks():
      tick.label.set_fontsize(tick_font_size)
    self.ax3.legend(fontsize=legend_font_size)

    # setup axis 4
    self.ax4 = self.fig.add_subplot(414)
    self.ax4.grid(color='0.5', which='major', axis='both')
    self.ax4.set_xlim(0.0,1.50)
    self.ax4.set_ylim(-0.1,1.1)
    self.ax4.set_ylabel("True/False", fontsize=ylabel_font_size)
    self.ax4.set_xlabel("Time", fontsize=ylabel_font_size)
    self.line7, = self.ax4.plot(self.data_x,
                                self.data_auto_start,
                                label='Auto Start',
                                linewidth=plot_line_width,
                                color='c')
    self.line8, = self.ax4.plot(self.data_x,
                                self.data_inner_warning,
                                label='Inner Warning',
                                linewidth=plot_line_width,
                                color='g')
    self.line9, = self.ax4.plot(self.data_x,
                                self.data_outer_warning,
                                label='Outer Warning',
                                linewidth=plot_line_width,
                                color='b')
    for tick in self.ax4.xaxis.get_major_ticks():
      tick.label.set_fontsize(tick_font_size)

    for tick in self.ax4.yaxis.get_major_ticks():
      tick.label.set_fontsize(tick_font_size)

    # test stuff
    self.testRunning = False
    self.testFile = open('test_running_on_start.data','a+')

    # open serial port
    self.ser = serial.Serial(strPort, 115200)
    self.ser.flush()

  # add to buffer
  def addToBuf(self, buf, val):
    if len(buf) < self.maxLen:
      buf.append(val)
    else:
      buf.pop()
      buf.appendleft(val)

  # add to buffer filter 
  def addToBufFilter(self, buf, val):
    if len(buf) <self.filterLen:
      buf.append(val)
    else:
      buf.pop()
      buf.appendleft(val)

  # add to buffer filter negative values only
  def addToBufFilterNeg(self, buf, val):
    if val > 0.0:
      val = 0.0
    if len(buf) <self.filterLen:
      buf.append(val)
    else:
      buf.pop()
      buf.appendleft(val)
    
  # add data
  def add(self, temp_data):
    assert(len(temp_data) == self.length_data)

    self.addToBufFilter(self.data_load_cell_avg, temp_data[14])
    self.addToBuf(self.data_load_cell, np.mean(self.data_load_cell_avg))
    self.addToBuf(self.data_load_cell_actual, temp_data[14])
    self.addToBufFilter(self.data_displacement_avg, temp_data[16])
    self.addToBuf(self.data_displacement, np.mean(self.data_displacement_avg))
    self.addToBuf(self.data_displacement_actual, temp_data[16])
    self.addToBuf(self.data_gravity, temp_data[17])
    self.addToBuf(self.data_gravity_x, temp_data[18])
    self.addToBuf(self.data_gravity_y, temp_data[19])
    self.addToBuf(self.data_gravity_z, temp_data[20])
    self.addToBuf(self.data_auto_start, temp_data[10])
    self.addToBuf(self.data_inner_warning, temp_data[11])
    self.addToBuf(self.data_outer_warning, temp_data[12])
    
  # update plot
  def update(self):
    try:

      # increment data count
      self.count += 1

      # reset data count to not overrun int size
      if self.count == 10000000:
        self.count = 0

        # change to new file to prevent file from getting huge
        self.dataFileCount += 1
        self.dataFile.close()
        self.dataFile = open(self.dataFileName+'{0:04d}'.format(self.dataFileCount)+'.data','a+')

      # read data line
      line = self.ser.readline()

      # split data into array
      temp_data = [float(val) for val in line.split()]

      # write data to file
      self.write_data(temp_data)

      # write test data if test is running
      self.checkTest(temp_data[24])
      if self.testRunning is True:
        self.write_test(temp_data)

      # add data to self data structures
      if(len(temp_data) == self.length_data):
        self.add(temp_data)

      # plot data every n steps
      if self.count%10 == 0:
        self.line1.set_ydata(self.data_displacement)
        self.line_disp_act.set_ydata(self.data_displacement_actual)
        self.line2.set_ydata(self.data_gravity)
        self.line3.set_ydata(self.data_load_cell)
        self.line_load_act.set_ydata(self.data_load_cell_actual)
        self.line4.set_ydata(self.data_gravity_x)
        self.line5.set_ydata(self.data_gravity_y)
        self.line6.set_ydata(self.data_gravity_z)
        self.line7.set_ydata(self.data_auto_start)
        self.line8.set_ydata(self.data_inner_warning)
        self.line9.set_ydata(self.data_outer_warning)
        self.fig.canvas.draw()

      # everything good, keep running
      return True

    except ValueError:
      print('ValueError (misread of serial data?)')
      # keep running
      return True 
    except IndexError:
      print('IndexError (misread of serial data?)')
      # keep running
      return True
    except KeyboardInterrupt:
      # exit
      return False

  # write line to file
  def write_line(self, temp_data, my_file):
    for i in range(len(temp_data)):
      my_file.write('{0:9.5f} '.format(temp_data[i]))
    my_file.write('\n')

  # write data to streaming file
  def write_data(self, temp_data):
    self.write_line(temp_data, self.dataFile)

  # write data to test file
  def write_test(self, data):
    self.write_line(data, self.testFile)

  # check to see if test is running
  def checkTest(self, temp_test_running):

    # check if test is running
    if temp_test_running < 0.5:
      running = False
    else:
      running = True

    # logic switch based on running state
    if self.testRunning is False and running is False:
      return
    elif self.testRunning is False and running is True:
      self.testRunning = True
      self.testFile.close()
      self.testFile = open(self.testFileName+'-'+ datetime.now().strftime('%Y-%m-%d-%H-%M-%S')+'.data','a+')
      self.testFileCount += 1
      return
    elif self.testRunning is True and running is True:
      return
    elif self.testRunning is True and running is False:
      self.testRunning = False
      return
        
  # clean up
  def close(self):

    # close serial
    self.ser.flush()
    self.ser.close()

    # close data files
    self.dataFile.close()
    self.testFile.close()
 
# main() function
def main():
  
  #SerialDevice = "/dev/ttyACM0"
  #port = 'dummy'
  port = "/dev/ttyACM0"
  baudrate = 19200
  parity = serial.PARITY_NONE
  stopbits = serial.STOPBITS_ONE
  bytesize = serial.EIGHTBITS
  timeout = 1

  print("Reading from serial port {} ...".format(port))
  num_attempts = 7
  for i in range(1, num_attempts):
    if i is num_attempts-1:
      print('Failed too many times.  Exiting')
      exit()
    try:
      ser = serial.Serial(port = port,
                          baudrate = baudrate,
                          parity = parity,
                          stopbits = stopbits,
                          bytesize = bytesize,
                          timeout = timeout)
      ser.flush()
      print('Success.')
      break
    except ValueError:
      print("Attempt {}: Parameters out of range, e.g. baud rate, data bits. Retrying ...".format(i))
      sleep(2)
    except serial.SerialException:
      print("Attempt {}: Device can not be found or can not be configured. Retrying ...".format(i))
      sleep(2)

  #cur = time()
  cur = datetime.now().strftime("%S.%f")
  for i in range(0,100):
    ser.write("PR\r")

    # return ead 
    eol = '/'
    leneol = len(eol)
    line = bytearray()
    while True:
      c = ser.read(1)
      if c:
        line += c
        if line[-leneol:] == eol:
          break
      else:
        break

  fin = datetime.now().strftime("%S.%f")
  #fin = time()
  ser.close()
  #line = ser.readline()
  print(line)
  print(10.0*(float(fin)-float(cur)))
  print(fin)
  print(cur)
  


  '''
  # plot parameters
  LivePlot = AnalogPlot(SerialDevice, 100)

  keepRunning = True
  
  while(keepRunning):
    keepRunning = analogPlot.update()
    
  # clean up
  analogPlot.close()
    
  print('exiting.')
  '''
 
# call main
if __name__ == '__main__':
  main()
