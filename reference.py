from ScopusWp.config import PATH

from ScopusWp.database import MySQLDatabaseAccess

from ScopusWp.data import Publication

import json
import pathlib


class IDManagerInterface:

    def new(self):
        raise NotImplementedError()

    def delete(self, publication_id):
        raise NotImplementedError

    @property
    def all(self):
        raise NotImplementedError()

    @property
    def used(self):
        raise NotImplementedError()

    @property
    def unused(self):
        raise NotImplementedError()


class IDManagerSingleton(IDManagerInterface):

    _instance = None

    def __init__(self):
        self.path_string = '{}/ids.json'.format(PATH)
        self.path = pathlib.Path(self.path_string)

        content_dict = self.load()
        self.used_ids = content_dict['used']
        self.unused_ids = content_dict['unused']
        self.pointer = content_dict['pointer']

    def save(self):
        with self.path.open(mode='w') as file:
            content_dict = {
                'used': self.used_ids,
                'unused': self.unused_ids,
                'pointer': self.pointer
            }
            json.dump(content_dict, file)

    def new(self):
        self.pointer += 1
        return self.pointer

    def delete(self, publication_id):
        if publication_id in self.used_ids:
            self.used_ids.remove(publication_id)
            self.unused_ids.append(publication_id)

    def load(self):
        with self.path.open(mode='r') as file:
            content_dict = json.load(file)
        return content_dict

    @staticmethod
    def get_instance():
        if IDManagerSingleton._instance is None:
            # Creating a new instance
            id_manager = IDManagerSingleton()
            IDManagerSingleton._instance = id_manager
            return id_manager
        else:
            return IDManagerSingleton._instance

    @property
    def all(self):
        return self.used_ids

    @property
    def used(self):
        return self.used_ids

    @property
    def unused(self):
        return self.unused_ids


class ReferenceController:

    def __init__(self):

        self.reference_model = ReferenceModel()
        self.id_manager = IDManagerSingleton.get_instance()

    def select_reference(self, internal_id):
        return self.reference_model.select(internal_id)

    def select_all_references(self):
        return self.reference_model.select_all()

    def insert_reference(self, internal_id, wordpress_id, scopus_id):
        self.reference_model.insert(internal_id, wordpress_id, scopus_id)

    def insert_publication(self, publication, wordpress_id, scopus_id):
        assert isinstance(publication, Publication)

        self.reference_model.insert(publication.id, wordpress_id, scopus_id)

    def publication_from_scopus(self, scopus_publication):
        # Getting an id from the id manager
        publication_id = self.id_manager.new()

        # Creating the publication object
        publication = Publication.from_scopus_publication(scopus_publication, publication_id)
        return publication


# TODO: Think about dependency injection for database access?

class ReferenceModel:

    def __init__(self):
        self.id_manager = IDManagerSingleton.get_instance()  # type: IDManagerSingleton

        # The actual data base access
        self.database_access = MySQLDatabaseAccess()

    def select(self, internal_id):
        sql = (
            'SELECT '
            'id, '
            'wordpress_id, '
            'scopus_id '
            'FROM reference '
            'WHERE id={internal_id}'
        ).format(
            internal_id=internal_id
        )

        row_list = self.database_access.select(sql)
        return row_list[0]
        # TODO: an if decision if actually exists and possibly exception

    def select_all(self):
        sql = (
            'SELECT '
            'id,'
            'wordpress_id,'
            'scopus_id'
            'FROM reference'
        )

        row_list = self.database_access.select(sql)
        return row_list

    def insert(self, internal_id, wordpress_id, scopus_id):
        sql = (
            'INSERT IGNORE INTO '
            'reference ('
            'id, '
            'wordpress_id, '
            'scopus_id)'
            'VALUES ('
            '{internal_id},'
            '{wordpress_id}, '
            '{scopus_id})'
        ).format(
            internal_id=internal_id,
            wordpress_id=wordpress_id,
            scopus_id=scopus_id
        )

        self.database_access.execute(sql)

    def search_by_wordpress(self, wordpress_id):
        pass

    def search_by_scopus(self, scopus_id):
        pass
