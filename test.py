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


def test_table():
    from ScopusWp.views import PublicationObservedView

    controller = ScopusWpController()
    publications1, publications2 = controller.get_relevant_publications()
    publications = publications1 + publications2

    controller.build_publications(publications)
    view = PublicationObservedView(publications, controller.observed_author_model)
    string = view.get_table_string()
    print('\n THE LIST OF ALL THE AFFILIATION IDS ANY ONE OF THE AUTHORS HAD IN THE PAST')
    print(string)
    pprint(view.affiliations)


def test_affil_table():
    from ScopusWp.views import AuthorsAffiliationsView

    controller = ScopusWpController()
    authors = controller.all_author_backup()
    publications = controller.all_publication_backup()

    view = AuthorsAffiliationsView(authors, publications)
    string = view.get_string()

    print(string)


def build_all():
    controller = ScopusWpController()
    author_list = controller.get_observed_authors()
    publication_list = []
    for author in author_list:
        _temp = []
        for scopus_id in author.publications:
            pub = controller.get_publication(scopus_id)
            _temp.append(pub)
        publication_list += _temp

    controller.build_publications(publication_list)
    controller.close()

    controller.build_publications(publication_list)

test_affiliation(109707652)