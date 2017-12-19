from unidecode import unidecode


class Publication:

    def __init__(self, scopus_id, eid, doi, author_list, citation_list, keyword_list, creator, title, description,
                 citation_count, journal, volume, date, affiliation_tuple_list):

        self.id = scopus_id
        self.eid = eid
        self.authors = author_list
        self.citations = citation_list
        self.keywords = keyword_list
        self.title = unidecode(title).replace('"', "'")
        self.description = unidecode(description).replace('"', "'")
        self.citation_count = citation_count
        self.journal = journal.replace('"', "'")
        self.volume = volume
        self.date = date
        self.doi = doi
        self.creator = creator

        self.affiliations = []
        for author in self.authors:
            self.affiliations += list(set(author.affiliations) - set(self.affiliations))

    def basic_equals(self, publication):
        """
        basic comparison only means checking if the two Publication objects describe the same publication by comparing
        the scopus id.

        :param publication: The other Publication object to check, whether based on same publication
        :return: The boolean value of whether or not
        """
        if isinstance(publication, Publication):
            # basic compare only compares if the object describes the same publication, by comparing the scopus id
            return self.id == publication.id
        else:
            return False

    def advanced_equals(self, publication):
        """
        Not impl.
        :param publication:
        :return:
        """
        # Todo: method, that really compares all
        raise NotImplementedError()

    def __int__(self):
        """
        This magic method for when the int() conversion operator is being called on a publication.
        In this case the int scopus id of the publication is being returned.

        :return: The int scopus id
        """
        return int(self.id)


class Author:

    def __init__(self, author_id, first_name, last_name, affiliation_list):
        self.id = author_id
        self.first_name = unidecode(first_name).replace('"', '').replace("'", '')
        self.last_name = unidecode(last_name).replace('"', '').replace("'", '')
        self.affiliations = affiliation_list

    @property
    def index_name(self):
        if len(self.first_name) > 0:
            index_name = '{} {}.'.format(self.last_name, self.first_name[0].upper())
        else:
            index_name = '{}'.format(self.last_name)
        return index_name

    def to_dict(self):
        content_dict = {
            'id': str(self.id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'affiliations': self.affiliations
        }

        return content_dict

    @staticmethod
    def from_dict(dictionary):
        author_id = dictionary['id']
        first_name = dictionary['first_name']
        last_name = dictionary['last_name']
        affiliations = dictionary['affiliations']

        return Author(author_id, first_name, last_name, affiliations)

    def __int__(self):
        """
        This method is called when the int conversion operator is used on the Auhtor obeject.
        Returns the int author id of the Author.

        :return: The int author id
        """
        return int(self.id)


class AuthorProfile:

    def __init__(self, author_id, first_name, last_name, h_index, publication_id_list, citation_count,
                 document_count, affiliation_id, affiliation_country, affiliation_city, affiliation_name):

        self.id = author_id
        self.first_name = unidecode(first_name)
        self.last_name = unidecode(last_name)
        if len(first_name) != 0:
            self.index_name = last_name + ' ' + first_name[0].upper() + '.'
        else:
            self.index_name = ''
        self.h_index = h_index
        self.citation_count = citation_count
        self.publications = publication_id_list
        self.document_count = document_count
        self.affiliation_id = affiliation_id
        self.country = affiliation_country
        self.city = affiliation_city
        self.institute = affiliation_name

    def __int__(self):
        """
        This method will be called, when the int conversion operator is called on the AuhtorProfile object.
        The int author id of the author will be returned.

        :return: The in author id of the author
        """
        return int(self.id)


class AuthorObservation:

    def __init__(self, author_id_list, first_name, last_name, keyword_list, whitelist, blacklist):
        self.ids = author_id_list
        self.first_name = first_name
        self.last_name = last_name
        self.keywords = keyword_list
        self.whitelist = whitelist
        self.blacklist = blacklist

    def check_whitelist(self, affiliation_id_list):
        for affiliation_id in affiliation_id_list:
            if self.in_whitelist(affiliation_id):
                return True
        return False

    def in_whitelist(self, affiliation_id):
        try:
            return int(affiliation_id) in self.whitelist
        except:
            return False

    def check_blacklist(self, affiliation_id_list):
        for affiliation_id in affiliation_id_list:
            if self.in_blacklist(affiliation_id):
                return True
        return False

    def in_blacklist(self, affiliation_id):
        try:
            return int(affiliation_id) in self.blacklist
        except:
            return False


class Affiliation:

    def __init__(self, affiliation_id, country, city, institute):
        self.id = affiliation_id
        self.country = country
        self.city = city
        self.institute = institute

