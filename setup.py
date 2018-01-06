from setuptools import setup
from setuptools import find_packages

import configparser
import os

# TODO: Make the installation shit


class ConfigInstallationController:

    DEFAULT_VALUE_DICT = {
        ('SCOPUS', 'api_key'): '',
        ('SCOPUS', 'url'): '',
        ('WORDPRESS', 'username'): '',
        ('WORDPRESS', 'password'): '',
        ('WORDPRESS', 'url'): '',
        ('MYSQL', 'username'): '',
        ('MYSQL', 'password'): '',
        ('MYSQL', 'host'): '',
        ('MYSQL', 'database'): ''
    }

    def __init__(self, package_path):
        self.package_path = package_path
        self.path = '{}/config.ini'.format(self.package_path)

        # If the file exists, loading the file as it is. If the file does not exist, creating a new file and then
        # populating it with the necessary sections
        if not self.file_exists():
            self.create_file()
        self.config = self.load_config()

        # Checking if the file already is formatted in the way, that is required for the ScopusWp system
        # If it is not formatted creating the format with the key tuples of the default dict as the section;key
        # combination and the given values
        if not self.is_formatted():
            self.format_default()

    def is_formatted(self):
        for key_tuple in self.DEFAULT_VALUE_DICT.keys():
            if not self.contains_item(key_tuple[0], key_tuple[1]):
                return False
        return True

    def get_default_sections(self):
        sections = []
        for key_tuple in self.DEFAULT_VALUE_DICT.keys():
            section_name = key_tuple[0]
            if section_name not in sections:
                sections.append(section_name)
        return sections

    def create_default_sections(self):
        sections = self.get_default_sections()
        for section in sections:
            self.create_section(section)

    def create_default_items(self):
        for key_tuple, value in self.DEFAULT_VALUE_DICT.items():
            self.create_item(key_tuple[0], key_tuple[1], value)

    def format_default(self):
        self.create_default_sections()
        self.create_default_items()

    def create_section(self, section):
        self.config[section] = {}

    def create_item(self, section, key, value):
        self.config[section][key] = value

    def contains_item(self, section, key):
        try:
            value = self.config[section][key]
            return True
        except KeyError:
            return False

    def create_file(self):
        with open(self.path, mode='w+') as file:
            file.write(' ')

    def save_config(self):
        with open(self.path, mode='w+') as file:
            self.config.write(file)

    def load_config(self):
        config = configparser.ConfigParser()
        config.read(self.path)
        return config

    def file_exists(self):
        # Checking if the path to the config file exists
        exists = os.path.exists(self.path)
        # Checking if the target to the path is actually a file
        is_file = os.path.isfile(self.path)

        return exists and is_file


class IdJsonInstallationController:

    def __init__(self, package_path):
        self.package_path = package_path
        self.path = '{}/ids.json'.format(self.package_path)

    def create_file(self):
        with open(self.path, mode='w+') as file:
            file.write(' ')

    def file_exists(self):
        # Checking if the path to the config file exists
        exists = os.path.exists(self.path)
        # Checking if the target to the path is actually a file
        is_file = os.path.isfile(self.path)

        return exists and is_file


setup(
    name='scopus.wp',
    version='0.0.0.dev16',
    description='A tool for a wordpress server which will automatically post science publications from scopus database',
    url='https://github.com/the16thpythonist/ScopusWp',
    author='Jonas Teufel',
    author_email='jonseb1998@gmail.com',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests>=2.0',
        'mysqlclient>=1.2',
        'unidecode>=0.4',
        'tabulate>=0.8',
        'python-wordpress-xmlrpc>=2.3'
    ],
    python_requires='>=3, <4',
    package_data={
        '': ['*.sql', '*.json', '*.pkl', '*.ini']
    },
)
