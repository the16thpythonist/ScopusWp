import importlib
import threading
import configparser
import pathlib
import pickle
import os

from ScopusWp.database import MySQLDatabaseAccess
from ScopusWp.config import PATH


MODULES = [
        'scopus.main',
        'controller',
        'data',
        'database',
        'main',
        'reference',
        'view',
        'wordpress'
    ]

HEADER = '\033[95m'
BLUE = '\033[94m'
GREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
END = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'


class OutputController:
    RED = '\u001b[31m'
    GREEN = '\u001b[32;1m'
    YELLOW = '\u001b[33m'
    BLUE = ' \u001b[34m'
    MAGENTA = '\u001b[35m'
    CYAN = '\u001b[36m'

    BOLD = '\u001b[1m'
    UNDERLINE = '\u001b[4m'

    RESET = '\u001b[0m'

    def __init__(self):
        pass

    def print_error(self, message):
        error_string = '[!]  {}'.format(message)
        error_string_red = self.get_red(error_string)
        print(error_string_red)

    def print_exception(self, exception):
        exception_string = 'Exception: "{}"'.format(str(exception))
        self.print_error(exception_string)

    def print_header(self, message):
        header_string = '\n{}\n'.format(message)
        header_string = self.get_bold(header_string)
        header_string = self.get_underline(header_string)
        print(header_string)

    def print_progress(self, message):
        progress_string = '{}...'.format(message)
        print(progress_string)

    def print_empty_line(self):
        print(' ')

    def print_info(self, message):
        print(message)

    def print_success(self, message):
        success_string = '...{}'.format(message)
        success_string_green = self.get_green(success_string)
        print(success_string_green)

    def print_warning(self, message):
        warning_string = '[!]  {}'.format(message)
        warning_string_yellow = self.get_yellow(warning_string)
        print(warning_string_yellow)

    def get_red(self, string):
        return '{}{}{}'.format(self.RED, string, self.RESET)

    def get_blue(self, string):
        return '{}{}{}'.format(self.BLUE, string, self.RESET)

    def get_magenta(self, string):
        return '{}{}{}'.format(self.MAGENTA, string, self.RESET)

    def get_cyan(self, string):
        return '{}{}{}'.format(self.CYAN, string, self.RESET)

    def get_yellow(self, string):
        return '{}{}{}'.format(self.YELLOW, string, self.RESET)

    def get_green(self, string):
        return '{}{}{}'.format(self.GREEN, string, self.RESET)

    def get_bold(self, string):
        return '{}{}{}'.format(self.BOLD, string, self.RESET)

    def get_underline(self, string):
        return '{}{}{}'.format(self.UNDERLINE, string, self.RESET)


class InputController:

    def __init__(self):
        pass

    def pause(self):
        input('\nPress enter to continue...')
        print(' ')


