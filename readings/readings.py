
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
import time
import pandas as pd
from errors.errors import MongoConnectError, MongoCollectionError, NoReadingsError
from pymongo.errors import ConfigurationError

#########################################################
# ***** PowerReading class
#
# The PowerReadings class is a helper class to retrieve
# active power readings from mongo into a pandas df
# that can be used for visualization (in bokeh for eg.)
#
# Public Functions:
# ****** get_DataFrame_for_date()
##########################################################
ALL_READINGS = '*'


class PowerReadings:
    ###################################################
    # ****** _get_DataFrame_for_date
    # Get records from the mongod db service and
    # transfer them into a DataFrame.
    #
    # The date input is either:
    #  - an ISODate string
    #  - the string '*'
    #
    # NOTE: An ISO Date formatted string is
    # 'YYYY-MM-DD' , e.g.: '2020-01-12'
    #
    #  If '*', all readings in the
    # aggregate readings collection are returned.
    #
    # By default, all readings are returned.
    #
    # The records are returned as a Pandas DataFrame
    # with the datetimeindex set to the datetime the
    # reading was put into the mongod db and the a 'Pa'
    # column that are the active power values taken with
    # the datetime.
    # Pandas DataFrame.  The index is the datetimeindex
    # where the date will be the date passed in and the
    # time will be hh:mm:ss of each reading.  There is
    # one column for the active power readings.
    ##################################################
    # Date is in ISODATE format.
    def get_DataFrame_for_date(self, date=ALL_READINGS):
        if date not in ALL_READINGS:
            self._check_date(date)
        collection = self.get_connection_to_collection()
        return self._get_readings(date, collection)

    ###################################################
    # ****** get_connection_to_collection
    #
    # We have our mongodb hard coded.
    # 1) Can we connect to the mongod (is the service running)?
    # 2) Can we get to the FitHome db (does it exist)?
    # 3) Can we get to the aggregate collection?
    # If we can get to the aggregate collection, YIPPEE!
    ###################################################

    def get_connection_to_collection(self):
        # Create a connection and attempt to access mongod
        client = MongoClient("mongodb://127.0.0.1:27017")
        try:
            client.server_info()  # will throw an exception
        except ConfigurationError as e:
            raise MongoConnectError(f'Could not connect to mongo db. Error{e}')
        # Check to see if the db and the collection exist.
        db = client['FitHome']
        # On the mac, we use db.list_collection_names() - newer version of pymongo.
        # on Rasp Pi, we need v 3.4 of pymongo so the method is collection_names.
        if 'aggregate' not in db.collection_names():
            raise MongoCollectionError(
                'Could not access the aggregate collection.')
        return db['aggregate']

    def _get_first_and_last_isodate(self, collection):
        try:
            first_record = collection.find_one()
            last_record = list(collection.find().sort(
                [('_id', -1)]).limit(1))[0]
            isodate_first = self._id_to_isodate(first_record['_id'])
            isodate_last = self._id_to_isodate(last_record['_id'])
            print(f'first date: {isodate_first}  Last date: {isodate_last}')
        except Exception as e:
            raise
        return isodate_first, isodate_last

    def get_isodate_list(self, collection):
        iso_days_list = []
        try:
            isodate_first, isodate_last = self._get_first_and_last_isodate(
                collection)
            start_date = datetime.fromisoformat(isodate_first).date()
            end_date = datetime.fromisoformat(isodate_last).date()
            gen_expr = (start_date + timedelta(n)
                        for n in range(int((end_date-start_date).days)+1))
            for dt in gen_expr:
                iso_days_list.append(dt.isoformat())
        except Exception as e:
            raise
        return iso_days_list

    def _id_to_isodate(self, id):
        id_str = str(id)
        hex_str = id_str[0:8]
        ts = int(hex_str, 16)
        return datetime.fromtimestamp(ts).isoformat()
    ###################################################
    # ****** _check_date
    #
    # It's great that mongo uses ISODate...it standardizes
    # what the string date input has to be.  Here we
    # check if the string is formatted as an ISODate.
    # An ISO Date formated string is passed in ('YYYY-MM-DD' , e.g.: '2020-01-12')

    ###################################################
    def _check_date(self, isodate):
        try:
            date.fromisoformat(isodate)
        # See stackoverflow https://stackoverflow.com/questions/4730435/exception-passing-in-python
        except Exception as e:
            raise

    def _get_readings(self, date, collection):
        df = pd.DataFrame()
        if date not in ALL_READINGS:
            # Get the object Ids that bound our query
            minId, maxId = self._get_min_max_objectIds(date)
            # Query for the Pa (active power) readings for the date(s) between min and max.
            # Returns a DataFrame of two columns.  The first column is the mongo object ids.
            # The second is the active power reaadings.
            try:
                df = pd.DataFrame.from_records(collection.find(
                    {"_id": {'$gt': minId, '$lt': maxId}}, {'_id': 1, 'Pa': 1}))
            except Exception as e:
                raise
        # This query might be a "get a cup of coffee and wait...."
        else:
            try:
                df = pd.DataFrame.from_records(
                    collection.find(projection={'_id': 1, 'Pa': 1}))
            except Exception as e:
                raise
        if df.empty:
            raise NoReadingsError(
                f'There are no readings in the database for {date}.')

        df['timestamp'] = df['_id'].astype('|S').str.slice(
            start=0, stop=8).apply(int, base=16)
        # Ugh....timezones/timestamps/datetime.... I used this
        # Goop to get what I want plotted in bokeh...there
        # is most likely a MUCH BETTER WAY.
        df.index = pd.to_datetime(df['timestamp'], unit='s')
        df.index = df.index.tz_localize('UTC').tz_convert('US/Pacific')
        df.index = df.index.round('s').tz_localize(None)
        df.drop(['timestamp', '_id'], axis=1, inplace=True)
        return df

    def _get_min_max_objectIds(self, isodate_string):
        minId = self._make_objectid(isodate_string)
        isodate_plus_day = self._add_one_day(isodate_string)
        maxId = self._make_objectid(isodate_plus_day)
        return minId, maxId
    # ###########################
    # The object id in the mongodb is a string of 12 bytes.
    # The first 4 bytes is the unix timestamp when the entry
    # was made.  We use these bytes to get readings of a specific
    # date.  Once we have the 4 bytes, we put the string '00'in the remaining
    # 8 characters.

    def _make_objectid(self, isodate_string):
        d = self._make_date(isodate_string)
        # Get the timestamp as a 4 byte hex string
        ts_string = '{:x}'.format(int(time.mktime(d.timetuple())))
        # Create an object id starting with the time stamp string then padded with
        # 00's to have 12 hex bytes represented within the object id string.
        object_id = ObjectId(ts_string + "0000000000000000")
        return object_id

    def _make_date(self, isodate_string):
        try:
            d = date.fromisoformat(isodate_string)
        except Exception as e:
            raise
        return d

    def _add_one_day(self, isodate_string):
        d = self._make_date(isodate_string)
        d += timedelta(days=1)
        return d.isoformat()
