import importlib
import threading
import configparser
import pathlib
import pickle
import os

from ScopusWp.database import MySQLDatabaseAccess
from ScopusWp.config import PATH


class FolderSetupController:

    def __init__(self):
        self.path = PATH

        self.logs_path = pathlib.Path(PATH + '/logs')

        self.temp_path = pathlib.Path(PATH + '/temp')

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
        'post_reference_table = reference\n'
        'comment_reference_table = comment_reference\n'
    )

    def __init__(self):
        self.path = PATH

        self.config_path = pathlib.Path(PATH + '/config.ini')

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

        self.ids_path = pathlib.Path(PATH + '/ids.json')

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
        self.authors_path = pathlib.Path(PATH + '/scopus/authors.ini')

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

    COMMENT_REFERENCE_SQL = (
        'CREATE TABLE comment_reference'
        '('
        'internal_id BIGINT PRIMARY KEY,'
        'wordpress_post_id BIGINT,'
        'wordpress_comment_id BIGINT,'
        'scopus_id BIGINT'
        ');'
        'CREATE UNIQUE INDEX comment_reference_inernal_id_uindex ON comment_reference (internal_id);'
        'ALTER TABLE comment_reference ENGINE=INNODB;'
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

        if not self.database_exists('comment_reference'):
            self.access.execute(self.COMMENT_REFERENCE_SQL)

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
        self.folder_setup_controller = FolderSetupController()
        self.ids_setup_controller = IdsJsonSetupController()
        self.config_setup_controller = ConfigSetupController()
        self.observed_author_setup_controller = ObservedAuthorsSetupController()

    def run(self):
        self.folder_setup_controller.run()
        self.config_setup_controller.run()
        self.ids_setup_controller.run()
        self.observed_author_setup_controller.run()


if __name__ == '__main__':
    setup_controller = SetupController()
    setup_controller.run()
