"""
DEPENDENCIES tabulate, SQLldb
"""

import ScopusWp.config as cfg

from wordpress_xmlrpc import Client
from wordpress_xmlrpc import WordPressPost, WordPressComment
from wordpress_xmlrpc.methods.posts import NewPost, EditPost, GetPost
from wordpress_xmlrpc.methods.comments import NewComment, EditComment

from ScopusWp.repr import Publication
from ScopusWp.repr import Author, AuthorProfile
from ScopusWp.repr import Affiliation

from ScopusWp.models import ObservedAuthorsModel, ScopusBackupModel, CacheModel, WordpressReferenceModel

from ScopusWp.processors import PublicationSetSubtractionProcessor, PostKeywordProcessor

from ScopusWp.views import PublicationWordpressPostView, PublicationWordpressCitationView
from ScopusWp.views import AuthorSimpleView, AffiliationSimpleView, PublicationSimpleView
from ScopusWp.views import AuthorsAffiliationsView, AffiliationTableView
from ScopusWp.views import PublicationTableView

import logging
import urllib.parse as urlparse
import os
import requests
import json

from unidecode import unidecode


from pprint import pprint


class KITOpenController:

    def __init__(self):
        # Getting the config instance for the project
        self.config = cfg.Config.get_instance()

        # Getting the logger for the the scopus part of the project
        scopus_logger_id = cfg.SCOPUS_LOGGING_EXTENSION
        self.logger = logging.getLogger(scopus_logger_id)

        self.url_base = self.config['KITOPEN']['url']

        self.query_base = {
            'referencing': 'all',
            'external_publications': 'all',
            'lang': 'de',
            'format': 'csl_json',
            'style': 'kit-3lines-title_b-authors-other'
        }

    def request_search(self, query):
        total_query = query.update(self.query_base)
        # Preparing the url to which to send the GET request
        url = '{}?{}'.format(self.url_base, urlparse.urlencode(total_query))
        # Sending the url request and fetching the response
        response = requests.get(url)

        return response


class ScopusController:

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

    def request_search(self, query):
        """
        Sends the given query in the form of url encoding to the scopus search api

        :param query: The query dictionary to be used for the url encoding
        :return: The requests.response object of the query
        """
        # Preparing the url to send the GET request to
        url_base = os.path.join(self.url_base, 'search/scopus')
        url = '{}?{}'.format(url_base, urlparse.urlencode(query))

        response = requests.get(url, headers=self.headers)
        return response

    def _get_scopus_id_list(self, search_entry_list):
        """
        Gets a list of scopus ids for the search results represented by the entry dicts, which are the items of the
        search entry list given

        :param search_entry_list: The list of search results, extracted from the response dict of a scopus search
        :return: A list of int scopus ids, one for each publication, that spring up as a result for the search
        """
        scopus_id_list = []
        for search_entry_dict in search_entry_list:
            scopus_id = self._get_scopus_id(search_entry_dict)
            scopus_id_list.append(scopus_id)

        return scopus_id_list

    def _get_scopus_id(self, search_entry_dict):
        """
        Gets the scopus id of a publication, that is a search result represented by the entry dict given.
        (Would also work for the coredata dict of a abstract retrieval)

        :param search_entry_dict: A entry dict, that was part of the list for the search results extracted from the
            response dict of a search result retrieval.
        :return: The scopus id of the publication
        """
        scopus_id_string = self._get_dict_item(search_entry_dict, 'dc:identifier', '')
        scopus_id = scopus_id_string.replace('SCOPUS_ID:', '')

        return scopus_id

    def _extract_search_response_dict(self, response_dict):
        entry_list = self._get_dict_item(response_dict, 'entry', [])

        return entry_list

    def _get_dict_item(self, dictionary, key, default):
        raise NotImplementedError()


