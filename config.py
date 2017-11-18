import configparser
import logging
import os

import datetime

# Getting the absolute path to the folder of this very script file, so that can be used to open the config file, which
# is also located in this folder
PATH = os.path.dirname(os.path.realpath(__file__))

LOGGING_PATH = os.path.join(PATH, 'logs')

SCOPUS_LOGGING_EXTENSION = 'scopus'



def _format_log_file_name(datetime_object, extension_string):

    # Formatting the string of the date
    date_string = _format_date(datetime_object)
    # Joining the date string with the string extension
    file_name_string = '-'.join([date_string, extension_string])
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
    file_path = get_log_file_path(datetime_object, SCOPUS_LOGGING_EXTENSION)
    # Checking if the log already exists, if not
    if log_exists(datetime_object, SCOPUS_LOGGING_EXTENSION):
        file_mode = 'a'
    else:
        file_mode = 'w+'

    logging.basicConfig(level=logging.INFO,
                        filename=file_path,
                        filemode=file_mode,
                        format='%(asctime)s %(name)-40s %(levelname)-8s %(message)s')


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
        path = os.path.join(PATH, 'config.ini')
        return path




