from ScopusWp.config import PATH
from ScopusWp.config import Config

from ScopusWp.database import MySQLDatabaseAccess

from ScopusWp.data import Publication

import datetime

import json
import pathlib

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


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
        """
        Saves the the content dict, which contains the info about the used ids into a json file in the project folder

        :return: void
        """
        with self.path.open(mode='w') as file:
            content_dict = {
                'used': self.used_ids,
                'unused': self.unused_ids,
                'pointer': self.pointer
            }
            json.dump(content_dict, file)

    def new(self):
        """
        Creates and returns a new id to use.

        Updates the created id into the list of used ids directly and increments the pointer, that indicates the amount
        of used ids.
        :return: The int id that has been created
        """
        self.pointer += 1
        self.used_ids.append(self.pointer)
        return self.pointer

    def delete(self, publication_id):
        if publication_id in self.used_ids:
            self.used_ids.remove(publication_id)
            self.unused_ids.append(publication_id)

    def load(self):
        """
        Loads the information about the used ids from the json file in the project folder.

        :return: the dict, that contains the list if used and unused ids as well as the pointer for the amount of ids
        """
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

        self.reference_model = PostReferenceModel()

        self.id_manager = IDManagerSingleton.get_instance()

        # The model for the comment reference model
        self.comment_reference_model = CommentReferenceModel()

    def select_reference(self, internal_id):
        return self.reference_model.select(internal_id)

    def select_all_references(self):
        """
        Returns a list of tuples, where each tuple represents one entry in the reference database, with the first
        item being the internal id for the publication, the second being the wordpress id and the third being the
        scopus id for the publication.

        :return: A list of tuples with three items each
        """
        return self.reference_model.select_all()

    def insert_reference(self, internal_id, wordpress_id, scopus_id):
        self.reference_model.insert(internal_id, wordpress_id, scopus_id)

    def insert_comment_reference(self, internal_id, wordpress_post_id, wordpress_comment_id, scopus_id):
        """
        Inserts a new comment reference into the comment reference database

        :param internal_id: The internally created id for the post
        :param wordpress_post_id: The id of the wordpress post, the comment is added to
        :param wordpress_comment_id: The comment id specifically
        :param scopus_id: The scopus id of the publication on which the comment is based on
        :return: void
        """
        self.comment_reference_model.insert(
            internal_id,
            wordpress_post_id,
            wordpress_comment_id,
            scopus_id
        )

    def select_comment_reference_list_py_post(self, wordpress_post_id):
        """
        Gets a list of all the comment references for the post specified by the wordpress id

        :param wordpress_post_id: The int id of the wordpress post
        :return: [(internal id, post id, comment id, scopus id)]
        """
        return self.comment_reference_model.select_by_wordpress_post_id(wordpress_post_id)

    def insert_publication(self, publication, wordpress_id, scopus_id):
        assert isinstance(publication, Publication)

        self.reference_model.insert(publication.id, wordpress_id, scopus_id)

    def publication_from_scopus(self, scopus_publication):
        # Getting an id from the id manager
        publication_id = self.id_manager.new()

        # Creating the publication object
        publication = Publication.from_scopus_publication(scopus_publication, publication_id)
        return publication

    def select_post_reference_by_scopus(self, scopus_id):
        """
        Select the reference by the scopus id.

        :param scopus_id: The int scopus id
        :return: (internal id, wordpress id, scopus id)
        """
        return self.reference_model.search_by_scopus(scopus_id)

    def select_post_reference_by_wordpress(self, wordpress_post_id):
        """
        Select the reference by the wordpress id of the post.

        :param wordpress_post_id: The int wordpress id
        :return: (internal id, wordpress id, scopus id)
        """
        return self.reference_model.search_by_wordpress(wordpress_post_id)

    def wipe(self):
        self.reference_model.wipe()
        self.comment_reference_model.wipe()
        self.id_manager.used_ids = []
        self.id_manager.pointer = 1

    def save(self):
        self.reference_model.save()

    def close(self):
        self.reference_model.save()
        self.id_manager.save()


# TODO: Think about dependency injection for database access?

