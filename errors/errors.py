import traceback
import sys
def handle_exception(e):
    print(f'*******\nERROR: {e}\n*******')
    print('TRACEBACK: \n*******')
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_tb(exc_traceback, file=sys.stdout)


class MongoConnectError(Exception):
    pass


class MongoCollectionError(Exception):
    pass


class NoReadingsError(Exception):
    pass


class PlotNoDatesFound(Exception):
    pass
