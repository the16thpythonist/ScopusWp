from ScopusWp.scopus.data import ScopusPublication

from ScopusWp.scopus.observe import ScopusObservationController

from ScopusWp.scopus.persistency import ScopusBackupController, ScopusCacheController, ScopusPickleCacheModel

from ScopusWp.scopus.scopus import ScopusController


class ScopusTopController:

    def __init__(self):
        self.observation_controller = ScopusObservationController()
        self.scopus_controller = ScopusController()
        self.backup_controller = ScopusBackupController()
        self.cache_controller = ScopusCacheController(ScopusPickleCacheModel)

    #####################
    # TOP LEVEL METHODS #
    #####################

    ######################
    # THE SCOPUS METHODS #
    ######################

    def get_publication(self, scopus_id):
        return self.scopus_controller.get_publication(scopus_id)

    def get_multiple_publications(self, scopus_id_list):
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

    def select_multiple_publication_backup(self, scopus_id_list):
        return self.backup_controller.select_multiple_publications(scopus_id_list)

    def insert_publication_backup(self, publication):
        self.backup_controller.insert_publication(publication)

    def insert_multiple_publication_backup(self, publication_list):
        self.backup_controller.insert_multiple_publications(publication_list)

    #####################
    # THE CACHE METHODS #
    #####################

    def select_publication_cache(self, scopus_id):
        return self.cache_controller.select_publication(scopus_id)

    def select_multiple_publication_cache(self, scopus_id_list):
        return self.cache_controller.select_multiple_publications(scopus_id_list)

    def insert_publication_cache(self, publication):
        self.cache_controller.insert_publication(publication)

    def insert_multiple_publications_cache(self, publication_list):
        self.cache_controller.insert_multiple_publications(publication_list)

