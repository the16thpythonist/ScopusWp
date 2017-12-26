from ScopusWp.scopus.main import ScopusTopController

from ScopusWp.reference import ReferenceController

from ScopusWp.wordpress import WordpressPublicationPostController


# Todo: make the scopus controller get publication look into the cache first and the requesting a new one separate method

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

    def update_publications_website(self):
        # THE SCOPUS PART
        # Getting the new and relevant publications
        new_scopus_publication_list = self.new_scopus_publications()
        # Posting those new publications to the website
        for scopus_publication in new_scopus_publication_list:
            self.post_scopus_publication(scopus_publication)

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
        cache_id_list = self.scopus_controller.cache_controller.select_all_ids()

        # Getting the difference of the scopus ids in the cache and the scopus ids from the reference as exactly those
        # scopus ids, which are the new publications to be updated to the website
        new_id_list = list(set(cache_id_list) - set(reference_scopus_id_list))
        # Getting those publications from the cache
        new_publications_list = self.scopus_controller.select_multiple_publications_cache(new_id_list)

        # Filtering the new publications by the observed author criteria
        (
            filtered_publication_list,
            blacklist,
            remaining
         ) = self.scopus_controller.filter_by_observation(new_publications_list)

        return filtered_publication_list

    def post_scopus_publication(self, scopus_publication):
        # Creating a new generalized publication object from the scopus publication using the reference controller to
        # create a new internal id for the object
        publication = self.reference_controller.publication_from_scopus(scopus_publication)

        # Posting this publication to the wordpress site
        wordpress_id = self.wordpress_controller.post_publication(publication, [])
        # Saving the posting in the reference database
        self.reference_controller.insert_reference(publication.id, wordpress_id, scopus_publication.id)
        # Saving the publication to the backup system
        self.scopus_controller.insert_publication_backup(scopus_publication)

        # Getting all the citations from the scopus site
        citation_scopus_publication_list = self.scopus_controller.get_multiple_publications(scopus_publication.citations)
        citation_publication_list = []
        for citation_scopus_publication in citation_scopus_publication_list:
            # Saving the citation publication to the backup system
            self.scopus_controller.insert_publication_backup(citation_scopus_publication)
            publication = self.reference_controller.publication_from_scopus(citation_scopus_publication)
            citation_publication_list.append(publication)
        # Posting the comments
        self.wordpress_controller.post_citations(wordpress_id, citation_publication_list)

        # Saving the backup database and the reference database
        self.scopus_controller.backup_controller.save()
        self.reference_controller.save()

    def insert_scopus_cache_observed(self):
        self.scopus_controller.insert_cache_observed()

    def select_all_scopus_cache(self):
        return self.scopus_controller.select_all_publications_cache()