import ScopusWp.config as cfg

from wordpress_xmlrpc import Client
from wordpress_xmlrpc import WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost, EditPost

from ScopusWp.repr import Publication
from ScopusWp.repr import Author

from ScopusWp.views import PublicationWordpressPostView

import logging
import urllib.parse as urlparse
import os
import requests
import json

from pprint import pprint

# TODO: generic dict unpacking


class ScopusController:

    COREDATA_KEY_DICT = {
        'title': 'dc:title',
        'description': 'dc:description',
        'eid': 'eid',
        'citation_count': 'citedby-count',
        'author_citation_count': 'cited-by-count',
        'document_count': 'document-count',
        'journal': 'prism:publicationName',
        'volume': 'prism:volume',
        'date': 'prism:coverDate',
        'id': 'dc:identifier',
        'doi': 'prism:doi'
    }

    COREDATA_DEFAULT_DICT = {
        'dc:title': '',
        'dc:description': '',
        'dc:identifier': 0,
        'eid': 0,
        'citedby-count': 0,
        'cited-by-count': 0,
        'document-count': 0,
        'prism:publicationName': '',
        'prism:volume': 0,
        'prism:coverDate': '',
        'prism_doi': ''
    }

    def __init__(self):
        # Getting the config instance for the project
        self.config = cfg.Config.get_instance()

        # Getting the logger for the the scopus part of the project
        scopus_logger_id = cfg.SCOPUS_LOGGING_EXTENSION
        self.logger = logging.getLogger(scopus_logger_id)

        # Getting the base url to the scopus site from the config
        self.url_base = self.config['SCOPUS']['url']

        # Getting the api key from the config
        self.api_key = self.config['SCOPUS']['api_key']

        # Constructing the headers dict from the API key
        self.headers = {
            'Accept': 'application/json',
            'X-ELS-APIKey': self.api_key
        }

    def request_citations_search(self, eid, start=0, count=200):
        query = {
            'query': 'refeid({})'.format(eid),
            'count': str(count),
            'start': str(start)
        }

        response = self.request_search(query)
        return response

    def request_search(self, query):
        # Preparing the url to send the GET request to
        url_base = os.path.join(self.url_base, 'search/scopus')
        url = '{}?{}'.format(url_base, urlparse.urlencode(query))

        response = requests.get(url, headers=self.headers)
        return response

    def request_abstract_retrieval(self, scopus_id):
        # The query which will be added to the url and transmit the serach parameters
        query = {
            'field': ('description,title,authors,authkeywords,publicationName,volume, coverDate,'
                      'eid,citedby-count,doi')
        }

        # Preparing the url to which to send the GET request
        url_base = os.path.join(self.url_base, 'abstract/scopus_id', str(scopus_id))
        url = '{}?{}'.format(url_base, urlparse.urlencode(query))

        # Sending the url request and fetching the response
        response = requests.get(url, headers=self.headers)

        return response

    def request_author_retrieval(self, author_id):
        # The query with the url parameters for all the fields the HTTP response is supposed to contain
        query = {
            'field': 'eid,given-name,surname,h-index,document-count,affiliation-current'
        }

        # Preparing the url to which to send the GET request
        url_base = os.path.join(self.url_base, 'author/author_id', str(author_id))
        url = '{}?{}'.format(url_base, urlparse.urlencode(query))

        # Sending the url request and fetching the response
        response = requests.get(url, headers=self.headers)

        return response

    def request_author_publication_search(self, author_id):
        query = {
            'query': 'AU-ID({})'.format(author_id)
        }

        response = self.request_search(query)
        return response

    def get_publication(self, scopus_ids):

        if isinstance(scopus_ids, int) or isinstance(scopus_ids, str):
            # Converting it into a string
            scopus_id_string = str(scopus_ids)

            # Requesting the abstract retrieval
            response = self.request_abstract_retrieval(scopus_id_string)

            # Extracting the requests response object into the response dictionary
            response_dict = self._extract_response(response)
            # Extracting the authors, keywords and coredata dict from the response dict
            s, coredata_dict, authors_dict, keywords_dict = self._extract_abstract_retrieval_response_dict(response_dict)

            # Extracting the authors dict into a list of author ids
            author_id_list = self._extract_abstract_retrieval_authors_dict(authors_dict)
            # Extracting the keywords dict into a list of string keywords
            keywords_list = self._extract_abstract_retrieval_keywords_dict(keywords_dict)
            # Extracting the coredata dict into another dictionary only containing the most important data
            # using the same keys as the COREDATA_KEYS_DICT
            data_dict = self._extract_abstract_retrieval_coredata_dict(coredata_dict)

            eid = data_dict['eid']
            # Requesting the reference to all the publications, that cited this one
            response = self.request_citations_search(eid)
            response_dict = self._extract_response(response)

            citation_scopus_id_list = self._extract_citation_search_response_dict(response_dict)

            publication = Publication(
                scopus_id_string,
                eid,
                data_dict['doi'],
                author_id_list,
                citation_scopus_id_list,
                keywords_list,
                data_dict['title'],
                data_dict['description'],
                data_dict['citation_count'],
                data_dict['journal'],
                data_dict['volume'],
                data_dict['date']
            )

            return publication

        elif isinstance(scopus_ids, list):
            publication_list = []
            for scopus_id in scopus_ids:
                publication = self.get_publication(scopus_id)
                publication_list.append(publication)

            return publication_list

    def get_author(self, author_ids):

        if isinstance(author_ids, int) or isinstance(author_ids, str):

            author_id_string = str(author_ids)

            # Requesting the author retrieval
            response = self.request_author_retrieval(author_id_string)
            response_dict = self._extract_response(response)

            (
                h_index,
                coredata_dict,
                affiliation_dict,
                name_dict
             ) = self._extract_author_retrieval_response_dict(response_dict)

            # Getting the coredata information
            data_dict = self._extract_author_retrieval_coredata_dict(coredata_dict)
            document_count = data_dict['document_count']
            citation_count = data_dict['citation_count']

            # Getting the affiliation information
            (
                affiliation_country,
                affiliation_city,
                affiliation_name
            ) = self._extract_author_retrieval_affiliation_dict(affiliation_dict)

            # Getting the name information
            first_name, last_name = self._extract_author_retrieval_name_dict(name_dict)

            # Getting the list of the publications
            response = self.request_author_publication_search(author_id_string)
            response_dict = self._extract_response(response)

            publication_scopus_id_list = self._extract_citation_search_response_dict(response_dict)

            # Creating the author object

            author = Author(
                int(author_id_string),
                first_name,
                last_name,
                h_index,
                publication_scopus_id_list,
                citation_count,
                document_count,
                affiliation_country,
                affiliation_city,
                affiliation_name
            )

            return author

        if isinstance(author_ids, list):
            author_list = []

            for author_id in author_ids:
                author = self.get_author(author_id)
                author_list.append(author)

            return author_list

    def _extract_response(self, response):
        # Getting the whole response dict from the encoded json string
        json_dict = json.loads(response.text)

        # Now checking which type of response it is by checking for keys in the dict
        if 'abstracts-retrieval-response' in json_dict:
            response_dict = json_dict['abstracts-retrieval-response']
        elif 'author-retrieval-response' in json_dict:
            response_dict = json_dict['author-retrieval-response'][0]
        elif 'search-results' in json_dict:
            response_dict = json_dict['search-results']
        else:
            # In case it contains neither the result to a author, abstract or search retrieval: Assuming something
            # is wrong, returning an empty dict and writing an error into the logs
            self.logger.error('The response did not contain a valid content: response text: {}'.format(response.text))
            return {}

        # Returning the response dict
        return response_dict

    def _extract_citation_search_response_dict(self, response_dict):
        scopus_id_list = []
        citation_entry_dict_list = response_dict['entry']

        if 'error' in citation_entry_dict_list[0].keys():
            return []

        for citation_entry_dict in citation_entry_dict_list:
            scopus_id = citation_entry_dict['dc:identifier'].replace('SCOPUS_ID:', '')
            scopus_id_list.append(scopus_id)

        return scopus_id_list

    def _extract_author_retrieval_response_dict(self, response_dict):

        # Getting the h index of the author
        if 'h-index' in response_dict.keys():
            h_index = int(response_dict['h-index'])
        else:
            error_message = 'No h index int the author response with the dict: {}'.format(str(response_dict))
            self.logger.warning(error_message)
            h_index = 0

        if 'coredata' in response_dict.keys():
            coredata_dict = response_dict['coredata']
        else:
            error_message = 'No coredata in the author response with the dict: {}'.format(str(response_dict))
            self.logger.warning(error_message)
            coredata_dict = {}

        if 'affiliation-current' in response_dict.keys():
            affiliation_dict = response_dict['affiliation-current']
        else:
            error_message = 'No affiliation in author response with the dict: {}'.format(str(response_dict))
            self.logger.warning(error_message)
            affiliation_dict = {}

        if 'preferred-name' in response_dict.keys():
            name_dict = response_dict['preferred-name']
        else:
            error_message = 'No name in author response with dict: {}'.format(str(response_dict))
            self.logger.warning(error_message)
            name_dict = {}

        return h_index, coredata_dict, affiliation_dict, name_dict

    def _extract_author_retrieval_coredata_dict(self, coredata_dict):
        citation_count = self._get_coredata_item(coredata_dict, 'author_citation_count')
        document_count = self._get_coredata_item(coredata_dict, 'document_count')

        return_dict = {
            'citation_count': int(citation_count),
            'document_count': int(document_count)
        }

        return return_dict

    def _extract_author_retrieval_affiliation_dict(self, affiliation_dict):
        affiliation_city = affiliation_dict['affiliation-city']
        affiliation_country = affiliation_dict['affiliation-country']
        affiliation_name = affiliation_dict['affiliation-name']

        return affiliation_country, affiliation_city, affiliation_name

    def _extract_author_retrieval_name_dict(self, name_dict):
        first_name = name_dict['given-name']
        last_name = name_dict['surname']

        return first_name, last_name

    def _extract_abstract_retrieval_response_dict(self, response_dict):
        # Checking for the core data dict
        if 'coredata' in response_dict.keys():
            coredata_dict = response_dict['coredata']
            # Getting the scopus id from the coredata dict so that this can also be returned
            scopus_id = self._get_coredata_item(coredata_dict, 'id')
        else:
            error_message = 'No coredata in the response with the dictionary: {}'.format(str(response_dict))
            self.logger.warning(error_message)
            coredata_dict = {}
            scopus_id = 0

        # Checking for the keywords dict
        if 'authkeywords' in response_dict.keys():
            keywords_dict = response_dict['authkeywords']
        else:
            error_message = 'No keywords dict in the response with the dictionary: {}'.format(str(response_dict))
            self.logger.warning(error_message)
            keywords_dict = {}

        # Checking the authors dict
        if 'authors' in response_dict.keys():
            authors_dict = response_dict['authors']
        else:
            error_message = 'No keywords dict in the response with the dictionary: {}'.format(str(response_dict))
            self.logger.warning(error_message)
            authors_dict = {}

        return scopus_id, coredata_dict, authors_dict, keywords_dict

    def _extract_abstract_retrieval_keywords_dict(self, keywords_dict):
        """

        :param keywords_dict:
        :return: A list of string keywords
        """
        keyword_list = []
        keywords_entry_dict_list = keywords_dict['author-keyword']

        for keywords_entry_dict in keywords_entry_dict_list:
            keyword = keywords_entry_dict['$']
            keyword_list.append(keyword)

        return keyword_list

    def _extract_abstract_retrieval_authors_dict(self, authors_dict):
        """

        :param authors_dict:
        :return: a list with the author id's
        """
        author_id_list = []
        author_entry_dict_list = authors_dict['author']

        for author_entry_dict in author_entry_dict_list:
            author_id = author_entry_dict['@auid']
            author_id_list.append(author_id)

        return author_id_list

    def _extract_abstract_retrieval_coredata_dict(self, coredata_dict):

        title = self._get_coredata_item(coredata_dict, 'title')
        description = self._get_coredata_item(coredata_dict, 'description')
        citation_count = self._get_coredata_item(coredata_dict, 'citation_count')

        eid = self._get_coredata_item(coredata_dict, 'eid')
        journal = self._get_coredata_item(coredata_dict, 'journal')
        volume = self._get_coredata_item(coredata_dict, 'volume')
        date = self._get_coredata_item(coredata_dict, 'date')
        doi = self._get_coredata_item(coredata_dict, 'doi')

        return_dict = {
            'title': title,
            'description': description,
            'citation_count': citation_count,
            'eid': eid,
            'journal': journal,
            'volume': volume,
            'date': date,
            'doi': doi
        }

        return return_dict

    def _get_coredata_item(self, coredata_dict, key):
        # Checking if the key is heuristic in the way, that is purely descriptional and needs to be mapped to an actual
        # key of the coredata dict structure or if it already is one ofe those keys
        coredata_key, is_native_key = self._get_coredata_key(key)

        if coredata_key in coredata_dict.keys():
            coredata_value = coredata_dict[coredata_key]
            return coredata_value
        else:
            # Getting the default value for the specific key, so that there is being at least SOME sort of data
            # returned
            default_value = self._get_coredata_default(key)

            error_message = 'The coredata dict did not contain data for the key {}'.format(key)
            self.logger.debug(error_message)

            return default_value

    def _get_coredata_default(self, key):
        # Getting the key for the coredata dict structure
        coredata_key, is_native_key = self._get_coredata_key(key)

        # Getting the default value for the according key from the internal dictionary, that maps the keys
        # to their designated default values (in case, there is nothing specified in the response)
        coredata_default = self.COREDATA_DEFAULT_DICT[coredata_key]

        return coredata_default

    def _get_coredata_key(self, key):

        # Checking if the key already is a key of the coredata dict
        if key in self.COREDATA_KEY_DICT.values():
            # In case the key is already a coredata key it is returned just the way it is
            return key, True

        else:
            if key in self.COREDATA_KEY_DICT.keys():
                coredata_key = self.COREDATA_KEY_DICT[key]
                return coredata_key, False
            else:
                error_message = 'The key "{}" is not a valid descriptor for a coredata key'.format(key)
                self.logger.error(error_message)
                raise KeyError(error_message)