class InstallationController:

    MODULES = [
        'scopus.main',
        'scopus.data',
        'scopus.observe',
        'scopus.persistency',
        'scopus.scopus',
        'config',
        'controller',
        'data',
        'database',
        'main',
        'reference',
        'view',
        'wordpress'
    ]

    def __init__(self):
        self.input = InputController()
        self.output = OutputController()

        self.config = None

        self.db_access = None
        self.username = None
        self.database = None
        self.password = None
        self.host = None

        self.path = None

        self.config_path = None
        self.authors_path = None
        self.publications_cache = None
        self.ids_json = None

    def run(self):

        done = False
        stage = 0
        while not done:
            self.input.pause()
            if stage == 0:
                if not self.check_import():
                    continue
                stage += 1

            if stage == 1:
                if not self.install_files():
                    continue
                stage += 1

            if stage == 2:
                if not self.check_database():
                    continue
                stage += 1

            if stage == 3:
                if not self.install_database():
                    continue
                stage += 1

            if stage == 4:
                done = True
                continue

        self.output.print_success('INSTALLATION FINISHED')

    def progress(self, message):
        self.output.print_progress(message)

    def error(self, message, exception):
        self.output.print_error(message)
        self.output.print_exception(exception)

    def success(self, message):
        self.output.print_success(message)

    def install_files(self):
        self.output.print_header('INSTALLING THE NECESSARY FILES')

        # Getting the base path of the ScopusWp package
        try:
            self.progress('Fetching the path of the package from the config module')
            from ScopusWp.config import PATH
            self.path = PATH
            self.success('Successfully fetched the path "{}"'.format(PATH))
        except Exception as exception:
            self.error('The Path could not be fetched from the config', exception)

        # installing the config file
        if not self.install_config_file():
            return False

        if not self.install_cache_files():
            return False

        if not self.install_ids_json():
            return  False

        return True

    def install_config_file(self):
        # Using the path of the package to assemble the path for the config file and then creating a path object
        # and saving it as a instance attribute
        config_file_path_string = '{}/config.ini'.format(self.path)
        self.config_path = pathlib.Path(config_file_path_string)

        try:
            self.progress('Creating entries for the config file')
            config = configparser.ConfigParser()
            config.read(config_file_path_string)

            self.progress('creating scopus entries')
            config['SCOPUS'] = {}
            config['SCOPUS']['api_key'] = ''
            config['SCOPUS']['url'] = ''

            self.progress('creating kit open entries')
            config['KITOPEN'] = {}
            config['KITOPEN']['url'] = ''

            self.progress('creating wordpress entries')
            config['WORDPRESS'] = {}
            config['WORDPRESS']['url'] = ''
            config['WORDPRESS']['username'] = ''
            config['WORDPRESS']['password'] = ''

            self.progress('creating mysql entries')
            config['MYSQL'] = {}
            config['MYSQL']['host'] = ''
            config['MYSQL']['database'] = ''
            config['MYSQL']['username'] = ''
            config['MYSQL']['password'] = ''

            self.progress('Saving the config file')
            config.write(self.config_path.open(mode='w+'))
            self.success('Config file created')
        except Exception as exception:
            self.error('There was en error during the creation of the config file', exception)
            return False

        return True

    def install_cache_files(self):
        try:
            self.progress('Creating the folder, which contains the cache files')
            # Using the path of the package to assemble the path of the cache folder and then creating the cache folder
            # with a pathlib path object
            cache_folder_path_string = '{}/cache'.format(self.path)
            cache_folder_path = pathlib.Path(cache_folder_path_string)
            if not cache_folder_path.exists():
                cache_folder_path.mkdir()
            self.success('Cache folder created')
        except Exception as exception:
            self.error('There was an error creating the cache folder', exception)
            return False

        try:
            self.progress('creating the path to the publications cache')
            # Creating the string file paths to the publications cache and the according path object
            publications_cache_path_string = '{}/publications.pkl'.format(cache_folder_path_string)
            publications_cache_path = pathlib.Path(publications_cache_path_string)
            self.progress('creating the publications cache file')
            with publications_cache_path.open(mode='wb+') as file:
                self.progress('Pickle dumping an empty dict to the file')
                pickle.dump({}, file)
            self.success('publications cache was created')
        except Exception as exception:
            self.error('there was an error during the creation of the "publications" cache', exception2)
            return False

        try:
            self.progress('creating the path to the authors cache')
            authors_cache_path_string = '{}/authors.pkl'.format(self.path)
            authors_cache_path = pathlib.Path(authors_cache_path_string)
            self.progress('creating the authors cache file')
            with authors_cache_path.open(mode='wb+') as file:
                self.progress('pickle dumping an empty dict into the file')
                pickle.dump({}, file)
            self.success('authors cache was created')
        except Exception as exception:
            self.error('there was en error during the creation of the "authors" cache', exception)
            return False

        return True

    def install_ids_json(self):
        try:
            self.progress('Creating the path to the ids json file')
            ids_json_path_string = '{}/ids.json'.format(self.path)
            ids_json_path = pathlib.Path(ids_json_path_string)
            self.progress('Creating the ids json file')
            with ids_json_path.open(mode='w+') as file:
                file.write(
                    '{\n'
                    'used: []\n'
                    'unused: []\n'
                    'pointer: 0\n'
                    '}\n'
                )
            self.success('ids json storage was created')
        except Exception as exception:
            self.error('There was an error during the creation of the ids json file', exception)
            return False

        return True

    def install_database(self):
        string = (
            'INSTALLING THE DATABASE TABLES'
        )
        self.output.print_header(string)

        string = (
            'Proceeding to install all the database tables\n'
        )
        self.output.print_progress(string)

        string = (
            'Before installing the new database tables, the installation script will drop the tables by the names '
            '"publications" and "reference", which will cause them to loose all data they currently contain, if you '
            'dont want this to happen, you may now backup the data or continue right away.'
        )
        self.output.print_warning(string)

        self.input.pause()

        try:
            string = (
                'Deleting all the data in the tables "reference" and "publications" on the database "{}"'
            ).format(self.database)
            self.output.print_progress(string)
            self.db_access.execute('DROP TABLE publications;')
            self.db_access.execute('DROP TABLE reference;')
            string = (
                'Dropped the tables "reference" and "publications"'
            )
            self.output.print_success(string)
        except Exception as exception:
            self.output.print_exception(exception)
            return False

        try:
            string = (
                'Creating the tables "reference" and "publications" as needed by the ScopusWp program'
            )
            self.output.print_progress(string)
            from ScopusWp.config import PATH
            sql_setup_path = '{}/setup.sql'.format(PATH)
            with open(sql_setup_path, mode='r+') as file:
                sql = file.read()
                self.db_access.execute(sql)
            string = (
                'Created the database tables'
            )
            self.output.print_success(string)
        except Exception as exception:
            self.output.print_exception(exception)
            return False

        return True

    def check_database(self):
        string = (
            'CHECKING THE DATABASE ACCESS'
        )
        self.output.print_header(string)

        string = (
            'The ScopusWp program uses a MySQL database to store all the publication data as a backup locally '
            'and to store a reference table, that connects the internel ID System with the various external ID systems '
            'for the publications for example the scopus website or the Wordpress Post IDs.\n'
            'So tu use ScopusWp there has to be a functional MySQL database installed and ready for usage.\n'
            'The USERNAME, PASSWORD and DATABASE to be used have to be specified in the "config.ini" file in the root '
            'folder'
        )
        self.output.print_info(string)

        # Importing the config
        try:
            string = (
                'Importing the ScopusWp config file'
            )
            self.output.print_progress(string)
            import ScopusWp.config as cfg
            self.config = cfg.Config.get_instance()
            string = (
                'fetched config information'
            )
            self.output.print_success(string)
        except Exception as exception:
            string = (
                'Failed to import the config of the project'
            )
            self.output.print_error(string)
            self.output.print_exception(exception)
            return False

        # Reading the config for the data base login Information
        self.host = self.config['MYSQL']['host']
        self.username = self.config['MYSQL']['username']
        self.password = self.config['MYSQL']['password']
        self.database = self.config['MYSQL']['database']

        string = (
            'Fetched the following data from the config file:\n'
            'HOST:       {}\n'
            'USERNAME:   {}\n'
            'PASSWORD:   {}\n'
            'DATABASE:   {}\n'
        ).format(
            self.output.get_cyan(self.host),
            self.output.get_cyan(self.username),
            self.output.get_cyan(self.password),
            self.output.get_cyan(self.database)
        )
        self.output.print_info(string)

        # Attempting to connect to the database
        try:
            string = (
                'Attempting to connect to the MySQL database'
            )
            self.output.print_progress(string)
            import ScopusWp.database as db
            self.db_access = db.MySQLDatabaseAccess()
            string = (
                'Connected to the MySQL database "{}" with "{}"@"{}"'
            ).format(
                self.database,
                self.password,
                self.username
            )
            self.output.print_success(string)
        except Exception as exception:
            string = (
                'Failed to connect to the MySQL database'
            )
            self.output.print_error(string)
            self.output.print_exception(exception)
            return False

        return True

    def check_import(self):
        string = (
            'CHECKING THE IMPORTS'
        )
        self.output.print_header(string)

        string = (
            'To use the ScopusWp program, the installation folder for the ScopusWp package has to be '
            'part of the PYTHONPATH environmental variable for the operating system.\n'
        )
        self.output.print_info(string)

        string = (
            'Attempting to import all the modules of the package dynamically, to check for import errors of required '
            'packages in the individual modules as well...\n'
        )
        self.output.print_info(string)

        # Importing all the modules
        error_occurred = False
        for module_name in self.MODULES:
            if self._import_module(module_name) is True:
                error_occurred = True

        success = not error_occurred
        return success

    def _import_module(self, module_name):
        module_name_split_list = module_name.split('.')
        module_name_short_string = '{}'.format(
            module_name_split_list[-1]
        )
        string = (
            'Attempting to import the module "ScopusWp.{}" as "{}"'
        ).format(
            module_name,
            module_name_short_string
        )
        self.output.print_progress(string)

        # Creating the python code string, that is to be dynamically executed and which will contain the statement to
        # import the module given
        execute_string = (
            'import ScopusWp.{} as {}'
        ).format(
            module_name,
            module_name_short_string
        )
        try:
            exec(execute_string)
            # Printing the message, that everything went fine
            string = (
                'The module "ScopusWp.{}" was imported'
            ).format(module_name)
            self.output.print_success(string)
            # Returning false when the import went well and there was no error
            return False
        except Exception as exception:
            # Printing the error
            string = (
                'There has been a problem with importing the module "ScopusWp.{}"'
            ).format(module_name)
            self.output.print_error(string)
            string = (
                'Exception: "{}"'
            ).format(str(exception))
            self.output.print_error(string)
            # Returning true in case of error
            return True


