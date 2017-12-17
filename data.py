class ScopusIdentifierInterface:
    """
    Interface, that promises, that when implemented the identifier of an object (id) can be acquired by calling an
    integer conversion on the object, or calling the 'get_id' method.
    """
    def get_id(self):
        raise NotImplementedError()

    def __int__(self):
        raise NotImplementedError()


class ScopusPublication(ScopusIdentifierInterface):
    """
    Object, that represents a publication, that was retrieved from the Scopus database.
    """
    def __init__(self, scopus_id, eid, doi, title, description, date, creator, author_list, citation_list,
                 keyword_list, journal, volume):
        # Init the interfaces
        ScopusIdentifierInterface.__int__(self)

        self.id = scopus_id
        self.eid = eid
        self.doi = doi
        self.title = title
        self.description = description
        self.date = date
        self.creator = creator
        self.authors = author_list
        self.citations = citation_list
        self.keywords = keyword_list
        self.journal = journal
        self.volume = volume

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


class ScopusAuthor(ScopusIdentifierInterface):
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

        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.id = id
        self.affiliations = affiliation_list

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


class ScopusAuthorProfile(ScopusIdentifierInterface):

    def __init__(self, author_id, first_name, last_name, h_index, citation_count, document_count, publication_list):
        # Init the reference
        ScopusIdentifierInterface.__init__(self)

        self.id = author_id
        self.first_name = first_name
        self.last_name = last_name
        self.h_index = h_index
        self.citation_count = citation_count
        self.document_count = document_count
        self.publications = publication_list

    def get_id(self):
        return int(self.id)

    def __int__(self):
        return self.get_id()

    def contains_publication(self, scopus_publication):
        for scopus_id in self.publications:
            if scopus_id == int(scopus_publication):
                return True

        return False

