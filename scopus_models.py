from config import Config, init_logging, SCOPUS_LOGGING_EXTENSION

import os
import logging
import json
import requests
import urllib.parse as urlparse

init_logging()

# The most important Constants
config = Config.get_instance()
API_KEY = config['SCOPUS']['api_key']
URL_BASE = config['SCOPUS']['url']

HEADERS = {
    'Accept': 'application/json',
    'X-ELS-APIKey': API_KEY
}


# TODO: Write a function for automatic dict key checking and log writing

def get_publication_list(scopus_id_list):
    publications = []
    for scopus_id in scopus_id_list:
        temp_publication = Publication.from_scopus_id(scopus_id)
        publications.append(temp_publication)

    return publications


def request_scopus_search(query):
    # Creating the url, which us used to transmit the search query
    url_base = os.path.join(URL_BASE, 'search/scopus')
    url = url_base + '?' + urlparse.urlencode(query)

    # Fetching the response of the request
    response = requests.get(url, headers=HEADERS)

    return response


def request_abstract_retrieval(scopus_id, query):
    logger = logging.getLogger(SCOPUS_LOGGING_EXTENSION)
    logger.info('Requesting abstract retrieval for SCOPUS ID:{}'.format(scopus_id))

    # Preparing the url, to which to send the request to
    url_base = os.path.join(URL_BASE, "abstract/scopus_id", str(scopus_id))
    url = url_base + '?' + urlparse.urlencode(query)
    # Fetching the response of the request
    response = requests.get(url, headers=HEADERS)

    return response


def request_scopus_author_retrieval(author_id, query):
    logger = logging.getLogger(SCOPUS_LOGGING_EXTENSION)
    logger.info('Requesting abstract retrieval for AUTHOR ID:{}'.format(author_id))

    # Creating the url, which is used to transmit the fields to get
    url_base = os.path.join(URL_BASE, 'author/author_id', str(author_id))
    url = url_base + '?' + urlparse.urlencode(query)

    # Fetching the response of the request
    response = requests.get(url, headers=HEADERS)

    return response


def request_citation_search(eid, start):
    logger = logging.getLogger(SCOPUS_LOGGING_EXTENSION)
    logger.info('Requesting citation search for EID:{} starting@{}'.format(eid, start))

    query = {
        'query' : 'refeid({})'.format(eid),
        'count': '200',
        'start': start
    }
    response = request_scopus_search(query)

    return response


def extract_scopus_id_list(search_entry_dict_list):
    scopus_id_list = []
    for search_entry_dict in search_entry_dict_list:
        id_string_raw = search_entry_dict['dc:identifier']
        scopus_id = id_string_raw.replace('SCOPUS_ID:', '')
        scopus_id_list.append(scopus_id)

    return scopus_id_list


def extract_search_result_list(search_entry_dict_list):
    search_result_list = []
    for search_entry_dict in search_entry_dict_list:
        search_result = SearchResult(search_entry_dict)
        search_result_list.append(search_result)

    return search_result_list


class SearchResult:

    def __init__(self, search_result_entry_dict):

        self._dict = search_result_entry_dict

        self.id = self._extract_identifier()
        self.creator = self._extract_creator()
        self.citation_count = self._extract_citation_count()
        self.publication = self._extract_publication()
        self.date = self._extract_cover_date()
        self.title = self._extract_title()

    def _extract_creator(self):
        return self._dict['dc:creator']

    def _extract_citation_count(self):
        return self._dict['citedby-count']

    def _extract_identifier(self):
        id_string_raw = self._dict['dc:identifier']
        id_string = id_string_raw.replace('SCOPUS_ID:', '')
        id = int(id_string)
        return id

    def _extract_title(self):
        return self._dict["dc:title"]

    def _extract_cover_date(self):
        return self._dict["prism:coverDate"]

    def _extract_publication(self):
        aggregation_type = self._dict["prism:aggregationType"]
        name = self._dict["prism:publicationName"]
        volume = int(self._dict["prism:volume"])
        publication_info = {
            'type': aggregation_type,
            'name': name,
            'volume': volume
        }
        return publication_info


class Author:

    def __init__(self, author_id, first_name, last_name):

        self.id = author_id
        self.first_name = first_name
        self.last_name = last_name

    def request_publication_list(self):
        scopus_id_list = self.request_publication_scopus_id_list()
        publications = get_publication_list(scopus_id_list)

        return publications

    def request_publication_scopus_id_list(self):

        publication_list = []
        start = 0

        while True:

            temp_query = {
                'query': 'AU-ID({})'.format(self.id),
                'count': 200,
                'start': start
            }

            temp_response = request_scopus_search(temp_query)
            temp_response_dict = json.loads(temp_response.text)

            total_count = int(temp_response_dict['search-results']['opensearch:totalResults'])

            search_entry_dict_list = temp_response_dict['search-results']['entry']
            temp_scopus_id_list = extract_scopus_id_list(search_entry_dict_list)

            publication_list += temp_scopus_id_list

            if len(publication_list) >= total_count:
                break
            else:
                start = len(publication_list)

        return publication_list

    @staticmethod
    def from_author_id(author_id):
        query = {
            'field': 'eid,given-name,surname'
        }
        response = request_scopus_author_retrieval(author_id, query)
        response_dict = json.loads(response.text)

        author_entry_dict = response_dict['author-retrieval-response']
        first_name = Author._extract_first_name(author_entry_dict)
        last_name = Author._extract_last_name(author_entry_dict)

        author = Author(author_id, first_name, last_name)

        return author

    @staticmethod
    def from_author_entry_dict(author_entry_dict):
        author_id = Author._extract_author_id(author_entry_dict)
        first_name = Author._extract_first_name(author_entry_dict)
        last_name = Author._extract_last_name(author_entry_dict)
        # Creating a new Author object from the information
        author = Author(author_id, first_name, last_name)

        return author

    @staticmethod
    def _extract_author_id(author_entry_dict):
        return int(author_entry_dict["@auid"])

    @staticmethod
    def _extract_first_name(author_entry_dict):
        return author_entry_dict['preferred-name']['ce:given-name']

    @staticmethod
    def _extract_last_name(author_entry_dict):
        return author_entry_dict['preferred-name']['ce:surname']