def main(start_point):
    done = False
    start_point = 0

    if start_point == 0:
        string = (
            '########################################\n'
            '##   {}SCOPUS WP INSTALLATION PROCESS{}   ##\n'
            '########################################\n'
        ).format(HEADER, END)
        print(string)

        string = (
            'If you have not already entered the required data into the {}"config.ini"{} config file than please \n'
            'do so now and continue, when done.'
        ).format(
            BOLD,
            END
        )
        print(string)

        input('Press enter to continue...')
        start_point += 1

    if start_point == 1:
        string = (
            'To use this program, the package itself has to be located in a folder, which is part of the PYTHONPATH'
            'environmental variable of the operating system.\n'
            'If that is not already the case: Google the following "Adding to Python Path on {insert your OS}"!'
        )
        print(string)

        string = (
            '\nAttempting to import the necessary modules from within the ScopusWp package...\n'
        )
        print(string)

        # Dynamically importing all the modules of the package to test if the package has been installed correctly
        # with the installation folder being added to the python path of the operating system
        for module_name in MODULES:
            # Dynamically parsing and executing the
            try:
                string = (
                    'Importing module "ScopusWp.{}"...'
                ).format(module_name)
                print(string)
                execution_string = 'import ScopusWp.{module} as {short}'.format(
                    module=module_name,
                    short=module_name.split('.')[0]
                )
                exec(execution_string)
            except Exception as exception:
                string = (
                    '{fail}[!] There seems to be a problem with the module import.\n'
                    '[!] The module {module} could not be imported.\n'
                    '[!] The following exception has been risen: "{exception}"\n'
                    '[!] For debugging your current python path is: "{path}"{end}'
                ).format(
                    fail=FAIL,
                    end=END,
                    module=module_name,
                    exception=str(exception).replace('\n', ''),
                    path=str(os.sys.path)
                )
                print(string)
                start_point = 1
                break
            string = (
                '{}...Done{}'
            ).format(GREEN, END)
            print(string)

    return done, start_point


