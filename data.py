
class ScopusPublication:

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
        for author in self.authors:

            # Comparing the id of the author object given with the author objects in the list of authors for the
            # publication.
            if int(author) == int(scopus_author):
                return True

        # Returning False if True has not been returned in any of the previous iterations
        return False

    def contains_keyword(self, keyword):
        return keyword in self.keywords

    def contains_affiliation(self, affiliation_id):
        return affiliation_id in self.affiliations