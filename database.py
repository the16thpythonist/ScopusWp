from ScopusWp.config import Config
from ScopusWp.config import SQL_LOGGING_EXTENSION

import logging

import MySQLdb


class Db:

    _instance = None

    def __init__(self):
        pass

    @staticmethod
    def get_instance():

        if Db._instance is None:
            config = Config.get_instance()
            database = config['MYSQL']['database']
            username = config['MYSQL']['username']
            password = config['MYSQL']['password']
            connector = MySQLdb.connect(host='localhost', user=username, passwd=password, db=database)
            Db._instance = connector

        return Db._instance


class SQLDatabaseAccessInterface:

    def execute(self, sql):
        """
        Supposed to execute a sql command without return

        :param sql: The string sql code to return
        :return: void
        """
        raise NotImplementedError()

    def select(self, sql):
        """
        Supposed to execute a sql command and then return a list of lists, where each sub list represents one row
        in the database.

        :param sql: The string sql command to return
        :return: A list of lists
        """
        raise NotImplementedError()


class MySQLDatabaseAccess(SQLDatabaseAccessInterface):

    def __init__(self):
        # Getting the database object and the according cursor
        self.db = Db.get_instance()
        self.cursor = self.db.cursor()

        # Getting the according logger
        self.logger = logging.getLogger(SQL_LOGGING_EXTENSION)

    def execute(self, sql):
        try:
            self.cursor.execute(sql)
        except Exception as exception:
            # Logging the error
            error_string = (
                'During the handling of the SQL expression {} occurred the following exception {}'
            ).format(
                str(sql).replace('\n', ' '),
                str(exception).replace('\n', ' ')
            )
            self.logger.error(error_string)
            # Actually raising an exception
            raise exception

    def select(self, sql):
        # First: Actually executing the sql command
        self.execute(sql)

        # Second: iterating through the contents of the cursor
        row_list = []
        for row in self.cursor:
            if isinstance(row, list):
                row_list.append(row)
            else:
                # If the contents of the cursor are no rows, than either there was an error, or the method was misused
                error_message = (
                    'There seems to be an error with the SQL statement {}, '
                    'the returned data is not in the row format: {}'
                ).format(
                    str(sql).replace('\n', ' '),
                    str(row).replace('\n', ' ')
                )
