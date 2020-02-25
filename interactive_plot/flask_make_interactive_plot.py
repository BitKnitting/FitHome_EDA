from bokeh.models import ColumnDataSource, HoverTool, ResetTool, BoxZoomTool
from bokeh.models.widgets import DateSlider
from bokeh.plotting import figure
from bokeh.io import output_file, show
from bokeh.layouts import column
import pandas as pd
from readings.readings import PowerReadings
import time
import errors.errors
import logging

logger = logging.getLogger(__name__)


class PowerPlot:
    def __init__(self, doc):
        # output_file('readings.html')
        self.date_slider = None
        self.source = None
        self.f = None
        self.isodays = []
        self.doc = doc

    #############################################################
    # * make_interactive_plot()
    # gets the list of dates that have
    # active power readings in the mongo db.  It then calls
    # into _draw_plot_with_date_slider to draw a bokeh plot
    # with a date slider containing the list of dates and an
    # interactive plot based on the date the date slider is
    # set to.
    #
    # Note: Because the date_slider widget interacts with the plot,
    # this code requires the bokeh server to be running.
    ############################################################

    def make_interactive_plot(self):
        # Get all the readings...this can take awhile...
        p = PowerReadings()
        try:
            connection = p.get_connection_to_collection()
            self.isodays = p.get_isodate_list(connection)
            if self.isodays == []:
                raise PlotNoDatesFound('Could not find any dates to plot.')
            # Start with the first of the available dates.
            start_time = time.perf_counter()
            df = p.get_DataFrame_for_date(self.isodays[0])
            end_time = time.perf_counter()
            logger.debug(
                f'Got DataFrame for {self.isodays[0]}.  It took {end_time-start_time:.2f} seconds to get the readings.')
            logger.debug(df.describe())
            self._draw_plot_with_date_slider(df)
        except Exception as e:
            raise

    ###################################################
    # **** _get_source()
    # Here we are converting the DataFrame into
    # a ColumnDataSource that makes it easy for us
    # to provide data to a Bokeh plot.
    # We assume the incoming is a DataFrame of the
    # format created by the PowerReadings class in
    # get_DataFrame.py
    ###################################################
    def _get_source(self, df):
        data = {'x': df.index, 'y': df['Pa']}
        return ColumnDataSource(data)

    def _draw_plot_with_date_slider(self, df):
        self.source = self._get_source(df)

        # Set up a DateSlider widget if there is more than one date.
        self._add_date_slider(self.isodays)
        # self.doc.add_root(self.date_slider)
        # Stylize the plot.
        self.f = self._stylize_plot(self.isodays[0])
        self.f.line(x='x', y='y', source=self.source)
        # self.doc.add_root(self.f)
        c = column(self.date_slider, self.f)
        self.doc.add_root(c)

    def _filter_date(self, attr, old, new):
        isodate = self.date_slider.value.__str__()
        if isodate not in self.isodays:
            return
        plot_date = self.date_slider.value.strftime('%B %d, %Y')
        logger.debug(f'Asking to plot readings for {plot_date}')

        p = PowerReadings()
        try:
            start_time = time.perf_counter()
            plotting_data = p.get_DataFrame_for_date(isodate)
            end_time = time.perf_counter()
            logger.debug(
                f'Got DataFrame for {self.isodays[0]}.  It took {end_time-start_time:.2f} seconds to get the readings.')

        except errors.NoReadingsError:
            logger.debug(
                f'Could not get readings for {isodate}.  Using the date {self.isodays[0]} ')
            plotting_data = p.get_DataFrame_for_date(self.isodays[0])
        start_time = time.perf_counter()
        self.source.data = {'x': plotting_data.index, 'y': plotting_data['Pa']}
        self.f.xaxis.axis_label = plot_date
        end_time = time.perf_counter()
        logger.debug(
            f'It took {end_time-start_time:.2f} seconds to plot the readings.')

    def _add_date_slider(self, isoday_list):
        self.date_slider = DateSlider(
            title="Date", value=isoday_list[0], start=isoday_list[0],
            end=isoday_list[-1], step=1)
        self.date_slider.callback_policy = "mouseup"
        self.date_slider.on_change(
            'value_throttled', self._filter_date)

    def _stylize_plot(self, isoday):
        f = figure(plot_width=1000, plot_height=500, x_axis_type='datetime')
        # see bokeh colors at https://docs.bokeh.org/en/latest/docs/reference/colors.html
        f.background_fill_color = 'gainsboro'
        # f.background_fill_alpha=.1
        # Style the tools.
        hover_tool = HoverTool(tooltips=[('time', '@x{%H:%M:%S}'), ('watts', '@y{%0.2f}')],
                               formatters={
            'x': 'datetime',  # use 'datetime' formatter for 'date' field
            'y': 'printf', },)
        f.tools = [hover_tool, BoxZoomTool(), ResetTool()]
        # Set the hover and zoom tools as active.
        # f.toolbar.active_inspect = [hover_tool,BoxZoomTool()]
        # Set up the hover tool tip.
        f.toolbar_location = 'above'
        f.toolbar.logo = None
        # Style the title.
        f.title.text = 'Power Readings'
        f.title.text_color = 'midnightblue'
        f.title.text_font = 'Arial'
        f.title.text_font_size = '24px'
        f.title.align = 'center'
        # Style the axis
        f.xaxis.axis_label = isoday
        f.yaxis.axis_label = 'Watts'
        f.axis.axis_label_text_font_size = '18px'
        return f
