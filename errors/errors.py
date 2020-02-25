import traceback
import sys
import logging
logger = logging.getLogger(__name__)


def handle_exception(e):
    logger.exception(f'Exception...{e}')
    # print('TRACEBACK: \n*******')
    # exc_type, exc_value, exc_traceback = sys.exc_info()
    # traceback.print_tb(exc_traceback, file=sys.stdout)


class MongoConnectError(Exception):
    pass


class MongoCollectionError(Exception):
    pass


class NoReadingsError(Exception):
    pass


class PlotNoDatesFound(Exception):
    pass
