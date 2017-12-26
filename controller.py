from ScopusWp.scopus.main import ScopusTopController

from ScopusWp.reference import ReferenceController

from ScopusWp.wordpress import WordpressPublicationPostController


class TopController:

    def __init__(self):
        self.scopus_controller = ScopusTopController()
        self.reference_controller = ReferenceController()
        self.wordpress_controller = WordpressPublicationPostController()

    def update_website(self):
        # Getting all the publications that are saved in the backup system
        # Getting the user profiles of all the observed users
        # Getting the list of all the scopus ids of those users
        pass

    def new_scopus_publications(self):
        # loading the list of all the scopus publications, that are already on the website, by checking the reference
        # database
        reference_list = self.reference_controller.select_all_references()
        # Getting all the scopus ids into one list
        reference_scopus_id_list = []
        for reference in reference_list:
            scopus_id = int(reference[2])
            if scopus_id != 0:
                reference_scopus_id_list.append(scopus_id)

        # Getting a list with all the scopus ids of the publications currently saved in the cache
        self.scopus_controller.cache_controller.cache_model


    def load_scopus_cache(self, scopus_id_list):
        self.scopus_controller.load_cache(scopus_id_list)

    def insert_scopus_cache_observed(self):
        self.scopus_controller.insert_cache_observed()

    def select_all_scopus_cache(self):
        return self.scopus_controller.select_all_publications_cache()