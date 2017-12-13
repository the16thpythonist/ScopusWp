from ScopusWp.repr import Publication, AuthorObservation
from ScopusWp.models import ObservedAuthorsModel


class PublicationSetSubtractionProcessor:

    def __init__(self, publication_list1, publication_list2):
        self.publications_first = publication_list1
        self.publications_second = publication_list2

        # Getting the lists of publications, which the two sets have in common and the ones, that are the difference
        # in the way of those being in the set one and not in the set two
        common, difference = self.subtract(self.publications_first, self.publications_second)

        self.common = common
        self.difference = difference

    @staticmethod
    def subtract(publication_list1, publication_list2):
        """
        'Substracts' the two publication lists by building two new lists of publications, one that contains all the
        publications from list one, that are also in list two and the other which contains all the publications, that
        are in list one but not in list two.

        :param publication_list1: list one of publications
        :param publication_list2: list two of publications
        :return: common, difference
        common - list of publications from list one, also in list two
        difference - list of publications from list one, not in list two
        """
        # The difference will be calculated as all those publications, that are in set one but not in set two
        common = []
        difference = []
        for publication1 in publication_list1:  # type: Publication
            _contains = False
            for publication2 in publication_list2:  # type: Publication
                # If the two publication objects describe the same publication/ have the same scopus id, the
                # publication from the first set will be added to the common list
                if int(publication1) == int(publication2):
                    _contains = True
                    common.append(publication1)
                    break

            # If the publication is in set one, but not in set two, the publication from set one will be added to the
            # difference list
            if not _contains:
                difference.append(publication1)

        return common, difference


class PostKeywordProcessor:

    def __init__(self, publication, observed_authors_model):
        self.observed_authors_model = observed_authors_model  # type: ObservedAuthorsModel
        self.publication = publication  # type: Publication

    def get_keywords(self):
        """
        Builds a list of all the keywords, that have been given to the observed authors, that have contributed
        to the publication given to the processor.
        Does this by looping through all the authors of the publication, checking if its an observed auhtor and
        adding his keywords to the total list, if they are not already part of rhe list.

        :return: The list of string keywords
        """
        keywords = []
        # Looping through the publications authors and checking if observed author. for observed author getting
        # the keywords and adding them, if not already in the list
        for author in self.publication.authors:
            if author in self.observed_authors_model:
                author_id = int(author)
                author_observation = self.observed_authors_model.author_observation_dict[author_id]
                author_keyword_list = author_observation.keywords

                # Adding the keywords to the total list, if they are not already in there #
                difference = list(set(author_keyword_list) - set(keywords))
                keywords += difference

        # Returning the keywords list
        return keywords
