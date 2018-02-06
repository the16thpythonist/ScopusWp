from ScopusWp.config import PATH

from ScopusWp.scopus.data import ScopusAuthorObservation

import os
import json
import configparser

#############
#  CLASSES  #
#############


class AuthorObservationInterface:

    def get_observation(self, author):
        raise NotImplementedError()

    def contains_author(self, author):
        raise NotImplementedError()

    def values(self):
        raise NotImplementedError()

    def keys(self):
        raise NotImplementedError()

    def __getitem__(self, item):
        raise NotImplementedError()

    def __contains__(self, item):
        raise NotImplementedError()

###############
# Controllers #
###############


class ScopusObservationController:

    def __init__(self):

        self.author_observation_model = AuthorObservationModel()

    def get_author_keywords(self, author):
        author_observation = self.author_observation_model[int(author)]  # type: ScopusAuthorObservation
        return author_observation.keywords

    def all_observations(self):
        return self.author_observation_model.values()

    def all_observed_ids(self):
        return self.author_observation_model.keys()

    def get_publication_keywords(self, publication):
        keywords = []
        author_observation_id_set = set(map(lambda x: int(x), self.author_observation_model.keys()))
        publication_author_id_set = set(map(lambda x: int(x), publication.authors))

        publication_observed_authors = list(publication_author_id_set.intersection(author_observation_id_set))
        # Going through all the authors of the publication and adding all the keywords of each observed author found
        for author in publication_observed_authors:
            author_keywords = self.get_author_keywords(author)
            difference = list(set(author_keywords) - set(keywords))
            keywords += difference
        return keywords

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
                if author_id in self.author_observation_model.keys():
                    author_observation = self.author_observation_model[author_id] # type: ScopusAuthorObservation
                    _is_whitelist = author_observation.whitelist_contains_any(author.affiliations)
                    # If there was a blacklist found it would be overwritten with the next author, like this a TRUE
                    # will be preserved until the end of the loop
                    if not _is_blacklist:
                        _is_blacklist = author_observation.blacklist_contains_any(author.affiliations)

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



############
#  Models  #
############


class AuthorObservationModel:

    def __init__(self):
        self.path_string = '{}/scopus/authors.ini'.format(PATH)
        self.config = configparser.ConfigParser()
        self.config.read(self.path_string)

        self.dict, self.author_observations = self.load()

    def __contains__(self, item):
        self.contains_author(item)

    def __getitem__(self, item):
        return self.get_observation(item)

    def get_observation(self, author):
        return self.dict[int(author)]

    def contains_author(self, author):

        return int(author) in self.keys()

    def keys(self):
        return list(self.dict.keys())

    def values(self):
        return self.author_observations

    def load(self):
        content_dict = {}
        author_observation_list = []
        for section in self.config.keys():
            if section == 'DEFAULT':
                continue

            sub_dict = dict(self.config[section])

            # Getting the author observation
            author_observation = self._get_author_observation(sub_dict)
            author_observation_list.append(author_observation)
            # Adding a reference to the same author observation to all the author ids in the list
            for author_id in author_observation.ids:
                content_dict[int(author_id)] = author_observation

        return content_dict, author_observation_list

    @staticmethod
    def _get_author_observation(sub_dict):

        scopus_ids_json_string = sub_dict['ids']
        scopus_ids = json.loads(scopus_ids_json_string)

        keywords_json_string = sub_dict['keywords']
        keywords = json.loads(keywords_json_string)

        whitelist_json_string = sub_dict['scopus_whitelist']
        whitelist = json.loads(whitelist_json_string)

        blacklist_json_string = sub_dict['scopus_blacklist']
        blacklist = json.loads(blacklist_json_string)

        author_observation = ScopusAuthorObservation(
            scopus_ids,
            sub_dict['first_name'],
            sub_dict['last_name'],
            keywords,
            whitelist,
            blacklist
        )

        return author_observation


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