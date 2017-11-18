import textwrap
import scopus_models


def format_bullet_point(string_list, bullet_point, line_limit):
    string_line_list = []

    # Creating the bullet point string and the whitespaces to be added to all the additional lines, to accommodate to
    # the indent level of the bullet point
    bullet_point_string = ''.join([bullet_point, ' '])
    whitespaces = ' ' * len(bullet_point_string)

    for string in string_list:

        # Formatting each line according to the line limit
        width = line_limit - len(bullet_point_string)
        lines = textwrap.wrap(string, width)
        # Adding the bullet point string to the front of the first wrapper line
        lines[0] = bullet_point_string + lines[0]
        # Adding the whitespace indent to all other lines
        for index in range(1, len(lines)):
            lines[index] = whitespaces + lines[index]
        lines.append('')

        # Adding the temp lines to the list of total lines
        string_line_list += lines

    return '\n'.join(string_line_list)


class PublicationBriefView:

    def __init__(self, publication, line_limit=100):
        self.publication = publication
        self.line_limit = line_limit

    def get_string(self):

        title_string = self._format_title_string()
        published_string = self._format_published_string()
        description_string = self._format_published_string()

        string = (
            '{title}\n'
            '{published}\n\n'
            '{description}'
        ).format(title=title_string,
                 published=published_string,
                 description=description_string)

        return string

    def _format_title_string(self):
        title_string = self.publication.title
        title_string_line_list = textwrap.wrap(title_string, self.line_limit)

        return '\n'.join(title_string_line_list)

    def _format_published_string(self):
        published_string = 'Published in {} ({})'.format(self.publication.journal, self.publication.date)
        published_string_line_list = textwrap.wrap(published_string, self.line_limit)

        return '\n'.join(published_string_line_list)

    def _format_description_string(self):
        description_string = self.publication.description
        description_string_line_list = textwrap.wrap(description_string, self.line_limit)

        return '\n'.join(description_string_line_list)


class PublicationPrettyView(PublicationBriefView):

    def __init__(self, publication, line_limit=100, bullet_point='*'):
        PublicationBriefView.__init__(self, publication, line_limit=line_limit)
        self.bullet_point_style = bullet_point

    def get_string(self):

        title_string = self._format_title_string()
        published_string = self._format_published_string()
        description_string = self._format_description_string()
        authors_string = self._format_authors_string()
        citations_string = self._format_citations_string()

        string = (
            '{title}\n\n'
            '{published}\n'
            '{authors}\n\n'
            '{description}\n\n'
            'cited by:\n'
            '{citations}'
        ).format(title=title_string,
                 published=published_string,
                 authors=authors_string,
                 description=description_string,
                 citations=citations_string)

        return string

    def _format_authors_string(self):
        authors_string_list = []
        for author in self.publication.authors:
            name = '{} {}'.format(author.first_name, author.last_name)
            authors_string_list.append(name)
        authors_string = 'Written by: ' + ', '.join(authors_string_list)
        authors_string_line_list = textwrap.wrap(authors_string, self.line_limit)

        return '\n'.join(authors_string_line_list)

    def _format_citations_string(self):

        # Getting a list with Publication objects from the scopus id's given
        citation_publication_list = scopus_models.get_publication_list(self.publication.citations)
        citation_string_list = []

        for citation_publication in citation_publication_list:
            # For every citation in the list of the papers, that cited the publication a bullet point is created so
            # that even when line wrapped, the strings have the same indent towards side
            string = '{} ({})'.format(citation_publication.title, citation_publication.date)
            citation_string_list.append(string)

        citation_bullet_point_string = format_bullet_point(citation_string_list,
                                                           self.bullet_point_style,
                                                           self.line_limit)

        return citation_bullet_point_string


class AuthorBriefView:

    def __init__(self, author, line_limit=100, bullet_point='*'):
        self.author = author
        self.line_limit = line_limit
        self.bullet_point_style = bullet_point

    def get_string(self):

        publications_string = self._format_publications_string()

        string = (
            '{last_name}, {last_name}\n\n'
            'Publications:\n\n'
            '{publications}'
        ).format(first_name=self.author.first_name.upper(),
                 last_name=self.author.last_name.upper(),
                 publications=publications_string)

        return string

    def _format_publications_string(self):

        # Getting the list of all the publications of the author
        publication_list = self.author.request_publication_list()

        publication_string_list = []
        for publication in publication_list:
            # Creating a PublicationBriefView object for each publication to format it into a string
            publication_brief_view = PublicationBriefView(publication, self.line_limit)
            publication_string = publication_brief_view.get_string()
            publication_string_list.append(publication_string)

        # Formatting the publications into a bullet point list
        publication_bullet_point_string = format_bullet_point(publication_string_list,
                                                              self.bullet_point_style,
                                                              self.line_limit)

        return publication_bullet_point_string
