from ScopusWp.scopus.controller import ScopusTopController

from ScopusWp.reference import ReferenceController

from ScopusWp.wordpress import WordpressPublicationPostController

from ScopusWp.config import Config, LoggingController

from wordpress_xmlrpc.exceptions import InvalidCredentialsError

from ScopusWp.reference import DATETIME_FORMAT

import socket
import wordpress_xmlrpc
import datetime
import logging


class TopController:

    def __init__(self):

        self.logging_controller = LoggingController()
        self.logging_controller.init()

        self.activity_logger = logging.getLogger('ACTIVITY')
        self.logger = logging.getLogger('TopController')

        self.scopus_controller = ScopusTopController()
        self.reference_controller = ReferenceController()
        self.wordpress_controller = WordpressPublicationPostController()

        self.config = Config.get_instance()

    def close(self):
        self.logger.debug('Closing the top controller')

        self.reference_controller.close()
        self.logging_controller.close()

    def update_website(self):
        # Getting all the publications that are saved in the backup system
        # Getting the user profiles of all the observed users
        # Getting the list of all the scopus ids of those users
        pass

    def update_citations_website(self, max_amount=200):
        """
        Updates the citations of those wordpress publication posts that have not been updated for a specified amount
        of time.

        Iterates through the list of all post references and gets the citation references for each as the
        representation of the citations already on the website and requests a new publication object from the scopus
        website for a new list of citations. The difference between those two is requested as scopus publications
        and then posted onto the website.
        :param max_amount: The max amount of publications to be requested
        :return: void
        """
        # Getting all the publications currently on the website
        post_reference_list = self.reference_controller.select_all_references()
        # for each publication getting the comment reference and the new publication from scopus
        counter = 0
        for post_reference in post_reference_list:
            wordpress_post_id = post_reference[1]
            updated_datetime = post_reference[3]
            current_datetime = datetime.datetime.now()
            update_interval = int(self.config['WORDPRESS']['update_expiration'])
            if (current_datetime - updated_datetime).days < update_interval:
                continue
            amount_comments_posted = self.update_citations_post(wordpress_post_id)
            counter += amount_comments_posted
            if counter >= max_amount:
                break

    def update_citations_post(self, wordpress_post_id):

        # Getting the list of all the comment publications from the comment reference database
        comment_reference_list = self.reference_controller.select_comment_reference_list_py_post(wordpress_post_id)
        old_citation_list = list(map(lambda x: x[3], comment_reference_list))
        # Getting the post reference tuple
        post_reference = self.reference_controller.select_post_reference_by_wordpress(wordpress_post_id)
        post_scopus_id = post_reference[2]
        post_publication = self.scopus_controller.get_publication(post_scopus_id, caching=True)
        # Saving the new publication into the backup system
        self.scopus_controller.insert_publication_backup(post_publication)
        new_citation_list = list(map(lambda x: int(x), post_publication.citations))
        # Building the difference from the new and old citation list
        difference = list(set(new_citation_list) - set(old_citation_list))
        # Requesting the publication itself from scopus to check for new citations
        counter = 0
        for scopus_id in difference:
            citation_publication = self.scopus_controller.get_publication(scopus_id)
            self.post_scopus_citation(post_publication, citation_publication)
            counter += 1
        # Updating the time, when was updated
        self.reference_controller.insert_reference(*post_reference[:-1])
        return counter

    def update_publications_website(self):
        # THE SCOPUS PART
        # Getting the new and relevant publications
        new_scopus_publication_list = self.new_scopus_publications()
        # Posting those new publications to the website
        for scopus_publication in new_scopus_publication_list:
            try:
                self.post_scopus_publication(scopus_publication)
            except Exception as e:
                self.logger.error('The scopus publication "{}" could not be posted due to the error "{}"'.format(
                    int(scopus_publication),
                    str(e)
                ))

    def populate_website(self):
        # THE SCOPUS PART
        # Getting the new and relevant publications
        new_scopus_publication_list = self.new_scopus_publications()
        # Posting those new publications to the website
        for scopus_publication in new_scopus_publication_list:
            self.post_scopus_publication(scopus_publication)
            reference = self.reference_controller.select_post_reference_by_scopus(int(scopus_publication))
            self.update_citations_post(reference[1])

    def new_scopus_publications(self):
        """
        Gets all the new publications from the observed authors, that have to be added to the website.

        :return: [ScopusPublication]
        """
        # Getting a list of all the scopus ids for the publications already in the website
        reference_list = self.reference_controller.select_all_references()
        old_scopus_id_list = list(map(lambda x: x[2], reference_list))

        print(old_scopus_id_list)

        # Getting a list of ALL the scopus ids for the observed authors, but without caching as we want to know whether
        # something has changed from before
        new_scopus_id_list = self.scopus_controller.get_publication_ids_observed(caching=True)

        print(new_scopus_id_list)

        # Getting all the new publications
        scopus_id_difference_list = list(set(new_scopus_id_list) - set(old_scopus_id_list))
        print(scopus_id_difference_list)
        publication_list = []
        for scopus_id in scopus_id_difference_list:
            # obviously without caching as we want the newest version of the publications, so they are fresh for as
            # long as possible
            publication = self.scopus_controller.get_publication(scopus_id, caching=True)
            publication_list.append(publication)

        # Filtering those publications by the whitelist blacklist criteria of the affiliations
        (
            publication_whitelist,
            publication_blacklist,
            publication_remaining_list
        ) = self.scopus_controller.filter_by_observation(publication_list)

        return publication_whitelist

    def repopulate_website(self, caching):
        """
        Wipes the website clean and then posts all the publications & citation comments a new

        :param caching: The boolean flag of whether to call the get requests against the cache first or use a new
            scopus request every time.
        :return: void
        """
        # Deleting all current posts and the reference database before inserting the new entries
        self.wipe_website()

        # All the relevant (already filtered) publications of the observed authors
        observed_publications_list = self.scopus_controller.get_publications_observed(caching=caching)

        # Uploading all the publications to the website
        for publication in observed_publications_list:
            self.post_scopus_publication(publication)

            # posting all the citations as comments
            citation_publication_list = self.scopus_controller.get_multiple_publications(
                publication.citations,
                caching=caching
            )
            for citation_scopus_publication in citation_publication_list:
                self.post_scopus_citation(publication, citation_scopus_publication)

    def post_scopus_citation(self, post_publication, citation_scopus_publication):
        """
        Posts the given citation publication as a citation to the post publication, upon which a wordpress post is
        based on the website.

        Also saves the citation publication in the wordpress backup database.
        :param post_publication: The ScopusPublication upon which a wordpress post is based on
        :param citation_scopus_publication: The ScopusPublication that cites the post publication and is supposed to appear as
            a comment on the wordpress post of the post publication
        :return: void
        """
        # Getting the wordpress id of the according post from the reference database
        scopus_id_post_publication = int(post_publication)
        reference_tuple = self.reference_controller.select_post_reference_by_scopus(scopus_id_post_publication)

        # Posting the citation to the actual
        citation_publication = self.reference_controller.publication_from_scopus(citation_scopus_publication)
        wordpress_post_id = reference_tuple[1]
        try:
            wordpress_comment_id = self.wordpress_controller.post_citations(
                wordpress_post_id,
                [citation_publication]
            )[0]
            self.reference_controller.insert_comment_reference(
                citation_publication.id,
                wordpress_post_id,
                wordpress_comment_id,
                citation_scopus_publication.id
            )
            self.activity_logger.info(
                'Comment posted, post id: {}, comment id: {}, scopus id: {}'.format(
                    wordpress_post_id,
                    wordpress_comment_id,
                    citation_scopus_publication.id
                )
            )
        except wordpress_xmlrpc.exceptions.InvalidCredentialsError:
            self.logger.error(
                'Duplicate comment for wordpress comment scopus id: {}'.format(
                    citation_scopus_publication.id
                )
            )
        except socket.gaierror:
            print('socket error wordpress')
        except IndexError:
            self.logger.error(
                'No comment id returned; Comment post attempt failed for comment scopus id: {}'.format(
                    citation_scopus_publication.id
                )
            )
            print('No comment id returned')

        # Saving the citation publication in the backup database for possible future use
        self.scopus_controller.insert_publication_backup(citation_scopus_publication)
        self.reference_controller.save()
        self.scopus_controller.backup_controller.save()

    def post_scopus_publication(self, scopus_publication):
        """
        Posts a scopus publication object onto the wordpress site.

        Turns the scopus publication into a generalized publication object by the reference controller and then uploads
        the post to the wordpress site and saves the wordpress id in the reference controller and the scopus publication
        in the scopus backup database.
        :param scopus_publication: The ScopusPublication object to be posted on the website
        :return:
        """
        # Creating a new generalized publication object from the scopus publication using the reference controller to
        # create a new internal id for the object
        publication = self.reference_controller.publication_from_scopus(scopus_publication)

        # Getting the keywords for each publication
        keywords = self.scopus_controller.publication_observation_keywords(scopus_publication)

        # Posting this publication to the wordpress site
        wordpress_id = self.wordpress_controller.post_publication(publication, keywords)
        # Saving the posting in the reference database
        self.reference_controller.insert_reference(publication.id, wordpress_id, scopus_publication.id)
        # Saving the publication to the backup system
        self.scopus_controller.insert_publication_backup(scopus_publication)

        # Saving the backup database and the reference database
        self.scopus_controller.backup_controller.save()
        self.reference_controller.save()

        self.activity_logger.info(
            'Publication posted, post id: {}, scopus id:{}, internal id:{}'.format(
                wordpress_id,
                scopus_publication.id,
                publication.id
            )
        )

        return publication.id, wordpress_id, scopus_publication.id

    def wipe_website(self):
        # Getting all the wordpress ids from the reference database to delete all the posts from the website
        reference_list = self.reference_controller.select_all_references()
        for reference in reference_list:
            wordpress_id = reference[1]
            self.wordpress_controller.delete_post(wordpress_id)
        self.logger.info('wiped all posts in the reference table from the website')

        # Deleting the backup database
        self.scopus_controller.backup_controller.wipe()
        self.logger.info('wiped the backup database')
        # Deleting the reference database
        self.reference_controller.wipe()
        self.logger.info('Wiped the reference database')

        self.reference_controller.save()
        self.scopus_controller.backup_controller.save()

    def reload_scopus_cache_observed(self):
        self.scopus_controller.reload_cache_observed()

    def load_scopus_cache_observed(self):
        self.scopus_controller.load_cache_observed()

    def select_all_scopus_cache(self):
        return self.scopus_controller.select_all_publications_cache()