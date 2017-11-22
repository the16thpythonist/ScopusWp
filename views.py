import datetime


class PublicationWordpressPostView:

    def __init__(self, publication, author_list):

        self.publication = publication
        self.authors = author_list

    def get_title(self):
        # Encoding the title in utf 8
        title_encoded = self.publication.title.encode('utf-8')
        return title_encoded

    def get_date(self):
        date_string = self.publication.date.encode('utf-8')
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
        author_string = self._get_authors_string(20).encode('utf-8')
        journal_string = self.publication.journal.encode('utf-8')
        volume_string = self.publication.volume.encode('utf-8')
        description_string = self.publication.description.encode('utf-8')
        doi_string = self.publication.doi.encode('utf-8')

        content_string = (
            u'<p>{authors}</p>'
            u'<p> in <em>{journal}</em>, {volume}.</p>'
            u'<div class="accordion-inner"><h4>Abstract</h4>{description}</div>\n'
            u'<div class="accordion-inner"><a href="http://dx.doi.org/{doi}" class="btn btn-primary">'
            u'<i class="icon-download icon-white"></i> Get it</a></div>'
        ).format(
            authors=author_string,
            journal=journal_string,
            volume=volume_string,
            description=description_string,
            doi=doi_string
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
                author_string = ', {}'.format(self.authors[index])
                authors_string_list.append(author_string)

        else:
            # In case the list of authors is too long just adding an et al. after the first, most important, author
            authors_string_list.append(' et al.')

        authors_string = ''.join(authors_string_list)
        return authors_string
