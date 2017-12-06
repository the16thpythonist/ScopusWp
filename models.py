import os
import configparser
import logging

from ScopusWp.repr import Author, Publication, AuthorProfile

from ScopusWp.config import Config, SQL_LOGGING_EXTENSION

import _mysql, MySQLdb
import json

# Getting the absolute path to the folder of this very script file, so that can be used to open the config file, which
# is also located in this folder
PATH = os.path.dirname(os.path.realpath(__file__))


class ObservedAuthorsModel:

    def __init__(self):
        self.path = os.path.join(PATH, 'authors.ini')

        self.source = configparser.ConfigParser()
        self.source.read(self.path)

        self.author_category_dict = {}
        self.category_author_dict = {}

        # Getting the list of tuples, that contain the author id int as the first item and the category string as the
        # second item
        author_tuple_list = self._load_observed_author_tuple_list()
        # Using the tuples to populate the author and category dictionary structures
        for author_tuple in author_tuple_list:
            author_id = author_tuple[0]
            author_category = author_tuple[1]
            self.author_category_dict[author_id] = author_category
            if author_category not in self.category_author_dict.keys():
                self.category_author_dict[author_category] = []

            self.category_author_dict[author_category].append(author_id)

    def _load_observed_author_tuple_list(self):
        tuple_list = []

        for key in self.source.keys():
            # The sub directories contain the scopus ids as the keys and the categories as the values
            for author_id_string in self.source[key].keys():
                category_string = self.source[key][author_id_string]
                author_id = int(author_id_string)
                tuple_list.append((author_id, category_string))

        return tuple_list

    def contains(self, author):
        if int(author.id) in self.author_category_dict.keys():
            return True
        else:
            return False

    def get_categories(self, authors):
        if isinstance(authors, list):
            category_list = []
            for author in authors:
                author_category = self.get_categories(author)
                if author_category not in category_list:
                    category_list.append(author_category)

            return category_list

        elif isinstance(authors, int):
            author_category = self.author_category_dict[authors]
            return author_category

        elif isinstance(authors, Author):
            author_id = authors.id
            author_category = self.author_category_dict[author_id]
            return author_category

    def get_observed_authors(self, categories=None):
        if categories is None:
            # In case there is no special category chosen, all the authors are requested, which is the totality of the
            # keys of the dict that assigns the category string to the author ids
            return list(self.author_category_dict.keys())

        else:
            # Category could be a single string or a list of strings for requesting mulitple categories
            if isinstance(categories, list):
                author_id_list = []
                for category in categories:
                    author_id_list += self.get_observed_authors(category)
                return author_id_list

            elif isinstance(categories, str):
                # For one category there is already a dict, that assigns a list of author ids to a specific category
                return self.category_author_dict[categories]


# Database access singleton
class Db:

    _instance = None

    def __init__(self):
        pass

    @staticmethod
    def get_instance():

        if Db._instance is None:
            config = Config.get_instance()
            database = config['MYSQL']['database']
            username = config['MYSQL']['username']
            password = config['MYSQL']['password']
            connector = MySQLdb.connect(host='localhost', user=username, passwd=password, db=database)
            Db._instance = connector

        return Db._instance


