from ScopusWp.controller import TopController

import optparse

# TODO: Make a fail proof for the citation comment wordpress not well formed
# TODO: Make the new citations functionality with update date
# TODO: Make update date into the main reference
# TODO: Make error safe for http request pool exceptions wrapper method for requests


def main():

    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()

    if len(args) != 1:
        raise ValueError('Incorrect amount of arguments passed to ScopusWp')

    if args[0] not in ['publications', 'citations', 'wipe']:
        raise ValueError('Incorrect argument passed to Scopus Wp')

    if args[0] == 'publications':
        controller = TopController()
        try:
            controller.update_publications_website()
        finally:
            controller.close()

    elif args[0] == 'citations':
        controller = TopController()
        try:
            controller.update_publications_website()
        finally:
            controller.close()

    elif args[0] == 'wipe':
        controller = TopController()
        controller.wipe_website()
        controller.close()


if __name__ == '__main__':
    #main()
    controller = TopController()
    try:
        controller.update_publications_website()
    finally:
        controller.close()
