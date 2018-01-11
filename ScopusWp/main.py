import optparse


def main():

    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()

    if len(args) != 1:
        raise ValueError('Incorrect amount of arguments passed to ScopusWp')

    if args[0] not in ['publications', 'citations', 'reload']:
        raise ValueError('Incorrect argument passed to Scopus Wp')

    if args[0] == 'publications':
        pass

    elif args[0] == 'citations':
        pass

    elif args[0] == 'reload':
        pass