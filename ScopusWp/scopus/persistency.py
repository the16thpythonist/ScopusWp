from ScopusWp.database import MySQLDatabaseAccess

from ScopusWp.scopus.data import ScopusPublication, ScopusAuthorProfile
from ScopusWp.scopus.data import from_dict, to_dict

from ScopusWp.config import PATH, Config

import json
import pathlib

import pickle
import os


###############
#   CLASSES   #
###############

# todo: Make the cache update save and the refill via delete, so progress does not get lost with connection error
# todo: in the long run, even the cache has to be a database, or anything that does not clog the RAM, maybe shelve


# TODO: Make it a dict-like object
class PublicationPersistencyInterface:

    def select(self, scopus_id):
        raise NotImplementedError()

    def select_all(self):
        raise NotImplementedError()

    def select_all_ids(self):
        raise NotImplementedError()

    def insert(self, publication):
        raise NotImplementedError()

    def contains(self, publication):
        raise NotImplementedError()

    def save(self):
        raise NotImplementedError()

    def wipe(self):
        raise NotImplementedError()


class AuthorProfilePersistencyInterface:

    def select(self, author_id):
        raise NotImplementedError()

    def select_all(self):
        raise NotImplementedError()

    def select_all_ids(self):
        raise NotImplementedError()

    def insert(self, author_profile):
        raise NotImplementedError()

    def contains(self, author):
        raise NotImplementedError()

    def save(self):
        raise NotImplementedError()

    def wipe(self):
        raise NotImplementedError()


###############
# Controllers #
###############


class ScopusBackupController:

    def __init__(self):

        self.backup_model = ScopusBackupPublicationModel()

    def insert_publication(self, publication):
        self.backup_model.insert(publication)

    def insert_multiple_publications(self, publication_list):
        for publication in publication_list:
            self.insert_publication(publication)

    def select_publication(self, scopus_id):
        return self.backup_model.select(scopus_id)

    def select_multiple_publications(self, scopus_id_list):
        publication_list = []
        for scopus_id in scopus_id_list:
            publication = self.select_publication(scopus_id)
            publication_list.append(publication)
        return publication_list

    def select_all_publications(self):
        return self.backup_model.select_all()

    def wipe(self):
        self.backup_model.wipe()

    def save(self):
        self.backup_model.save()


class ScopusCacheController:

    def __init__(self, publication_cache_model_class, author_cache_model_class):

        self.publication_cache_model = publication_cache_model_class()  # type: ScopusPublicationDatabaseCacheModel
        self.author_cache_model = author_cache_model_class()  # type: ScopusAuthorDatabaseCacheModel

    def insert_author_profile(self, author_profile):
        self.author_cache_model.insert(author_profile)

    def contains_author_profile(self, author):
        return self.author_cache_model.contains(author)

    def select_author_profile(self, author_id):
        return self.author_cache_model.select(author_id)

    def select_all_author_profiles(self):
        return self.author_cache_model.select_all()

    def insert_publication(self, publication):
        self.publication_cache_model.insert(publication)

    def insert_multiple_publications(self, publication_list):
        for publication in publication_list:
            self.insert_publication(publication)

    def contains_publication(self, publication):
        return self.publication_cache_model.contains(publication)

    def select_publication(self, scopus_id):
        return self.publication_cache_model.select(scopus_id)

    def select_multiple_publications(self, scopus_id_list):
        publication_list = []
        for scopus_id in scopus_id_list:
            publication = self.select_publication(scopus_id)
            publication_list.append(publication)
        return publication_list

    def select_all_publications(self):
        return self.publication_cache_model.select_all()

    def select_all_publication_ids(self):
        return self.publication_cache_model.select_all_ids()

    def select_all_author_ids(self):
        return self.author_cache_model.select_all_ids()

    def save(self):
        self.publication_cache_model.save()
        self.author_cache_model.save()

    def wipe(self):
        self.publication_cache_model.wipe()
        self.author_cache_model.wipe()

##########
# Models #
##########


