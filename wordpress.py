from wordpress_xmlrpc import Client
from wordpress_xmlrpc import WordPressPost, WordPressComment
from wordpress_xmlrpc.methods.posts import NewPost, EditPost, GetPost, DeletePost
from wordpress_xmlrpc.methods.comments import NewComment, EditComment


class WordpressPublicationPostController:

    def __init__(self):
        # Getting the config instance for the project
        self.config = cfg.Config.get_instance()

        # Getting the logger for the the scopus part of the project
        scopus_logger_id = cfg.SCOPUS_LOGGING_EXTENSION
        self.logger = logging.getLogger(scopus_logger_id)

        # Getting the url path to the xmlrpc.php file from the config file
        self.url = self.config['WORDPRESS']['url']
        # Getting the username and the password for the access to the wordpress api from the config file
        self.username = self.config['WORDPRESS']['username']
        self.password = self.config['WORDPRESS']['password']

        # Creating the client object from the login data
        self.client = Client(self.url, self.username, self.password)

    def post_publication(self, publication, keywords):
        # Creating the view specifically for the wordpress posts
        wp_post_view = PublicationWordpressPostView(publication, keywords)

        post = WordPressPost()

        post.title = wp_post_view.get_title()
        post.excerpt = wp_post_view.get_excerpt()
        # post.date = wp_post_view.get_date()
        post.slug = wp_post_view.get_slug()
        post.content = wp_post_view.get_content()
        post.date = wp_post_view.get_date()

        post.id = self.client.call(NewPost(post))

        post.terms_names = {
            'category': wp_post_view.get_category_list(),
            'post_tag': wp_post_view.get_tag_list()
        }

        post.post_status = 'publish'
        post.comment_status = 'closed'

        self.client.call(EditPost(post.id, post))

        return post.id

    def post_citation(self, wordpress_id, publications, multiple=False):

        if isinstance(publications, list):
            self.enable_comments(wordpress_id)
            # In case there are no multiple post, if the one passed
            comment_id_list = []
            for publication in publications:
                comment_id = self.post_citation(wordpress_id, publication, multiple=True)
                comment_id_list.append(comment_id)

            self.disable_comments(wordpress_id)

        elif isinstance(publications, Publication):
            # In case there are no multiple citations to be added, if its only the one passed post, then adding
            # mod. the comment status of the post locally
            if not multiple:
                self.enable_comments(wordpress_id)

            # Actually posting the comment
            comment = WordPressComment()

            wp_comment_view = PublicationWordpressCitationView(publications)

            comment.content = wp_comment_view.get_content()

            comment_id = self.client.call(NewComment(wordpress_id, comment))

            # Changing the date of the comment, but only if there is a data specified for the publication
            date_created = wp_comment_view.get_date()
            if date_created is not None:
                comment.date_created = date_created
            self.client.call(EditComment(comment_id, comment))

            if not multiple:
                self.disable_comments(wordpress_id)

            return comment_id

    def delete_post(self, wordpress_id):
        self.client.call(DeletePost(wordpress_id))

    def delete_posts(self, wordpress_id_list):
        for wordpress_id in wordpress_id_list:
            self.delete_post(wordpress_id)

    def enable_comments(self, wordpress_id):
        # Getting the Post
        post = self.client.call(GetPost(wordpress_id))

        # Changing the comment status of the post to open
        post.comment_status = 'open'

        self.client.call(EditPost(wordpress_id, post))

    def disable_comments(self, wordpress_id):
        # Getting the post
        post = self.client.call(GetPost(wordpress_id))

        # Changing the comment status
        post.comment_status = 'closed'

        self.client.call(EditPost(wordpress_id, post))