class ScopusAffiliationController(ScopusController):

    def __init__(self):
        ScopusController.__init__(self)

        self.current_affiliation_id = None

    def get_affiliation(self, affiliation_id):

        # Requesting the affiliation retrieval and getting the response dict
        response = self.request_affiliation_retrieval(affiliation_id)
        response_dict = self._get_response_dict(response)

        (
            coredata_dict,
            country,
            city,
            institute
        ) = self._extract_affiliation_retrieval(response_dict)

        # Creating the new affiliation representation object
        affiliation = Affiliation(
            affiliation_id,
            country,
            city,
            institute
        )

        return affiliation

    def request_affiliation_retrieval(self, affiliation_id):
        query = {
            'field': 'affiliation-name,city,country'
        }

        # Preparing the url to which to send the GET request
        url_base = os.path.join(self.url_base, 'affiliation/affiliation_id', str(affiliation_id))
        url = '{}?{}'.format(url_base, urlparse.urlencode(query))
        # Sending the url request and fetching the response
        response = requests.get(url, headers=self.headers)

        return response

    def _extract_affiliation_retrieval(self, response_dict):
        country = self._get_dict_item(response_dict, 'country', '')
        city = self._get_dict_item(response_dict, 'city', '')
        institute = self._get_dict_item(response_dict, 'affiliation-name', '')
        coredata_dict = self._get_dict_item(response_dict, 'coredata', {})

        return coredata_dict, country, city, institute

    def _get_response_dict(self, response):
        # Turning the json response text from the requests response into a dict
        try:
            json_dict = json.loads(response.text)
        except Exception as e:
            # In case it contains neither the result to a author, abstract or search retrieval: Assuming something
            # is wrong, returning an empty dict and writing an error into the logs
            error_message = 'The response for the affiliation "{}" was not valid: {}'.format(
                self.current_affiliation_id,
                str(e)
            )
            self.logger.warning(error_message)
            return {}

        # It could be either the response from a abstract retrieval or the response for a search query
        if 'affiliation-retrieval-response' in json_dict.keys():
            response_dict = json_dict['affiliation-retrieval-response']
        else:
            # In case it contains neither the result to a author, abstract or search retrieval: Assuming something
            # is wrong, returning an empty dict and writing an error into the logs
            error_message = 'The response for the affiliation "{}" was not valid: {}'.format(
                self.current_affiliation_id,
                response.text
            )
            self.logger.warning(error_message)
            # Returning an empty dict
            return {}

        # Returning the response dict
        return response_dict

    def _get_dict_item(self, dictionary, key, default):
        if isinstance(dictionary, dict) and key in dictionary.keys():
            return dictionary[key]
        else:
            error_message = 'There is no item to the key "{}" for the affiliation "{}" with the sub dict: {}'.format(
                key,
                self.current_affiliation_id,
                str(dictionary)
            )
            self.logger.warning(error_message)
            # Returning the default value, so that the program can still run in case there was no item in the dict
            return default


