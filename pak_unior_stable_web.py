import serial.tools.list_ports
from struct import unpack
from time import sleep, process_time
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
from bokeh.models.annotations import BoxAnnotation
from bokeh.layouts import layout
from bokeh.palettes import Spectral6
from bokeh.models import HoverTool
from bokeh.transform import linear_cmap
from bokeh.models import Toggle

std_speed = 57600  # Скорость COM порта
com_port = 'COM6'  # TODO: chose port to open

cmd = 0xff
EEG = 0

NAMBER_OF_VALUES = 200
LABELS = ['EEG', 'EEG_CURV', 'FURIE(EEG)', 'FURIE(EEG_CURV)', 'FURIE(EEG)_CURV', '(FURIE(EEG)_m_FURIE(EEG_CURV))_CURV']


class Unior:
    """Create connection with PAK UNIOR"""

    def __init__(self):
        print('INITIALIZE... | Unior...', end='')
        self.piSerial = serial.Serial()
        self.piSerial.close()
        print(' DONE |')

    def begin(self, channel):
        """Setup COM-port and connect to PAK UNIOR"""
        print(f'INITIALIZE... | unior_begin {channel}', end='')
        self.piSerial.baudrate = std_speed
        self.piSerial.port = com_port
        self.piSerial.timeout = 1
        self.piSerial.write_timeout = 1
        print(' DONE |')
        self.piSerial.open()
        print(f'|PORT:{com_port}| OPENED')
        self.piSerial.write(cmd)
        print(f'|WRITE| {cmd}')
        print('|WHAITING...', end='')
        status = 0
        while True:
            if keyboard.is_pressed('q'):
                self.piSerial.close()
                print('CLOSING... | EXIT')
                break
            s = self.piSerial.readline()
            print(end='.')
            if s == b'OK\n':
                print('CONNECTED')
                self.piSerial.write((str(channel) + '\r\n\0').encode())  # send channels mask
                print('|WHAITING DATA...')
                status = 1
                break
        return status

    def read(self, channel):
        """Read data from PAK UNIOR"""
        if self.piSerial.inWaiting() > 0:
            self.piSerial.flushInput()
        self.piSerial.write((str(channel) + '\r\n\0').encode())
        beg_time = process_time()
        while self.piSerial.inWaiting() < 4:
            if process_time() - beg_time > 1:
                return 0
        try:
            tmp = unpack('<f', self.piSerial.read(4))[0]
            if tmp != tmp:
                return 0
            else:
                return float("%.2f" % tmp)
        except ValueError:
            return 0

    def close(self):
        self.piSerial.close()


