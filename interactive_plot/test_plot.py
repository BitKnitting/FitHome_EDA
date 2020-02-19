from make_interactive_plot import PowerPlot
from errors import handle_exception

p = PowerPlot()
try:
    p.make_interactive_plot()
except Exception as e:
    handle_exception(e)
