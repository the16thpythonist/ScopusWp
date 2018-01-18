from ScopusWp.controller import TopController

import optparse

# TODO: Make a citations reference database
# TODO: Make the new citations functionality with update date
# TODO: Make update date into the main reference
# TODO: Finally clean up the installation process


def main():

    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()

    if len(args) != 1:
        raise ValueError('Incorrect amount of arguments passed to ScopusWp')

    if args[0] not in ['publications', 'citations', 'reload', 'wipe']:
        raise ValueError('Incorrect argument passed to Scopus Wp')

    if args[0] == 'publications':
        controller = TopController()
        controller.update_publications_website()

    elif args[0] == 'citations':
        print('works')

    elif args[0] == 'reload':
        controller = TopController()
        controller.reload_scopus_cache_observed()

    elif args[0] == 'wipe':
        controller = TopController()
        controller.wipe_website()


if __name__ == '__main__':
    #main()
    controller = TopController()
    controller.update_publications_website()