class PlotDynamicUpdate:
    """Class for dynamic updating plot"""

    def __init__(self):
        print('INITIALIZE... | PlotDynamicUpdate...', end='')
        self._unior = None
        self.key = 0
        self.status = 0
        self.update_value = 0
        self._rpm = 0
        self._time_rpm = 0
        self.activate_value = 400
        self.activate_diapason = [9, 14]
        self.xdata = deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES)
        self.ydata = deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES)
        self.x_a = deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES)
        self.y_a = deque([0.0 for _ in range(0, NAMBER_OF_VALUES)], maxlen=NAMBER_OF_VALUES)
        print(' DONE |')

    def curve_on(self, data):
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
        ydata_curved = self.curve_on(self.ydata)
        source2.data.update({"x": [v for i, v in enumerate(self.xdata) if i > 49],
                             "y": [v for i, v in enumerate(ydata_curved) if i > 49]})

        # FURIE(EEG)#############################################
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
        yf_m_curved = np.abs(self.curve_on(yf_m))
        source3.data.update({"x": xf_f, "y": yf_m_curved})

        # ACTIVATE LINE######################################
        self.activate_value = np.mean(yf_m_curved) + 50
        source4.data.update({"x": xf_f, "y": self.activate_line_on_(xf_f, self.activate_value)})

        # ALFA DIAPASON######################################
        act_l = self.activate_line_on_(xf_f, 0, values=yf_m_curved)
        source5.data.update({"x": xf_f, "y": act_l})
        self.x_a.append(self.xdata[-1])
        self.y_a.append(int(np.average(act_l) * 10))
        source6.data.update({"x": self.x_a, "y": self.y_a})

        self.update_value = 0

    def __call__(self):
        """Main"""
        print('INITIALIZE... | d()')

        self._unior = Unior()
        self.status = self._unior.begin(EEG)

        def update(source, source2, source3, source4, source5, source6, source7):
            """LOOP updaiting values of plots and read data"""

            if keyboard.is_pressed('q'):
                self._unior.close()
                print('CLOSING... | EXIT')
                sys.exit()

            data_r = self._unior.read(0)
            if abs(data_r) > 100:
                data_r = random.randint(0, 30)
            time_v = process_time()
            while time_v == self.xdata[-1]:
                time_v = process_time()

            self._rpm += 1
            if time_v - self._time_rpm > 1:
                source7.data.update({"x": deque([10]), "y": deque([self._rpm])})
                self._time_rpm = time_v
                self._rpm = 0

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
            """Setting web plots and widgets"""

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
            source7 = ColumnDataSource({"x": deque([10]),
                                        "y": deque([10])})

            ht = HoverTool(
                tooltips=[
                    ('TIME:', '@x'),
                    ('EEG VAL:', '$@y'),  # use @{ } for field names with spaces
                ],

                formatters={
                    '@x': 'numeral',  # use 'datetime' formatter for '@date' field
                    '@y': 'numeral',  # use 'printf' formatter for '@{adj close}' field
                    # use default 'numeral' formatter for other fields
                },

                # display a tooltip whenever the cursor is vertically in line with a glyph
                mode='vline'
            )

            p = figure(title='EEG INPUT | EEG CURVED')
            p.xaxis.axis_label = "TIME"
            p.yaxis.axis_label = "EEG VALUE"
            p.title.text_font_size = "20px"
            p.background_fill_color = "beige"
            p.background_fill_alpha = 0.5
            input_eeg = p.line(x="x", y="y", legend="EEG", source=source)
            curved = p.line(x="x", y="y", line_width=3,  legend="EEG_CURVED", color="firebrick", source=source2)
            toggle1 = Toggle(max_height=50, label="CURVED", button_type="success", active=True)
            toggle1.js_link('active', curved, 'visible')
            toggle2 = Toggle(max_height=50, label="INPUT", button_type="success", active=True)
            toggle2.js_link('active', input_eeg, 'visible')

            c = figure(title='FURIE(EEG) -> RITMS')
            c.title.text_font_size = "20px"
            c.xaxis.axis_label = "Hz"
            c.yaxis.axis_label = "Hz RITM VALUE"
            mapper = linear_cmap(field_name='y', palette=Spectral6, low=0, high=700)
            c.vbar(x="x", width=0.5, bottom=0, top="y", line_color=mapper, color=mapper, source=source3)
            c.line(x="x", y="y", source=source4)
            center = BoxAnnotation(top=600, bottom=0, left=8, right=14, fill_alpha=0.3, fill_color='navy')
            c.add_layout(center)

            rpm_b = figure(title='RPM INPUT')
            mapper2 = linear_cmap(field_name='y', palette=Spectral6, low=0, high=100)
            rpm_b.vbar(x="x", bottom=0, top="y", line_color=mapper2, color=mapper2, source=source7)

            gfq = figure(title='ALFA RITM')
            gfq.title.text_font_size = "20px"
            gfq.xaxis.axis_label = "TIME"
            c.yaxis.axis_label = "ALFA RITM VALUE"
            gfq.add_tools(ht)
            gfq.line(x="x", y="y", legend="ALFA VAL", source=source6)

            gfc = figure(title='ALFA RITM IN MOMENT')
            gfc.title.text_font_size = "20px"
            c.xaxis.axis_label = "Hz"
            c.yaxis.axis_label = "ALFA RITM VALUE"
            gfc.vbar(x="x", width=0.5, bottom=0, top="y", color="firebrick", source=source5)

            gspec = layout([
                [p, c],
                [[[toggle1, toggle2], rpm_b], gfq, gfc],
            ], sizing_mode="stretch_both", max_height=900)

            sleep(2)
            print('INITIALIZE... | cb = pn.state.add_periodic_callback')
            cb = pn.state.add_periodic_callback(partial(update, source, source2, source3, source4, source5, source6, source7), 10)
            sleep(2)
            return gspec

        print('INITIALIZE... | pn.serve(panel_app)')
        pn.serve(panel_app, title='PAK UNIOR EEG', port=40000)


d = PlotDynamicUpdate()
d()
