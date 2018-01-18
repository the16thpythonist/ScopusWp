import json
from unidecode import unidecode

# TODO: Make the to_dict and from_dict accept lists

###############
#  FUNCTIONS  #
###############


def to_dict(obj):
    """
    Turns every object, that implements the DictConversionInterface into a dict.

    :param obj: The scopus data type, that converts into a dict
    :return: a dict object built from the data of the given object
    """
    if issubclass(obj.__class__, DictionaryConversionInterface):
        return obj.to_dict()
    elif isinstance(obj, list):
        dict_list = []
        for item in obj:
            _dict = to_dict(item)
            dict_list.append(_dict)
        return dict_list


def from_dict(scopus_dict):
    """
    Creates a object from the dict, that was created by the DictConversionInterface.

    :param scopus_dict: The dict to create an object from
    :return: An object of the class, that implements a DictConversionInterface
    """
    if isinstance(scopus_dict, dict):
        if 'type' in scopus_dict:
            code_string = (
                '{}.from_dict(scopus_dict)'
            ).format(scopus_dict['type'])
            scopus_object = eval(code_string)

            return scopus_object

    elif isinstance(scopus_dict, list):
        object_list = []
        for dictionary in scopus_dict:
            _object = from_dict(dictionary)
            object_list.append(_object)
        return object_list

###############
#   CLASSES   #
###############


class ScopusIdentifierInterface:
    """
    Interface, that promises, that when implemented the identifier of an object (id) can be acquired by calling an
    integer conversion on the object, or calling the 'get_id' method.
    """
    def get_id(self):
        raise NotImplementedError()

    def __int__(self):
        raise NotImplementedError()


class DictionaryConversionInterface:
    """
    Interface, that promises, that the implementing object can be converted into a dict and also that objects can be
    loaded/ created from such dicts.
    """
    def to_dict(self):
        """
        Supposed to convert all the data stored in the object into a dictionary.

        :return: A dict object
        """
        raise NotImplementedError()

    @staticmethod
    def from_dict(dictionary):
        """
        A static method supposed to be able to load objects of that class from a dictionary object

        :param dictionary: The dict object, containing the data about the construction of an object of that type
        :return: A class of the type, that implements this interface
        """
        raise NotImplementedError()


class ScopusPublication(ScopusIdentifierInterface, DictionaryConversionInterface):
    """
    Object, that represents a publication, that was retrieved from the Scopus database.
    """
    def __init__(self, scopus_id, eid, doi, title, description, date, creator, author_list, citation_list,
                 keyword_list, journal, volume):
        # Init the interfaces
        # ScopusIdentifierInterface.__int__(self)
        DictionaryConversionInterface.__init__(self)

        self.id = scopus_id
        self.eid = eid
        self.doi = doi
        self.title = unidecode(title).replace('"', "'")
        self.description = unidecode(description).replace('"', "'")
        self.date = date
        self.creator = creator
        self.authors = author_list
        self.citations = citation_list
        if '' in self.citations:
            self.citations.remove('')
        self.keywords = list(map(self._rip, keyword_list))
        self.journal = unidecode(journal).replace('"', "'")
        self.volume = volume

    @staticmethod
    def _rip(keyword_string):
        keyword_string = unidecode(keyword_string)
        keyword_string = keyword_string.replace(',', '')
        keyword_string = keyword_string.replace("'", '').replace('"', '')
        return keyword_string

    @property
    def affiliations(self):
        """
        The property, that will return the list of all affiliation ids, which the authors of the publication have.

        :return: A list of int affiliation ids
        """
        affiliation_list = []
        # Looping through the authors and adding all the affiliations, that have not already been added
        for author in self.authors:
            affiliation_list_difference = list(set(author.affiliations) - set(affiliation_list))
            affiliation_list += affiliation_list_difference

        return affiliation_list

    def get_id(self):
        """
        Returns the int scopus id of the publication.

        :return: int id
        """
        return int(self.id)

    def __int__(self):
        """
        Function to convert the object into an integer type. Returns the in scopus id, that identifies the publication.

        :return:The integer scopus id of the publication
        """
        return self.get_id()

    def contains_author(self, scopus_author):
        """
        Whether or not the given author has participated in this publication.

        :param scopus_author: The ScopusAuthor object representing the author, for which to check if he has worked on
            the publication
        :return: boolean
        """
        for author in self.authors:

            # Comparing the id of the author object given with the author objects in the list of authors for the
            # publication.
            if int(author) == int(scopus_author):
                return True

        # Returning False if True has not been returned in any of the previous iterations
        return False

    def contains_keyword(self, keyword):
        """
        Whether or not the publication is tagged with the given keyword.

        :param keyword: The string keyword for which to check the publication
        :return: boolean
        """
        return keyword in self.keywords

    def contains_affiliation(self, affiliation_id):
        """
        Whether ot not the publication is affiliated with the given affiliation id.

        Assembles a list of all different affiliation ids associated with all the authors of the publication and checks
        if the given affiliation id is in this list.
        :param affiliation_id: The int affiliation id to check for
        :return: boolean
        """
        return affiliation_id in self.affiliations

    def to_dict(self):

        author_dict_list = []
        for author in self.authors:
            author_dict = author.to_dict()
            author_dict_list.append(author_dict)

        dictionary = {
            'id': self.id,
            'eid': self.eid,
            'doi': self.doi,
            'title': self.title,
            'description': self.description,
            'date': self.date,
            'journal': self.journal,
            'volume': self.volume,
            'creator': self.creator.to_dict(),
            'keywords': self.keywords,
            'authors': author_dict_list,
            'citations': self.citations
        }
        return dictionary

    @staticmethod
    def from_dict(dictionary):
        if 'type' in dictionary and dictionary['type'] == 'ScopusPublication':
            author_list = []
            for author_dict in dictionary['authors']:
                author = ScopusAuthor.from_dict(author_dict)
                author_list.append(author)

            publication = ScopusPublication(
                dictionary['id'],
                dictionary['eid'],
                dictionary['doi'],
                dictionary['title'],
                dictionary['description'],
                dictionary['date'],
                ScopusAuthor.from_dict(dictionary['creator']),
                author_list,
                dictionary['citations'],
                dictionary['keywords'],
                dictionary['journal'],
                dictionary['volume']
            )
            return publication

        else:
            error_message = (
                'The type of the dict {} is not compatible for a ScopusAuthor conversion'
            ).format(
                str(dictionary)
            )
            raise TypeError(error_message)


