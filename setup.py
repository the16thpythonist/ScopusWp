from setuptools import setup


setup(
    name='scopus.wp',
    version='0.2.0',
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
