from pprint import pprint

from ScopusWp.config import init_logging
from ScopusWp.config import PATH

from ScopusWp.view import ScopusPublicationTableView

init_logging()


def test_loading_scopus_cache():
    from ScopusWp.scopus.main import ScopusTopController

    controller = ScopusTopController()
    author_profile = controller.scopus_controller.get_author_profile(35313939900)
    publications = controller.scopus_controller.get_author_publications(author_profile)
    #publications = controller.select_all_publications_cache()

    controller.cache_controller.wipe()
    controller.cache_controller.insert_multiple_publications(publications)
    controller.cache_controller.save()
    controller.backup_controller.wipe()
    controller.backup_controller.insert_multiple_publications(publications)
    controller.backup_controller.save()

    publications = controller.select_all_publications_cache()
    table_view = ScopusPublicationTableView(publications)

    print(str(table_view))

    publications = controller.select_all_publications_backup()
    table_view = ScopusPublicationTableView(publications)

    print(str(table_view))


test_loading_scopus_cache()