class ScopusAuthorPickleCacheModel(AuthorProfilePersistencyInterface):

    def __init__(self):
        self.path_string = '{}/cache/authors.pkl'.format(PATH)
        self.path = pathlib.Path(self.path_string)
        self.content = self.load()

    def load(self):
        with self.path.open(mode='rb') as file:
            content = pickle.load(file)
        return content

    def insert(self, author_profile):
        self.content[int(author_profile)] = author_profile

    def select(self, author_id):
        if author_id in self.content.keys():
            return self.content[author_id]

    def select_all(self):
        author_profile_list = []
        for key in self.content.keys():
            author_profile = self.content[key]
            author_profile_list.append(author_profile)
        return author_profile_list

    def contains(self, author):
        return int(author) in self.content.keys()

    def wipe(self):
        self.content = {}
        self.save()

    def save(self):
        with self.path.open(mode="wb+") as file:
            pickle.dump(self.content, file)


class ScopusPublicationPickleCacheModel(PublicationPersistencyInterface):

    def __init__(self):

        self.path_string = '{}/cache/publications.pkl'.format(PATH)

        self.path = pathlib.Path(self.path_string)

        self.content = self.load()

    def load(self):
        with self.path.open(mode='rb') as file:
            content = pickle.load(file)
        return content

    def insert(self, publication):
        self.content[int(publication)] = publication

    def select(self, scopus_id):
        if scopus_id in self.content.keys():
            return self.content[scopus_id]

    def select_all(self):
        publication_list = []
        for key in self.content.keys():
            publication = self.content[key]
            publication_list.append(publication)
        return publication_list

    def contains(self, publication):
        return int(publication) in self.content.keys()

    def wipe(self):
        self.content = {}
        self.save()

    def save(self):
        with self.path.open(mode="wb+") as file:
            pickle.dump(self.content, file)


class ScopusAuthorDatabaseCacheModel(AuthorProfilePersistencyInterface):

    def __init__(self):
        AuthorProfilePersistencyInterface.__init__(self)

        self.database_access = MySQLDatabaseAccess()

        self.config = Config.get_instance()
        self.database_name = self.config['MYSQL']['author_cache_table']

    def wipe(self):
        sql = 'TRUNCATE {};'.format(self.database_name)
        self.database_access.execute(sql)

    def insert(self, author):
        # Converting all the data into json so it fits into the data base columns

        # Turning the list of publication scopus ids for the author into a json string
        publication_list_json = json.dumps(author.publications).replace('"', "'")

        sql = (
            'INSERT INTO '
            '{database} ('
            'author_id,'
            'first_name, '
            'last_name, '
            'h_index, '
            'citation_count, '
            'document_count, '
            'publications) '
            'VALUES ('
            '{author_id},'
            '"{first_name}",'
            '"{last_name}",'
            '{h_index},'
            '{citation_count},'
            '{document_count},'
            '"{publications}") '
            'ON DUPLICATE KEY UPDATE '
            'author_id = {author_id},'
            'first_name = "{first_name}",'
            'last_name = "{last_name}",'
            'h_index = {h_index},'
            'citation_count = {citation_count},'
            'document_count = {document_count},'
            'publications = "{publications}";'
            'COMMIT;'
        ).format(
            database=self.database_name,
            author_id=author.id,
            first_name=author.first_name,
            last_name=author.last_name,
            h_index=author.h_index,
            document_count=author.document_count,
            citation_count=author.citation_count,
            publications=publication_list_json
        )

        self.database_access.execute(sql)

    def select(self, author_id):
        sql = (
            'SELECT '
            'author_id, '
            'first_name, '
            'last_name, '
            'h_index, '
            'citation_count, '
            'document_count, '
            'publications '
            'FROM {database} WHERE author_id={author_id}'
        ).format(
            database=self.database_name,
            author_id=author_id
        )

        row_list = self.database_access.select(sql)

        if len(row_list) != 0:
            row = row_list[0]
            author_profile = self._author_profile_from_list(row)
            return author_profile

    @staticmethod
    def _author_profile_from_list(row):
        author_id = row[0]
        first_name = row[1]
        last_name = row[2]
        h_index = row[3]
        citation_count = row[4]
        document_count = row[5]

        publications_json_string = row[6]
        publication_list = json.loads(publications_json_string.replace("'", '"'))
        publication_list = list(map(lambda x: int(x), publication_list))

        author_profile = ScopusAuthorProfile(
            author_id,
            first_name,
            last_name,
            h_index,
            citation_count,
            document_count,
            publication_list
        )

        return author_profile

    def select_all(self):

        sql = (
            'SELECT '
            'author_id, '
            'first_name, '
            'last_name, '
            'h_index, '
            'citation_count, '
            'document_count, '
            'publications'
            'FROM {database}'
        ).format(
            database=self.database_name
        )

        row_list = self.database_access.select(sql)
        author_profile_list = []
        for row in row_list:
            author_profile = self._author_profile_from_list(row)
            author_profile_list.append(author_profile)

        return author_profile_list

    def select_all_ids(self):
        sql = (
            'SELECT '
            'author_id '
            'FROM {database};'
        ).format(
            database=self.database_name
        )

        row_list = self.database_access.select(sql)
        id_list = list(map(lambda x: x[0], row_list))
        return id_list

    def contains(self, author):

        sql = (
            'SELECT * FROM {database} WHERE author_id={author_id}'
        ).format(
            database=self.database_name,
            author_id=int(author)
        )

        row_list = self.database_access.select(sql)
        return len(row_list) > 0

    def save(self):
        self.database_access.save()


