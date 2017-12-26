from ScopusWp.scopus.data import ScopusPublication

from ScopusWp.scopus.observe import ScopusObservationController

from ScopusWp.scopus.persistency import ScopusBackupController, ScopusCacheController, ScopusPickleCacheModel

from ScopusWp.scopus.scopus import ScopusController

# TODO: Implement massive logging


class ScopusTopController:

    def __init__(self):
        self.observation_controller = ScopusObservationController()
        self.scopus_controller = ScopusController()
        self.backup_controller = ScopusBackupController()
        self.cache_controller = ScopusCacheController(ScopusPickleCacheModel)

    #####################
    # TOP LEVEL METHODS #
    #####################

    def get_publication(self, scopus_id):
        # Checking if the publication is in the cache and returning the cached value if possible
        is_cached = self.cache_controller.contains_publication(scopus_id)
        if is_cached:
            publication = self.cache_controller.select_publication(scopus_id)
        else:
            # If the publication is not cached, getting it from the scopus website
            publication = self.scopus_controller.get_publication(scopus_id)
        return publication

    def get_multiple_publications(self, scopus_id_list):
        publication_list = []
        for scopus_id in scopus_id_list:
            publication = self.get_publication(scopus_id)
            publication_list.append(publication)
        return publication_list

    def get_publications_observed(self):
        # Getting the author ids of all the observed authors for the scopus database
        author_id_list = self.observation_controller.all_observed_ids()
        # Getting the author profiles for all the authors
        author_profile_list = self.scopus_controller.get_multiple_author_profiles(author_id_list)
        # Getting the publications for all the author profiles
        publication_list = []
        for author_profile in author_profile_list:
            _publications = self.scopus_controller.get_author_publications(author_profile)
            publication_list += _publications
        return publication_list

    def insert_cache_observed(self):
        # Getting the publications of the observed authors
        publication_list = self.get_publications_observed()
        # Loading the cache with those publications
        self.cache_controller.insert_multiple_publications(publication_list)
        # Saving the cache data
        self.cache_controller.save()

        # Getting all the citations
        for publication in publication_list:
            # Getting all the publications, that have cited the observed publications also into the cache
            citation_publication_list = self.request_multiple_publications(publication.citations)
            self.cache_controller.insert_multiple_publications(citation_publication_list)

            self.cache_controller.save()

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

