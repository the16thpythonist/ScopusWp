from pprint import pprint

from ScopusWp.config import init_logging
from ScopusWp.config import PATH

from ScopusWp.view import ScopusPublicationTableView

init_logging()


def test_loading_scopus_cache(author_id=56950893700):
    from ScopusWp.scopus.main import ScopusTopController

    string = (
        '############################\n'
        '# TESTING THE SCOPUS CACHE #\n'
        '############################\n'
        'Testing the scopus cache by downloading the publications of the author {author_id} and then inserting them \n'
        'into the cache.\n'
    )
    print(string)
    controller = ScopusTopController()
    author_profile = controller.scopus_controller.get_author_profile(author_id)
    print('[!] Getting the publications from the scopus database...\n')
    publications = controller.scopus_controller.get_author_publications(author_profile)
    print('[i] These publications have been fetched\n')
    table_view = ScopusPublicationTableView(publications)
    print(str(table_view))
    print('[!] Wiping the cache clean...\n')
    controller.cache_controller.wipe()
    print('[!] Inserting into the cache...\n')
    controller.cache_controller.insert_multiple_publications(publications)
    print("[!] Saving the cache...\n")
    controller.cache_controller.save()
    print('[!] Loading all the data from the cache...\n')
    publications = controller.select_all_publications_cache()
    print('[i] These publications have been loaded from the cache:\n')
    table_view = ScopusPublicationTableView(publications)
    print(str(table_view))


def test_scopus_backup_database(author_id=56950893700):
    from ScopusWp.scopus.main import ScopusTopController

    string = (
        '######################################\n'
        '# TESTING THE SCOPUS BACKUP DATABASE #\n'
        '######################################\n'
        'Testing the database by fetching all the publications of the author "{}" from the scopus website by requests\n'
        'Then Wiping the database, inserting the new data, loading this data again and then displaying it\n'
    )
    print(string)
    controller = ScopusTopController()
    print('[!] Requesting all the publications from the scopus website...\n')
    author_profile = controller.scopus_controller.get_author_profile(author_id)
    publications = controller.scopus_controller.get_multiple_publications(author_profile.publications)
    print('[i] These publications have been fetched from the scopus website:\n')
    table_view = ScopusPublicationTableView(publications)
    print(str(table_view))
    print('[!] Wiping the database clean first...\n')
    controller.backup_controller.wipe()
    print('[!] Inserting the new publications into the database...\n')
    controller.backup_controller.insert_multiple_publications(publications)
    print('[!] Fetching all the publications from the database...\n')
    publications = controller.backup_controller.select_all_publications()
    print('[i] These publications have been fetched from the backup database:\n')
    table_view = ScopusPublicationTableView(publications)
    print(str(table_view))


def test_wordpress(author_id=56950893700):
    from ScopusWp.scopus.main import ScopusTopController
    from ScopusWp.wordpress import WordpressPublicationPostController
    from ScopusWp.reference import ReferenceController

    string = (
        '#################################################\n'
        '# TESTING THE WORDPRESS PUBLICATION POST SYSTEM #\n'
        '#################################################\n'
        '\n'
        'Testing by doing the following:\n'
        '+ Getting all the publications of the author "{}" from the scopus website\n'
        '+ Turning those scopus publications into generalized publication via the reference system\n'
        '+ Posting those publications to the website\n'
    )
    print(string)
    scopus_controller = ScopusTopController()
    print('[!] Requesting all the publications from the scopus website...\n')
    author_profile = scopus_controller.scopus_controller.get_author_profile(author_id)
    scopus_publications = scopus_controller.scopus_controller.get_multiple_publications(author_profile.publications)
    print('[i] These publications have been fetched from the scopus website:\n')
    table_view = ScopusPublicationTableView(scopus_publications)
    print(str(table_view))
    print('[!] Turning the scopus publications into generalized publications through the reference system...\n')
    reference_controller = ReferenceController()
    publications = []
    for scopus_publication in scopus_publications:
        publication = reference_controller.publication_from_scopus(scopus_publication)
        publications.append(publication)
    print('[i] These are the publication objects created from the scopus publication:\n')
    print(publications)
    print('[!] Posting the publications to the website...\n')
    wordpress_ids = []
    wordpress_controller = WordpressPublicationPostController()
    for publication in publications:
        wordpress_id = wordpress_controller.post_publication(publication, [])
        wordpress_ids.append(wordpress_id)
    print('[!] All the publications are posted!')
    print('[i] The posts have the following ids:')
    print(wordpress_ids)
    input('[?] Press any button to continue and delete the posts')

    print('[!] Deleting the posts...\n')
    for wordpress_id in wordpress_ids:
        wordpress_controller.delete_post(wordpress_id)
    print('[!] Finished deleting!')


def test_scopus_cache_observed():
    from ScopusWp.controller import TopController

    string = (
        '##########################################################\n'
        '# TESTING LOADING THE SCOPUS CACHE WITH OBSERVED AUTHORS #\n'
        '##########################################################\n'
    )
    print(string)
    print('[!] Requesting all the publications from the observed authors from the scopus website...\n')
    controller = TopController()
    controller.insert_scopus_cache_observed()
    print('[!] Getting all the publications from the cache...\n')
    scopus_publications = controller.select_all_scopus_cache()
    print('[i] These are the publications in the cache ')
    table_view = ScopusPublicationTableView(scopus_publications)
    print(str(table_view))


def test_scopus_cache():

    from ScopusWp.scopus.main import ScopusTopController

    controller = ScopusTopController()

    publications = controller.select_all_publications_cache()

    table_view = ScopusPublicationTableView(publications)
    print(str(table_view))


def test_update_publications_website():

    from ScopusWp.controller import TopController

    controller = TopController()

    controller.update_publications_website()


test_scopus_cache_observed()