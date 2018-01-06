import importlib
import threading
import configparser
import pathlib
import pickle
import os


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


if __name__ == '__main__':
    from ScopusWp.database import MySQLDatabaseAccess
    from ScopusWp.config import PATH

    access = MySQLDatabaseAccess()
    with open('{}/setup.sql'.format(PATH), mode='r') as file:
        sql = file.read()
        access.execute(sql)