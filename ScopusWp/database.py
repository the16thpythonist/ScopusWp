from ScopusWp.config import Config
from ScopusWp.config import SQL_LOGGING_EXTENSION

import logging

import MySQLdb


class Db:
    """
    This is the singleton class which manages the database connection object.
    On the first call to the get instance method a new "MySQLdb" connection object is being created using the database
    name, username and password given in the config file of the project.
    The connection object is stored in a class variable and is returned each time the get instance method is called
    again.
    """
    _instance = None

    def __init__(self):
        pass

    @staticmethod
    def get_instance():
        """
        This method returns the connection object for the database that is stored inside this singleton.

        :return: MySQLdb.connect() object
        """
        # In case this is the first call to the method a new connection object will be created and saved in the static
        # class variable.
        if Db._instance is None:
            Db.new_instance()

        # Otherwise the saved object will be returned
        return Db._instance

    @staticmethod
    def new_instance():
        """
        This method creates the new database connection object from the database name, the username and password in
        the config file of the project and then saves the object in the class variable
        :return:
        """
        config = Config.get_instance()
        database = config['MYSQL']['database']
        username = config['MYSQL']['username']
        password = config['MYSQL']['password']
        connector = MySQLdb.connect(host='localhost', user=username, passwd=password, db=database)
        Db._instance = connector


class SQLDatabaseAccessInterface:
    """
    Simple interface for a sql database access wrapper.
    The database wrapper, however it is implemented should implement two methods of interacting with a database:

    EXECUTE
    The execute method takes some sql code snippet and simply executes it onto the database, without any return
    whatsoever, this is designed to be used for insert or update statements

    SELECT
    The select method is supposed to also execute the sql code on the database, but return a list of tuples. This
    is manly supposed to be used with the sql select statement and the returned list to be the list of rows as the
    response to such a select statement
    """
    def save(self):
        """
        Supposed to save the changes made to the database

        :return: void
        """
        raise NotImplementedError()

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
    """
    MySQL database access wrapper.
    THis class implements the SQL database access interface.
    it is used to execute Insert, update statements onto the database or fetch rows of data with the select statement.
    This wrapper is to be used everywhere, where a interface to the mysql database is needed.
    """
    def __init__(self):
        # Getting the database access from the singleton and creating a new cursor to interact with the database
        self.db = Db.get_instance()
        self.cursor = self.db.cursor()

        # Getting the according logger
        self.logger = logging.getLogger('MYSQLDatabaseAccess')

    def save(self):
        #self.db.commit()
        #self.cursor.close()
        #self.cursor = self.db.cursor()
        a = 1

    def execute(self, sql):
        """
        Executes the given string of sql statements on the mysql database of this project, which is specified in the
        config file.

        :param sql: The string of sql code.
        :return: void
        """
        try:
            self.cursor.execute(sql)
        except Exception as exception:
            # Logging the error
            error_string = (
                'During the handling of the SQL expression "{}" occurred the following exception "{}"'
            ).format(
                str(sql).replace('\n', ' '),
                str(exception).replace('\n', ' ')
            )
            self.logger.error(error_string)
            # Actually raising an exception
            raise exception

    def select(self, sql):
        """
        Executes the sql code string on the database and returns the list of rows selected.
        This method is supposed to be used with the select statement.

        :param sql: The sql code string.
        :return: [data tuples, each one for one row, that matches the select statement]
        """
        # First: Actually executing the sql command
        self.execute(sql)

        # Second: iterating through the contents of the cursor
        row_list = []
        for row in self.cursor:
            if isinstance(row, (list, tuple)):
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
                self.logger.error(error_message)
        return row_list
