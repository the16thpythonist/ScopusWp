class Publication:

    def __init__(self, id, title, description, date, doi, author_list, tag_list, journal, volume):
        self.id = id
        self.tags = tag_list
        self.title = title
        self.description = description
        self.date = date
        self.doi = doi
        self.authors = author_list
        self.journal = journal
        self.volume = volume

    @staticmethod
    def from_scopus_publication(scopus_publication, publication_id):
        author_list = []
        for author in scopus_publication.authors:
            author_tuple = (author.first_name, author.last_name)
            author_list.append(author_tuple)

        publication = Publication(
            publication_id,
            scopus_publication.title,
            scopus_publication.description,
            scopus_publication.date,
            scopus_publication.doi,
            author_list,
            scopus_publication.keywords,
            scopus_publication.journal,
            scopus_publication.volume
        )
        return publication
