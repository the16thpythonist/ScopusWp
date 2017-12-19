from ScopusWp.scopus.main import ScopusTopController

from ScopusWp.reference import ReferenceController

from ScopusWp.wordpress import WordpressPublicationPostController


class TopController:

    def __init__(self):
        self.scopus_controller = ScopusTopController()
        self.reference_controller = ReferenceController()
        self.wordpress_controller = WordpressPublicationPostController()

    def load_scopus_cache(self, scopus_id_list):
        self.scopus_controller.load_cache(scopus_id_list)

