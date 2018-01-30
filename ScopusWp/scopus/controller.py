from ScopusWp.scopus.data import ScopusPublication, ScopusAuthor

from ScopusWp.scopus.observe import ScopusObservationController

from ScopusWp.scopus.persistency import ScopusBackupController, ScopusCacheController
from ScopusWp.scopus.persistency import ScopusPublicationPickleCacheModel, ScopusAuthorPickleCacheModel
from ScopusWp.scopus.persistency import ScopusPublicationDatabaseCacheModel, ScopusAuthorDatabaseCacheModel
from ScopusWp.scopus.persistency import TempPersistentSequenceModel

from ScopusWp.scopus.scopus import ScopusController

from ScopusWp.config import PATH

import logging

# TODO: Implement massive logging


# TODO: Make a controller for temp Persistency
# Todo: Make the new methods use the get methods that also cache

# todo: Make new cache based on database cuz faster
# todo: Logging mal richtig angehen


class ScopusTopController:

    def __init__(self):
        self.observation_controller = ScopusObservationController()
        self.scopus_controller = ScopusController()
        self.backup_controller = ScopusBackupController()
        self.cache_controller = ScopusCacheController(
            ScopusPublicationDatabaseCacheModel,
            ScopusAuthorDatabaseCacheModel
        )

        self.logger = logging.getLogger('ScopusTop')

    #####################
    # TOP LEVEL METHODS #
    #####################

    def explore_author_affiliations(self, author_dict):
        """
        Gets the list of all affiliation ids occurring in the history of all the publications to a author id of an
        author.

        Takes a dict, that assigns a list of possible author ids to a string tuple with last name and first name of
        an author
        Returns a dict with the string name tuple as keys and the values being dicts, that assigns list of affiliation
        ids to the author ids given in the input dict
        Example:
        IN: {('john', 'doe'): [1987623, 1294401]}
        OUT: {('john', 'doe'): {1987623: [8383992, 12387293],
                                1294401: [2312123]}
        :param author_dict: {('first name', 'last name') -> [author ids]}}
        :return: {('first name', 'last name') -> {author id -> [affiliation ids]}}
        """
        author_affiliation_dict = {}

        self.logger.info('loading temp storage for author aff.')

        # The naming function for the storage files
        def name_function(obj): return ''.join(list(obj.keys())[0])
        # Creating the temp storage list to save data persistently in case of crash
        temp_list = TempPersistentSequenceModel('au_aff', PATH + '/temp', name_function)
        temp_list.load()

        # Loading the values, that were already saved in the temp list
        for temp_dict in temp_list:
            author_affiliation_dict.update(temp_dict)

        self.logger.info('requesting publications for affiliations')
        for name_tuple, author_id_list in author_dict.items():
            # Only really processing and requesting for a user, if that user is not already in the dict
            if name_tuple not in author_affiliation_dict.keys():
                # Getting the affiliation id list for each of the author ids and saving the list as the value to the key
                # being the author id
                affiliation_dict = {}
                for author_id in author_id_list:
                    affiliation_id_list = self.get_affiliations_author(author_id)
                    affiliation_dict[author_id] = affiliation_id_list
                # Adding the affiliation dict as the value to the name tuple key to the main dict
                temp_dict = {name_tuple: affiliation_dict}
                author_affiliation_dict.update(temp_dict)
                # Saving the temp dict, which represents the main entry for a single author
                temp_list.append(temp_dict)

        self.logger.info('finished exploring affiliations')
        return author_affiliation_dict

    def get_affiliations_author(self, author_id):
        """
        Requests the author profile for the author from the scopus system and then all the publications of that author.
        Goes through all publications and returns a list of all the different affiliation ids, which the author had
        in the history of all his publications.

        Uses caching on default.
        :param author_id: The id of the author for which to get the affiliations
        :return:
        """
        # Getting the author profile for the author id
        author_profile = self.get_author_profile(author_id)
        # Getting all the publications for the author
        publication_list = self.get_multiple_publications(author_profile.publications)

        affiliation_list = []
        for publication in publication_list:  # type: ScopusPublication
            # Getting the author entry from the publication object, that belongs to the author specified by the passed
            # author id
            if len(publication.authors) > 0:
                author = publication.authors[0]
                for author in publication.authors:  # type: ScopusAuthor
                    if int(author_profile) == int(author):
                        break

                difference = list(set(author.affiliations) - set(affiliation_list))
                affiliation_list += difference

        return affiliation_list

    def get_author_observations(self):
        """
        This method will return all the ScopusAuthorObservation objects. Those objects contain the data specified in
        the config file for which authors to be represented in the system and the website.

        :return: [ScopusAuthorObservation]
        """
        return self.observation_controller.all_observations()

    def get_author_profile(self, author_id, caching=True):
        """
        Returns the author profile for the given author id.
        Uses caching if flag is set. so tries to get from cache first and if not in cache gets from the scopus website
        and then writes back into the cache.

        :param author_id: The int author id for the author
        :param caching: boolean flag if use caching or not
        :return: ScopusAuthorProfile
        """
        # Checking if the author profile is already in the cache
        is_cached = self.cache_controller.contains_author_profile(author_id)
        if is_cached and caching:
            author_profile = self.cache_controller.select_author_profile(author_id)
        else:
            # Actually requesting from scopus website and then writing back into the cache
            author_profile = self.scopus_controller.get_author_profile(author_id)
            self.cache_controller.insert_author_profile(author_profile)
            self.cache_controller.save()
        return author_profile

    def get_publication(self, scopus_id, caching=True):
        """
        Returns the publication object for the given scopus id.
        Uses caching if flag is set. So tries to get the publication from the cache first, if not in the cache, gets
        the publication from the scopus website and then writes back into the cache.

        :param scopus_id: The in scopus id identifying the publication
        :param caching: boolean flag if caching enbled or not
        :return: ScopusPublication
        """
        # Checking if the publication is in the cache and returning the cached value if possible
        is_cached = self.cache_controller.contains_publication(scopus_id)
        if is_cached and caching:
            publication = self.cache_controller.select_publication(scopus_id)
        else:
            # If the publication is not cached, getting it from the scopus website
            publication = self.scopus_controller.get_publication(scopus_id)

            # And then writing it into the cache for the next time
            self.cache_controller.insert_publication(publication)
            self.cache_controller.save()
        return publication

    def get_multiple_publications(self, scopus_id_list, caching=True):
        """
        Gets multiple publications based on the multiple scopus ids given in the list.

        :param scopus_id_list: The list of scopus ids for which to get the publications
        :param caching: The boolean flag of whether to use caching or not
        :return: [ScopusPublication]
        """
        publication_list = []
        for scopus_id in scopus_id_list:
            publication = self.get_publication(scopus_id, caching=caching)
            publication_list.append(publication)
        return publication_list

    def get_publications_observed(self, caching=True):
        """
        Gets ALL the publications from the observed authors.

        :param caching: The boolean flag of whether to use caching or not
        :return: [ScopusPublication]
        """
        # Getting the author ids of all the observed authors for the scopus database
        author_id_list = self.observation_controller.all_observed_ids()
        # Getting the author profiles for all the authors
        author_profile_list = []
        for author_id in author_id_list:
            author_profile = self.get_author_profile(author_id, caching=caching)
            author_profile_list.append(author_profile)
        # Getting the publications for all the author profiles
        scopus_id_list = []
        for author_profile in author_profile_list:
            _scopus_id_list = author_profile.publications
            _difference = list(set(_scopus_id_list) - set(scopus_id_list))
            scopus_id_list += _difference
        if '' in scopus_id_list:
            scopus_id_list.remove('')

        publication_list = self.get_multiple_publications(scopus_id_list)

        return publication_list

    def get_publication_ids_observed(self, caching=True):
        """
        Gets the publication ids of all the publications of all the observed authors

        Gets all the author ids of the observed authors, gets all the author profiles for those ids and then gets from
        the profiles the lists of publications and adds those to the overall list, that have not already been added by
        a co author. returns the over all list.
        :param caching: The boolean flag of whether or not to use caching for the author profiles
        :return: [int] the scopus ids
        """
        # Getting the list of observed authors from the observation controller
        observed_author_id_list = self.observation_controller.all_observed_ids()

        publication_id_list = []
        for author_id in observed_author_id_list:
            # Attempting to get the author profiles for the publication id lists from the cache and if the cache
            # does not contain them, requesting them from scopus
            author_profile = self.get_author_profile(author_id, caching=caching)
            publication_difference_list = list(set(author_profile.publications) - set(publication_id_list))
            publication_id_list += publication_difference_list
            self.logger.info(
                'Fetched the author profile and author publication data for author {}-{}-{}'.format(
                    author_profile.id,
                    author_profile.first_name,
                    author_profile.last_name
                )
            )

        return publication_id_list

    def request_publication_ids_observed(self):
        # Getting the author ids of all the observed authors for the scopus database
        author_id_list = self.observation_controller.all_observed_ids()
        # Getting the author profiles for all the authors
        author_profile_list = self.scopus_controller.get_multiple_author_profiles(author_id_list)
        # Assembling the list of publications for each author profile
        scopus_id_list = []
        for author_profile in author_profile_list:
            difference = list(set(author_profile.publications) - set(scopus_id_list))
            scopus_id_list += difference
        return scopus_id_list

    def reload_cache_observed(self):

        # Loading the cache anew
        self.load_cache_observed()

    def load_cache_observed(self, load_citations=True):
        """
        First loads the observed authors profiles into the cache (requests only those not already in the cache).
        Based on those author profiles loads the publications of all the observed authors into the cache and if the
        load_citations flag is set (default), all the publications, that have cited those publications will also be
        loaded into the cache.

        :param load_citations: boolean flag of whether or not to load the citation publications into the cache as well
        :return: void
        """
        # Loading the author profiles into the cache
        self._load_cache_observed_authors()

        # Loading the publications of the observed authors into the cache
        self._load_cache_observed_publications(load_citations=load_citations)

    def load_publications_cache(self, scopus_id_list, auto_save_interval=10, reload=False):
        """
        Loads the publication info about the publications described by the scopus ids in the list from the scopus
        website and saves them in the cache.

        Although only specifically requests those publications from the web, that are not already in the cache, for
        network performance reasons. All the publications can be requested by setting reload to true.
        Also the cache auto saves after the specified amount for the auto save interval in case of connection error.

        :param scopus_id_list: The list of scopus ids, for all the publications to be loaded into the cache
        :param auto_save_interval: The amount of publications to be fetched from the scopus website, before the
            cache saves the progress. default on 20
        :param reload: The boolean value of whether or not to get all the specified publications from the scopus
            website or leave out those, already in the cache
        :return: void
        """
        # Getting the list of publication ids for those publications, that are still in the cache
        cache_scopus_id_list = self.cache_controller.select_all_publication_ids()

        # If the reload flag is True, using the whole scopus id list as the list to be requested from the scopus site
        # else, only using those ids, that are not in the cache already
        if reload:
            difference_scopus_id_list = scopus_id_list
        else:
            difference_scopus_id_list = list(set(scopus_id_list) - set(cache_scopus_id_list))

        auto_save_count = 0
        for scopus_id in difference_scopus_id_list:
            # Auto saving if the count has reached the specified interval and then resetting the counter
            if auto_save_count == auto_save_interval:
                self.cache_controller.save()
                auto_save_count = 0

            # Getting the publication from the scopus website
            publication = self.scopus_controller.get_publication(scopus_id)
            self.cache_controller.insert_publication(publication)

            auto_save_count += 1

        self.cache_controller.save()

    def load_authors_cache(self, author_id_list, auto_save_interval=10, reload=False):
        """
        Loads the author profiles for the authors given by the author id list into the cache, by requesting them
        from the scopus website.

        On default, only those author profiles, that cannot already be found in the cache will be explicitly
        requested from the scopus website. When reload is True, all the author profiles will be requested and the
        possibly existing cache will be overwritten.
        Also the cache auto saves after the specified amount for the auto save interval, in case of connection
        error or exception.

        :param author_id_list: The list of author ids for the author profiles to be loaded into the cache
        :param auto_save_interval: The int amount of author profiles to be requested before the cache saves the
            progress into persistency.
        :param reload: The boolean value of whether or not the
        :return: void
        """
        cache_author_id_list = self.cache_controller.select_all_author_ids()

        # Subtracting the the observed from the cached ids and adding only the left over to the cache
        if reload:
            difference_author_id_list = author_id_list
        else:
            difference_author_id_list = list(set(author_id_list) - set(cache_author_id_list))

        auto_save_counter = 0
        for author_id in difference_author_id_list:
            # Saving during the process, so progress is not lost after connection error
            if auto_save_counter == auto_save_interval:
                self.cache_controller.save()
                auto_save_counter = 0

            # Requesting the author profile from the scopus website
            author_profile = self.scopus_controller.get_author_profile(author_id)
            self.cache_controller.insert_author_profile(author_profile)
            auto_save_counter += 1
        self.cache_controller.save()

    def _load_cache_observed_authors(self):
        """
        Loads the author profiles for all the observed authors into the cache, but only specifically requests those,
        which are not already in the cache.

        :return: void
        """
        # Getting the list of author ids for the observed authors from the observation controller
        observed_author_id_list = self.observation_controller.all_observed_ids()

        # Loading all those author profiles of the observed authors into the cache
        self.load_authors_cache(observed_author_id_list)

    def _load_cache_observed_publications(self, load_citations=True):
        """
        Loads all the publications of the observed authors into the cache, but only those, that are not already in the
        cache. Also loads all the publication, that have cited the observed publications into the cache if enabled.

        :param load_citations: boolean flag of whether or not to also load the citation publications into the cache
        :return: void
        """
        # Getting the list of publication ids for all the observed authors from the cache
        observed_publication_id_list = self.get_publication_ids_observed()

        # Loading all those publications into the cache after having them requested from the scopus website
        self.load_publications_cache(observed_publication_id_list)

        if load_citations:
            # Getting the citations scopus id list from every one of those publications
            citation_scopus_id_list = []
            for scopus_id in observed_publication_id_list:
                publication = self.cache_controller.select_publication(scopus_id)

                # Protecting against the unlikely case of corrupted data with double checking for None
                if publication is not None:
                    difference = list(set(publication.citations) - set(citation_scopus_id_list))
                    citation_scopus_id_list += difference

            # Loading all those publications into the cache as well
            self.load_publications_cache(citation_scopus_id_list)

    def get_citation_publications(self, publication):
        publication_list = self.scopus_controller.get_citation_publications(publication)
        # Caching all the citation publications
        for publication in publication_list:
            self.cache_controller.insert_publication(publication)
        return publication_list

    ######################
    # THE SCOPUS METHODS #
    ######################

    def request_publication(self, scopus_id):
        return self.scopus_controller.get_publication(scopus_id)

    def request_multiple_publications(self, scopus_id_list):
        return self.scopus_controller.get_multiple_publications(scopus_id_list)

    ###########################
    # THE OBSERVATION METHODS #
    ###########################

    def filter_by_observation(self, publication_list):
        return self.observation_controller.filter(publication_list)

    def publication_observation_keywords(self, publication):
        return self.observation_controller.get_publication_keywords(publication)

    ######################
    # THE BACKUP METHODS #
    ######################

    def select_publication_backup(self, scopus_id):
        return self.backup_controller.select_publication(scopus_id)

    def select_multiple_publications_backup(self, scopus_id_list):
        return self.backup_controller.select_multiple_publications(scopus_id_list)

    def select_all_publications_backup(self):
        return self.backup_controller.select_all_publications()

    def insert_publication_backup(self, publication):
        self.backup_controller.insert_publication(publication)

    def insert_multiple_publication_backup(self, publication_list):
        self.backup_controller.insert_multiple_publications(publication_list)

    #####################
    # THE CACHE METHODS #
    #####################

    def select_publication_cache(self, scopus_id):
        return self.cache_controller.select_publication(scopus_id)

    def select_multiple_publications_cache(self, scopus_id_list):
        return self.cache_controller.select_multiple_publications(scopus_id_list)

    def select_all_publications_cache(self):
        return self.cache_controller.select_all_publications()

    def insert_publication_cache(self, publication):
        self.cache_controller.insert_publication(publication)

    def insert_multiple_publications_cache(self, publication_list):
        self.cache_controller.insert_multiple_publications(publication_list)
