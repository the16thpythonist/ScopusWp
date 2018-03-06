import os

print('BUILDING SOURCE AND BINARY DIST')

print('\nDELETING THE LIB CACHE')
os.system((
    'sudo rm -r /home/jonas/PycharmProjects/ScopusWp/build/lib/* && '
    'sudo python3 /home/jonas/PycharmProjects/ScopusWp/setup.py sdist bdist_wheel --universal'
))

print('\nUPLOADING TO PYTHON PACKAGE INDEX WITH TWINE')
os.system((
    'twine upload '
    '--username the16thplayer '
    '--password struppi98@snake@silver '
    '--skip-existing '
    '/home/jonas/PycharmProjects/ScopusWp/dist/*'
))

print('\nBUILDING THE PROJECT IN THE PROJECTS FOLDER')
os.system(
    'cd /home/jonas/Projekte/ScopusWp && '
    'sudo pipenv run pip3 install -I --pre --no-cache-dir scopus.wp'
)