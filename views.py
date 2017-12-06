import datetime
import textwrap
import tabulate


class PublicationObservedView:

    def __init__(self, publication_list, observed_authors_model, max_length=40):
        # TODO: rework the contains method
        self.publications = publication_list
        self.observed_authors_model = observed_authors_model
        self.max_length = max_length

        # The list, which will contain all the affiliation ids, that have occurred for the observed authors in the
        # given list of publications
        self.affiliations = []

    def get_table_string(self):
        table_list = [['SCOPUS ID', 'TITLE', 'AUTHOR IDS', 'AFFILIATION IDS']]

        for publication in self.publications:
            publication_row_list = self._get_row_list(publication)
            table_list.append(publication_row_list)

        table_string = tabulate.tabulate(table_list, tablefmt='fancy_grid')

        return table_string

    def _all_affiliations_observed_authors(self):
        for publication in self.publications:
            for author in publication.authors:
                pass

    def _get_row_list(self, publication):
        # The publication id
        scopus_id_string = str(publication.id)

        # The first 20~ characters of the title for easier identification
        if len(publication.title) < self.max_length:
            title_string = publication.title
        else:
            title_string = '{}...'.format(publication.title[:self.max_length])

        # Getting only those author ids, which are among the observed authors
        author_list = []
        author_id_list = []
        for author in publication.authors:
            if self.observed_authors_model.contains(author):
                author_list.append(author)
                author_id_list.append(author.id)
        authors_string = ', '.join(author_id_list)
        authors_string = textwrap.fill(authors_string, self.max_length)

        # Getting only the affiliation ids of the observed authors
        affiliation_id_list = []
        for author in author_list:
            affiliation_id_list += list(set(author.affiliations) - set(affiliation_id_list))
            self.affiliations += list(set(affiliation_id_list) - set(self.affiliations))
        affiliations_string = ', '.join(affiliation_id_list)
        affiliations_string = textwrap.fill(affiliations_string, self.max_length)

        row_list = [
            scopus_id_string,
            title_string,
            authors_string,
            affiliations_string
        ]

        return row_list


class PublicationTableView:
    def __init__(self, publication_list, max_length=40):
        self.publications = publication_list
        self.max_length = max_length

    def get_string(self):
        table_list = [['SCOPUS ID', 'TITLE', 'DOI', 'EID', 'AUTHOR IDS', 'AFFILIATION IDS']]
        for publication in self.publications:
            publication_row_list = self._get_row_list(publication)
            table_list.append(publication_row_list)

        table_string = tabulate.tabulate(table_list, tablefmt='fancy_grid')
        return table_string

    def _get_row_list(self, publication):
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
        author_id_list = map(lambda x: x.id, publication.authors)
        authors_string = ', '.join(author_id_list)
        authors_string = textwrap.fill(authors_string, self.max_length)

        # The affiliations of the publications
        affiliations_string = ', '.join(publication.affiliations)
        affiliations_string = textwrap.fill(affiliations_string, self.max_length)

        row_list = [
            scopus_id_string,
            title_string,
            eid_string,
            doi_string,
            authors_string,
            affiliations_string
        ]

        return row_list

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

    def __init__(self, publication, author_list):

        self.publication = publication
        self.authors = author_list

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
        first_author_string = self.authors[0].index_name
        authors_string_list = [first_author_string]

        author_count = len(self.authors)
        if author_count < max_amount:
            # Adding all the author names to one long string
            for index in range(1, author_count):
                author_string = ', {}'.format(self.authors[index].index_name)
                authors_string_list.append(author_string)

        else:
            # In case the list of authors is too long just adding an et al. after the first, most important, author
            authors_string_list.append(' et al.')

        authors_string = ''.join(authors_string_list)
        return authors_string


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
            '    Authors:'
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