class ScopusPublicationDatabaseCacheModel(PublicationPersistencyInterface):

    def __init__(self):
        PublicationPersistencyInterface.__init__(self)

        self.database_access = MySQLDatabaseAccess()

        self.config = Config.get_instance()
        self.database_name = self.config['MYSQL']['publication_cache_table']

    def wipe(self):
        sql = 'TRUNCATE {};'.format(self.database_name)
        self.database_access.execute(sql)

    def insert(self, publication):
        if publication is None or publication.id == '':
            return None
        # Converting all the data so it fits into a database data column

        # Turning the creator ScopusAuthor object into a json string
        creator_dict = to_dict(publication.creator)
        creator_json_string = json.dumps(creator_dict).replace('"', "'")

        # Turning the authors list, list of ScopusAuthor objects into a json string
        author_dict_list = to_dict(publication.authors)
        authors_json_string = json.dumps(author_dict_list).replace('"', "'")

        # Turning the keywords list and the citations list of str/int into a json object
        keywords_json_string = json.dumps(publication.keywords).replace('"', "'")
        citations_json_string = json.dumps(publication.citations).replace('"', "'")

        sql = (
            'INSERT INTO '
            '{database} ('
            'scopus_id, '
            'eid, '
            'doi, '
            'creator, '
            'title, '
            'description, '
            'journal, '
            'volume, '
            'date, '
            'authors, '
            'keywords, '
            'citations ) '
            'VALUES '
            '({scopus_id}, '
            '"{eid}", '
            '"{doi}", '
            '"{creator}", '
            '"{title}", '
            '"{description}", '
            '"{journal}", '
            '"{volume}", '
            '"{date}", '
            '"{authors}", '
            '"{keywords}", '
            '"{citations}") '
            'ON DUPLICATE KEY UPDATE '
            'scopus_id = {scopus_id}, '
            'eid = "{eid}", '
            'doi = "{doi}", '
            'creator = "{creator}", '
            'title = "{title}", '
            'description = "{description}", '
            'journal = "{journal}", '
            'volume = "{volume}", '
            'date = "{date}", '
            'authors = "{authors}", '
            'keywords = "{keywords}", '
            'citations = "{citations}";'
            'COMMIT;'
        ).format(
            database=self.database_name,
            scopus_id=publication.id,
            eid=publication.eid,
            doi=publication.doi,
            creator=creator_json_string,
            title=publication.title,
            description=publication.description,
            journal=publication.journal,
            volume=publication.volume,
            date=publication.date,
            authors=authors_json_string,
            keywords=keywords_json_string,
            citations=citations_json_string
        )

        # Executing the sql on the database
        self.database_access.execute(sql)

    def select(self, scopus_id):

        sql = (
            'SELECT '
            'scopus_id, '
            'eid, '
            'doi, '
            'creator, '
            'title, '
            'description, '
            'journal, '
            'volume, '
            'date, '
            'authors, '
            'keywords, '
            'citations '
            'FROM {database} WHERE scopus_id={id}'
        ).format(
            database=self.database_name,
            id=scopus_id
        )

        row_list = self.database_access.select(sql)

        if len(row_list) != 0:
            row = row_list[0]

            scopus_id = row[0]
            eid = row[1]
            doi = row[2]
            title = row[4]
            description = row[5]
            journal = row[6]
            volume = row[7]
            date = row[8]

            creator_json_string = row[3].replace("'", '"')
            creator_dict = json.loads(creator_json_string)
            creator = from_dict(creator_dict)

            authors_json_string = row[9].replace("'", '"')
            author_dict_list = json.loads(authors_json_string)
            author_list = from_dict(author_dict_list)

            keywords_json_string = row[10].replace("'", '"')
            keywords_list = json.loads(keywords_json_string)

            citations_json_string = row[11].replace("'", '"')
            citations_list = json.loads(citations_json_string)

            publication = ScopusPublication(
                scopus_id,
                eid,
                doi,
                title,
                description,
                date,
                creator,
                author_list,
                citations_list,
                keywords_list,
                journal,
                volume
            )

            return publication

    def contains(self, publication):
        if publication == '':
            return False

        sql = (
            'SELECT * FROM {database} WHERE scopus_id={scopus_id}'
        ).format(
            database=self.database_name,
            scopus_id=int(publication)
        )

        row_list = self.database_access.select(sql)
        return len(row_list) > 0

    def select_all(self):
        scopus_id_list = self.select_all_ids()
        publication_list = []
        for scopus_id in scopus_id_list:
            publication = self.select(scopus_id)
            publication_list.append(publication)
        return publication_list

    def select_all_ids(self):
        sql = (
            'SELECT '
            'scopus_id '
            'FROM {database};'
        ).format(
            database=self.database_name
        )

        row_list = self.database_access.select(sql)
        id_list = list(map(lambda x: x[0], row_list))
        return id_list

    def save(self):
        self.database_access.save()