class ScopusAuthor(ScopusIdentifierInterface, DictionaryConversionInterface):
    """
    The representation of the Author data saved with a publication, that was retrieved from the scopus database.

    This Author representation only contains very basic information such as the scopus author id, the first name, the
    last name and the list of affiliations. Objects of this kind will only be created from the data of a publication
    retrieval.
    The data for a author varies greatly in the scopus database and one cannot assume to get legitimate information
    from a author retrieval.
    """
    def __init__(self, first_name, last_name, id, affiliation_list):
        # Init the interface
        ScopusIdentifierInterface.__init__(self)
        DictionaryConversionInterface.__init__(self)

        self.id = id
        self.first_name = unidecode(first_name).replace("'", "")
        self.last_name = unidecode(last_name).replace("'", "")
        self.id = id
        self.affiliations = affiliation_list
        if '' in self.affiliations:
            self.affiliations.remove('')

    def get_id(self):
        """
        Returns the int author id of the author.

        :return: int
        """
        return int(self.id)

    def __int__(self):
        """
        Function to convert an object into an integer. Returns the int author id of the author.

        :return: int
        """
        return self.get_id()

    def contains_affiliation(self, affiliation_id):
        """
        Whether the author is affiliated with the given affiliation id.

        :param affiliation_id: The int affiliation id to check for
        :return:
        """
        return int(affiliation_id) in self.affiliations

    def to_dict(self):
        """
        Turns the data inside the object into a dict

        :return: a dict object containing all the data of the object
        """
        dictionary = {
            'type': 'ScopusAuthor',
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'affiliations': self.affiliations
        }
        return dictionary

    @staticmethod
    def from_dict(dictionary):
        """
        Loads a ScopusAuthor object from a dictionary, that has the correct format.

        :param dictionary: The dict to convert into a ScopusAuthor object
        :return: A scopusAuthor object
        """
        if 'type' in dictionary.keys() and dictionary['type'] == 'ScopusAuthor':
            author = ScopusAuthor(
                dictionary['first_name'],
                dictionary['last_name'],
                dictionary['id'],
                dictionary['affiliations']
            )
            return author
        else:
            error_message = (
                'The type of the dict {} is not compatible for a ScopusAuthor conversion'
            ).format(
                str(dictionary)
            )
            raise TypeError(error_message)