class FolderSetupController:

    def __init__(self):
        self.path = PATH

        self.logs_path = pathlib.Path(PATH)
        self.logs_path.joinpath('logs')

        self.temp_path = pathlib.Path(PATH)
        self.temp_path.joinpath('temp')

    def run(self):
        if not self.logs_exists():
            self.create_logs_folder()
            print('created the logs folder')
        else:
            print('Logs folder already exists')

        if not self.temp_exists():
            self.create_temp_folder()
            print('created the temp folder')
        else:
            print('temp folder already exists')

    def create_logs_folder(self):
        self.logs_path.mkdir()

    def create_temp_folder(self):
        self.temp_path.mkdir()

    def logs_exists(self):
        return self.logs_path.exists() and self.logs_path.is_dir()

    def temp_exists(self):
        return self.temp_path.exists() and self.temp_path.is_dir()


class ConfigSetupController:

    TEMPLATE = (
        '[SCOPUS]\n'
        '# Get your personal API key from scopus by visiting the website:\n'
        'api_key = your api key\n'
        '# The url to the scopus web API\n'
        'url = https://api.elsevier.com/content\n'
        '\n'
        '[WORDPRESS]'
        '# The ScopusWp program will post the publications onto the website you specify in this section identifying \n'
        '# as the user defined here by username and password. Please remember to create a user with this data first\n'
        'url = the url to your wordpress xmlrpc.php site\n'
        'username = Username\n'
        'password = Password\n'
        '\n'
        '[MYSQL}]\n'
        '# The ScopusWp program needs access to a running MySQL/MariaDB database enter the user credentials below\n'
        'host = localhost\n'
        'database = Name of the database to be used by ScopusWp\n'
        'username = Username\n'
        'password = Password\n'
        '# The section below defines the names for the individual tables to be used by ScopusWp. You may change the\n'
        '# the table names if you wish. It is recommended to keep the default\n'
        'publication_cache_table = publication_cache\n'
        'author_cache_table = author_cache\n'
    )

    def __init__(self):
        self.path = PATH

        self.config_path = pathlib.Path(PATH)
        self.config_path.joinpath('config.ini')

    def run(self):
        if not self.exists():
            self.create()
            print('created the config file')
        else:
            print('config file already existed')

    def create(self):
        with self.config_path.open(mode='w+') as file:
            file.write(self.TEMPLATE)

    def exists(self):
        return self.config_path.exists() and self.config_path.is_file()


