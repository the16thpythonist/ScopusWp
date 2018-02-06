import datetime
import tabulate
import unidecode
import textwrap

from ScopusWp.data import Publication




def _author_index_name(author_tuple):
    index_name_string = '{} {}.'.format(author_tuple[1], author_tuple[0][0])
    return index_name_string


class PublicationWordpressCommentView:

    def __init__(self, publication):
        self.publication = publication

    def get_content(self):

        author_string = _author_index_name(self.publication.authors[0])
        title_string = self.publication.title

        journal_string = self.publication.journal
        volume_string = self.publication.volume
        doi_string = self.publication.doi

        date_tuple = self.get_date()
        year_string = str(date_tuple.tm_year)

        content_string = (
            u'{author} et al.: '
            u'<a href="http://dx.doi.org/{doi}"><b>{title}</b></a>'
            u' in {journal}, {volume} ({year}).'
        ).format(
            author=author_string,
            doi=doi_string,
            title=title_string,
            journal=journal_string,
            volume=volume_string,
            year=year_string
        )

        return content_string

    def get_date(self):
        date_string = self.publication.date
        date_tuple = datetime.datetime.strptime(date_string, '%Y-%m-%d').timetuple()
        return date_tuple


class PublicationWordpressPostView:

    def __init__(self, publication, keyword_list):
        self.publication = publication  # type: Publication
        self.categories = keyword_list

    def get_title(self):
        # Encoding the title in utf 8
        title_encoded = self.publication.title.encode('utf-8')
        return title_encoded

    def get_date(self):
        date_string = self.publication.date
        date_tuple = datetime.datetime.strptime(date_string, '%Y-%m-%d').timetuple()
        return date_tuple

    def get_slug(self):
        slug_string = str(self.publication.id).encode('utf-8')

        return slug_string

    def get_excerpt(self):

        # Getting the author string
        author_string = self._authors_string(2).encode('utf-8')

        journal_string = self.publication.journal.encode('utf-8')
        volume_string = self.publication.volume.encode('utf-8')
        publication_string = u', in {}, volume {}'.format(journal_string, volume_string)

        excerpt_string = u'{}, in <em>{}</em>, volume: {}'.format(
            author_string,
            journal_string,
            publication_string
        )

        return excerpt_string

    def get_content(self):
        author_string = self._authors_string(20)
        journal_string = self.publication.journal
        volume_string = self.publication.volume
        description_string = self.publication.description
        doi_string = self.publication.doi

        date_tuple = self.get_date()
        year_string = str(date_tuple.tm_year)

        content_string = (
            u'<p>{authors}</p>'
            u'<p> in <em>{journal}</em>, {volume} ({year}). DOI: {doi}</p>'
            u'<div class="accordion-inner"><h4>Abstract</h4>{description}</div>\n'
            u'<div class="accordion-inner"><a href="http://dx.doi.org/{doi}" class="btn btn-primary">'
            u'<i class="icon-download icon-white"></i> Get it</a></div>'
        ).format(
            authors=author_string,
            journal=journal_string,
            volume=volume_string,
            description=description_string,
            doi=doi_string,
            year=year_string
        )

        return content_string

    def get_category_list(self):
        return self.categories

    def get_tag_list(self):
        tag_list = self.publication.tags
        if '' in tag_list:
            tag_list.remove('')
        # Processing the tags, so that there absolutely is no malicious character in there
        tag_list = list(map(lambda x: unidecode.unidecode(x.replace("'", '')), tag_list))
        return tag_list

    def _authors_string(self, max_amount):

        author_count = len(self.publication.authors)

        author_string_list = []

        for index in range(1, author_count):
            author_tuple = self.publication.authors[index]
            author_index_name = _author_index_name(author_tuple)
            author_string = ', {}'.format(author_index_name)
            author_string_list.append(author_string)
            if index == max_amount:
                author_string_list.append(' et al.')
                break

        authors_string = ''.join(author_string_list)
        return authors_string