class PostReferenceModel:

    def __init__(self):
        self.id_manager = IDManagerSingleton.get_instance()  # type: IDManagerSingleton

        # The actual data base access
        self.database_access = MySQLDatabaseAccess()

        self.config = Config.get_instance()
        self.database_name = self.config['MYSQL']['post_reference_table']

    def wipe(self):
        sql = (
            'TRUNCATE TABLE {database};'
            'COMMIT;'
        ).format(
            database=self.database_name
        )
        self.database_access.execute(sql)

    def update_comments_updated_datetime(self, scopus_id, datetime_object):
        # TODO: Make general and scopus id usable
        sql = (
            'UPDATE {database} '
            'SET '
            'comments_updated_datetime = {comments_updated} '
            'WHERE '
            'scopus_id = {scopus_id}'
        ).format(
            database=self.database_name,
            comments_updated=datetime_object.strftime(DATETIME_FORMAT),
            scopus_id=scopus_id
        )

        self.database_access.execute(sql)

    def save(self):
        self.database_access.save()

    def select_all(self):
        """
        Returns a list of all reference tuples, currently saved in the reference database. A reference tuple contains
        the internal id as the first item, the wordpress id as the second, the scopus id as the third.

        :return: A list of tuples with three items
        """
        sql = (
            'SELECT '
            'internal_id, '
            'wordpress_id,'
            'scopus_id,'
            'comments_updated_datetime '
            'FROM {database} '
        ).format(
            database=self.database_name
        )
        row_list = self.database_access.select(sql)
        return row_list

    def select(self, internal_id):
        sql = (
            'SELECT '
            'internal_id, '
            'wordpress_id,'
            'scopus_id,'
            'comments_updated_datetime '
            'FROM {database} '
            'WHERE id={internal_id}'
        ).format(
            database=self.database_name,
            internal_id=internal_id
        )

        row_list = self.database_access.select(sql)
        return row_list[0]
        # TODO: an if decision if actually exists and possibly exception

    def insert(self, internal_id, wordpress_id, scopus_id):
        sql = (
            'INSERT INTO {database}'
            '('
            'internal_id, '
            'wordpress_id, '
            'scopus_id '
            ')'
            'VALUES'
            '('
            '{internal_id},'
            '{wordpress_id}, '
            '{scopus_id}'
            ') '
            'ON DUPLICATE KEY UPDATE '
            'internal_id = {internal_id},'
            'wordpress_id = {wordpress_id},'
            'scopus_id = {scopus_id};'
            'COMMIT;'
        ).format(
            database=self.database_name,
            internal_id=internal_id,
            wordpress_id=wordpress_id,
            scopus_id=scopus_id
        )

        self.database_access.execute(sql)

    def search_by_wordpress(self, wordpress_id):
        sql = (
            'SELECT '
            'internal_id, '
            'wordpress_id, '
            'scopus_id, '
            'comments_updated_datetime '
            'FROM {database} '
            'WHERE '
            'wordpress_id={wordpress_id}'
        ).format(
            database=self.database_name,
            wordpress_id=wordpress_id
        )

        row_list = self.database_access.select(sql)
        return row_list[0]

    def search_by_scopus(self, scopus_id):
        """
        Searches a reference entry by the scopus id and returns a tuple with the internal id, worpdress id and the
        scopus id

        :param scopus_id: The int scopus id for the post
        :return: (internal id, wordpress id, scopus id)
        """
        sql = (
            'SELECT '
            'internal_id,'
            'wordpress_id,'
            'scopus_id,'
            'comments_updated_datetime '
            'FROM {database} '
            'WHERE '
            'scopus_id={scopus_id}'
        ).format(
            database=self.database_name,
            scopus_id=scopus_id
        )

        row_list = self.database_access.select(sql)
        return row_list[0]


class CommentReferenceModel:

    def __init__(self):

        self.config = Config.get_instance()
        # Getting the database table name for the comment reference table
        self.database_name = self.config['MYSQL']['comment_reference_table']

        self.database_access = MySQLDatabaseAccess()

    def insert(self, internal_id, wordpress_post_id, wordpress_citation_id, scopus_id):
        """
        Inserts a new reference entry into the system.

        :param internal_id: The internal id of the ScopusWp program
        :param wordpress_post_id: The int id of the wordpress post, on which the comment was posted
        :param wordpress_citation_id: The int wordpress id of the comment
        :param scopus_id: The scopus id of the publication, which was posted as the comment
        :return: void
        """
        sql = (
            'INSERT INTO {database}'
            '('
            'internal_id,'
            'wordpress_post_id,'
            'wordpress_comment_id,'
            'scopus_id'
            ')'
            'VALUES'
            '('
            '{internal_id},'
            '{wordpress_post_id},'
            '{wordpress_citation_id},'
            '{scopus_id}'
            ')'
            'ON DUPLICATE KEY UPDATE '
            'internal_id = {internal_id},'
            'wordpress_post_id = {wordpress_post_id},'
            'wordpress_comment_id = {wordpress_citation_id},'
            'scopus_id = {scopus_id};'
            'COMMIT;'
        ).format(
            database=self.database_name,
            internal_id=internal_id,
            wordpress_post_id=wordpress_post_id,
            wordpress_citation_id=wordpress_citation_id,
            scopus_id=scopus_id
        )

        self.database_access.execute(sql)

    def select(self, internal_id):
        """
        A reference tuple selected by its internal id.

        :param internal_id: The int internal id
        :return: (internal id, wordpress post id, wordpress comment id, scopus id)
        """
        sql = (
            'SELECT '
            'internal_id,'
            'wordpress_post_id,'
            'wordpress_comment_id,'
            'scopus_id '
            'FROM {database} '
            'WHERE internal_id={internal_id};'
        ).format(
            database=self.database_name,
            internal_id=internal_id
        )

        row_list = self.database_access.select(sql)

        if len(row_list) != 1:
            # TODO: Think of whether to throw an error or w/e
            pass

        return row_list[0]

    def select_all(self):
        """
        A list with all the reference tuple objects.

        :return: [(internal id, wordpress post id, wordpress comment id, scopus id)]
        """
        sql = (
            'SELECT '
            'internal_id,'
            'wordpress_post_id,'
            'wordpress_comment_id,'
            'scopus_id '
            'FROM {database} '
        ).format(
            database=self.database_name
        )

        row_list = self.database_access.select(sql)

        return row_list

    def select_by_wordpress_post_id(self, wordpress_post_id):
        """
        Gets a specific comment reference tuple, by the wordpress id of the post, on which the comment was posted to.

        :param wordpress_post_id: The int id of the wordpress post.
        :return: (internal id, wordpress post id, wordpress comment id, scopus id)
        """
        sql = (
            'SELECT '
            'internal_id,'
            'wordpress_post_id,'
            'wordpress_comment_id,'
            'scopus_id '
            'FROM {database} '
            'WHERE '
            'wordpress_post_id={wordpress_post_id}'
        ).format(
            database=self.database_name,
            wordpress_post_id=wordpress_post_id
        )

        row_list = self.database_access.select(sql)

        return row_list

    def wipe(self):
        """
        Completely deletes all the entries in the database.

        :return: void
        """
        sql = (
            'TRUNCATE {database};'
            'COMMIT;'
        ).format(
            database=self.database_name
        )

        self.database_access.execute(sql)
