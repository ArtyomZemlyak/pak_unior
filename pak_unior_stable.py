import matplotlib.pyplot as plt
import serial
import serial.tools.list_ports
from struct import unpack
import numpy as np
import time
from time import sleep, process_time
from collections import deque
import re
from scipy.fft import rfft, rfftfreq
from numpy import array, sign, zeros
from scipy.interpolate import interp1d
import msvcrt
import random



std_speed = 57600 #Скорость COM порта
com_port = 'COM6'

paritys = 'N'   #Бит четности
stopbitss = 1            #Количество стоп-бит
bite_size = 8               #Биты данных
t_out = 1                   #Таймаут в секундах, должен быть больше 1с
flag1 = 0                     #Флаг для остановки программы, устанавливается в 1, если найдена сигнатура  
reading_bytes = 10          #Количество байт для чтения после открытия порта
keyword = b'\x00\x00\x00'     #!Сигнатура для поиска
cmd = 0xff
EEG = 0
k = [1]

NOMBER_OF_VALUES = 200
LABELS = ['EEG', 'EEG_CURVED', 'FURIE(EEG)', 'FURIE(EEG_CURVED)', 'FURIE(EEG)_CURVED', '(FURIE(EEG)_m_FURIE(EEG_CURVED))_CURVED']

plt.ion()

time_start = process_time()

piSerial = serial.Serial() 
print(f'S:- Port:{piSerial.is_open}')
piSerial.close()
print(f'S:- Port:{piSerial.is_open}')

def unior_begin(channel):
    #Setup COM-port and connect to PAK UNIOR
    piSerial.baudrate = std_speed
    piSerial.port = com_port;
    piSerial.timeout = 1
    piSerial.write_timeout = 1
    piSerial.open(); print(f'|PORT:{com_port}| OPENED') 
    piSerial.write(cmd); print(f'|WRITE| {cmd}') 
    print('|WHAITING...', end='') 
    status = 0
    while True: 
        if msvcrt.kbhit():                  # Button pressed?
                key = ord(msvcrt.getch())   # Value of batton
                if key == 13:               # Enter:
                    piSerial.close()
                    break
        s = piSerial.readline()
        print(end='.')
        if s == b'OK\n':
            print('CONNECTED')
            piSerial.write((str(channel) + '\r\n\0').encode()) # send channels mask
            print('|WHAITING DATA...')
            status = 1
            break
    return status
            
def curve_on(data):
    #Curved on array of smth values
    s = array(data) #vector of values.
    q_u = zeros(s.shape)
    q_l = zeros(s.shape)
    u_x = [0,]
    u_y = [s[0],]
    l_x = [0,]
    l_y = [s[0],]
    for k in range(1,len(s)-1):
        if (sign(s[k]-s[k-1])==1) and (sign(s[k]-s[k+1])==1):
            u_x.append(k)
            u_y.append(s[k])
        if (sign(s[k]-s[k-1])==-1) and ((sign(s[k]-s[k+1]))==-1):
            l_x.append(k)
            l_y.append(s[k])
    u_x.append(len(s)-1)
    u_y.append(s[-1])
    l_x.append(len(s)-1)
    l_y.append(s[-1])
    u_p = interp1d(u_x,u_y, kind = 'cubic',bounds_error = False, fill_value=0.0)
    l_p = interp1d(l_x,l_y,kind = 'cubic',bounds_error = False, fill_value=0.0)
    for k in range(0,len(s)):
        q_u[k] = u_p(k) #up
        q_l[k] = l_p(k) #down
    return q_u
            
