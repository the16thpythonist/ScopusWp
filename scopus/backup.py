from ScopusWp.database import MySQLDatabaseAccess

from ScopusWp.scopus.data import ScopusPublication
from ScopusWp.scopus.data import from_dict, to_dict

import json





class ScopusBackupPublicationModel:

    def __init__(self):

        self.database_access = MySQLDatabaseAccess

    def execute(self, sql):
        return self.database_access.select(sql)

    def insert(self, publication):
        assert isinstance(publication, ScopusPublication)

        # Converting all the data so it fits into a database data column

        # Turning the creator ScopusAuthor object into a json string
        creator_dict = to_dict(publication.creator)
        creator_json_string = json.dumps(creator_dict)

        # Turning the authors list, list of ScopusAuthor objects into a json string
        author_dict_list = to_dict(publication.authors)
        authors_json_string = json.dumps(author_dict_list)

        # Turning the keywords list and the citations list of str/int into a json object
        keywords_json_string = json.dumps(publication.keywords)
        citations_json_string = json.dumps(publication.citations)

        sql = (
            'INSERT IGNORE INTO '
            'publications ('
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
            'VALUES '
            '({scopus_id}, '
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

        if len(row_list != 0):
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

            keywords_json_string = row[10]
            keywords_list = json.loads(keywords_json_string)

            citations_json_string = row[11]
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