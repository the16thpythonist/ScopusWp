from wordpress_xmlrpc import Client
from wordpress_xmlrpc import WordPressPost, WordPressComment
from wordpress_xmlrpc.methods.posts import NewPost, EditPost, GetPost, DeletePost
from wordpress_xmlrpc.methods.comments import NewComment, EditComment

from ScopusWp.view import PublicationWordpressPostView
from ScopusWp.view import PublicationWordpressCommentView

import ScopusWp.config as cfg
import logging


class WordpressPublicationPostController:
    """
    This controller is in charge of actually posting the publications as wordpress posts or comments onto the website.

    """
    def __init__(self):
        # Getting the config instance for the project
        self.config = cfg.Config.get_instance()

        # Getting the logger for the the scopus part of the project
        self.logger = logging.getLogger('Wordpress')

        # Getting the url path to the xmlrpc.php file from the config file
        self.url = self.config['WORDPRESS']['url']
        # Getting the username and the password for the access to the wordpress api from the config file
        self.username = self.config['WORDPRESS']['username']
        self.password = self.config['WORDPRESS']['password']

        # Creating the client object from the login data
        self.client = Client(self.url, self.username, self.password)

    def post_publication(self, publication, keywords):
        """
        If given a generalized publication object and a list of keywords posts the publication as a new post to the
        wordpress website.

        :param publication: The generalized publication object describing  what to be posted
        :param keywords: A list of string keywords, which will be used as the categories of the post
        :return: The int wordpress id of the post
        """
        # Creating the view specifically for the wordpress posts
        post_view = PublicationWordpressPostView(publication, keywords)

        post = WordPressPost()

        post.title = post_view.get_title()
        post.excerpt = post_view.get_excerpt()
        # post.date = wp_post_view.get_date()
        post.slug = post_view.get_slug()
        post.content = post_view.get_content()
        post.date = post_view.get_date()

        post.id = self.client.call(NewPost(post))

        category_list = post_view.get_category_list()
        tag_list = post_view.get_tag_list()

        post.terms_names = {
            'category': category_list,
            'post_tag': tag_list
        }

        post.post_status = 'publish'
        post.comment_status = 'closed'

        self.client.call(EditPost(post.id, post))
        self.logger.info('WORDPRESS POSTED PUBLICATION, publication id: {}, wordpress id: {}'.format(
            publication.id,
            post.id
        ))

        return post.id

    def post_citations(self, wordpress_id, publication_list):
        """
        Given the wordpress post id of an already posted publication, this method will post the comments given by
        the list of generalized publication objects.

        :param wordpress_id: The int id of the post, which to extend with comments
        :param publication_list: A list of generalized publication objects
        :return: A list of int wordpress comment ids
        """
        comment_id_list = []
        self.enable_comments(wordpress_id)

        for publication in publication_list:
            if publication.title == '':
                continue
            comment = WordPressComment()
            comment_view = PublicationWordpressCommentView(publication)

            comment.content = comment_view.get_content()

            comment_id = self.client.call(NewComment(wordpress_id, comment))
            comment_id_list.append(comment_id)

            date_created = comment_view.get_date()
            comment.date_created = date_created
            self.client.call(EditComment(comment_id, comment))
            self.logger.info('WORDPRESS COMMENT POSTED, publication id: {}, comment id: {}'.format(
                publication.id,
                comment_id
            ))

        self.disable_comments(wordpress_id)
        return comment_id_list

    def delete_post(self, wordpress_id):
        """
        Calls a method om the wordpress site, which deletes the post of the given wordpress post id.

        :param wordpress_id: The int id of the post to delete
        :return: void
        """
        self.client.call(DeletePost(wordpress_id))

    def delete_posts(self, wordpress_id_list):
        """
        Deletes all the posts, given by the list of wordpress ids

        :param wordpress_id_list: The list of int ids
        :return: void
        """
        for wordpress_id in wordpress_id_list:
            self.delete_post(wordpress_id)

    def enable_comments(self, wordpress_id):
        """
        Calls a method on the wordpress site, which enables the comment for the post of the given wordpress id

        :param wordpress_id: The int id of the wordpress post
        :return: void
        """
        # Getting the Post
        post = self.client.call(GetPost(wordpress_id))

        # Changing the comment status of the post to open
        post.comment_status = 'open'

        self.client.call(EditPost(wordpress_id, post))

    def disable_comments(self, wordpress_id):
        """
        Calls a method on the wordpress site, which disables the comments for the post of the given wordpress post id

        :param wordpress_id: The int id of the post, whose comments to disable
        :return: void
        """
        # Getting the post
        post = self.client.call(GetPost(wordpress_id))

        # Changing the comment status
        post.comment_status = 'closed'

        self.client.call(EditPost(wordpress_id, post))
