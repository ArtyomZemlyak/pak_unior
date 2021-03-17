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
from bokeh.layouts import layout
from bokeh.palettes import Spectral6
from bokeh.models import HoverTool
from bokeh.transform import linear_cmap
from bokeh.models import Toggle
from bokeh.models import Div


class WebPlot:
    """Class for web updating plot"""

    def __init__(self, plt, unr, nov):
        self._NAMBER_OF_VALUES = nov
        self._plot = plt
        self._unior = unr
        self.source_list = []
        self.status = 0
        self._status_rec = 0
        self._status_l = 'Whaiting to connect PAK UNIOR ...'

    def gen_data(self, start_v):
        return deque([0.1 for _ in range(start_v, self._NAMBER_OF_VALUES)],
                     maxlen=self._NAMBER_OF_VALUES)

    def source_init(self):
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
            "x": self.gen_data(0),
            "y": self.gen_data(0)}))
        self.source_list.append(ColumnDataSource({"x": deque([10]),
                                                  "y": deque([10])}))

    def update(self, source_list):
        """LOOP updaiting values of plots and read data"""

        if keyboard.is_pressed('q'):
            self._unior.close()
            print('CLOSING... | EXIT')
            sys.exit()

        if self.status == 1:
            data_r = self._unior.read()
            if abs(data_r) > 100:
                data_r = random.randint(0, 30)
            time_v = process_time()
            while time_v == self._plot.xdata[-1]:
                time_v = process_time()

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

            if self._plot.key == int(self._NAMBER_OF_VALUES / 10):
                self._plot.key = 0
                self._plot.update_value = 1
                self._plot.on_running(source_list)
            self._plot.key = self._plot.key + 1

            print(f'TIME:{self._plot.xdata[-1]} VAL:{self._plot.ydata[-1]}')

            source_list[0].data.update({"x": self._plot.xdata,
                                        "y": self._plot.ydata})

            self.source_list[7].text = f"""<b>STATUS:</b><br>
                           <b>PAK UNIOR:</b> {'ONLINE'}<br>
                           {self._status_l}
                           """
        else:
            self.source_list[7].text = f"""<b>STATUS:</b><br>
                           <b>PAK UNIOR:</b> {'OFFLINE'}<br>
                           {self._status_l}
                           """
            self.status = self._unior.begin()

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

        p = figure(title='EEG INPUT | EEG CURVED')
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

        c = figure(title='FURIE(EEG) -> RITMS')
        c.title.text_font_size = "20px"
        c.xaxis.axis_label = "Hz"
        c.yaxis.axis_label = "Hz RITM VALUE"
        mapper = linear_cmap(field_name='y',
                             palette=Spectral6, low=0, high=700)
        c.vbar(x="x", width=0.5, bottom=0, top="y",
               line_color=mapper, color=mapper, source=self.source_list[2])
        c.line(x="x", y="y", source=self.source_list[3])
        center = BoxAnnotation(top=600, bottom=0, left=8, right=14,
                               fill_alpha=0.3, fill_color='navy')
        c.add_layout(center)

        rpm_b = figure(title='RPM INPUT')
        mapper2 = linear_cmap(field_name='y',
                              palette=Spectral6, low=0, high=100)
        rpm_b.vbar(x="x", bottom=0, top="y",
                   line_color=mapper2, color=mapper2,
                   source=self.source_list[6])

        gfq = figure(title='ALFA RITM')
        gfq.title.text_font_size = "20px"
        gfq.xaxis.axis_label = "TIME"
        gfq.yaxis.axis_label = "ALFA RITM VALUE"
        gfq.add_tools(ht)
        gfq.line(x="x", y="y", legend="ALFA VAL", source=self.source_list[5])

        gfc = figure(title='ALFA RITM IN MOMENT')
        gfc.title.text_font_size = "20px"
        gfc.xaxis.axis_label = "Hz"
        gfc.yaxis.axis_label = "ALFA RITM VALUE"
        gfc.vbar(x="x", width=0.5, bottom=0, top="y",
                 color="firebrick", source=self.source_list[4])

        div = Div(text=f"""<b>STATUS:</b><br>
                       <b>PAK UNIOR:</b> {'OFFLINE'}<br>
                       {self._status_l}
                       """, width=200, height=100)
        self.source_list.append(div)  # 7 index

        gspec = layout([
            [p, c],
            [[[toggle1, toggle2], [rpm_b, div]], gfq, gfc],
        ], sizing_mode="stretch_both", max_height=900)

        print('INITIALIZE... | cb = pn.state.add_periodic_callback')
        cb = pn.state.add_periodic_callback(partial(self.update,
                                                    self.source_list
                                                    ), 10)

        print(f'| THIS IS gspec:{gspec}|')
        return gspec

    def start(self):
        print('INITIALIZE... | pn.serve(panel_app)')
        pn.serve(self.panel_app, title='PAK UNIOR EEG', port=40000)
