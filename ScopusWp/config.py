import configparser
import logging
import os

import datetime
import pathlib
import threading

# Getting the absolute path to the folder of this very script file, so that can be used to open the config file, which
# is also located in this folder
PATH = os.path.dirname(os.path.realpath(__file__))
VERSION = '0.3.0'
PROJECT_PATH = '/home/jonas/PycharmProjects/ScopusWp/ScopusWp'

LOGGING_PATH = os.path.join(PATH, 'logs')

SCOPUS_LOGGING_EXTENSION = 'SCOPUS'
SQL_LOGGING_EXTENSION = 'SQL'


def _format_log_file_name(datetime_object, extension_string):

    # Formatting the string of the date
    date_string = _format_date(datetime_object)
    # Joining the date string with the string extension
    file_name_string = '-'.join([date_string, 'log'])
    file_name_string += '.txt'

    return file_name_string


def _format_date(datetime_object):
    date_string = '{}-{}-{}'.format(datetime_object.year, datetime_object.month, datetime_object.day)
    return date_string


def get_log_file_path(datetime_object, extension_string):
    file_name = _format_log_file_name(datetime_object, extension_string)
    file_path = os.path.join(LOGGING_PATH, file_name)
    return file_path


def log_exists(datetime_object, extension_string):
    file_path = get_log_file_path(datetime_object, extension_string)

    return os.path.exists(file_path) and os.path.isfile(file_path)


def init_logging():
    datetime_object = datetime.datetime.now()
    file_path = get_log_file_path(datetime_object, '')
    # Checking if the log already exists, if not
    if log_exists(datetime_object, ''):
        file_mode = 'a'
        with open(file_path, 'a') as file:
            file.write('\n\nSTARTING A NEW SESSION:\n\n')
    else:
        file_mode = 'w+'

    logging.basicConfig(level=logging.INFO,
                        filename=file_path,
                        filemode=file_mode,
                        format='%(asctime)s %(name)-40s %(levelname)-8s %(message)s')


class LoggingController:

    DATE_FORMAT = '%Y-%m-%d'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self):
        self.config = Config.get_instance()

        self.log_file_path = pathlib.Path(LOGGING_PATH) / self.create_log_file_name()

    def init(self):
        self.prepare_log_file(self.log_file_path)

    def close(self):
        self.post_process_log_file(self.log_file_path)

    def prepare_log_file(self, path):

        # Checking if the path exists and if it does, that means there was a log written on that day already, then
        # opening the file in append mode
        # Getting the current datetime string
        datetime_object = datetime.datetime.now()
        datetime_string = datetime_object.strftime(self.DATETIME_FORMAT)

        line_string = '\n\nSTARTING A NEW SESSION @ "{}"\n\n'.format(datetime_string)

        file_mode = 'a'
        with path.open(mode=file_mode) as file:
            file.write(line_string)

        file_path = str(path)
        logging.basicConfig(
            level=logging.INFO,
            filename=file_path,
            filemode='a',
            format='%(asctime)s %(name)-40s %(levelname)-8s %(message)s'
        )

    def post_process_log_file(self, path):
        datetime_object = datetime.datetime.now()
        datetime_string = datetime_object.strftime(self.DATETIME_FORMAT)

        line_string = '\n\nCLOSING SESSION @ "{}"\n\n'.format(datetime_string)

        with path.open(mode='a') as file:
            file.write(line_string)

    def create_activity_file_name(self):
        # Creating the date string from the current datetime object
        datetime_object = datetime.datetime.now()
        date_string = datetime_object.strftime(self.DATE_FORMAT)
        # The base name extension for the file name is saved as a entry in the config file
        base_name_string = self.config['LOGGING']['activity_log_name']

        # Joining the date string and the base string into the log file name
        name_string = '{}-{}.txt'.format(
            date_string,
            base_name_string
        )

        return name_string

    def create_log_file_name(self):
        # Creating the date string from the current datetime object
        datetime_object = datetime.datetime.now()
        date_string = datetime_object.strftime(self.DATE_FORMAT)
        # The base name extension for the file name is saved as a entry in the config file
        base_name_string = self.config['LOGGING']['debug_log_name']

        # Joining the date string and the base string into the log file name
        name_string = '{}-{}.txt'.format(
            date_string,
            base_name_string
        )

        return name_string


class LoggingObserver(threading.Thread):

    def __init__(self, logger_name):

        self.logger = logging.getLogger(logger_name)


class Config:
    """
    A singleton class for the access to the config object
    """
    _instance = None

    def __init__(self):
        pass

    @staticmethod
    def get_instance():

        if Config._instance is None:
            Config._instance = Config._create_instance()

        return Config._instance

    @staticmethod
    def _create_instance():
        # Getting the path to the config file
        path = Config._config_path()
        # Creating the config parser object and returning it
        config = configparser.ConfigParser()
        config.read(path)

        return config

    @staticmethod
    def _config_path():
        # Joining the config path
        path = os.path.join(PROJECT_PATH, 'config.ini')
        return path




