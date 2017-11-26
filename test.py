from ScopusWp.config import init_logging
from ScopusWp.controllers import ScopusController, WordpressController

init_logging()

scopus_controller = ScopusController()

author = scopus_controller.get_author(35313939900)
print(author.index_name)

publication_id = author.publications[0]
publication = scopus_controller.get_publication(publication_id)
print(publication.title)

author_list = scopus_controller.get_author(publication.authors)

wordpress_controller = WordpressController()
wpid = wordpress_controller.post_publication(publication, author_list)

wordpress_controller.post_citation(wpid, publication)
print(wpid)
