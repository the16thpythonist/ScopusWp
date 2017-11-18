import textwrap
import scopus_models


def format_bullet_point(string_list, bullet_point, line_limit):
    string_line_list = []

    # Creating the bullet point string and the whitespaces to be added to all the additional lines, to accommodate to
    # the indent level of the bullet point
    bullet_point_string = ''.join(['', bullet_point])
    whitespaces = ' ' * len(bullet_point_string)

    for string in string_list:

        # Formatting each line according to the line limit
        lines = textwrap.wrap(string, line_limit - len(bullet_point_string))
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

        string_lines_list = []

        string_lines_list.append(self._format_title_string())
        string_lines_list.append(self._format_published_string())

        string_lines_list.append('')

        string_lines_list.append(self._format_description_string())

        string_lines_list.append('')

        return '\n'.join(string_lines_list)

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
        description_string_line_list = textwrap.wrap(description_string)

        return '\n'.join(description_string_line_list)


class PublicationPrettyView(PublicationBriefView):

    def __init__(self, publication, line_limit=100, bullet_point='*'):
        self.publication = publication
        self.line_limit = line_limit
        self.bullet_point_style = bullet_point

    def get_string(self):

        string_lines_list = []

        string_lines_list.append(self._format_title_string())

        string_lines_list.append('')

        string_lines_list.append(self._format_published_string())
        string_lines_list.append(self._format_authors_string())

        string_lines_list.append('')

        string_lines_list.append(self._format_description_string())

        string_lines_list.append('')

        string_lines_list.append(self._format_citations_string())

        print()

        return '\n'.join(string_lines_list)

    def _format_authors_string(self):
        authors_string_list = []
        for author in self.publication.authors:
            name = '{} {}'.format(author.first_name, author.last_name)
            authors_string_list.append(name)
        authors_string = 'Written by: ' + ', '.join(authors_string_list)
        authors_string_line_list = textwrap.wrap(authors_string)

        return '\n'.join(authors_string_line_list)

    def _format_citations_string(self):
        citations_string_line_list = ['Cited by:']

        # Getting a list with Publication objects from the scopus id's given
        citation_publication_list = scopus_models.get_publication_list(self.publication.citations)

        for citation_publication in citation_publication_list:
            # For every citation in the list of the papers, that cited the publication a bullet point is created so
            # that even when line wrapped, the strings have the same indent towards side
            title = '{} ({})'.format(citation_publication.title, citation_publication.date)
            lines = textwrap.wrap(title)
            # Adding the bullet point to the start of the first line, if the lines were wrapped
            bullet_point_string = self.bullet_point_style + ' '
            lines[0] = bullet_point_string + lines[0]
            # Adding the same indent
            for index in range(1, len(lines)):
                # Adding so many whitespaces to the additional lines, to accommodate them to the same level of indent
                # as the line with the bullet point
                whitespaces = ' ' * len(bullet_point_string)
                lines[index] = whitespaces + lines[index]
            lines.append('')

            # Adding the temp lines for a single citation bullet point to the lines list for the whole string
            citations_string_line_list += lines

        return '\n'.join(citations_string_line_list)


class AuthorBriefView:

    def __init__(self, author):
        pass