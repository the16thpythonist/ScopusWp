import importlib
import threading
import configparser
import pathlib
import pickle
import os
import MySQLdb

# THE TEMPLATES FOR THE NON CODE FILES

CONFIG_INI_TEMPLATE = (
    '[SCOPUS]\n'
    '; YOUR SCOPUS API KEY'
    'api-key = \n'
    'url = https://api.elsevier.com/content\n'
    '\n'
    '[KITOPEN]\n'
    'url = https://publikationen.bibliothek.kit.edu/publikationslisten\n'
    '\n'
    '[WORDPRESS]\n'
    '; THE URL TO YOUR WORDPRESS "xmlrpc.php"\n'
    'url = \n'
    '; YOUR WP USER\n'
    'username = \n'
    '; YOUR WP PASSWORD\n'
    'password = \n'
    '; AMOUNT OF DAYS BETWEEN UPDATE\n'
    'update_expiration = \n'
    '\n'
    '[MYSQL]\n'
    'host = localhost\n'
    'database = \n'
    'username = \n'
    'password = \n'
    '\n'
    '[LOGGING]\n'
    'folder = logs\n'
    'debug_log_name = log\n'
    'activity_log_name = log\n'
)

AUTHORS_INI_TEMPLATE = (
    '[SHORTHAND]\n'
    'ids = [] ; LIST OF SCOPUS IDS ASSOCIATED WITH AUTHOR\n'
    'first_name = ; FIRST NAME\n'
    'last_name = ; LAST NAME\n'
    'keywords = [] ; WORDPRESS CATEGORIES TO ASSOCIATE AUTHOR PUBLICATIONS WITH\n'
    'scopus_whitelist = [] ; SCOPUS AFFILIATION IDS TO ACCEPT\n'
    'scopus_blacklist = [] ; SCOPUS AFFILIATION IDS TO IGNORE\n'
    '\n'
    '; You can add more authors by appending sections like the template above\n'
)

ID_JSON_TEMPLATE = (
    '{\n'
    '"counter": 0,\n'
    '"used": [],\n'
    '"unused": []\n'
    '}\n'
)

# THE SQL SCRIPTS NEEDED FOR THE SETUP

REFERENCE_SQL = (
    'CREATE TABLE reference '
    '('
    'id BIGINT PRIMARY KEY,'
    'wordpress_id BIGINT,'
    'scopus_id BIGINT,'
    'comments_updated_datetime DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
    ') ENGINE INNODB;'
    'CREATE UNIQUE INDEX reference_id_uindex ON reference (id);'
    'COMMIT;'
)

COMMENT_REFERENCE_SQL = (
    'CREATE TABLE comment_reference'
    '('
    'internal_id BIGINT PRIMARY KEY,'
    'wordpress_post_id BIGINT,'
    'wordpress_comment_id BIGINT,'
    'scopus_id BIGINT'
    ') ENGINE INNODB;'
    'CREATE UNIQUE INDEX comment_reference_inernal_id_uindex ON comment_reference (internal_id);'
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
    'citations TEXT'
    ') ENGINE INNODB;'
    'CREATE UNIQUE INDEX publications_scopus_id_uindex ON publications (scopus_id);'
    'CREATE UNIQUE INDEX publications_eid_uindex ON publications (eid);'
    'CREATE UNIQUE INDEX publications_doi_unidex ON publications (doi);'
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
    'citations TEXT'
    ') ENGINE INNODB;'
    'CREATE UNIQUE INDEX publications_scopus_id_uindex ON publications (scopus_id);'
    'CREATE UNIQUE INDEX publications_eid_uindex ON publications (eid);'
    'CREATE UNIQUE INDEX publications_doi_unidex ON publications (doi);'
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
    'publications TEXT'
    ') ENGINE INNODB;'
    'CREATE UNIQUE INDEX author_cache_author_id_uindex ON author_cache (author_id);'
    'COMMIT;'
)


class ProjectPathInputController:

    def __init__(self):
        self._path = None

    @property
    def path(self):
        self.run()
        return self._path

    def run(self):
        if not self.check_config():
            self.prompt_path()

    def prompt_path(self):
        while True:
            inp = input('\nENTER PROJECT PATH: ')
            try:
                path = pathlib.Path(inp)
                if path.exists() and path.is_dir():
                    self._path = str(path)
                    break
                else:
                    print('INVALID PATH, TRY AGAIN')
                    continue
            except:
                print('INVALID INPUT, TRY AGAIN')
                continue

    def check_config(self):
        import ScopusWp.config as _config
        # In case the project path value is not empty, it is save to assume it has been set already and the path is
        # still valid
        if _config.PROJECT_PATH == '':
            print('NO PATH HAS BEEN SET')
            return False

        # Asking the user if he wants to keep that path or change it
        print('CURRENT PATH:\n{}'.format(_config.PROJECT_PATH))
        inp = input('\nDo you want to keep that path? Type "N" to change...')
        if inp.lower() == 'n' or inp.lower() == 'no':
            return False
        else:
            self._path = _config.PROJECT_PATH
            return True


