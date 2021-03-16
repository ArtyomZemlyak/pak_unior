import matplotlib.pyplot as plt
import serial.tools.list_ports
from struct import unpack
import numpy as np
from time import process_time
from collections import deque
from scipy.fft import rfft, rfftfreq
from numpy import array, sign, zeros
from scipy.interpolate import interp1d
import random
import keyboard
import sys

from functools import partial

import numpy as np
import panel as pn

from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.layouts import gridplot
from bokeh.models.annotations import BoxAnnotation
from tornado.ioloop import IOLoop

std_speed = 57600  # Скорость COM порта
com_port = 'COM6'  # TODO: chose port to open

paritys = 'N'  # Бит четности
stopbitss = 1  # Количество стоп-бит

bite_size = 8  # Биты данных
t_out = 1  # Таймаут в секундах, должен быть больше 1с
flag1 = 0  # Флаг для остановки программы, устанавливается в 1, если найдена сигнатура
reading_bytes = 10  # Количество байт для чтения после открытия порта
keyword = b'\x00\x00\x00'  # !Сигнатура для поиска
cmd = 0xff
EEG = 0

NAMBER_OF_VALUES = 200
LABELS = ['EEG', 'EEG_CURV', 'FURIE(EEG)', 'FURIE(EEG_CURV)', 'FURIE(EEG)_CURV', '(FURIE(EEG)_m_FURIE(EEG_CURV))_CURV']

time_start = process_time()

piSerial = serial.Serial()  # TODO: can be use self serial?
print(f'S:- Port:{piSerial.is_open}')
piSerial.close()
print(f'S:- Port:{piSerial.is_open}')

def unior_begin(channel):
    """Setup COM-port and connect to PAK UNIOR"""
    print(f'INITIALIZE... | unior_begin {channel}')
    piSerial.baudrate = std_speed
    piSerial.port = com_port
    piSerial.timeout = 1
    piSerial.write_timeout = 1
    piSerial.open()
    print(f'|PORT:{com_port}| OPENED')
    piSerial.write(cmd)
    print(f'|WRITE| {cmd}')
    print('|WHAITING...', end='')
    status = 0
    while True:
        if keyboard.is_pressed('q'):  # Enter:
            piSerial.close()
            print('CLOSING... | EXIT')
            break
        s = piSerial.readline()
        print(end='.')
        if s == b'OK\n':
            print('CONNECTED')
            piSerial.write((str(channel) + '\r\n\0').encode())  # send channels mask
            print('|WHAITING DATA...')
            status = 1
            break
    return status


def unior_read(channel):
    """Read data from PAK UNIOR"""
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
    except ValueError:
        return 0


def curve_on(data):
    """Curved on array of smth values"""
    try:
        s = array(data)  # vector of values.
        q_u = zeros(s.shape)
        u_x = [0, ]
        u_y = [s[0], ]
        for k in range(1, len(s) - 1):
            if (sign(s[k] - s[k - 1]) == 1) and (sign(s[k] - s[k + 1]) == 1):
                u_x.append(k)
                u_y.append(s[k])
        u_x.append(len(s) - 1)
        u_y.append(s[-1])
        u_p = interp1d(u_x, u_y, kind='cubic', bounds_error=False, fill_value=0.0)
        for k in range(0, len(s)):
            q_u[k] = u_p(k)  # up
        return q_u
    except ValueError:
        return data