class ScopusAuthorProfile(ScopusIdentifierInterface):
    """
    Represents the basic data structure from a scopus author retrieval.
    """
    def __init__(self, author_id, first_name, last_name, h_index, citation_count, document_count, publication_list):
        # Init the reference
        ScopusIdentifierInterface.__init__(self)

        self.id = author_id
        self.first_name = unidecode(first_name).replace("'", '')
        self.last_name = unidecode(last_name).replace("'", '')
        self.h_index = h_index
        if h_index is None:
            self.h_index = 0
        self.citation_count = citation_count
        if citation_count is None:
            self.citation_count = 0
        self.document_count = document_count
        if document_count is None:
            self.document_count = 0
        self.publications = publication_list
        if '' in self.publications:
            self.publications.remove('')

    def get_id(self):
        """
        Returns the int author id of the author.

        :return: int
        """
        return int(self.id)

    def __int__(self):
        """
        Method to convert an object to int. Returns the int author id of the author.

        :return: int
        """
        return self.get_id()

    def contains_publication(self, scopus_publication):
        """
        whether or not the author has contributed to the given publication.

        :param scopus_publication: The ScopusPublication object to check for contribution of the author
        :return: boolean
        """
        for scopus_id in self.publications:
            if scopus_id == int(scopus_publication):
                return True

        return False


class ScopusAffiliation(ScopusIdentifierInterface):
    """
    Represents the basic information about a scopus affiliation retrieval.
    """
    def __init__(self, affiliation_id, country, city, institute):
        # Init the Interface
        ScopusIdentifierInterface.__init__(self)

        self.id = affiliation_id
        self.country = country
        self.city = city
        self.institute = institute

    def get_id(self):
        """
        The int affiliation id.

        :return: int
        """
        return int(self.id)

    def __int__(self):
        """
        The method to convert the object to int. Returns the int affiliation id of the affiliation.

        :return: int
        """
        return self.get_id()


class ScopusAuthorObservation:

    def __init__(self, author_id_list, first_name, last_name, keyword_list, whitelist, blacklist):

        self.ids = author_id_list
        self.first_name = first_name
        self.last_name = last_name
        self.keywords = keyword_list
        self.whitelist = whitelist
        self.blacklist = blacklist

    def whitelist_contains(self, affiliation_id):
        """
        Whether or not the affiliation id is in the affiliation whitelist for that author.

        :param affiliation_id: The int id to check for
        :return: boolean
        """
        try:
            return int(affiliation_id) in self.whitelist
        except ValueError:
            return False

    def whitelist_contains_any(self, affiliation_id_list):
        """
        Whether or not any one of the affiliation ids of the given list is in the whitelist for that author.

        :param affiliation_id_list: A list of int affiliation ids to check
        :return: boolean
        """
        for affiliation_id in affiliation_id_list:
            if self.whitelist_contains(affiliation_id):
                return True
        return False

    def whitelist_check_publication(self, scopus_publication):
        """
        Whether the observed author is author of the given publication and if one of the affiliations of the
        publication is in the affiliation whitelist.

        :param scopus_publication: The ScopusPublication to check
        :return: boolean
        """
        # Checks whether the observed author is actually an author of the given pub and then if any of the affiliations
        # of the author is in the whitelist
        _contains = False
        for id in self.ids:
            if scopus_publication.contains_author(id):
                _contains = True
                break
        return _contains and self.whitelist_contains_any(scopus_publication.affiliations)

    def blacklist_contains(self, affiliation_id):
        """
        Whether the given affiliation id in the affiliation blacklist.

        :param affiliation_id: The int id
        :return: boolean
        """
        try:
            return int(affiliation_id) in self.blacklist
        except ValueError:
            return False

    def blacklist_contains_any(self, affiliation_id_list):
        """
        Whether one of the affiliation ids of the given list is in the blacklist for that author.

        :param affiliation_id_list: A list of affiliation ids to check
        :return: boolean
        """
        for affiliation_id in affiliation_id_list:
            if self.blacklist_contains(affiliation_id):
                return True
        return False

    def blacklist_check_publication(self, scopus_publication):
        """
        Whether the observed author is author of the given publication and if one of the affiliation of the
        publication is in the affiliation blacklist.

        :param scopus_publication: The ScopusPublication to check
        :return: boolean
        """
        # Checks whether the observed author is actually an author of the given pub and then if any of the affiliations
        # of the author is in the blacklist
        _contains = False
        for id in self.ids:
            if scopus_publication.contains_author(id):
                _contains = True
                break
        return _contains and self.blacklist_contains_any(scopus_publication.affiliations)

