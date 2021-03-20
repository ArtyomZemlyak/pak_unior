# PlotDynamicUpdate.py
"""Class PlotDynamicUpdate, use for update data plots and initialize Unior
module"""

from collections import deque
from numpy import array, sign, zeros
import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.interpolate import interp1d

from WebPlot import WebPlot
from Unior import Unior
from ComConnect import ComConnect

EEG = 0
NAMBER_OF_VALUES = 200
LABELS = ['EEG', 'EEG_CURV', 'FURIE(EEG)', 'FURIE(EEG_CURV)',
          'FURIE(EEG)_CURV', '(FURIE(EEG)_m_FURIE(EEG_CURV))_CURV']


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
        self.activate_diapason = [8, 13]
        self.xdata = deque([0.0 for _ in range(0, NAMBER_OF_VALUES)],
                           maxlen=NAMBER_OF_VALUES)
        self.ydata = deque([0.0 for _ in range(0, NAMBER_OF_VALUES)],
                           maxlen=NAMBER_OF_VALUES)
        self.x_a = deque([0.0 * _ for _ in range(50, NAMBER_OF_VALUES)],
                         maxlen=NAMBER_OF_VALUES)
        self.y_a = deque([0.0 for _ in range(50, NAMBER_OF_VALUES)],
                         maxlen=NAMBER_OF_VALUES)
        self.com_data = 0
        print(' DONE |')

    @staticmethod
    def curve_on(data):
        """Curved on array of smth values"""
        try:
            s = array(data)  # vector of values.
            q_u = zeros(s.shape)
            u_x = [0, ]
            u_y = [s[0], ]
            for k in range(1, len(s) - 1):
                if (sign(s[k] - s[k - 1]) == 1) and\
                        (sign(s[k] - s[k + 1]) == 1):
                    u_x.append(k)
                    u_y.append(s[k])
            u_x.append(len(s) - 1)
            u_y.append(s[-1])
            u_p = interp1d(u_x, u_y, kind='cubic', bounds_error=False,
                           fill_value=0.0)
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

    def on_running(self, source_list):
        """Update data (with the new _and_ the old points)"""
        lft, rgt = source_list[11].value
        self.activate_diapason[0] = lft
        self.activate_diapason[1] = rgt
        source_list[12].left = lft
        source_list[12].right = rgt
        if self.ydata[0] > 1:
            # EEG_CURVED######################################
            ydata_curved = self.curve_on(self.ydata)
            source_list[1].data.update({"x": [v for i, v in
                                       enumerate(self.xdata) if i > 49],
                                        "y": [v for i, v in
                                       enumerate(ydata_curved) if i > 49]})

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
            source_list[2].data.update({"x": xf_f, "y": yf_m_curved})

            # ACTIVATE LINE######################################
            self.activate_value = np.mean(yf_m_curved) + 50
            source_list[3].data.update({
                "x": xf_f,
                "y": self.activate_line_on_(xf_f, self.activate_value)})

            # ALFA DIAPASON######################################
            act_l = self.activate_line_on_(xf_f, 0, values=yf_m_curved)
            source_list[4].data.update({"x": xf_f, "y": act_l})
            self.x_a.append(self.xdata[-1])
            self.y_a.append(int(np.average(act_l) * 10))
            source_list[5].data.update({"x": self.x_a, "y": self.y_a})

            if self.y_a[0] == 0:
                y_a_p = []
                y_a_n = []
                for i in self.y_a:
                    if i > 0:
                        y_a_p.append(i)
                    else:
                        y_a_n.append(i)
                y_a_all = [i for i in y_a_n]
                for i in self.curve_on(y_a_p):
                    y_a_all.append(i)
                source_list[10].data.update({"x": self.x_a,
                                             "y": y_a_all})
                self.com_data = y_a_all[-1]
            else:
                y_a_all = self.curve_on(self.y_a)
                source_list[10].data.update({"x": self.x_a,
                                             "y": y_a_all})
                self.com_data = y_a_all[-1]

        self.update_value = 0

    def __call__(self):
        """Main"""
        print('INITIALIZE... | d()')

        self._unior = Unior(EEG)
        self._comcn = ComConnect()

        self._webplot = WebPlot(self, self._unior, self._comcn,
                                NAMBER_OF_VALUES)
        self._webplot.start()
