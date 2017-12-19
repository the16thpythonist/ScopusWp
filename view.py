import datetime

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
