import textwrap
import scopus_models


class PublicationPrettyView:

    def __init__(self, publication, line_limit=2000):
        self.publication = publication
        self.line_limit = line_limit


    def get_string(self):

        # The lines list to which every line will be added
        lines_list = []

        title = self.publication.title
        lines_list.append(title)
        lines_list.append('')

        lines_list.append('Published in: {} ({})'.format(self.publication.journal, self.publication.date))
        authors_string_list = []
        for author in self.publication.authors:
            name = '{} {}'.format(author.first_name, author.last_name)
            authors_string_list.append(name)
        authors_string = 'Written by: ' + ', '.join(authors_string_list)

        lines_list += textwrap.wrap(authors_string, self.line_limit)

        lines_list.append('')
        description = self.publication.description
        lines_list += textwrap.wrap(description, self.line_limit)

        lines_list.append('')
        lines_list.append('Cited by:')
        citation_publications = scopus_models.get_publication_list(self.publication.citations)
        for citation_publication in citation_publications:
            title = '{} ({})'.format(citation_publication.title, citation_publication.date)
            lines = textwrap.wrap(title)
            lines[0] = '- ' + lines[0]
            for i in range(1, len(lines)):
                lines[i] = '  ' + lines[i]
            lines.append('')
            lines_list += lines

        temp_string = '\n'.join(lines_list)

        return temp_string


class PublicationBriefView:

    def __init__(self, publication):
        self.publication = publication

    def get_string(self):
        # The lines list to which every line will be added
        lines_list = []

        title = self.publication.title
        lines_list.append(title)
        lines_list.append('')

        description = self.publication.description
        lines_list += textwrap.wrap(description, self.line_limit)

        temp_string = '\n'.join(lines_list)

        return temp_string