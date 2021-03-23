# WebPolt.py
"""CLass WebPlot(), use for loop reading data from unior and plotting on
Bokeh WEB"""

import random
import sys
from time import process_time
import keyboard
import panel as pn
import numpy as np
from collections import deque
from scipy.fft import rfft, rfftfreq

from functools import partial
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.models.annotations import BoxAnnotation
from bokeh.palettes import Spectral6
from bokeh.models import HoverTool
from bokeh.transform import linear_cmap
from bokeh.models import Toggle
from bokeh.models import Div


class WebPlot:
    """Class for web updating plot"""

    def __init__(self, plt, unr, com, nov):
        self._NAMBER_OF_VALUES = nov
        self._plot = plt
        self._unior = unr
        self._com = com
        self.source_list = []
        self.status = 0
        self.status_com = 0
        self._status_rec = 0
        self._ports = []
        self.time_start = 0
        self._status_l = 'Whaiting to connect PAK UNIOR ...'
        self._status_com_l = "Whaiting to connect COM PORT..."

    def gen_data(self, start_v):
        """Gen template data for sources"""
        return deque([0.1 for _ in range(start_v, self._NAMBER_OF_VALUES)],
                     maxlen=self._NAMBER_OF_VALUES)

    def source_init(self):
        """Initialize main sources of data to WEB ploting"""
        self.source_list.append(ColumnDataSource({
            "x": self.gen_data(0),
            "y": self.gen_data(0)}))
        self.source_list.append(ColumnDataSource({  # 50
            "x": self.gen_data(50),
            "y": self.gen_data(50)}))
        self.source_list.append(ColumnDataSource({
            "x": np.abs(rfftfreq(self._NAMBER_OF_VALUES, 1 / 60)),
            "y": np.abs(rfft(self.gen_data(0)))}))
        self.source_list.append(ColumnDataSource({
            "x": np.abs(rfftfreq(self._NAMBER_OF_VALUES, 1 / 60)),
            "y": np.abs(rfft(self.gen_data(0)))}))
        self.source_list.append(ColumnDataSource({
            "x": np.abs(rfftfreq(self._NAMBER_OF_VALUES, 1 / 60)),
            "y": np.abs(rfft(self.gen_data(0)))}))
        self.source_list.append(ColumnDataSource({
            "x": self.gen_data(50),
            "y": self.gen_data(50)}))
        self.source_list.append(ColumnDataSource({"x": deque([10]),
                                                  "y": deque([10])}))

    def update(self, source_list):
        """LOOP updaiting values of plots and read data"""
        if keyboard.is_pressed('q'):
            self._com.close()
            self._unior.close()
            print('CLOSING... | EXIT')
            sys.exit()

        if self.status == 1:
            data_r = self._unior.read()
            if data_r != "NO CONN":
                if abs(data_r) > 100:
                    data_r = random.randint(0, 30)
                time_v = process_time()
                while time_v == self._plot.xdata[-1]:
                    time_v = process_time()
                time_v = time_v - self.time_start

                self._plot._rpm += 1
                if time_v - self._plot._time_rpm > 1:
                    source_list[6].data.update({"x": deque([10]),
                                                "y": deque([self._plot._rpm])})
                    self._status_l = f'Reading data from PAK UNIOR'
                    # cheking connection (if > 5 seconds)
                    if self._plot._rpm < 2:
                        self._status_rec += 1
                        if self._status_rec > 3:
                            self._status_l = 'CHECKING CONNECTION...'
                        if self._status_rec == 10:
                            # restart connection
                            self.status = 0
                            self._unior.set_status(2)
                            self._status_rec = 0
                            self._status_l = 'Try to reconnect PAK UNIOR'
                    self._plot._time_rpm = time_v
                    self._plot._rpm = 0

                self._plot.xdata.append(time_v)
                self._plot.ydata.append(data_r)

                self._plot.on_running(source_list)

                source_list[0].data.update({"x": self._plot.xdata,
                                            "y": self._plot.ydata})

                self.source_list[7].text = f"""<b>STATUS:</b><br>
                               <b>PAK UNIOR:</b> {'ONLINE'}<br>
                               {self._status_l}
                               {self._status_com_l}
                               """
            else:
                self.status = 0
                self._status_l = "Connection failed!"
        else:
            self.source_list[7].text = f"""<b>STATUS:</b><br>
                           <b>PAK UNIOR:</b> {'OFFLINE'}<br>
                           {self._status_l}
                           {self._status_com_l}
                           """
            self._ports = self._unior.serial_ports()
            if len(self._ports) > 0:
                self.source_list[11].disabled = True
                self.source_list[8].options = self._ports
                if self.source_list[8].value in self._ports:
                    self._status_l = "Whaiting to connect PAK UNIOR"
                    self.status = self._unior.begin(com_port=
                                                    self.source_list[8].value)
                else:
                    self._status_l = \
                        f"Choose COM PORT" + \
                        f"<br>PORT:{self.source_list[8].value}" + \
                        f"<br>Ports: {self.source_list[8].options}"
            else:
                lft, rgt = self.source_list[11].value
                self.source_list[12].left = lft
                self.source_list[12].right = rgt
                self._plot.activate_diapason[0] = lft
                self._plot.activate_diapason[1] = rgt
                self._status_l = "PLUG IN PAK UNIOR"
                self.status == 0
                self.source_list[11].disabled = False

        if self.status_com == 1:
            if self._com.write(self._plot.com_data):
                self._status_com_l = "<br><b>COM PORT:</b> {'ONLINE'}<br>" \
                                     f"Write data to {self._com.com_port}"
            else:
                self.status_com = 0
                self._status_com_l = "<br><b>COM PORT:</b> {'OFFLINE'}<br>" \
                                     f"Conct to {self._com.com_port} failed"
        else:
            if len(self._ports) > 0:
                self.source_list[9].options = self._ports
                if self.source_list[9].value in self._ports and \
                   self.source_list[9].value != self.source_list[8].value:
                    self._status_com_l = "<br><b>COM PORT:</b>" \
                                         "{'OFFLINE'}<br>" \
                                        f"Connect to {self._com.com_port}"
                    self.status_com = self._com.begin(com_port=
                                                      self.source_list[
                                                          9].value)
                else:
                    self._status_com_l = \
                        f"<br>Choose COM PORT" + \
                        f"<br>PORT:{self.source_list[9].value}" + \
                        f"<br>Ports: {self.source_list[9].options}"
            else:
                self._status_com_l = "<br>PLUG IN DEVICE TO COM PORT"

    def panel_app(self):
        """Setting web plots and widgets"""
        pn.extension()

        self.source_init()

        ht = HoverTool(
            tooltips=[
                ('TIME:', '@x'),
                ('EEG VAL:', '$@y'),  # use @{ } for names with spaces
            ],

            formatters={
                '@x': 'numeral',
                '@y': 'numeral',
                # use default 'numeral' formatter for other fields
            },

            # displ a tooltip whnver crsor is vrtclly in line with a glyph
            mode='vline'
        )

        p = figure(title='EEG INPUT | EEG CURVED', output_backend="webgl")
        p.xaxis.axis_label = "TIME"
        p.yaxis.axis_label = "EEG VALUE"
        p.title.text_font_size = "20px"
        p.background_fill_color = "beige"
        p.background_fill_alpha = 0.5
        input_eeg = p.line(x="x", y="y", legend="EEG",
                           source=self.source_list[0])
        curved = p.line(x="x", y="y", line_width=3, legend="EEG_CURVED",
                        color="firebrick", source=self.source_list[1])
        toggle1 = Toggle(max_height=50, label="CURVED",
                         button_type="success", active=True)
        toggle1.js_link('active', curved, 'visible')
        toggle2 = Toggle(max_height=50, label="INPUT",
                         button_type="success", active=True)
        toggle2.js_link('active', input_eeg, 'visible')

        c = figure(title='FURIE(EEG) -> RITMS', output_backend="webgl")
        c.title.text_font_size = "20px"
        c.xaxis.axis_label = "Hz"
        c.yaxis.axis_label = "Hz RITM VALUE"
        mapper = linear_cmap(field_name='y',
                             palette=Spectral6, low=0, high=700)
        c.vbar(x="x", width=0.5, bottom=0, top="y",
               line_color=mapper, color=mapper, source=self.source_list[2])
        c.line(x="x", y="y", source=self.source_list[3])
        lft, rgt = self._plot.activate_diapason
        center = BoxAnnotation(top=600, bottom=0, left=lft, right=rgt,
                               fill_alpha=0.3, fill_color='navy')
        sld = pn.widgets.IntRangeSlider(value=(lft, rgt), start=0, end=30,
                                        name='DIAPASON')
        c.add_layout(center)

        rpm_b = figure(title='RPM INPUT', output_backend="webgl")
        mapper2 = linear_cmap(field_name='y',
                              palette=Spectral6, low=0, high=100)
        rpm_b.vbar(x="x", bottom=0, top="y",
                   line_color=mapper2, color=mapper2,
                   source=self.source_list[6])

        gfq = figure(title='ALFA RITM', output_backend="webgl")
        gfq.title.text_font_size = "20px"
        gfq.xaxis.axis_label = "TIME"
        gfq.yaxis.axis_label = "ALFA RITM VALUE"
        gfq.add_tools(ht)
        gfq.line(x="x", y="y", legend="ALFA VAL", source=self.source_list[5])

        gfc = figure(title='ALFA RITM IN MOMENT', output_backend="webgl")
        gfc.title.text_font_size = "20px"
        gfc.xaxis.axis_label = "Hz"
        gfc.yaxis.axis_label = "ALFA RITM VALUE"
        gfc.vbar(x="x", width=0.5, bottom=0, top="y",
                 color="firebrick", source=self.source_list[4])

        div = Div(text=f"""<b>STATUS:</b><br>
                       <b>PAK UNIOR:</b> {'OFFLINE'}<br>
                       {self._status_l}
                       {self._status_com_l}
                       """, width=200, height=100)
        self.source_list.append(div)  # 7 index

        slct1 = pn.widgets.Select(name='COM PORT PAK UNIOR', options=[])
        self.source_list.append(slct1)  # 8 index

        slct2 = pn.widgets.Select(name='COM PORT ARDUINO', options=[])
        self.source_list.append(slct2)  # 9 index

        self.source_list.append(ColumnDataSource({
            "x": self.gen_data(50),
            "y": self.gen_data(50)}))  # 10 index
        gfq.line(x="x", y="y", line_width=3, legend="ALFA VAL CURV",
                 color="firebrick", source=self.source_list[10])

        self.source_list.append(sld)  # 11 index
        self.source_list.append(center)  # 12 index

        print('INITIALIZE... | cb = pn.state.add_periodic_callback')

        cb = pn.state.add_periodic_callback(partial(self.update,
                                                    self.source_list
                                                    ), 10)

        gspec = pn.GridSpec(sizing_mode='stretch_both', max_height=900)
        gspec[0:5, 0:6] = p
        gspec[0:5, 6:10] = c
        gspec[5:6, 6:10] = sld
        # gspec[5:6, 9:10] = watcher
        gspec[6:7, 0:1] = toggle1
        gspec[6:7, 1:2] = toggle2
        gspec[7:8, 0:1] = slct1
        gspec[7:8, 1:2] = slct2
        gspec[8:10, 0:1] = rpm_b
        gspec[8:10, 1:3] = div
        gspec[6:10, 3:7] = gfq
        gspec[6:10, 7:10] = gfc

        self.time_start = process_time()
        print(f'| THIS IS gspec:{gspec}|')
        return gspec

    def start(self):
        """Starting WEB server bokeh. Use 4000 port, but he can dont launch
        - try use another port"""
        print('INITIALIZE... | pn.serve(panel_app)')
        pn.serve(self.panel_app, title='PAK UNIOR EEG', port=4000)
