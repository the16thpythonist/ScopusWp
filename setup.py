from setuptools import setup
from setuptools import find_packages

from setuptools.command.install import install
from setuptools.command.egg_info import egg_info
from setuptools.command.develop import develop

import configparser
import os


setup(
    name='scopus.wp',
    version='0.0.0.dev38',
    description='A tool for a wordpress server which will automatically post science publications from scopus database',
    url='https://github.com/the16thpythonist/ScopusWp',
    author='Jonas Teufel',
    author_email='jonseb1998@gmail.com',
    license='MIT',
    packages=['ScopusWp', 'ScopusWp/scopus'],
    include_package_data=False,
    install_requires=[
        'requests>=2.0',
        'mysqlclient>=1.2',
        'unidecode>=0.4',
        'tabulate>=0.8',
        'python-wordpress-xmlrpc>=2.3'
    ],
    python_requires='>=3, <4',
    package_data={
        '': [] #['*.sql', '*.json', '*.pkl', '*.ini']
    },
)