class IdsJsonSetupController:

    TEMPLATE = (
        '{\n'
        '   "used" = [],\n'
        '   "unused" = [],\n'
        '   "pointer" = 0\n'
        '}\n'
    )

    def __init__(self):
        self.path = PATH

        self.ids_path = pathlib.Path(PATH)
        self.ids_path.joinpath('ids.json')

    def run(self):
        if not self.exists():
            self.create()
            print('created the ids file')
        else:
            print('ids file already existed')

    def create(self):
        with self.ids_path.open(mode='w+') as file:
            file.write(self.TEMPLATE)

    def exists(self):
        return self.ids_path.exists() and self.ids_path.is_file()


class ObservedAuthorsSetupController:

    TEMPLATE = (
        '# Each section in jagged brackets is supposed to be a short, but UNIQUE identification of the author, \n'
        '# that is to be described by the section\n'
        '[NAME]\n'
        '# A list of scopus ids associated with the author\n'
        'ids = [12, 23, 45]\n'
        'first_name: John\n'
        'last_name: Doe\n'
        '# Keywords dictate with which WORDPRESS CATEGORIES the post will be tagged, when the author is a co author\n'
        '# of the publication\n'
        'keywords = ["A"]\n'
        '# The option to blacklist or whitelist SCOPUS AFFILIATION IDS on which to decide if a publication associated\n'
        '# with a affiliation should appear on the website or not\n'
        'scopus_whitelist = [23]\n'
        'scopus_blacklist = [23]\n'
    )

    def __init__(self):
        self.authors_path = pathlib.Path(PATH)
        self.authors_path.joinpath('scopus/authors.ini')

    def run(self):
        if not self.exists():
            self.create()

    def exists(self):
        return self.authors_path.exists() and self.authors_path.is_file()

    def create(self):
        with self.authors_path.open(mode='w+') as file:
            file.write(self.TEMPLATE)


