from ScopusWp.database import MySQLDatabaseAccess

from ScopusWp.scopus.data import ScopusPublication
from ScopusWp.scopus.data import from_dict, to_dict

from ScopusWp.config import PATH

import json
import pathlib

import pickle


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

    def insert(self, publication):
        raise NotImplementedError()

    def contains(self, publication):
        raise NotImplementedError()

    def save(self):
        raise NotImplementedError()


class AuthorProfilePersistencyInterface:

    def select(self, author_id):
        raise NotImplementedError()

    def select_all(self):
        raise NotImplementedError()

    def insert(self, author_profile):
        raise NotImplementedError()

    def contains(self, author):
        raise NotImplementedError()

    def save(self):
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

        self.publication_cache_model = publication_cache_model_class()  # type: ScopusPublicationPickleCacheModel
        self.author_cache_model = author_cache_model_class()  # type: ScopusAuthorPickleCacheModel

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
        return list(self.publication_cache_model.content.keys())

    def select_all_author_ids(self):
        return list(self.author_cache_model.content.keys())

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


class ScopusBackupPublicationModel(PublicationPersistencyInterface):

    def __init__(self):

        self.database_access = MySQLDatabaseAccess()

    def execute(self, sql):
        return self.database_access.select(sql)

    def insert(self, publication):
        assert isinstance(publication, ScopusPublication)

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
            'INSERT IGNORE INTO '
            'publications ('
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
            '"{citations}"'
            ');'
        ).format(
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
            'FROM publications WHERE scopus_id={id}'
        ).format(
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

            # TODO: error when no pub found

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
