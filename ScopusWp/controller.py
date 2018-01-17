from ScopusWp.scopus.controller import ScopusTopController

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
        observed_id_list = self.scopus_controller.get_publication_ids_observed()

        # Getting the difference of the scopus ids in the cache and the scopus ids from the reference as exactly those
        # scopus ids, which are the new publications to be updated to the website
        new_id_list = list(set(observed_id_list) - set(reference_scopus_id_list))
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

        # Getting the keywords for each publication
        keywords = self.scopus_controller.publication_observation_keywords(publication)

        # Posting this publication to the wordpress site
        wordpress_id = self.wordpress_controller.post_publication(publication, keywords)
        # Saving the posting in the reference database
        self.reference_controller.insert_reference(publication.id, wordpress_id, scopus_publication.id)
        # Saving the publication to the backup system
        self.scopus_controller.insert_publication_backup(scopus_publication)

        # Saving the backup database and the reference database
        self.scopus_controller.backup_controller.save()
        self.reference_controller.save()

    def wipe_website(self):
        # Getting all the wordpress ids from the reference database to delete all the posts from the website
        reference_list = self.reference_controller.select_all_references()
        for reference in reference_list:
            wordpress_id = reference[1]
            self.wordpress_controller.delete_post(wordpress_id)

        # Deleting the backup database
        self.scopus_controller.backup_controller.wipe()
        # Deleting the reference database
        self.reference_controller.wipe()

        self.reference_controller.save()
        self.scopus_controller.backup_controller.save()

    def reload_scopus_cache_observed(self):
        self.scopus_controller.reload_cache_observed()

    def load_scopus_cache_observed(self):
        self.scopus_controller.load_cache_observed()

    def select_all_scopus_cache(self):
        return self.scopus_controller.select_all_publications_cache()