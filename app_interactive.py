from threading import Thread
from flask import Flask, render_template

from bokeh.embed import server_document
from bokeh.server.server import Server
from tornado.ioloop import IOLoop
from interactive_plot.flask_make_interactive_plot import PowerPlot
from errors.errors import handle_exception
import logging
from flask.logging import default_handler
import logging

# Turn on logging so we see the log entries for the libraries
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',)
logger = logging.getLogger(__name__)
app = Flask(__name__)


def make_interactive(doc):
    p = PowerPlot(doc)
    try:
        # doc is added when using bokeh embedded server.
        p.make_interactive_plot()
    except Exception as e:
        handle_exception(e)


@app.route('/', methods=['GET'])
def bkapp_page():
    script = server_document("http://192.168.86.249:5006/bkapp")
    return render_template("interactive.html", script=script, template="Flask")


def bk_worker():
    # Can't pass num_procs > 1 in this configuration. If you need to run multiple
    # processes, see e.g. flask_gunicorn_embed.py
    server = Server({'/bkapp': make_interactive},
                    io_loop=IOLoop(), allow_websocket_origin=["*"])
    server.start()
    server.io_loop.start()


Thread(target=bk_worker).start()

if __name__ == '__main__':

    print('Opening single process Flask app with embedded Bokeh application.')
    print('The bokeh docs discuss this at')
    print('https://docs.bokeh.org/en/latest/docs/user_guide/server.html#embedding-bokeh-server-as-a-library')
    # Turning of reloader because when it is on, we get:
    # OSError: [Errno 98] Address already in use
    # which doesn't change the behavior other than give an ugly exception.
    # However, even with debug = True, it says it is reloading but the code
    # does not reload...there something about how bokeh server and Flask play
    # together....
    app.run(use_reloader=False, host='0.0.0.0', port=8000, debug=True)
    # app.run(host='0.0.0.0', port=8000, debug=True)
