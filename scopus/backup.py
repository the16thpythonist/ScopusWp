from ScopusWp.database import MySQLDatabaseAccess

from ScopusWp.scopus.data import ScopusPublication

class ScopusBackupModel:

    def __init__(self):

        self.database_access = MySQLDatabaseAccess

    def insert(self, publication):
        assert isinstance(publication, ScopusPublication)

        # Assembling the SQL for the action

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