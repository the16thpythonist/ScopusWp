from ScopusWp.config import init_logging
from ScopusWp.controllers import ScopusController, WordpressController, ScopusWpController
from ScopusWp.repr import Publication

from ScopusWp.controllers import ScopusPublicationController, ScopusAuthorController

from pprint import pprint

import json

import warnings

init_logging()
"""
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
"""



# response = controller.request_abstract_retrieval(84891274054)
# response = controller.request_citations_search('2-s2.0-84891274054')

# controller2 = ScopusAuthorController()

"""
controller3 = ScopusWpController()
publication = controller3.get_publication(84891274054)
author = controller3.get_author(35519411500)
publication_list = []
for pid in author.publications:
    publication = controller3.get_publication(pid)
    controller3.print_publication_info(publication)
"""

# TODO: Build all the stored pubs new because json encoding fails with some names
def relevant_test():
    warnings.filterwarnings('ignore')

    string = (
        'This divides the publications by checking if one of the authors is affiliated '
        'with the KIT or KIT campus north:\n\n'
    )
    print(string)

    controller = ScopusWpController()

    author = controller.get_author(35303862100)
    relevant, irrelevant = controller.get_relevant_publications()


    string = (
        '####################################\n'
        '# ALL THE IRRELEVANT PUBLICATIONS: #\n'
        '####################################\n'
    )
    print(string)

    for p in irrelevant:
        controller.print_publication_info(p)

    string = (
        '##################################\n'
        '# ALL THE RELEVANT PUBLICATIONS: #\n'
        '##################################\n'
    )
    print(string)

    for p in relevant:
        controller.print_publication_info(p)


def test_affiliation(affid):
    controller = ScopusWpController()
    response = controller.scopus_affiliation_controller.request_affiliation_retrieval(affid)
    d = json.loads(response.text)
    pprint(d)

test_affiliation(110986687)