class ScopusBackupPublicationModel(PublicationPersistencyInterface):

    def __init__(self):

        self.database_access = MySQLDatabaseAccess()
        self.database_name = 'publications'

    def execute(self, sql):
        return self.database_access.select(sql)

    def insert(self, publication):
        if not isinstance(publication.id, int):
            return None
        # Converting all the data so it fits into a database data column

        # Turning the creator ScopusAuthor object into a json string
        creator_dict = to_dict(publication.creator)
        creator_json_string = json.dumps(creator_dict).replace('"', "'")

        # Turning the authors list, list of ScopusAuthor objects into a json string
        author_dict_list = to_dict(publication.authors)
        authors_json_string = json.dumps(author_dict_list).replace('"', "'")

        # Turning the keywords list and the citations list of str/int into a json object
        keywords_json_string = json.dumps(publication.keywords).replace('"', "'")
        citations_json_string = json.dumps(publication.citations).replace('"', "'")

        sql = (
            'INSERT INTO '
            '{database} ('
            'scopus_id, '
            'eid, '
            'doi, '
            'creator, '
            'title, '
            'description, '
            'journal, '
            'volume, '
            'date, '
            'authors, '
            'keywords, '
            'citations ) '
            'VALUES '
            '({scopus_id}, '
            '"{eid}", '
            '"{doi}", '
            '"{creator}", '
            '"{title}", '
            '"{description}", '
            '"{journal}", '
            '"{volume}", '
            '"{date}", '
            '"{authors}", '
            '"{keywords}", '
            '"{citations}") '
            'ON DUPLICATE KEY UPDATE '
            'scopus_id = {scopus_id}, '
            'eid = "{eid}", '
            'doi = "{doi}", '
            'creator = "{creator}", '
            'title = "{title}", '
            'description = "{description}", '
            'journal = "{journal}", '
            'volume = "{volume}", '
            'date = "{date}", '
            'authors = "{authors}", '
            'keywords = "{keywords}", '
            'citations = "{citations}";'
        ).format(
            database=self.database_name,
            scopus_id=publication.id,
            eid=publication.eid,
            doi=publication.doi,
            creator=creator_json_string,
            title=publication.title,
            description=publication.description,
            journal=publication.journal,
            volume=publication.volume,
            date=publication.date,
            authors=authors_json_string,
            keywords=keywords_json_string,
            citations=citations_json_string
        )

        # Executing the sql on the database
        self.database_access.execute(sql)

    def select(self, scopus_id):

        sql = (
            'SELECT '
            'scopus_id, '
            'eid, '
            'doi, '
            'creator, '
            'title, '
            'description, '
            'journal, '
            'volume, '
            'date, '
            'authors, '
            'keywords, '
            'citations '
            'FROM {database} WHERE scopus_id={id}'
        ).format(
            database=self.database_name,
            id=scopus_id
        )

        row_list = self.database_access.select(sql)

        if len(row_list) != 0:
            row = row_list[0]

            scopus_id = row[0]
            eid = row[1]
            doi = row[2]
            title = row[4]
            description = row[5]
            journal = row[6]
            volume = row[7]
            date = row[8]

            creator_json_string = row[3].replace("'", '"')
            creator_dict = json.loads(creator_json_string)
            creator = from_dict(creator_dict)

            authors_json_string = row[9].replace("'", '"')
            author_dict_list = json.loads(authors_json_string)
            author_list = from_dict(author_dict_list)

            keywords_json_string = row[10].replace("'", '"')
            keywords_list = json.loads(keywords_json_string)

            citations_json_string = row[11].replace("'", '"')
            citations_list = json.loads(citations_json_string)

            publication = ScopusPublication(
                scopus_id,
                eid,
                doi,
                title,
                description,
                date,
                creator,
                author_list,
                citations_list,
                keywords_list,
                journal,
                volume
            )

            return publication

    def save(self):
        self.database_access.save()

    def select_all(self):
        # Todo: Make this to be more efficient by combining into one query
        scopus_id_list = self.select_all_ids()
        publication_list = []
        for scopus_id in scopus_id_list:
            publication = self.select(scopus_id)
            publication_list.append(publication)
        return publication_list

    def select_all_ids(self):

        sql = (
            'SELECT scopus_id FROM publications'
        )

        scopus_id_list = []
        row_list = self.database_access.select(sql)
        for row in row_list:
            scopus_id = row[0]
            scopus_id_list.append(scopus_id)
        return scopus_id_list

    def wipe(self):
        sql = "TRUNCATE publications"
        self.execute(sql)


