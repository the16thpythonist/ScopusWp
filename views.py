import datetime
import textwrap
import tabulate

from ScopusWp.repr import Author, AuthorProfile, Affiliation
from ScopusWp.repr import Publication


class AuthorsAffiliationsView:

    def __init__(self, author_list, publication_list, max_width=60):
        self.max_width = max_width

        self.publications = publication_list
        self.authors = author_list

        self.author_ids = []
        # The dict, that is supposed to contain the author ids as the key and a list of all the occurring
        # affiliation ids as the value
        self.affiliation_dict = {}
        for author in self.authors:
            self.author_ids.append(author.id)
            self.affiliation_dict[author.id] = []

        for publication in self.publications:
            for author in publication.authors:
                author_id = int(author.id)
                if author_id in self.author_ids:
                    difference = list(set(author.affiliations) - set(self.affiliation_dict[author_id]))
                    if '' in difference:
                        difference.remove('')
                    self.affiliation_dict[author_id] += difference

    def get_string(self):
        """
        The string is a tabular display of three columns: The author id, the name of the author and the affiliation
        ids, which have occurred in the given pool of publications, with each of the given authors being one row of
        the table

        :return: the string
        """
        table_list = [['AUTHOR IDS', 'AUTHOR INDEX NAME', 'AFFILIATION IDS']]

        # Getting the row lists for all the authors
        for author in self.authors:
            author_row_list = self._get_row_list(author)
            table_list.append(author_row_list)

        table_string = tabulate.tabulate(table_list, tablefmt='fancy_grid')
        return table_string

    def all_affiliations(self):
        affiliation_list = []
        for author in self.authors:
            difference = list(set(self[author]) - set(affiliation_list))
            affiliation_list += difference

        return affiliation_list

    def _get_row_list(self, author):
        """
        Gets the a ordered list of items (author id, indexed name, affiliations) that will be used as a row in the
        tabular display of the view.

        :param author: The Author for which to produce the row
        :return: The list acting as the table row
        """
        # Getting the string for the author id
        author_id_string = str(author.id)

        # Getting the name string
        name_string = author.index_name

        # Getting the string for the affiliation ids
        affiliation_id_list = self[author]
        affiliations_string = ', '.join(affiliation_id_list)
        affiliations_string = textwrap.fill(affiliations_string, self.max_width)

        row_list = [
            author_id_string,
            name_string,
            affiliations_string
        ]

        return row_list

    def __getitem__(self, item):
        """
        If given the author, will return the list of affiliations, that was created for him.

        :param item: Author, AuthorProfile for the author directly or str int for the author id
        :return: The list of affiliation ids that have occurred for that author in all the publications
        """
        if isinstance(item, Author) or isinstance(item, AuthorProfile):
            return self.affiliation_dict[item.id]
        elif isinstance(item, str) or isinstance(item, int):
            return self.affiliation_dict[str(item)]

    def __contains__(self, item):
        """
        If checked with a Author representation object, will return whether or not the author is part of the authors
        that are being searched for.
        If checked with a Publication object, will return whether that publication is part of the pubs that the
        authors are bing processed with.

        :param item: Publication, Author, AuthorProfile
        :return: The boolean value if the object is part of this processing
        """
        if isinstance(item, Author) or isinstance(item, AuthorProfile):
            return item.id in self.author_ids
        elif isinstance(item, Publication):
            # Since for the publications there is no much sense in maintaining an extra list for the scopus ids,
            # checking for all the publications in the list
            for publication in self.publications:
                # The basic equals method checks if the object describe the same publication, by comparing the
                # scopus ids
                if publication.basic_equals(item):
                    return True
            return False


class AffiliationTableView:

    def __init__(self, affiliation_list, max_width=40):
        self.affiliations = affiliation_list
        self.max_width = max_width

    def get_string(self):
        table_list = [['AFFIL. IDS', 'COUNTRY', 'CITY', 'INSTITUTE']]

        for affiliation in self.affiliations:
            affiliation_row_list = self._get_row_list(affiliation)
            table_list.append(affiliation_row_list)

        table_string = tabulate.tabulate(table_list, tablefmt='fancy_grid')
        return table_string

    def _get_row_list(self, affiliation):
        # Normalizing the strings to the maximum length
        country_string = textwrap.fill(affiliation.country, self.max_width)
        city_string = textwrap.fill(affiliation.city, self.max_width)
        institute_string = textwrap.fill(affiliation.institute, self.max_width)

        row_list = [
            affiliation.id,
            country_string,
            city_string,
            institute_string
        ]

        return row_list


class PublicationTableView:

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

    def _get_row_list(self, publication):
        """
        Gets the a ordered list of items (scopus id, title , doi, eid, authors, affiliations) that will be used as a
        row in the tabular display of the view.

        :param publication: The publication for which to create the row list
        :return: The list representing the row in the table
        """
        # The publication id
        scopus_id_string = str(publication.id)

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
                    author_id_list.append(author.id)
        else:
            author_id_list = list(map(lambda x: x.id, publication.authors))

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


