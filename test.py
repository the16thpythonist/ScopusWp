from pprint import pprint

from ScopusWp.config import init_logging
from ScopusWp.config import PATH

from ScopusWp.view import ScopusPublicationTableView

init_logging()


def test_loading_scopus_cache():
    from ScopusWp.scopus.main import ScopusTopController

    string = (
        'TESTING THE SCOPUS CACHE\n'
        'Testing the scopus cache by downloading the publications of the author {author_id} and then inserting them \n'
        'into the cache.\n'
    )
    print(string)
    controller = ScopusTopController()
    author_profile = controller.scopus_controller.get_author_profile(35313939900)
    print('[!] Getting the publications from the scopus database')
    publications = controller.scopus_controller.get_author_publications(author_profile)
    print('[i] These publications have been fetched\n')
    table_view = ScopusPublicationTableView(publications)
    print(str(table_view))
    print('[!] Wiping the cache clean')
    controller.cache_controller.wipe()
    print('[!] Inserting into the cache')
    controller.cache_controller.insert_multiple_publications(publications)
    print("[!] Saving the cache")
    controller.cache_controller.save()

    print('[!] Loading all the data from the cache...')
    publications = controller.select_all_publications_cache()
    print('[i] These publications have been loaded from the cache')
    table_view = ScopusPublicationTableView(publications)
    print(str(table_view))

test_loading_scopus_cache()