class TempPersistentSequenceModel:

    def __init__(self, id, folder_path, name_function=None):
        # This is the id of the model, which enables to identify all the files which belong to one model, which enables
        # the possibility of multiple models using the same folder for storage
        self.id = id

        # The path to the folder, which is supposed to contain all the files for the model
        self.path_string = folder_path

        # The ath to the info file. The info file contains the info about the current state of the counter for the model
        # of the specific id and the list of paths belonging to that model
        self.info_path_string = '{}/_info_{}.json'.format(self.path_string, self.id)

        # Stores the max amount of items in the sequence, used for creating the file names for the files which contain
        # the new objects
        self.index_counter = 0

        # The keys are the path strings to the files, which contain the binary data to the objects and the values are
        # the actual values
        self.content = {}

        if name_function is None:
            self.name_function = lambda x: str(x.__class__).replace('<class', '').replace("'", '').replace('>', '')
        else:
            self.name_function = name_function

    def load(self):
        # Loading the info file, which will create a entry for each file path in the content dict with the dummy value
        # None
        self.load_info()

        for path in self.content.keys():
            # Loading the objects
            self.load_object(path)

    def load_info(self):
        if os.path.exists(self.info_path_string):
            with open(self.info_path_string, mode='r') as file:
                info_dict = json.load(file)

            # Assigning the saved index counter
            self.index_counter = info_dict['counter']
            # Adding a dummy entry for every file path listed in the info file
            for path in info_dict['paths']:
                self.content[path] = None

    def load_object(self, path):
        with open(path, mode='rb') as file:
            obj = pickle.load(file)
            self.content[path] = obj

    def save_info(self):
        # Creating the info dict
        info_dict = {
            'counter': self.index_counter,
            'paths': list(self.content.keys())
        }

        # Actually saving that dict as a json to the file
        with open(self.info_path_string, mode='w+') as file:
            json.dump(info_dict, file)

    def save_object(self, obj, path):
        # Actually creating the file and saving the object as pickled data into it
        with open(path, mode='wb+') as file:
            pickle.dump(obj, file)

    def create_path(self, obj):
        # The file name for saving an object consists of the class name of the object saved, the index counter to show
        # which part of the sequence it is and the id of the model.
        object_file_name = self.name_function(obj)
        file_name_string = '{}_{}_{}.pkl'.format(str(self.id), str(self.index_counter), object_file_name)

        file_path_string = '{}/{}'.format(self.path_string, file_name_string)
        return file_path_string

    def append(self, obj):
        # Incrementing the counter for the saved files
        self.index_counter += 1

        # Creating the path for the file and saving the key value tuple with path and object in the internal dict
        file_path_string = self.create_path(obj)
        self.content[file_path_string] = obj

        # Saving the object into a file and saving the new info data
        self.save_object(obj, file_path_string)
        self.save_info()

    def __iter__(self):
        return self.content.values().__iter__()