class ScopusAuthorController(ScopusController):

    def __init__(self):
        ScopusController.__init__(self)

        self.current_author_id = None

    def get_author(self, author_id):
        # Setting the currently processed author id, for debugging and logging
        self.current_author_id = author_id

        # Requesting the author retrieval and processing the received response into a dict
        response = self.request_author_retrieval(author_id)
        response_dict = self._get_response_dict(response)

        # Extracting the most important data sets from the response dict
        (
            coredata_dict,
            name_dict,
            affiliation_dict,
            h_index
        ) = self._extract_author_response_dict(response_dict)

        # Getting the coredata
        document_count = self._get_coredata(coredata_dict)

        # Getting the name information
        first_name, last_name = self._get_name_data(name_dict)

        # Getting the affiliation data
        (
            affiliation_id,
            country,
            city,
            institute
        ) = self._get_affiliation_data(affiliation_dict)

        # Getting the list of scopus ids for all of the authors publications
        publication_id_list = self.get_publications(author_id)

        author_profile = AuthorProfile(
            author_id,
            first_name,
            last_name,
            h_index,
            publication_id_list,
            0,
            document_count,
            affiliation_id,
            country,
            city,
            institute
        )

        return author_profile

    def get_publications(self, author_id):
        """
        Gets a list with the scopus ids for all the publications, which were (partially) written by the author, whose
        author id was given.

        :param author_id: The author id of the author, whose publications to request
        :return: The list of scopus ids
        """
        # TODO: What to do for multiple authors
        self.current_author_id = author_id

        # Requesting the search for the author and processing the response into a dict
        response = self.request_publications(author_id)
        response_dict = self._get_response_dict(response)

        # Extracting the most important data sets from the response
        entry_list = self._extract_search_response_dict(response_dict)
        publication_id_list = self._get_scopus_id_list(entry_list)

        return publication_id_list

    def request_author_retrieval(self, author_id):
        """
        Requests a Author retrieval for the author, who is identifies by the given author id

        :param author_id: The id of the author, whose data is to be requested
        :return: The requests.response object
        """
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

    def request_publications(self, author_id):
        """
        If given a single author id or a list of author ids, returning a requests.response for a scopus search, that
        contains the information about all the publications.

        :param author_id: # int/str - The author id, for which to request the publications
            # list[int/str] - a list of author ids, of which all publications requested
        :return:
        """
        # Making the process better by using a single request for getting the pubs of multiple authors, instead of
        # having to request anew for each author
        # TODO: If its more than 200, it will not get all the pubs
        search_query_string = ''
        if isinstance(author_id, int) or isinstance(author_id, str):
            search_query_string = 'AU-ID({})'.format(author_id)
        elif isinstance(author_id, list):
            # If the input to the method is a list of author ids making a query string, that connects multiple searches
            # by author id by an OR Operator
            search_query_string_list = []
            for au_id in author_id:
                _temp_string = 'AU-ID({})'.format(au_id)
                search_query_string_list.append(_temp_string)
            search_query_string = ' OR '.join(search_query_string_list)

        query = {
            'query': search_query_string
        }

        response = self.request_search(query)
        return response

    def _get_coredata(self, coredata_dict):
        document_count = self._get_dict_item(coredata_dict, 'document-count', 0)
        return document_count

    def _get_affiliation_data(self, affiliation_dict):
        affiliation_id = self._get_dict_item(affiliation_dict, '@id', '')
        affiliation_country = self._get_dict_item(affiliation_dict, 'affiliation-country', '')
        affiliation_city = self._get_dict_item(affiliation_dict, 'affiliation-city', '')
        affiliation_institute = self._get_dict_item(affiliation_dict, 'affiliation-name', '')

        return affiliation_id, affiliation_country, affiliation_city, affiliation_institute

    def _get_name_data(self, name_dict):
        first_name = self._get_dict_item(name_dict, 'given-name', '')
        last_name = self._get_dict_item(name_dict, 'surname', '')

        return first_name, last_name

    def _extract_author_response_dict(self, response_dict):

        affiliation_dict = self._get_dict_item(response_dict, 'affiliation-current', {})
        coredata_dict = self._get_dict_item(response_dict, 'coredata', {})
        name_dict = self._get_dict_item(response_dict, 'preferred-name', {})
        h_index = self._get_dict_item(response_dict, 'h-index', 0)

        return coredata_dict, name_dict, affiliation_dict, h_index

    def _get_response_dict(self, response):
        """
        Turns the requests.response for a search request or a author retrieval request into a dictionary

        :param response: The requests.response object
        :return: A dict, that contains all the relevant requested information
        """
        # Turning the json response text from the requests response into a dict
        json_dict = json.loads(response.text)

        # It could be either the response from a abstract retrieval or the response for a search query
        if 'author-retrieval-response' in json_dict.keys():
            response_dict = json_dict['author-retrieval-response'][0]
        elif 'search-results' in json_dict:
            response_dict = json_dict['search-results']
        else:
            # In case it contains neither the result to a author, abstract or search retrieval: Assuming something
            # is wrong, returning an empty dict and writing an error into the logs
            error_message = 'The response for the author "{}" was not valid: {}'.format(
                self.current_author_id,
                response.text
            )
            self.logger.warning(error_message)
            # Returning an empty dict
            return {}

        # Returning the response dict
        return response_dict

    def _get_dict_item(self, dictionary, key, default):
        """
        Checks if the dictionary contains a item to the given key and returns that in case, but if there is no key
        a warning will be written in the scopus log and the given default value will be returned.

        :param dictionary: The dict from which to get an item, but unsure if the key really exists
        :param key: The key which to use on the dict
        :param default: The default value for that key, that is returned in case there is no value in the dict
        :return: The value of the dict
        """
        if isinstance(dictionary, dict) and key in dictionary.keys():
            return dictionary[key]
        else:
            error_message = 'There is no item to the key "{}" for the author "{}" with the sub dict: {}'.format(
                key,
                self.current_author_id,
                str(dictionary)
            )
            self.logger.warning(error_message)
            # Returning the default value, so that the program can still run in case there was no item in the dict
            return default