class FolderSetupController:

    def __init__(self, project_path):
        self.path = project_path

        self.logs_path = pathlib.Path(self.path) / 'logs'
        self.temp_path = pathlib.Path(self.path) / 'temp'

    def run(self):
        if not self.logs_exists():
            self.create_logs_folder()
            print('CREATED LOGS FOLDER')
        else:
            print('LOGS FOLDER ALREADY EXISTS')

        if not self.temp_exists():
            self.create_temp_folder()
            print('CREATED TEMP FOLDER')
        else:
            print('TEMP FOLDER ALREADY EXISTS')

    def create_logs_folder(self):
        self.logs_path.mkdir()

    def create_temp_folder(self):
        self.temp_path.mkdir()

    def logs_exists(self):
        return self.logs_path.exists() and self.logs_path.is_dir()

    def temp_exists(self):
        return self.temp_path.exists() and self.temp_path.is_dir()


class ConfigSetupController:

    def __init__(self, project_path):
        self.project_path = project_path

        self.path = pathlib.Path(self.project_path) / 'config.ini'

    def run(self):
        if not self.exists():
            self.create()
            print('CREATED CONFIG.INI')
        else:
            print('CONFIG FILE ALREADY EXISTS. KEEPING THE EXISTING FILE')

    def create(self):
        with self.path.open(mode='w+') as file:
            file.write(CONFIG_INI_TEMPLATE)
            file.flush()

    def exists(self):
        return self.path.exists() and self.path.is_file()


class IdsJsonSetupController:

    def __init__(self, project_path):
        self.project_path = project_path

        self.path = pathlib.Path(self.project_path) / 'ids.json'

    def run(self):
        if not self.exists():
            self.create()
            print('CREATED IDS.JSON')
        else:
            print('IDS.JSON ALREADY EXISTS. KEEPING THE EXISTING FILE')

    def create(self):
        with self.path.open(mode='w+') as file:
            file.write(ID_JSON_TEMPLATE)
            file.flush()

    def exists(self):
        return self.path.exists() and self.path.is_file()


class ObservedAuthorsSetupController:

    def __init__(self, project_path):
        self.project_path = project_path

        self.path = pathlib.Path(self.project_path) / 'authors.ini'

    def run(self):
        if not self.exists():
            self.create()
            print('CREATED AUTHORS.INI')
        else:
            print('AUTHORS.INI EXISTS. KEEPING THE EXISTING FILE')

    def exists(self):
        return self.path.exists() and self.path.is_file()

    def create(self):
        with self.path.open(mode='w+') as file:
            file.write(AUTHORS_INI_TEMPLATE)


class Db:

    _instance = None

    @staticmethod
    def get_cursor():
        conn = Db.get_instance()  # type: MySQLdb.Connection
        cursor = conn.cursor()
        return cursor

    @staticmethod
    def get_instance():
        if Db._instance is None:
            Db.new_instance()

        return Db._instance

    @staticmethod
    def new_instance():

        # Attempting to import the config of the project
        from ScopusWp.config import Config

        try:
            config = Config.get_instance()
            # Getting the values from the config
            host = config['MYSQL']['host']
            database = config['MYSQL']['database']
            username = config['MYSQL']['username']
            password = config['MYSQL']['password']
            connector = MySQLdb.connect(
                host=host,
                db=database,
                user=username,
                passwd=password
            )
            Db._instance = connector
            print('DATABASE CONNECTOR SUCCESSFULLY CREATED')
            return True
        except Exception as e:
            print('DURING THE ATTEMPT TO CREATE A DATABASE CONNECTION THE EXCEPTION OCCURRED\n"{}"'.format(str(e)))
            return False

    @staticmethod
    def test():
        return Db.new_instance()


class SQLSetupController:

    def __init__(self):
        self.access = None

    @staticmethod
    def test():
        return Db.test()

    def run(self):
        self.access = Db.get_cursor()

        if not self.database_exists('publication_cache'):
            self.access.execute(PUBLICATION_CACHE_SQL)

        if not self.database_exists('publications'):
            self.access.execute(PUBLICATIONS_SQL)

        if not self.database_exists('author_cache'):
            self.access.execute(AUTHOR_CACHE_SQL)

        if not self.database_exists('reference'):
            self.access.execute(REFERENCE_SQL)

        if not self.database_exists('comment_reference'):
            self.access.execute(COMMENT_REFERENCE_SQL)

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
        # Getting the path to the project folder
        self.path_input_controller = ProjectPathInputController()
        self.project_path = self.path_input_controller.path

        self.folder_setup_controller = FolderSetupController(self.project_path)
        self.ids_setup_controller = IdsJsonSetupController(self.project_path)
        self.config_setup_controller = ConfigSetupController(self.project_path)
        self.observed_author_setup_controller = ObservedAuthorsSetupController(self.project_path)

        self.database_setup_controller = SQLSetupController()

    def setup_files(self):
        print('\n[FILE SETUP]')
        # Setting up all the folders
        self.folder_setup_controller.run()

        # Setting up the data files
        self.config_setup_controller.run()
        self.ids_setup_controller.run()
        self.observed_author_setup_controller.run()

    def setup_database(self):
        print('\n[DATABASE SETUP]')
        # Testing the database setup first, to make sure the login credentials are set correctly
        value = self.database_setup_controller.test()
        if value:
            print('DATABASE LOGIN SUCCESSFUL. PROCEEDING TO SETUP TABLES')
            self.database_setup_controller.run()
        else:
            print('COULD NOT CONNECT TO DATABASE. PLEASE INPUT CREDENTIALS TO "CONFIG.INI"')

    @staticmethod
    def info():
        import ScopusWp.config as _config
        import os

        print('\nCURRENT VERSION:\n{}'.format(_config.VERSION))
        print('\nRUNNING IN FOLDER:\n{}'.format(_config.PATH))
        print('\nPACKAGE CONTENT:\n{}'.format(os.listdir(_config.PATH)))
