import importlib
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
    done = False
    start_point = 0
    while not done:
        done, start_point = main(start_point)