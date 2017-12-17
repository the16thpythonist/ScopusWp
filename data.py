
class ScopusPublication:
    """
    Object, that represents a publication, that was retrieved from the Scopus database.
    """
    def __init__(self, scopus_id, eid, doi, title, description, date, creator, author_list, citation_list,
                 keyword_list, journal, volume):

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

    def __int__(self):
        """
        Function to convert the object into an integer type. Returns the in scopus id, that identifies the publication.

        :return:The integer scopus id of the publication
        """
        return int(self.id)

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