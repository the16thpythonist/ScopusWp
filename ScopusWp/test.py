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
    controller.reload_scopus_cache_observed()
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

    controller.wipe_website()

    controller.update_publications_website()


def test_affiliation_script():

    from ScopusWp.controller import TopController

    controller = TopController()

    author_dict = {
        ('Tomy', 'Rolo'): [56118820400, 35194644400, 35277157300],
        ('An', 'Bao Ngoc'): [5719208222],
        ('Balzer', 'Matthias'): [35519411500],
        ('Belgarian', 'Armen'): [38560996700],
        ('Berger', 'Lutz'): [40661118100],
        ('Blank', 'Thomas'): [5681921880],
        ('Bormann', 'Dietmar'): [55231514500],
        ('Caselle', 'Michele'): [57194376511],
        ('Chandna', 'Swati'): [36974957500],
        ('Chilingaryan', 'Suren'): [15076530600],
        ('Demattio', 'Horst'): [6506285395],
        ('Dierlamm', 'Alexander'): [6603122027],
        ('Ebersoldt', 'Andreas'): [55480930900],
        ('Ehrler', 'Felix'): [56674370500],
        ('Eisenblätter', 'Lars'): [57094104200],
        ('Feldbusch', 'Fridtjof'): [6506526929, 56159012600],
        ('Hartmann', 'Volker'): [7005982861],
        ('Herth', 'Armin'): [42961332200],
        ('Jejkal', 'Thomas'): [24478712700],
        ('Karnick', 'Djorn'): [37081197400],
        ('Kleifges', 'Matthias'): [6602072426],
        ('Kopmann', 'Andreas'): [3531393990],
        ('Krömer', 'Oliver'): [8520193800],
        ('Kühner', 'Thomas'): [24776279000],
        ('Kunka', 'Norbert'): [35276889200],
        ('Peric', 'Ivan'): [9043482900],
        ('Petry', 'Klaus'): [7004446817],
        ('Prabhune', 'Ajinkya'): [56534978900],
        ('Rota', 'Lorenzo'): [56473442500],
        ('Ruiter', 'Nicole'): [6507953977],
        ('Sander', 'Oliver'): [22986354000],
        ('Schlote-Hubek', 'Klaus'): [8657745400],
        ('Stotzka', 'Rainer'): [6602188741, 55248233300],
        ('Tan', 'Wei Yap'): [57188641563],
        ('Tcherniakhovski', 'Denis'): [6508308928],
        ('Tonne', 'Danah'): [55248295800],
        ('Vogelgesang', 'Matthias'): [35303862100],
        ('Wüstling', 'Sascha'): [23480623800]
    }

    affiliation_dict = controller.scopus_controller.explore_author_affiliations(author_dict)
    pprint(affiliation_dict)

    import configparser
    import json
    with open('/home/jonas/PycharmProjects/ScopusWp/ScopusWp/scopus/authors2.ini', mode='w+') as file:
        parser = configparser.ConfigParser()
        parser.read_file(file)

        for name_tuple, author_dict in affiliation_dict.items():
            short_name = name_tuple[1][:2] + name_tuple[0][:2]
            short_name = short_name.upper()
            parser[short_name] = {}
            id_list = []
            affil_list = []
            for author_id, aff_list in author_dict.items():
                id_list.append(author_id)
                diff = list(set(aff_list) - set(affil_list))
                affil_list += diff
            affil_list = list(map(lambda x: int(x), affil_list))
            parser[short_name]['ids'] = json.dumps(id_list)
            parser[short_name]['first_name'] = name_tuple[1]
            parser[short_name]['last_name'] = name_tuple[0]
            parser[short_name]['keywords'] = '["Team"]'
            parser[short_name]['scopus_whitelist'] = json.dumps(affil_list)
            parser[short_name]['scopus_blacklist'] = '[]'
        parser.write(file)
    """
    # Creating a list with all the affiliations
    affiliation_list = []
    for name_tuple, author_dict in affiliation_dict.items():
        for author_id, affiliation_id_list in author_dict.items():
            difference = list(set(affiliation_id_list) - set(affiliation_list))
            affiliation_list += difference
    print(affiliation_list)

    affiliation_name_dict = {}
    for affiliation_id in affiliation_list:
        if affiliation_id != '':
            affiliation = controller.scopus_controller.scopus_controller.affiliation_controller.get_affiliation(affiliation_id)
            affiliation_name_dict[affiliation_id] = affiliation

    print(affiliation_name_dict)
    from ScopusWp.view import AuthorAffiliationTableView
    view = AuthorAffiliationTableView(affiliation_dict, affiliation_name_dict)
    print(view.get_string())
    """


def test_kit_open():
    import requests

    url = 'https://publikationen.bibliothek.kit.edu/publikationslisten/get.php?referencing=all&external_publications=all&lang=de&format=html&style=kit-3lines-title_b-authors-other&authors=Kopmann%2C%20Andreas'
    response = requests.get(url)
    print(response.text)


def test_elsapy():
    from elsapy.elsclient import ElsClient
    from elsapy.elsprofile import ElsAuthor, ElsEntity
    from elsapy.elssearch import ElsSearch
    from pprint import pprint

    api_key = '3396e90e0692ebaa0496efa66d481c5c'
    client = ElsClient(api_key)
    search = ElsSearch()



test_elsapy()