class ScopusBackupModel:

    def __init__(self):
        self.database = Db.get_instance()
        self.cursor = self.database.cursor()

        self.logger = logging.getLogger(SQL_LOGGING_EXTENSION)

    def close(self):
        self.database.commit()
        self.database.close()

        self.logger.debug('The Backup database has been closed and committed')

    def insert_author(self, author):

        # Making the publications string
        publications_string = ','.join(author.publications)

        sql = (
            'INSERT IGNORE INTO authors ('
            'author_id, '
            'first_name, '
            'last_name, '
            'h_index, '
            'citation_count, '
            'document_count, '
            'affiliation_id, '
            'affiliation_country, '
            'affiliation_city, '
            'affiliation_name, '
            'publications ) '
            'VALUES ('
            '{author_id}, '
            '"{first_name}", '
            '"{last_name}", '
            '{h_index}, '
            '{citation_count}, '
            '{document_count}, '
            '{affiliation_id}, '
            '"{affiliation_country}", '
            '"{affiliation_city}", '
            '"{affiliation_name}", '
            '"{publications}");'
        ).format(
            author_id=author.id,
            first_name=author.first_name,
            last_name=author.last_name,
            h_index=author.h_index,
            citation_count=author.citation_count,
            document_count=author.document_count,
            affiliation_id=author.affiliation_id,
            affiliation_country=author.country,
            affiliation_city=author.city,
            affiliation_name=author.institute,
            publications=publications_string
        )
        try:
            self.cursor.execute(sql)
        except Exception as e:
            error_message = 'exception "{}" with the SQL query "{}"'.format(str(e), sql)
            self.logger.error(error_message)

    def get_author(self, author_id):
        sql = (
            'SELECT '
            'author_id, '
            'first_name, '
            'last_name, '
            'h_index, '
            'citation_count, '
            'document_count, '
            'affiliation_id, '
            'affiliation_country, '
            'affiliation_city, '
            'affiliation_name, '
            'publications '
            'FROM authors '
            'WHERE author_id={id};'
        ).format(
            id=author_id
        )

        print(sql)

        self.cursor.execute(sql)
        result = self.cursor.fetchall()

        if len(result) == 1:
            row = result[0]

            author_id = row[0]
            first_name = row[1]
            last_name = row[2]
            h_index = row[3]
            citation_count = row[4]
            document_count = row[5]
            affiliation_id = row[6]
            affiliation_country = row[7]
            affiliation_city = row[8]
            affiliation_name = row[9]

            publications_string = row[10]
            publications = publications_string.replace(' ', '').split(',')

            author = AuthorProfile(
                author_id,
                first_name,
                last_name,
                h_index,
                publications,
                citation_count,
                document_count,
                affiliation_id,
                affiliation_country,
                affiliation_city,
                affiliation_name
            )

            return author

        elif len(result) == 0:
            raise KeyError('There is no author in the backup database with the id "{}"'.format(author_id))

    def get_all_authors(self):

        sql = (
            'SELECT '
            'author_id, '
            'first_name, '
            'last_name, '
            'h_index, '
            'citation_count, '
            'document_count, '
            'affiliation_id, '
            'affiliation_country, '
            'affiliation_city, '
            'affiliation_name, '
            'publications '
            'FROM authors '
        )

        self.cursor.execute(sql)

        author_list = []
        for row in self.cursor:

            author_id = row[0]
            first_name = row[1]
            last_name = row[2]
            h_index = row[3]
            citation_count = row[4]
            document_count = row[5]
            affiliation_id = row[6]
            affiliation_country = row[7]
            affiliation_city = row[8]
            affiliation_name = row[9]

            publications_string = row[10]
            publications = publications_string.replace(' ', '').split(',')

            author = AuthorProfile(
                author_id,
                first_name,
                last_name,
                h_index,
                publications,
                citation_count,
                document_count,
                affiliation_id,
                affiliation_country,
                affiliation_city,
                affiliation_name
            )

            author_list.append(author)

        return author_list

    def get_authors(self, author_ids):
        author_ids_string = self._get_ids_string(author_ids)

        sql = (
            'SELECT '
            'author_id, '
            'first_name, '
            'last_name, '
            'h_index, '
            'citation_count, '
            'document_count, '
            'affiliation_id, '
            'affiliation_country, '
            'affiliation_city, '
            'affiliation_name, '
            'publications, '
            'WHERE author_id IN ({ids})'
        ).format(
            ids=author_ids_string
        )

        author_list = []

        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        for row in results:
            author_id = row[0]
            first_name = row[1]
            last_name = row[2]
            h_index = row[3]
            citation_count = row[4]
            document_count = row[5]
            affiliation_id = row[6]
            affiliation_country = row[7]
            affiliation_city = row[8]
            affiliation_name = row[9]

            publications_string = row[10]
            publications = publications_string.replace(' ', '').split(',')

            author = AuthorProfile(
                author_id,
                first_name,
                last_name,
                h_index,
                publications,
                citation_count,
                document_count,
                affiliation_id,
                affiliation_country,
                affiliation_city,
                affiliation_name
            )

            author_list.append(author)

        return author_list

    def insert_publication(self, publication):

        # Getting the creator JSON string
        creator_content_dict = publication.creator.to_dict()
        creator_json_string = json.dumps(creator_content_dict).replace('"', "'")

        # Getting the JSON string for the authors
        author_content_dict_list = []
        for author in publication.authors:
            author_content_dict = author.to_dict()
            author_content_dict_list.append(author_content_dict)
        authors_json_string = json.dumps(author_content_dict_list).replace('"', "'")

        # Putting the CSV Keywords string
        keywords_string = ';'.join(publication.keywords)

        citations_string = ','.join(publication.citations)

        sql = (
            'INSERT IGNORE INTO publications ( '
            'scopus_id, '
            'eid, '
            'doi, '
            'creator, '
            'title, '
            'description, '
            'citation_count, '
            'journal, '
            'volume, '
            'date, '
            'authors, '
            'keywords, '
            'citations ) '
            'VALUES ('
            '{scopus_id}, '
            '"{eid}", '
            '"{doi}", '
            '"{creator}", '
            '"{title}", '
            '"{description}", '
            '{citation_count}, '
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
            citation_count=publication.citation_count,
            journal=publication.journal,
            volume=publication.volume,
            date=publication.date,
            authors=authors_json_string,
            keywords=keywords_string,
            citations=citations_string
        )

        try:
            self.cursor.execute(sql)
        except Exception as e:
            error_message = 'EXCEPTION "{}" with SQL QUERY "{}"'.format(str(e), sql)
            self.logger.error(error_message)

    def get_publication(self, scopus_id):

        sql = (
            'SELECT '
            'scopus_id, '
            'eid, '
            'doi, '
            'creator, '
            'title, '
            'description, '
            'citation_count, '
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

        self.cursor.execute(sql)

        row = self.cursor.fetchone()
        scopus_id = row[0]
        eid = row[1]
        doi = row[2]
        creator_json_string = row[3].replace("'", '"')
        title = row[4]
        description = row[5]
        citation_count = row[6]
        journal = row[7]
        volume = row[8]
        date = row[9]

        authors_json_string = row[10].replace("'", '"')
        author_content_dict_list = json.loads(authors_json_string)
        author_list = []
        for author_content_dict in author_content_dict_list:
            author = Author.from_dict(author_content_dict)
            author_list.append(author)

        keywords_string = row[11]
        keywords = keywords_string.split(';')

        citations_string = row[12]
        citations = citations_string.split(',')

        creator_content_dict = json.loads(creator_json_string)
        creator = Author.from_dict(creator_content_dict)

        publication = Publication(
            scopus_id,
            eid,
            doi,
            author_list,
            citations,
            keywords,
            creator,
            title,
            description,
            citation_count,
            journal,
            volume,
            date,
            []
        )

        return publication

    def get_all_publications(self):
        sql = (
            'SELECT '
            'scopus_id, '
            'eid, '
            'doi, '
            'creator, '
            'title, '
            'description, '
            'citation_count, '
            'journal, '
            'volume, '
            'date, '
            'authors, '
            'keywords, '
            'citations '
            'FROM publications'
        )

        self.cursor.execute(sql)

        publication_list = []
        for row in self.cursor:
            try:
                scopus_id = row[0]
                eid = row[1]
                doi = row[2]
                creator_json_string = row[3].replace("'", '"')
                title = row[4]
                description = row[5]
                citation_count = row[6]
                journal = row[7]
                volume = row[8]
                date = row[9]

                authors_json_string = row[10].replace('"', '').replace("'", '"')
                author_content_dict_list = json.loads(authors_json_string)
                author_list = []
                for author_content_dict in author_content_dict_list:
                    author = Author.from_dict(author_content_dict)
                    author_list.append(author)

                keywords_string = row[11]
                keywords = keywords_string.split(';')

                citations_string = row[12]
                citations = citations_string.split(',')

                creator_content_dict = json.loads(creator_json_string)
                creator = Author.from_dict(creator_content_dict)

                publication = Publication(
                    scopus_id,
                    eid,
                    doi,
                    author_list,
                    citations,
                    keywords,
                    creator,
                    title,
                    description,
                    citation_count,
                    journal,
                    volume,
                    date,
                    []
                )
                publication_list.append(publication)
            except Exception as e:
                self.logger.error(str(e))

        return publication_list

    def _get_ids_string(self, ids):
        publication_ids_string_list = []
        for publication_id in ids:
            publication_ids_string_list.append(id)
        publication_ids_string = ', '.join(publication_ids_string_list)
        return publication_ids_string