class ScopusPublicationController(ScopusController):

    def __init__(self):
        ScopusController.__init__(self)

        self.current_scopus_id = None

    def request_abstract_retrieval(self, scopus_id):
        """
        Sends a request to the scopus abstract retrieval api, which is supposed to return the detailed information
        about the publication, identified by the given scopus id.

        :param scopus_id: The scopus id of the publication, for which to get the detailed information.
        :return: The requests.response object
        """
        # The query which will be added to the url and transmit the serach parameters
        query = {
            'field': ('description,title,authors,authkeywords,publicationName,volume,coverDate,'
                      'eid,citedby-count,doi,creator,afid,affiliation-name')
        }

        # Preparing the url to which to send the GET request
        url_base = os.path.join(self.url_base, 'abstract/scopus_id', str(scopus_id))
        url = '{}?{}'.format(url_base, urlparse.urlencode(query))

        # Sending the url request and fetching the response
        response = requests.get(url, headers=self.headers)

        return response

    def request_citations_search(self, eid, start=0, count=200):
        """
        Sends a search query to the scopus search api, which is supposed to return all the citations for the
        publication, identified by the given eid.

        :param eid: The string eid identifier of the publication for which to get the citations
        :param start: The start for the search results. Default start at 0
        :param count: The amount of search results to display in a single response. Default 200 results (max.)
        :return: The requests.response
        """
        query = {
            'query': 'refeid({})'.format(eid),
            'count': str(count),
            'start': str(start)
        }

        response = self.request_search(query)
        return response

    def get_publication(self, scopus_id):
        # Setting the scopus id, that is being processed at the moment by the controller for the logging purpose
        self.current_scopus_id = scopus_id

        # Requesting the abstract retrieval for the scopus id and processing the response into a dictionary
        response = self.request_abstract_retrieval(scopus_id)
        response_dict = self._get_response_dict(response)

        # Extracting the main info from the response dict, which are the coredata dict, the
        (
            coredata_dict,
            authors_entry_list,
            keywords_entry_list,
            affiliation_entry_list
        ) = self._extract_abstract_response_dict(response_dict)

        # Getting the coredata information
        (
            title,
            description,
            creator,
            citation_count,
            eid,
            doi,
            journal,
            volume,
            date
        ) = self._get_coredata(coredata_dict)

        # The list of all the author objects for the publication
        author_list = self._get_author_list(authors_entry_list)

        # The keywords of the publication
        keyword_list = self._get_keyword_list(keywords_entry_list)

        # The list of the scopus ids of those publications, that cite this publication
        citation_list = self.get_citations(eid)

        # Creating the publication object from the data
        publication = Publication(
            scopus_id,
            eid,
            doi,
            author_list,
            citation_list,
            keyword_list,
            creator,
            title,
            description,
            citation_count,
            journal,
            volume,
            date,
            []
        )

        return publication

    def get_citations(self, eid):
        """
        gets a list with all the scopus ids of the publications, which cite the one publication given by the eid

        :param eid: The eid of the publication, of which to get the citations
        :return: A list with the int scopus ids of the publications citing the specified publication
        """
        # Requesting the citation search and processing the response into a dictionary
        response = self.request_citations_search(eid)
        response_dict = self._get_response_dict(response)

        # Getting the list of scopus ids for the citing publications
        search_entry_list = self._extract_search_response_dict(response_dict)
        scopus_id_list = self._get_scopus_id_list(search_entry_list)

        return scopus_id_list

    def _get_coredata(self, coredata_dict):
        """
        Extracts all the important coredata information from the given coredata dict

        :param coredata_dict: The coredata dict, which was extracted from the response dict of a abstract retrieval
        :return:
        title - the string title of the publication
        description - the string abstract of the publication
        creator - the Author object for the main creator of the publication
        citation_count - The int amount the publication was cited
        eid - The eid id string
        doi - The doi string
        journal - The string name of the journal in which the publication was published
        volume - The string volume of that journal
        date - the date at which the publication was published. in teh format 'year-month-day'
        """
        title = self._get_dict_item(coredata_dict, 'dc:title', '')
        description = self._get_dict_item(coredata_dict, 'dc:description', '')
        citation_count = int(self._get_dict_item(coredata_dict, 'citedby-count', 0))

        eid = self._get_dict_item(coredata_dict, 'eid', '')
        doi = self._get_dict_item(coredata_dict, 'prism:doi', '')
        journal = self._get_dict_item(coredata_dict, 'prism:publicationName', '')
        volume = self._get_dict_item(coredata_dict, 'prism:volume', '')
        date = self._get_dict_item(coredata_dict, 'prism:coverDate', '0-0-0')

        # Fixed an issue where all tough I am working with the det dict item, that checks and has default value I then
        # just assumed, that there must be a first list item in the creator entry list
        _creator_dict = self._get_dict_item(coredata_dict, 'dc:creator', {})
        _creator_entry_list = self._get_dict_item(_creator_dict, 'author', [])
        _creator_entry_dict = self._get_dict_item(_creator_entry_list, 0, {})
        creator = self._get_author(_creator_entry_dict)

        return title, description, creator, citation_count, eid, doi, journal, volume, date

    def _get_keyword_list(self, keyword_entry_list):
        """
        Creates a list of string keywords from the keyword entry list given

        :param keyword_entry_list: The list of dicts, which was ectracted from the response dict of a abstract
            retrieval response request.
        :return: A list of string keywords for the publication
        """
        keyword_list = []
        for keyword_entry_dict in keyword_entry_list:
            keyword = self._get_dict_item(keyword_entry_dict, '$', '')
            keyword_list.append(keyword)

        return keyword_list

    def _get_author_list(self, author_entry_list):
        """
        Creates a list of Author objects, which contain the information of the author entry dicts from the list of
        all the authors to the publication.

        :param author_entry_list: The list of dict author entries, which was extracted from the response dict of a
            abstract retrieval response.
        :return: A list of Author objects, each one representing one author of the publication
        """
        author_list = []
        for author_entry_dict in author_entry_list:
            author = self._get_author(author_entry_dict)
            author_list.append(author)

        return author_list

    def _get_author(self, author_entry_dict):
        """
        Creating an author object from the author entry dict given.

        :param author_entry_dict: The author entry dict is one item of the author entry list extracted from the
            response dict of a abstract retrieval response
        :return: An Author object containing the relevant information
        """
        # Getting the author id for the author
        author_id = self._get_dict_item(author_entry_dict, '@auid', '')

        # Getting the name info about the author, which is the first name and the last name
        preferred_name_dict = self._get_dict_item(author_entry_dict, 'preferred-name', {})
        first_name = self._get_dict_item(preferred_name_dict, 'ce:given-name', '')
        last_name = self._get_dict_item(preferred_name_dict, 'ce:surname', '')

        # Getting the affiliation list, which is supposed to be a list of all the affiliation ids, with one affiliation
        # id representing a institution, with which the author was affiliated with, during the publication
        affiliation_list = []
        _temp_affiliation = self._get_dict_item(author_entry_dict, 'affiliation', {})
        # If the author only has one affiliation, the value to the key is a entry dict directly, but if the author has
        # multiple it is a list of such entry dicts.
        if isinstance(_temp_affiliation, dict):
            affiliation_id = self._get_dict_item(_temp_affiliation, '@id', '')
            affiliation_list.append(affiliation_id)
        elif isinstance(_temp_affiliation, list):
            for affiliation_entry_dict in _temp_affiliation:
                affiliation_id = self._get_dict_item(affiliation_entry_dict, '@id', '')
                affiliation_list.append(affiliation_id)

        # Creating the Author object from the extracted values
        author = Author(author_id, first_name, last_name, affiliation_list)
        return author

    def _extract_abstract_response_dict(self, response_dict):
        """
        Extracts the response dict for a abstract retrieval response into its most important sub-data structures,
        which are the dict for the coredata to the publication, the list containing the info about all the authors,
        the list for the keywords, the list for the affiliations.

        :param response_dict: The dict, that was extracted from the requests response of an abstract retrieval
            response.
        :return:
        """
        # Getting the coredata dict from the response dict
        coredata_dict = self._get_dict_item(response_dict, 'coredata', {})

        # Getting the list of author entry dicts from the reponse dict
        author_dict = self._get_dict_item(response_dict, 'authors', {})
        author_entry_list = self._get_dict_item(author_dict, 'author', [])

        # Getting the keywords entry list. This is a list, that contains dictionaries, that each contain the
        # information about one keyword, which is associated with one of the authors of the pub
        keyword_dict = self._get_dict_item(response_dict, 'authkeywords', {})
        keyword_entry_dict = self._get_dict_item(keyword_dict, 'author-keyword', [])

        # Getting the list of affiliation entries, which is a list of dicts, that each contain information about one
        # of the publications affiliation institutions
        _temp_affiliation = self._get_dict_item(response_dict, 'affiliation', [])
        if isinstance(_temp_affiliation, dict):
            # If there is only one affiliation for the publication, the value to the affiliation key will be a single
            # entry dict instead of a list of such dicts, but turning this into a list of one item, as not to cause
            # any special cases in further processing of the data
            affiliation_entry_list = [_temp_affiliation]
        else:
            affiliation_entry_list = _temp_affiliation

        return coredata_dict, author_entry_list, keyword_entry_dict, affiliation_entry_list

    def _get_response_dict(self, response):
        """
        converts the requests response object into a dict (JSON)

        :param response: The requests response from either a abstract retrieval or a search query
        :return: The dict containing all the necessary information
        """
        # Getting the whole response dict from the encoded json string
        json_dict = json.loads(response.text)

        # It could be either the response from a abstract retrieval or the response for a search query
        if 'abstracts-retrieval-response' in json_dict.keys():
            response_dict = json_dict['abstracts-retrieval-response']
        elif 'search-results' in json_dict:
            response_dict = json_dict['search-results']
        else:
            # In case it contains neither the result to a author, abstract or search retrieval: Assuming something
            # is wrong, returning an empty dict and writing an error into the logs
            error_message = 'The response for the publication "{}" was not valid: {}'.format(
                self.current_scopus_id,
                response.text
            )
            self.logger.warning(error_message)
            # Returning an empty dict
            return {}

        # Returning the response dict
        return response_dict

    def _get_dict_item(self, dictionary, key, default):
        """
        Checks if the dictionary contains a item to the given key and returns that in case, but if there is no key
        a warning will be written in the scopus log and the given default value will be returned.

        :param dictionary: The dict from which to get an item, but unsure if the key really exists
        :param key: The key which to use on the dict
        :param default: The default value for that key, that is returned in case there is no value in the dict
        :return: The value of the dict
        """
        if isinstance(dictionary, dict) and key in dictionary.keys():
            return dictionary[key]
        elif isinstance(dictionary, list) and key < len(dictionary):
            return dictionary[key]
        else:
            error_message = 'There is no item to the key "{}" in the publication "{}" with the sub dict: {}'.format(
                key,
                self.current_scopus_id,
                str(dictionary)
            )
            self.logger.warning(error_message)
            # Returning the default value, so that the program can still run in case there was no item in the dict
            return default


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

    def post_publication(self, publication, keywords):
        # Creating the view specifically for the wordpress posts
        wp_post_view = PublicationWordpressPostView(publication, keywords)

        post = WordPressPost()

        post.title = wp_post_view.get_title()
        post.excerpt = wp_post_view.get_excerpt()
        # post.date = wp_post_view.get_date()
        post.slug = wp_post_view.get_slug()
        post.content = wp_post_view.get_content()
        post.date = wp_post_view.get_date()

        post.id = self.client.call(NewPost(post))

        post.terms_names = {
            'category': wp_post_view.get_category_list(),
            'post_tag': wp_post_view.get_tag_list()
        }

        post.post_status = 'publish'
        post.comment_status = 'closed'

        self.client.call(EditPost(post.id, post))

        return post.id

    def post_citation(self, wordpress_id, publications, multiple=False):

        if isinstance(publications, list):
            self.enable_comments(wordpress_id)
            # In case there are no multiple post, if the one passed
            comment_id_list = []
            for publication in publications:
                comment_id = self.post_citation(wordpress_id, publication, multiple=True)
                comment_id_list.append(comment_id)

            self.disable_comments(wordpress_id)

        elif isinstance(publications, Publication):
            # In case there are no multiple citations to be added, if its only the one passed post, then adding
            # mod. the comment status of the post locally
            if not multiple:
                self.enable_comments(wordpress_id)

            # Actually posting the comment
            comment = WordPressComment()

            wp_comment_view = PublicationWordpressCitationView(publications)

            comment.content = wp_comment_view.get_content()

            comment_id = self.client.call(NewComment(wordpress_id, comment))

            # Changing the date of the comment
            comment.date_created = wp_comment_view.get_date()
            self.client.call(EditComment(comment_id, comment))

            if not multiple:
                self.disable_comments(wordpress_id)

            return comment_id

    def enable_comments(self, wordpress_id):
        # Getting the Post
        post = self.client.call(GetPost(wordpress_id))

        # Changing the comment status of the post to open
        post.comment_status = 'open'

        self.client.call(EditPost(wordpress_id, post))

    def disable_comments(self, wordpress_id):
        # Getting the post
        post = self.client.call(GetPost(wordpress_id))

        # Changing the comment status
        post.comment_status = 'closed'

        self.client.call(EditPost(wordpress_id, post))


