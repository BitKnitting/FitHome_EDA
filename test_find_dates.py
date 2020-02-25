###########################################################
# test_find_dates.py
# Simple test that validates we can connect to the mongo db
# and read records. It returns the dates in the mongo db
# where there are power readings in ISODate format.
###########################################################
from errors.errors import handle_exception
from readings.readings import PowerReadings
try:
    p = PowerReadings()
    collection = p.get_connection_to_collection()
    iso_days_list = p.get_isodate_list(collection)
    [print(n) for n in iso_days_list]
except Exception as e:
    handle_exception(e)