class Publication:

    def __init__(self, scopus_id, eid, author_list, keyword_list, title, description, citation_list, journal, volume,
                 date):
        self.id = scopus_id
        self.eid = eid
        self.authors = author_list
        self.keywords = keyword_list
        self.title = title
        self.description = description
        self.citations = citation_list
        self.journal = journal
        self.volume = volume
        self.date = date

    @staticmethod
    def from_scopus_id(scopus_id):
        logger = logging.getLogger(SCOPUS_LOGGING_EXTENSION)

        query = {
            "field": 'description,title,authors,authkeywords,publicationName,volume,issueIdentifier,coverDate,'
                     'eid,citedby-count'
        }
        response = request_abstract_retrieval(scopus_id, query)

        response_dict = json.loads(response.text)

        if 'authkeywords' in response_dict['abstracts-retrieval-response']:
            # In case there is a field specifying the keywords to the publication, the keyword list will be built from
            # that dictionary
            keyword_entry_dict_list = response_dict['abstracts-retrieval-response']['authkeywords']['author-keyword']
            keyword_list = Publication._extract_keyword_list(keyword_entry_dict_list)
        else:
            logger.warning('The publication with the SCOPUS ID:{} does not have keywords'.format(scopus_id))
            # If there are no keywords an empty keyword list will be passed to create the Publication object
            keyword_list = []

        author_entry_dict_list = response_dict['abstracts-retrieval-response']['authors']['author']
        coredata_dict = response_dict['abstracts-retrieval-response']['coredata']

        author_list = Publication._extract_author_list(author_entry_dict_list)
        title = Publication._extract_title(coredata_dict)
        description = Publication._extract_description(coredata_dict)
        eid = Publication._extract_eid(coredata_dict)
        citation_count = int(Publication._extract_citation_count(coredata_dict))
        journal = Publication._extract_publication_name(coredata_dict)
        volume = Publication._extract_volume(coredata_dict)
        date = Publication._extract_date(coredata_dict)

        if citation_count > 0:
            citation_list = Publication.get_citation_list(eid)
        else:
            citation_list = []

        # Creating a new Publication object from the data
        publication = Publication(scopus_id, eid, author_list, keyword_list, title, description, citation_list,
                                  journal, volume, date)

        return publication

    @staticmethod
    def get_citation_list(eid):
        citation_scopus_id_list = []
        total_count = None
        start = 0
        while True:
            # Requesting the next set of citation search results
            temp_response = request_citation_search(eid, start)
            temp_response_dict = json.loads(temp_response.text)

            total_count = int(temp_response_dict['search-results']['opensearch:totalResults'])

            search_entry_dict_list = temp_response_dict['search-results']['entry']
            temp_scopus_id_list = Publication._extract_citation_scopus_id_list(search_entry_dict_list)

            citation_scopus_id_list += temp_scopus_id_list

            if len(citation_scopus_id_list) >= total_count:
                break
            else:
                start = len(citation_scopus_id_list)

        return citation_scopus_id_list

    @staticmethod
    def _extract_author_list(author_entry_dict_list):
        author_list = []
        for author_entry_dict in author_entry_dict_list:
            author = Publication._extract_author(author_entry_dict)
            author_list.append(author)

        return author_list

    @staticmethod
    def _extract_author(author_entry_dict):
        # Create a new Author object from the dictionary and return that
        author = Author.from_author_entry_dict(author_entry_dict)

        return author

    @staticmethod
    def _extract_keyword_list(keyword_entry_dict_list):
        keyword_list = []
        for keyword_entry_dict in keyword_entry_dict_list:
            keyword = Publication._extract_keyword(keyword_entry_dict)
            keyword_list.append(keyword)

        return keyword_list

    @staticmethod
    def _extract_citation_search_result_list(search_entry_dict_list):
        search_result_list = []
        for search_entry_dict in search_entry_dict_list:
            search_result = SearchResult(search_entry_dict)
            search_result_list.append(search_result)

        return search_result_list

    @staticmethod
    def _extract_citation_scopus_id_list(search_entry_dict_list):
        scopus_id_list = []
        search_result_list = Publication._extract_citation_search_result_list(search_entry_dict_list)
        for search_result in search_result_list:
            scopus_id = search_result.id
            scopus_id_list.append(scopus_id)

        return scopus_id_list

    @staticmethod
    def _extract_keyword(keyword_entry_dict):
        return keyword_entry_dict['$']

    @staticmethod
    def _extract_title(coredata_dict):
        return coredata_dict['dc:title']

    @staticmethod
    def _extract_description(coredata_dict):
        return coredata_dict['dc:description']

    @staticmethod
    def _extract_publication_name(coredata_dict):
        return coredata_dict['prism:publicationName']

    @staticmethod
    def _extract_issue(coredata_dict):
        return coredata_dict['prism:issueIdentifier']

    @staticmethod
    def _extract_volume(coredata_dict):
        return coredata_dict["prism:volume"]

    @staticmethod
    def _extract_date(coredata_dict):
        return coredata_dict['prism:coverDate']

    @staticmethod
    def _extract_citation_count(coredata_dict):
        return coredata_dict['citedby-count']

    @staticmethod
    def _extract_eid(coredata_dict):
        return coredata_dict['eid']