class DynamicUpdate():
    #Suppose we know the x range
    min_x = process_time()
    max_x = process_time() + 30

    def on_launch(self):
        #Set up plot
        self.status = 0
        self.update_value = 0
        self.figure, self.ax = plt.subplots(nrows=3, ncols=2, figsize=(20, 20))
        self.figure.set_label('EEG')
        self.lines = []
        self.activate_value = 400
        self.activate_diapason = [9, 14]
        for i, axe in enumerate(self.ax.ravel()):
            line, = axe.plot([],[], 'b-', label=LABELS[i])
            self.lines.append(line)
            if i == 5:
                x = rfftfreq(NOMBER_OF_VALUES, 1 / 60)  
                x_f = [float("%.2f" % float(j)) for j in x]
                y = [self.activate_value for j in x_f]
                diapason_x = [0, 0]
                for j, val in enumerate(x_f):
                
                    if (val > self.activate_diapason[0]) and (diapason_x[0] == 0):
                        diapason_x[0] = j
                    if (val > self.activate_diapason[1]) and (diapason_x[1] == 0):
                        diapason_x[1] = j 
                diapason = range(diapason_x[0], diapason_x[1])
                for j in diapason:
                    y[j] = self.activate_value + 100
                line, = axe.plot(x_f, y, 'r--', label='ACTIVATE_VALUE')
                self.lines.append(line)
            axe.grid()
        #Autoscale on unknown axis and known lims on the other
        #self.ax.set_autoscaley_on(True)
        #self.ax.set_xlim(self.min_x, self.max_x)

    def on_running(self, xdata, ydata):
        #Update data (with the new _and_ the old points)
        
        #####EEG####################################################   
        self.lines[0].set_xdata(xdata)
        self.lines[0].set_ydata(ydata)
        if self.update_value == 0:
            self.ax.ravel()[0].relim()
            self.ax.ravel()[0].autoscale_view(True, True, True)
            self.ax.ravel()[0].legend()
        else:
            #####EEG_CURVED#############################################
            yf = rfft(ydata)
            xf = rfftfreq(NOMBER_OF_VALUES, 1 / 60)  
            xf_f = [float("%.2f" % float(i)) for i in xf]
            yf_f = [float("%.2f" % float(i)) for i in yf]
            for k in range(0,3):        
                yf_f[k] = 0
            self.lines[2].set_xdata(xf_f)
            self.lines[2].set_ydata(yf_f)
            
            #####FURIE(EEG)#############################################
            yf_curved = curve_on(yf_f)
            self.lines[4].set_xdata(xf_f)
            self.lines[4].set_ydata(yf_curved)
            
            #####FURIE(EEG_CURVED)######################################
            ydata_curved = curve_on(ydata)
            self.lines[1].set_xdata(xdata)
            self.lines[1].set_ydata(ydata_curved)
            
            #####FURIE(EEG)_CURVED######################################
            yf2 = rfft(ydata_curved)
            yf_f2 = [float("%.2f" % float(i)) for i in yf2]
            for k in range(0,3):        
                yf_f2[k] = 0
            self.lines[3].set_xdata(xf_f)
            self.lines[3].set_ydata(yf_f2)
            
            #####(FURIE(EEG)_m_FURIE(EEG_CURVED))_CURVED###############
            yf_m = []
            for y1, y2 in zip(yf_f, yf_f2):
                y_ = abs(y1) - abs(y2)
                if (y_ > 0):
                    yf_m.append(y_)
                else:
                    yf_m.append(0.0)
            yf_m_curved = curve_on(yf_m)
            #yf_m_curved = curve_on(yf_m_curved)
            self.lines[5].set_xdata(xf_f)
            self.lines[5].set_ydata(yf_m_curved)
            
            self.activate_value = np.mean(yf_m_curved) + 50
            y = [self.activate_value for j in xf_f]
            diapason_x = [0, 0]
            for j, val in enumerate(xf_f):
            
                if (val > self.activate_diapason[0]) and (diapason_x[0] == 0):
                    diapason_x[0] = j
                if (val > self.activate_diapason[1]) and (diapason_x[1] == 0):
                    diapason_x[1] = j 
            diapason = range(diapason_x[0], diapason_x[1])
            for j in diapason:
                y[j] = self.activate_value + 100
            self.lines[6].set_xdata(xf_f)
            self.lines[6].set_ydata(y)
            
            #Need both of these in order to rescale
            for i, axe in enumerate(self.ax.ravel()):
                axe.relim()
                axe.autoscale_view(True, True, True)
                axe.legend()
                
            self.update_value = 0
            
        #We need to draw *and* flush
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()
        
    def unior_read(self, channel):
        #Read data from PAK UNIOR
        if piSerial.inWaiting() > 0:
            piSerial.flushInput()       
        piSerial.write((str(channel) + '\r\n\0').encode())
        beg_time = process_time()
        while piSerial.inWaiting() < 4:
            if process_time() - beg_time > 1:
                return 0
        try:
            tmp = unpack('<f', piSerial.read(4))[0]
            if tmp != tmp:
                return 0
            else:
                return float("%.2f" % tmp)
        except:
            return 0
           

        
    #Example
    def __call__(self):
        #Main
        self.on_launch()
        xdata = deque([0.0 for i in range(0,NOMBER_OF_VALUES)], maxlen=NOMBER_OF_VALUES)
        ydata = deque([0.0 for i in range(0,NOMBER_OF_VALUES)], maxlen=NOMBER_OF_VALUES)
        
        self.status = unior_begin(EEG)
                
        while self.status:
            if msvcrt.kbhit():              # Button pressed?
                key = ord(msvcrt.getch())   # Value of batton
                if key == 13:               # Enter:
                    self.status = 0
                    piSerial.close()
                    break
            data_r = self.unior_read(0)
            if abs(data_r) > 100:
                data_r = random.randint(0, 30)
            xdata.append(float("%.2f" % process_time()))
            ydata.append(data_r)
            if k[0] == NOMBER_OF_VALUES:
                self.update_value = 1
                self.on_running(xdata, ydata)
                k[0] = 0
            k[0] = k[0] + 1
            print(f'TIME:{xdata[-1]} VAL:{ydata[-1]}')
             
        return xdata, ydata


d = DynamicUpdate()
d()