class ScopusPublicationTableView:

    def __init__(self, publication_list, max_length=40, observed_authors=[]):
        self.publications = publication_list

        self.observed_authors = observed_authors
        self.observing = len(self.observed_authors) != 0

        self.max_length = max_length

    def get_string(self):
        table_list = [['SCOPUS ID', 'TITLE', 'DOI', 'EID', 'AUTHOR IDS', 'AFFILIATION IDS']]
        for publication in self.publications:
            publication_row_list = self._get_row_list(publication)
            table_list.append(publication_row_list)

        table_string = tabulate.tabulate(table_list, tablefmt='fancy_grid')
        return table_string

    def __str__(self):
        return self.get_string()

    def _get_row_list(self, publication):
        """
        Gets the a ordered list of items (scopus id, title , doi, eid, authors, affiliations) that will be used as a
        row in the tabular display of the view.

        :param publication: The publication for which to create the row list
        :return: The list representing the row in the table
        """
        # The publication id
        scopus_id_string = str(int(publication))

        # The first 20~ characters of the title for easier identification
        if len(publication.title) < self.max_length:
            title_string = publication.title
        else:
            title_string = '{}...'.format(publication.title[:self.max_length])

        # The doi and the eid of the paper
        doi_string = publication.doi
        eid_string = publication.eid

        # All the authors of the publication
        authors_string = self._get_authors_string(publication)

        # The affiliations of the publications
        affiliations_string = self._get_affiliations_string(publication)

        row_list = [
            scopus_id_string,
            title_string,
            eid_string,
            doi_string,
            authors_string,
            affiliations_string
        ]

        return row_list

    def _get_authors_string(self, publication):
        """
        Gets the string to be used in the column 'authors' for the row of the given publication.
        If there are authors to be observed only uses the authors of the publication, that are part of the observed
        authors.

        :param publication: The publication for whose row to create the authors string
        :return: The string to be displayed in the authors colum of th row for the given publication
        """
        # In case there is a author list specified to observe
        if self.observing:
            author_id_list = []
            for author in publication.authors:
                if author.id in self.observed_authors:
                    author_id_list.append(str(author.id))
        else:
            author_id_list = list(map(lambda x: str(x.id), publication.authors))

        authors_string = ', '.join(author_id_list)
        authors_string = textwrap.fill(authors_string, self.max_length)

        return authors_string

    def _get_affiliations_string(self, publication):
        """
        Gets the string to be used for the column 'affiliation ids' for the row of the given publication.
        If there are authors to observe, only lists the affiliations from those authors, otherwise all

        :param publication: The publication for whose row to create the string to display
        :return: The string to be displayed in the affiliations column of the row for the given publication
        """
        affiliation_id_list = []
        for author in publication.authors:
            if self.observing:
                if author.id in self.observed_authors:
                    difference = list(set(author.affiliations) - set(affiliation_id_list))
                    affiliation_id_list += difference
            else:
                difference = list(set(author.affiliations) - set(affiliation_id_list))
                affiliation_id_list += difference

        # The affiliations of the publications
        affiliations_string = ', '.join(publication.affiliations)
        affiliations_string = textwrap.fill(affiliations_string, self.max_length)

        return affiliations_string


class AuthorAffiliationTableView:

    def __init__(self, author_affiliation_dict, affiliation_dict, max_length=40):
        self.author_affiliation_dict = author_affiliation_dict
        self.affiliation_dict = affiliation_dict

        self.max_length = max_length

    def get_string(self):
        table_list = [['AUTHOR', 'AUTHOR ID', 'AFFILIATION ID', 'INSTITUTE NAME']]
        table_list += self.get_row_list()

        table_string = tabulate.tabulate(table_list, tablefmt='fancy_grid')
        return table_string

    def get_row_list(self):
        row_list = []
        for author_name_tuple in self.author_affiliation_dict.keys():
            row_list += self.get_rows(author_name_tuple)
        return row_list

    def get_rows(self, author_name_tuple):
        row_list = []
        author_name = ' '.join(author_name_tuple)
        row_list.append([author_name, '', '', ''])
        for author_id, affiliation_id_list in self.author_affiliation_dict[author_name_tuple].items():
            row_list.append(['', author_id, '', ''])
            for affiliation_id in affiliation_id_list:
                affiliation = self.affiliation_dict[affiliation_id]
                row_list.append(['', '', affiliation_id, affiliation.institute])
        return row_list