class WordpressController:

    def __init__(self):
        # Getting the config instance for the project
        self.config = cfg.Config.get_instance()

        # Getting the logger for the the scopus part of the project
        scopus_logger_id = cfg.SCOPUS_LOGGING_EXTENSION
        self.logger = logging.getLogger(scopus_logger_id)

        # Getting the url path to the xmlrpc.php file from the config file
        self.url = self.config['WORDPRESS']['url']
        # Getting the username and the password for the access to the wordpress api from the config file
        self.username = self.config['WORDPRESS']['username']
        self.password = self.config['WORDPRESS']['password']

        # Creating the client object from the login data
        self.client = Client(self.url, self.username, self.password)

    def post_publication(self, publication, author_list):
        # Creating the view specifically for the wordpress posts
        wp_post_view = PublicationWordpressPostView(publication, author_list)

        post = WordPressPost()

        post.title = wp_post_view.get_title()
        post.excerpt = wp_post_view.get_excerpt()
        post.date = wp_post_view.get_date()
        post.slug = wp_post_view.get_slug()
        post.content = wp_post_view.get_content()

        post.id = self.client.call(NewPost(post))

        post.terms_names = {
            'category': wp_post_view.get_category_list(),
            'post_tag': wp_post_view.get_tag_list()
        }

        post.post_status = 'publish'
        post.comment_status = 'closed'

        self.client.call(EditPost(post.id, post))

        return post.id
