import os
import configparser

class AuthorObservationInterface:

    def get_observation(self, author):
        raise NotImplementedError()

    def contains_author(self, author):
        raise NotImplementedError()

    def values(self):
        pass

    def keys(self):
        pass

    def __getitem__(self, item):
        pass

    def __contains__(self, item):
        pass


class AuthorObservationModel:

    def __init__(self):

class ObservedAuthorsModel2:

    def __init__(self):
        self.path = os.path.join(PATH, 'authors2.ini')

        self.source = configparser.ConfigParser()
        self.source.read(self.path)

        self.author_observations = []
        self.author_ids = []

        self.author_observation_dict = {}
        # TODO: eventually dict struture for categories and ids to observ. objects

        for key in self.source.keys():
            if key == 'DEFAULT':
                continue
            # Each key represents one observed author
            value_dict = dict(self.source[key])

            author_observation = self._get_author_observation(value_dict)
            author_id_list = author_observation.ids
            self.author_ids += author_id_list
            self.author_observations.append(author_observation)
            for author_id in author_id_list:
                self.author_observation_dict[author_id] = author_observation

    def filter(self, publication_list):
        whitelist_publications = []
        blacklist_publications = []
        remaining_publications = []

        for publication in publication_list:
            _is_blacklist = False
            _is_whitelist = False
            # Checking the affiliations for all the authors
            for author in publication.authors:
                author_id = int(author.id)
                if author_id in self.author_ids:
                    author_observation = self.author_observation_dict[author_id]
                    _is_whitelist = author_observation.check_whitelist(author.affiliations)
                    # If there was a blacklist found it would be overwritten with the next author, like this a TRUE
                    # will be preserved until the end of the loop
                    if not _is_blacklist:
                        _is_blacklist = author_observation.check_blacklist(author.affiliations)

                    # In the case of whitelist, the publication will be added instantly, but for blacklist it is
                    # decided after all authors have been iterated
                    if _is_whitelist:
                        whitelist_publications.append(publication)
                        break

            if _is_blacklist:
                blacklist_publications.append(publication)
            else:
                remaining_publications.append(publication)

        return whitelist_publications, blacklist_publications, remaining_publications

    def get_observed_authors(self):
        return self.author_ids

    def _get_author_observation(self, value_dict):
        (
            first_name,
            last_name,
            author_id_list,
            keyword_list,
            scopus_whitelist,
            scopus_blacklist
        ) = self._extract_value_dict(value_dict)

        # Creating a new AuthorObservation object
        author_observation = AuthorObservation(
            author_id_list,
            first_name,
            last_name,
            keyword_list,
            scopus_whitelist,
            scopus_blacklist
        )

        return author_observation

    def _extract_value_dict(self, value_dict):
        first_name = value_dict['first_name']
        last_name = value_dict['last_name']

        author_ids_json = value_dict['ids']
        author_id_list = json.loads(author_ids_json)

        scopus_whitelist_json = value_dict['scopus_whitelist']
        scopus_whitelist = json.loads(scopus_whitelist_json)

        scopus_blacklist_json = value_dict['scopus_blacklist']
        scopus_blacklist = json.loads(scopus_blacklist_json)

        keyword_list_json = value_dict['keywords']
        keyword_list = json.loads(keyword_list_json)

        return first_name, last_name, author_id_list, keyword_list, scopus_whitelist, scopus_blacklist

    def __contains__(self, item):
        """
        The magic method for the 'xx in xx' Operator. If given an Author / AuthorProfile object or a author id string
        or int, checks and returns whether that author described by the author id is in the set of observed author ids

        :param item: Author/AuthorProfile/string/int anything that describes an author
        :return: The boolean value of whether or not that author is with the observed authors
        """
        return int(item) in self.author_ids

    def __getitem__(self, item):
        """
        Returns the AuthorObservation object for the given author

        :param item: Author/AuthorProfile/string/int anything that describes an author
        :return: The AuthorObservation object for the given author
        """
        # Works with the author id given directly as string/int and with the Author/AuthorProfile objects
        author_id = int(item)
        return self.author_observation_dict[author_id]  # type: AuthorObservation