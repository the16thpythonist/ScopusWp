class PublicationWordpressPostView:

    def __init__(self, publication, keyword_list):
        self.keywords = keyword_list  # type: list[str]
        self.publication = publication  # type: Publication

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
        year_string = ''
        if not(date_tuple is None):
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
        return self.keywords

    def get_tag_list(self):
        tag_list = self.publication.keywords
        if '' in tag_list:
            tag_list.remove('')
        return tag_list

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

class PublicationWordpressPostView:

    def __init__(self, publication, keyword_list):
        self.publication = publication
        self.keywords = keyword_list

    def