class SQLSetupController:

    REFERENCE_SQL = (
        'CREATE TABLE reference ('
        'id BIGINT PRIMARY KEY,'
        'wordpress_id BIGINT,'
        'scopus_id BIGINT );'
        'CREATE UNIQUE INDEX reference_id_uindex ON reference (id);'
        'ALTER TABLE reference ENGINE=INNODB;'
        'COMMIT;'
    )

    PUBLICATIONS_SQL = (
        'CREATE TABLE publications ('
        'scopus_id BIGINT PRIMARY KEY NOT NULL,'
        'eid VARCHAR(64),'
        'doi VARCHAR(64),'
        'creator TEXT,'
        'description LONGTEXT,'
        'journal TEXT,'
        'volume VARCHAR(64),'
        'date VARCHAR(64),'
        'authors LONGTEXT,'
        'keywords TEXT,'
        'citations TEXT);'
        'CREATE UNIQUE INDEX publications_scopus_id_uindex ON publications (scopus_id);'
        'CREATE UNIQUE INDEX publications_eid_uindex ON publications (eid);'
        'CREATE UNIQUE INDEX publications_doi_unidex ON publications (doi);'
        'ALTER TABLE publications ENGINE=INNODB;'
        'COMMIT;'
    )

    PUBLICATION_CACHE_SQL = (
        'CREATE TABLE publication_cache ('
        'scopus_id BIGINT PRIMARY KEY NOT NULL,'
        'eid VARCHAR(64),'
        'doi VARCHAR(64),'
        'creator TEXT,'
        'description LONGTEXT,'
        'journal TEXT,'
        'volume VARCHAR(64),'
        'date VARCHAR(64),'
        'authors LONGTEXT,'
        'keywords TEXT,'
        'citations TEXT);'
        'CREATE UNIQUE INDEX publications_scopus_id_uindex ON publications (scopus_id);'
        'CREATE UNIQUE INDEX publications_eid_uindex ON publications (eid);'
        'CREATE UNIQUE INDEX publications_doi_unidex ON publications (doi);'
        'ALTER TABLE publication_cache ENGINE=INNODB;'
        'COMMIT;'
    )

    AUTHOR_CACHE_SQL = (
        'CREATE TABLE author_cache ('
        'author_id BIGINT PRIMARY KEY NOT NULL,'
        'first_name TEXT,'
        'last_name TEXT,'
        'h_index INT,'
        'citation_count INT,'
        'document_count INT,'
        'publications TEXT);'
        'CREATE UNIQUE INDEX author_cache_author_id_uindex ON author_cache (author_id);'
        'ALTER TABLE author_cache ENGINE=INNODB;'
        'COMMIT;'
    )

    def __init__(self):
        self.access = MySQLDatabaseAccess()

    def run(self):
        if not self.database_exists('publication_cache'):
            self.access.execute(self.PUBLICATION_CACHE_SQL)

        if not self.database_exists('publications'):
            self.access.execute(self.PUBLICATIONS_SQL)

        if not self.database_exists('author_cache'):
            self.access.execute(self.AUTHOR_CACHE_SQL)

        if not self.database_exists('reference'):
            self.access.execute(self.REFERENCE_SQL)

    def database_exists(self, database_name):
        try:
            sql = (
                'SELECT * FROM {database};'
            ).format(database=database_name)
            self.access.execute(sql)
            return True
        except:
            return False


class SetupController:

    def __init__(self):
        self.sql_setup_controller = SQLSetupController()
        self.folder_setup_controller = FolderSetupController()
        self.ids_setup_controller = IdsJsonSetupController()
        self.config_setup_controller = ConfigSetupController()
        self.observed_author_setup_controller = ObservedAuthorsSetupController()

    def run(self):
        self.folder_setup_controller.run()
        self.config_setup_controller.run()
        self.ids_setup_controller.run()
        self.observed_author_setup_controller()
        self.sql_setup_controller()


if __name__ == '__main__':
    setup_controller = SetupController()
    setup_controller.run()