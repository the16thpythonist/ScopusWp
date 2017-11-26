
class Publication:

    def __init__(self, scopus_id, eid, doi, author_list, citation_list, keyword_list, creator, title, description,
                 citation_count, journal, volume, date):

        self.id = scopus_id
        self.eid = eid
        self.authors = author_list
        self.citations = citation_list
        self.keywords = keyword_list
        self.title = title
        self.description = description
        self.citation_count = citation_count
        self.journal = journal
        self.volume = volume
        self.date = date
        self.doi = doi
        self.creator = creator


class Author:

    def __init__(self, author_id, first_name, last_name, h_index, publication_id_list, citation_count,
                 document_count, affiliation_country, affiliation_city, affiliation_name):

        self.id = author_id
        self.first_name = first_name
        self.last_name = last_name
        self.index_name = last_name + ' ' + first_name[0].upper() + '.'
        self.h_index = h_index
        self.citation_count = citation_count
        self.publications = publication_id_list
        self.document_count = document_count
        self.country = affiliation_country
        self.city = affiliation_city
        self.institute = affiliation_name