class PublicationWordpressCitationView:

    def __init__(self, publication):
        self.publication = publication

    def get_content(self):

        author_string = self.publication.creator.index_name
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

    def __init__(self, publication):

        self.publication = publication

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
        author_string = self._get_authors_string(2).encode('utf-8')

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
        author_string = self._get_authors_string(20)
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
        # TODO: implement the category list function
        return ['Publication', 'algorithms']

    def get_tag_list(self):
        return self.publication.keywords

    def _get_authors_string(self, max_amount):
        first_author_string = self.publication.authors[0].index_name
        authors_string_list = [first_author_string]

        author_count = len(self.publication.authors)
        if author_count < max_amount:
            # Adding all the author names to one long string
            for index in range(1, author_count):
                author_string = ', {}'.format(self.publication.authors[index].index_name)
                authors_string_list.append(author_string)

        else:
            # In case the list of authors is too long just adding an et al. after the first, most important, author
            authors_string_list.append(' et al.')

        authors_string = ''.join(authors_string_list)
        return authors_string


class AffiliationSimpleView:

    def __init__(self, affiliation):
        self.affiliation = affiliation

    def get_string(self):

        string = (
            'AFFILIATION\n'
            '   id:         {id}\n'
            '   country:    {country}\n'
            '   city:       {city}\n'
            '   institute:  {institute}'
        ).format(
            id=self.affiliation.id,
            country=self.affiliation.country,
            city=self.affiliation.city,
            institute=self.affiliation.institute
        )

        return string


class PublicationSimpleView:

    def __init__(self, publication, width=120, indent=14):
        self.publication = publication

        self.indent = indent
        self.wrapper = textwrap.TextWrapper(width=width, initial_indent='', subsequent_indent=' ' * self.indent)

    def get_string(self):

        # TODO: clean up with the fill operation istead of wrap
        author_string = ', '.join(map(lambda x: x.index_name, self.publication.authors))
        # author_string = '\n'.join(self.wrapper.wrap(author_string))
        author_string = self.wrapper.fill(author_string)

        description_string = '\n'.join(self.wrapper.wrap(self.publication.description))
        title_string = '\n'.join(self.wrapper.wrap(self.publication.title))

        affiliation_string = self._get_affiliations_string()

        author_profiles = self._get_authors_string()

        string = (
            'PUBLICATION\n'
            '    id:       {id}\n'
            '    title:    {title}\n'
            '    authors:  {authors}\n'
            '    description:\n'
            '{indent}'
            '{description}\n'
            '    keywords: {keywords}\n'
            '    journal:  {journal}\n'
            '    date:     {date}\n'
            '    Affiliations:\n\n'
            '{affil}\n'
            '    Authors:\n'
            '{profiles}'
        ).format(
            id=str(self.publication.id),
            title=title_string,
            authors=author_string,
            description=description_string,
            indent=' ' * self.indent,
            keywords=' - ',
            journal=self.publication.journal,
            date=self.publication.date,
            affil=affiliation_string,
            profiles=author_profiles
        )

        return string

    def _get_authors_string(self):
        authors_string_list = []
        for author in self.publication.authors:
            _author_string = (
                '{indent}Author:\n'
                '{indent}   id:             {auid}\n'
                '{indent}   first name:     {first}\n'
                '{indent}   last name:      {last}\n'
                '{indent}   affiliations:   {affid}\n'
            ).format(
                indent=self.indent * ' ',
                auid=author.id,
                first=author.first_name,
                last=author.last_name,
                affid=', '.join(author.affiliations)
            )
            authors_string_list.append(_author_string)

        authors_string = '\n'.join(authors_string_list)
        return authors_string

    def _get_affiliations_string(self):
        affiliation_string_list = []
        for affiliation_id in self.publication.affiliations:
            temp_affiliation_string =(
                '{indent}Affil.:\n'
                '{indent}   id:     {id}\n'
            ).format(
                indent=self.indent * ' ',
                id=affiliation_id
            )

            affiliation_string_list.append(temp_affiliation_string)

        affiliation_string = '\n'.join(affiliation_string_list)
        return affiliation_string


class AuthorSimpleView:

    def __init__(self, author):
        self.author = author

    def get_string(self):
        string = (
            'AUTHOR PROFILE\n'
            '   author id:   {auid}\n'
            '   first name:  {first}\n'
            '   last name:   {last}\n'
            '   affiliation details:\n'
            '       id:        {affid}\n'
            '       country:   {country}\n'
            '       city:      {city}\n'
            '       institute: {institute}\n'
            '   h-index:     {index}\n'
            '   cited count: {cited}\n'
            '   pub. count:  {pubs}'
        ).format(
            auid=self.author.id,
            first=self.author.first_name,
            last=self.author.last_name,
            affid=self.author.affiliation_id,
            country=self.author.country,
            city=self.author.city,
            institute=self.author.institute,
            index=self.author.h_index,
            cited=self.author.citation_count,
            pubs=self.author.document_count
        )

        return string