# TODO: when a list of publications is given dont work them all and than print, print after each other
class ScopusWpController:

    def __init__(self):

        # Getting the config instance for the project
        self.config = cfg.Config.get_instance()

        self.logger = logging.getLogger('CONTROLLER')

        # Creating the controllers for the interfacing with the scopus database
        self.scopus_publication_controller = ScopusPublicationController()
        self.scopus_author_controller = ScopusAuthorController()
        self.scopus_affiliation_controller = ScopusAffiliationController()
        # Creating the wordpress controller
        self.wordpress_controller = WordpressController()

        self.observed_author_model = ObservedAuthorsModel()
        self.cache_model = CacheModel()
        self.wordpress_reference_model = WordpressReferenceModel()
        self.backup_model = ScopusBackupModel()

    def close(self):
        self.backup_model.close()

    #####################
    # TOP LEVEL METHODS #
    #####################

    def print_author_affiliations(self, author_list, publication_list):
        info_string = (
            'The following table contains the different affiliation ids that have occurred for the given authors \n'
            'in the given test set of publications:\n'
        )
        print(info_string)

        # Getting the author affiliations view and printing the table, that displays the affiliations that have
        # occurred for the different authors among the sample list of publications
        author_affiliations_view = AuthorsAffiliationsView(author_list, publication_list)
        author_affiliation_table_string = author_affiliations_view.get_string()
        print(author_affiliation_table_string)

        # Getting the list of all the occurred affiliations and printing the info for all of them
        affiliation_id_list = author_affiliations_view.all_affiliations()
        affiliation_list = []
        for affiliation_id in affiliation_id_list:
            affiliation = self.get_affiliation(affiliation_id)
            affiliation_list.append(affiliation)

        affiliation_table_view = AffiliationTableView(affiliation_list)
        affiliation_table_string = affiliation_table_view.get_string()
        print(affiliation_table_string)

        # self.print_affiliations_info(affiliation_list)

    def new_citations(self):
        pass

    def update_publications_wordpress(self):
        # Getting the new publications
        new_publications = self.new_publications()

        # Filtering the publications
        (
            whitelist_publications,
            blacklist_publications,
            remaining_publications
        ) = self.filter_publications(new_publications)

        # Updating the whitelist publications
        for publication in whitelist_publications:
            self.save_publication_backup(publication)
            wordpress_id = self.post_publication(publication)
            self.save_reference(publication, wordpress_id)

    def new_publications(self):
        # Getting all the publications from the backup database (which are the ones currently displayed on the website)
        # and getting all the publications from the cache
        cache_publications = self.all_publications_cache()
        backup_publications = self.all_publication_backup()

        # Getting the publications, that are in the cache, but not in the backup, those are the new ones
        subtraction_processor = PublicationSetSubtractionProcessor(cache_publications, backup_publications)
        new_publications = subtraction_processor.difference

        return new_publications

    ################################
    # WORDPRESS CONTROLLER METHODS #
    ################################

    def post_publication(self, publication):
        """
        Actually posts the given üpublication to the connected wordpress site.
        (Assembles the keywords list from the keywords given to the observed authors)

        :param publication: The publication to be posted as a post
        :return: The int wordpress id of the resulting post
        """
        # Creating the keywords list from the observed authors model and the publication
        post_keyword_processor = PostKeywordProcessor(publication, self.observed_author_model)
        keywords = post_keyword_processor.get_keywords()

        # Posting the publication post to the connected wordpress site and returning the wordpress id of the post
        wordpress_id = self.wordpress_controller.post_publication(publication, keywords)
        return wordpress_id

    def post_citation(self, publication_base, publication_list_cited):
        # Getting the wordpress id for the given publication from the reference database
        wordpress_id = self.get_wordpress_id(publication_base)
        self.wordpress_controller.post_citation(wordpress_id, publication_list_cited)

    #######################################
    # THE SCOPUS DATABASE REQUEST METHODS #
    #######################################

    def get_publication(self, scopus_id):
        """
        Gets a Publication object for the publication, identified by the given scopus id.
        Uses the ScopusPublicationController to send an abstract retrieval request to the scopus server.

        :param scopus_id: The scopus id, of which to get the info
        :return: A Publication object containing all the relevant data of the requested publication
        """
        return self.scopus_publication_controller.get_publication(scopus_id)

    def get_author(self, author_id):
        """
        Gets an AuthorProfile of the author, identified by the given author id.
        Uses the ScopusAuthorController to send an author retrieval request to the scopus server.

        :param author_id: The int id, of the author to retrieve the data from
        :return: An AuthorProfile object, that contains all the relevant data if the author
        """
        return self.scopus_author_controller.get_author(author_id)

    def get_affiliation(self, affiliation_id):
        return self.scopus_affiliation_controller.get_affiliation(affiliation_id)

    ###########################
    # THE CACHE MODEL METHODS #
    ###########################

    def cache_last_modify_time(self):
        """
        pass

        :return: The timestamp of the time, the cache was last modified
        """
        timestamp = self.cache_model.get_modify_timestamp()
        return timestamp

    def cache_publications(self, publication_list):
        """
        Overwrites the cache file with the given publication list.

        :param publication_list: The publications to be saved in the cache
        :return: void
        """
        self.cache_model.save(publication_list)

    def all_publications_cache(self):
        """
        Loads the Cache, which contains the publication list, that was fetched from scopus. Unfiltered all publications
        of the observed authors.

        :return: The list with all the publication objects from the cache
        """
        publication_list = self.cache_model.load()
        return publication_list

    #####################################
    # THE BACKUP DATABASE MODEL METHODS #
    #####################################

    def build_authors(self, author_list):
        """
        For every author in the list: If there is already an entry in the database for that author overrides that, if
        there is not yet an entry creates a new from the AuthorProfile object.

        :param author_list: A list of AuthorProfile objects
        :return: void
        """
        # For every author in the author list trying to create a new entry in the database
        for author in author_list:
            self.print_author_profile(author)
            self.backup_model.insert_author(author)

    def build_publications(self, publication_list):
        """
        For every publication in the list: If there already is an entry in the database for the publication overrides
        that entry, if there is no entry creates a new from the Publication object
        :param publication_list:
        :return:
        """
        for publication in publication_list:
            self.print_publication_info(publication)
            self.backup_model.insert_publication(publication)

    def get_author_backup(self, author_id):
        """
        If given an author id retrieves the data of that author and returns an AuthorProfile object.

        :param author_id: the string or int author id for the author of interest
        :return: AuthorProfile object
        """
        if isinstance(author_id, str) or isinstance(author_id, int):
            author_profile = self.backup_model.get_author(author_id)
            return author_profile
        elif isinstance(author_id, AuthorProfile):
            author_profile = self.get_author_backup(author_id.id)
            return author_profile

    def all_author_backup(self):
        return self.backup_model.get_all_authors()

    def get_publication_backup(self, scopus_id):
        """
        If given a scopus id retrieves the data of that publication and returns the Publication object

        :param scopus_id: The string or int scopus id for the publication of interest
        :return: Publication object
        """
        # In case the passed data is actually a scopus id, calling the according method of the model to get the
        # publication from the backup database
        if isinstance(scopus_id, str) or isinstance(scopus_id, int):
            publication = self.backup_model.get_publication(scopus_id)
            return publication
        elif isinstance(scopus_id, Publication):
            publication = self.get_publication_backup(scopus_id.id)
            return publication

    def all_publication_backup(self):
        return self.backup_model.get_all_publications()

    def save_author_backup(self, author):
        self.backup_model.insert_author(author)

    def save_publication_backup(self, publication):
        self.backup_model.insert_publication(publication)

    def get_wordpress_id(self, publication):
        """
        Getting the wordpress id of the post for the given publication

        :param publication: The Publication object, on which the post was based for which the wordpress id is
            required
        :return: The wordpress id
        """
        wordpress_id = self.wordpress_reference_model.get_wordpress_id(publication)
        return wordpress_id

    def save_reference(self, publication, wordpress_id):
        """
        Saves a new entry in the reference database, that connects the scopus id of the given publication with the
        given wordpress id

        :param publication: The Publication object, which was posted and now be connected with the wordpress id of
            the Post it is in
        :param wordpress_id: The wordpress id of the post of the publication
        :return: void
        """
        scopus_id = int(publication)
        self.wordpress_reference_model.insert_reference(scopus_id, wordpress_id)

    #####################################
    # THE OBSERVED AUTHOR MODEL METHODS #
    #####################################

    def filter_publications(self, publication_list):
        """
        Filters the publications by checking for the observed authors, that contributed if there is a observed author,
        whose affiliations match the whitelist, the publication gets taken. If there is no whitelist match but a
        blacklist match, the publication gets sorted in the second list.
        For all publications, that neither match white nor blacklist, they get sorted into the third,
        "remaining" list.

        :param publication_list: The publications to be sorted by the observed authors
        :return: whitelisted publications, black listed publications, remaining publication list
        """
        return self.observed_author_model.filter(publication_list)

    def get_observed_authors(self, categories=None):
        """
        Gets a list of all the AuthorProfiles for the authors, that are currently being observed

        :param categories: Could be a list of strings, each one a sepcific category of authors, for which to get the
            AuthorProfiles. Defaults to None. If None ALL authors will used.
        :return: A list of AuthorProfile objects
        """
        # Getting the author ids for all the observed authors
        author_id_list = self.observed_author_model.get_observed_authors(categories=categories)

        # Requesting the author retrieval for each one of them
        author_list = []
        for author_id in author_id_list:
            author = self.scopus_author_controller.get_author(author_id)
            author_list.append(author)

        return author_list

    # DISPLAYING METHODS

    def print_affiliations_info(self, affiliation_list):
        for affiliation in affiliation_list:
            self.print_affiliation_info(affiliation)
            print(' ')

    def print_affiliation_info(self, affiliation):
        affiliation_view = AffiliationSimpleView(affiliation)
        affiliation_view_string = affiliation_view.get_string()
        print(affiliation_view_string)

    def print_publications_info(self, publication_list):
        for publication in publication_list:
            self.print_publication_info(publication)

    def print_publication_info(self, publication):
        string = self._get_publication_info_string(publication)
        print(string)

        return string

    def _get_publication_info_string(self, publication):

        publication_view = PublicationSimpleView(publication)
        publication_view_string = publication_view.get_string()
        return publication_view_string

    def print_observed_authors_profile(self):
        observed_authors = self.observed_author_model.get_observed_authors()
        self.print_author_profile(observed_authors)

    def print_author_profile(self, author):

        author_profile_string = self._get_author_profile_string(author)
        print(author_profile_string)

    def _get_author_profile_string(self, author):

        author_profile_view = AuthorSimpleView(author)
        author_profile_view_string = author_profile_view.get_string()
        return author_profile_view_string
