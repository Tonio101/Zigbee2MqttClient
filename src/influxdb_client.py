import requests

from logger import Logger
log = Logger.getInstance().getLogger()


class InfluxDbClient(object):

    def __init__(self, url: str, auth: tuple, db_name: str,
                 measurement: str, tag_set: str):
        self.url = url
        self.auth = auth
        self.db = db_name
        self.params = (
            ('db', db_name),
        )
        self.headers = {'Content-Type': 'application/json'}
        self.measurement = measurement
        self.tag_set = tag_set

    def set_url(self, url):
        self.url = url

    def set_auth(self, auth):
        self.auth = auth

    def set_db(self, db_name):
        self.db = db_name
        self.params = (
            ('db', db_name),
        )

    def write_data(self, data):
        """
        Data should be a string of field_set=<val>.
        If there are multiple field_sets, comma delimiter
        should be used.

        Example of InfluxDB query:
        weather,location=home temperature=55.5,humidity=70.2

        Args:
            data (str): field_set=<val> to write in influx db.

        Returns:
            int: 0 if successful.
        """
        data = ("{0},{1} {2}").format(
            self.measurement,
            self.tag_set,
            data
        )

        log.debug(data)
        response = requests.post(url=self.url,
                                 params=self.params,
                                 data=data,
                                 auth=self.auth,
                                 headers=self.headers)
        log.debug(response)

        if response.status_code == 204:
            log.debug(("Successfully sent data to influx db "
                       "Elapsed time {0}").format(response.elapsed))
            return 0

        log.error("Error to send data to influx db {0}".format(
            response.status_code
        ))

        return response.status_code
