from threading import Thread
from flask import Flask, render_template

from bokeh.embed import server_document
from bokeh.server.server import Server
from tornado.ioloop import IOLoop
from interactive_plot.flask_make_interactive_plot import PowerPlot
from errors.errors import handle_exception
import logging

BOKEH_PY_LOG_LEVEL='debug'
app = Flask(__name__)


def make_interactive(doc):
    p = PowerPlot(doc)
    try:
        # doc is added when using bokeh embedded server.  Else, we could
        # Use an output_file in make_interactive_plot...
        p.make_interactive_plot()
    except Exception as e:
        handle_exception(e)


@app.route('/', methods=['GET'])
def bkapp_page():
    script = server_document('http://localhost:5006/bkapp')
    return render_template("interactive.html", script=script, template="Flask")


def bk_worker():
    # Can't pass num_procs > 1 in this configuration. If you need to run multiple
    # processes, see e.g. flask_gunicorn_embed.py
    server = Server({'/bkapp': make_interactive}, io_loop=IOLoop(), address='0.0.0.0',
                    allow_websocket_origin=["*"],log_level='info')
    # server = Server({'/bkapp': make_interactive}, io_loop=IOLoop(), address='0.0.0.0',
    #                 port=5006, allow_websocket_origin=["192.168.86.24","0.0.0.0", "127.0.0.1"])
    server.start()
    server.io_loop.start()


# Thread(target=bk_worker).start()

if __name__ == '__main__':
    # FORMAT = '%(asctime)-15s %(levelname)s:%(name)s: %(message)s'
    # formatter = logging.Formatter(FORMAT)
    # root_logger = logging.getLogger()
    # print(root_logger)
    # [print(f'****** {h}') for h in root_logger.handlers]

    print('Opening single process Flask app with embedded Bokeh application.')
    print('The bokeh docs discuss this at')
    print('https://docs.bokeh.org/en/latest/docs/user_guide/server.html#embedding-bokeh-server-as-a-library')
    app.run(host='0.0.0.0', port=8000, debug=True)