class DynamicUpdate:
    """Class for dynamic updating plot"""

    # If we know the x range use ->
    # min_x = process_time()
    # max_x = process_time() + 30

    def __init__(self):
        self.key = 0
        self.status = 0
        self.update_value = 0
        self._rpm = 0
        self._time_rpm = 0
        # self.figure, self.ax = plt.subplots(nrows=3, ncols=2, figsize=(20, 20))
        # self.figure.set_label('EEG')
        # self.lines = []
        self.activate_value = 400
        self.activate_diapason = [9, 14]
        # self.stream = Stream()
        self.xdata = deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES)
        self.ydata = deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES)
        self.x_a = deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES)
        self.y_a = deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES)

    def activate_line_on_(self, data, value, values=[0, 1]):
        """Set up line of barier of alfa ritms"""
        y = [value for _ in data]
        diapason_x = [0, 0]
        for j, val in enumerate(data):
            if (val > self.activate_diapason[0]) and (diapason_x[0] == 0):
                diapason_x[0] = j
            if (val > self.activate_diapason[1]) and (diapason_x[1] == 0):
                diapason_x[1] = j
        diapason = range(diapason_x[0], diapason_x[1])
        if values == [0, 1]:
            for j in diapason:
                y[j] = self.activate_value + 100
        else:
            for j in diapason:
                y[j] = values[j]
        return y


    def on_running(self, source2, source3, source4, source5, source6):
        """Update data (with the new _and_ the old points)"""

        # EEG_CURVED######################################
        ydata_curved = curve_on(self.ydata)
        source2.data.update({"x": [v for i, v in enumerate(self.xdata) if i > 49],
                             "y": [v for i, v in enumerate(ydata_curved) if i > 49]})

        # FURIE(EEG)#############################################  TODO : fix names
        yf = rfft(self.ydata)
        xf = rfftfreq(NAMBER_OF_VALUES, 1 / 60)
        xf_f = [float("%.3f" % np.real(i)) for i in xf]
        yf_f = [float("%.3f" % np.real(i)) for i in yf]
        for k in range(0, 3):
            yf_f[k] = 0
        # FURIE(EEG_CURVED)######################################
        yf2 = rfft(ydata_curved)
        yf_f2 = [float("%.3f" % np.real(i)) for i in yf2]
        for k in range(0, 3):
            yf_f2[k] = 0
        # (FURIE(EEG)_m_FURIE(EEG_CURVED))_CURVED###############
        yf_m = []
        for y1, y2 in zip(yf_f, yf_f2):
            y_ = abs(y1) - abs(y2)
            if y_ > 0:
                yf_m.append(y_)
            else:
                yf_m.append(0.0)
        yf_m_curved = np.abs(curve_on(yf_m))
        source3.data.update({"x": xf_f, "y": yf_m_curved})

        self.activate_value = np.mean(yf_m_curved) + 50
        source4.data.update({"x": xf_f, "y": self.activate_line_on_(xf_f, self.activate_value)})

        act_l = self.activate_line_on_(xf_f, 0, values=yf_m_curved)
        self.x_a.append(self.xdata[-1])
        self.y_a.append(int(np.average(act_l) * 10))
        source6.data.update({"x": self.x_a, "y": self.y_a})
        source5.data.update({"x": xf_f, "y": act_l})

        self.update_value = 0

    def __call__(self):
        """Main"""

        self.status = unior_begin(EEG)

        print("t1!!!!!!!!!!!!!!!")

        def update(source, source2, source3, source4, source5, source6, q):

            if keyboard.is_pressed('q'):
                piSerial.close()
                print('CLOSING... | EXIT')
                sys.exit()

            data_r = unior_read(0)
            if abs(data_r) > 100:
                data_r = random.randint(0, 30)
            time_v = process_time()
            while time_v == self.xdata[-1]:
                time_v = process_time()

            self._rpm += 1
            if time_v - self._time_rpm > 1:
                q.value = self._rpm
                self._time_rpm = time_v
                self._rpm = 0

            #for x_v in self.xdata:
            #    if x_v - time_v > 1:
            #        break

            self.xdata.append(time_v)
            self.ydata.append(data_r)

            if self.key == int(NAMBER_OF_VALUES / 10):
                self.key = 0
                self.update_value = 1
                self.on_running(source2, source3, source4, source5, source6)
            self.key = self.key + 1

            print(f'TIME:{self.xdata[-1]} VAL:{self.ydata[-1]}')

            source.data.update({"x": self.xdata, "y": self.ydata})

        def panel_app():
            pn.extension()
            source = ColumnDataSource({"x": deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES),
                                       "y": deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES)})
            source2 = ColumnDataSource({"x": deque([0.0 for _ in range(50, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES),
                                        "y": deque([0.0 for _ in range(50, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES)})
            source3 = ColumnDataSource({"x": rfftfreq(NAMBER_OF_VALUES, 1 / 60),
                                        "y": rfft(deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES))})
            source4 = ColumnDataSource({"x": rfftfreq(NAMBER_OF_VALUES, 1 / 60),
                                        "y": rfft(deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES))})
            source5 = ColumnDataSource({"x": rfftfreq(NAMBER_OF_VALUES, 1 / 60),
                                        "y": rfft(deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES))})
            source6 = ColumnDataSource({"x": deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES),
                                        "y": deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES)})
            p = figure()
            p.line(x="x", y="y", source=source)
            p.line(x="x", y="y", line_width=3, color="firebrick", source=source2)  # np.iscomplexobj()

            c = figure()

            c.vbar(x="x", width=0.5, bottom=0, top="y", color="firebrick", source=source3)
            c.line(x="x", y="y", source=source4)
            # a finite region
            center = BoxAnnotation(top=600, bottom=0, left=8, right=14, fill_alpha=0.3, fill_color='navy')
            c.add_layout(center)

            q = pn.indicators.Dial(
                name='FREQ COM', value=10, bounds=(0, 100), format='{value}',
                title_size="middle", needle_color='transparent',
                colors=[(0.2, 'green'), (0.8, 'gold'), (1, 'red')]
            )

            gfq = figure()
            gfq.line(x="x", y="y", source=source6)

            gfc = figure()
            gfc.vbar(x="x", width=0.5, bottom=0, top="y", color="firebrick", source=source5)

            gspec = pn.GridSpec(sizing_mode="stretch_both", max_height=1000)  # [fixed, stretch_width, stretch_height, stretch_both, scale_width, scale_height, scale_both, None]
            gspec[0, 0:5] = p
            gspec[0, 6:10] = c
            gspec[1, 1:2] = q
            gspec[1, 3:5] = gfq
            gspec[1, 6:10] = gfc

            print('INITIALIZE... | cb = pn.state.add_periodic_callback')
            cb = pn.state.add_periodic_callback(partial(update, source, source2, source3, source4, source5, source6, q), 10)
            return gspec  # TODO: set static host

        print("t3!!!!!!!!!!!!!!!")
        #io_loop = IOLoop()
        #io_loop.make_current()
        #IOLoop.current(instance=False)
        print("t4!!!!!!!!!!!!!!!")
        pn.serve(panel_app)
        print("t5!!!!!!!!!!!!!!!")

        '''
        while self.status:
            if keyboard.is_pressed('q'):  # Enter:
                piSerial.close()
                # server.stop()
                print('CLOSING... | EXIT')
                break
            data_r = unior_read(0)
            if abs(data_r) > 100:
                data_r = random.randint(0, 30)
            self.xdata.append(float("%.2f" % process_time()))
            self.ydata.append(data_r)
            global data_serial
            data_serial = (self.xdata, self.ydata)
            # callback(self)
            if self.key == NAMBER_OF_VALUES:
                self.key = 0
                self.update_value = 1
                # self.on_running(self.xdata, self.ydata)
            self.key = self.key + 1
            print(f'TIME:{self.xdata[-1]} VAL:{self.ydata[-1]}')

        return self.xdata, self.ydata
        '''


print('INITIALIZE... | DynamicUpdate')
d = DynamicUpdate()
print('INITIALIZE... | d()')
d()
