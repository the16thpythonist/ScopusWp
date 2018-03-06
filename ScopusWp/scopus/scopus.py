from ScopusWp.scopus.data import ScopusPublication, ScopusAuthor, ScopusAffiliation, ScopusAuthorProfile

import ScopusWp.config as cfg

import logging
import urllib.parse as urlparse
import requests
import json
import os

import pprint


class ScopusBaseController:
    """
    Abstract base class for all the specific scopus controllers.
    """
    def __init__(self):
        # Getting the config instance for the project
        self.config = cfg.Config.get_instance()

        # Getting the logger for the the scopus part of the project
        scopus_logger_id = cfg.SCOPUS_LOGGING_EXTENSION
        self.logger = logging.getLogger('scopus')

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
        print(url)

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
        """
        Given the response dict for a scopus search, gives the entry list.

        :param response_dict: The response dict from a search result.
        :return: list of entry dicts
        """
        entry_list = self._get_dict_item(response_dict, 'entry', [])

        return entry_list

    def _get_dict_item(self, dictionary, key, default):
        raise NotImplementedError()

    def _log(self, string):
        raise NotImplementedError()


class ScopusAffiliationController(ScopusBaseController):

    def __init__(self):
        ScopusBaseController.__init__(self)

        self.current_affiliation_id = None

    def get_affiliation(self, affiliation_id):
        """
        If given the affiliation id sends a affiliation retrieval request to scopus and builds a ScopusAffiliation
        object from the response.

        :param affiliation_id: The int affiliation id for which to get the info
        :return: The ScopusAffiliation object built from the scopus db info
        """
        self.logger.info('AFFILIATION REQUEST FOR {}'.format(affiliation_id))
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
        affiliation = ScopusAffiliation(
            affiliation_id,
            country,
            city,
            institute
        )

        return affiliation

    def request_affiliation_retrieval(self, affiliation_id):
        """
        Sends a affiliation retrieval request to the scopus database.

        :param affiliation_id: The affiliation id of which to retrieve the data
        :return: The requests.Response object
        """
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
        """
        Extracts the response dict of a affiliation retrieval into the coredata dict, the country, city and institute
        name of the affiliation.

        :param response_dict: The dict for the response
        :return: void
        """
        country = self._get_dict_item(response_dict, 'country', '')
        city = self._get_dict_item(response_dict, 'city', '')
        institute = self._get_dict_item(response_dict, 'affiliation-name', '')
        coredata_dict = self._get_dict_item(response_dict, 'coredata', {})

        return coredata_dict, country, city, institute

    def _get_response_dict(self, response):
        """
        Gets the dict, that contains all the relevant data from the given requests response object.

        First json loads the requests response object into a dict and then gets the sub dict, that actually contains
        the data, returns that.
        :param response: The requests Response object
        :return: dict
        """
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
        """
        Gets the value of the given dict for the given key. If there is a complication returns the value default
        instead.

        Also this method logs, whenever a complication occurs.
        :param dictionary: The dict for which to attempt to call the key on
        :param key: The key which to use on the dict
        :param default: The default value, that will be returned, when there is a complication with the dict/key
        :return:
        """
        if isinstance(dictionary, dict) and key in dictionary.keys():
            return dictionary[key]
        else:
            error_message = 'There is no item to the key "{}" for the affiliation "{}"'.format(
                key,
                self.current_affiliation_id,
            )
            self.logger.warning(error_message)
            # Returning the default value, so that the program can still run in case there was no item in the dict
            return default

    def _log(self, string):
        pass


class ScopusAuthorController(ScopusBaseController):

    def __init__(self):
        ScopusBaseController.__init__(self)

        self.current_author_id = None

    def get_author(self, author_id):
        self.logger.info('AUTHOR REQUEST FOR "{}"'.format(author_id))
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
        ) = self._extract_author_retrieval(response_dict)

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

        author_profile = ScopusAuthorProfile(
            author_id,
            first_name,
            last_name,
            h_index,
            0,
            document_count,
            publication_id_list
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

        # Creating a new author publication fetcher object to get all the publications of an author
        author_publication_fetcher = ScopusAuthorPublicationFetcher(author_id)
        scopus_id_list = author_publication_fetcher.fetch()

        return scopus_id_list

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
        pprint.pprint(json.loads(response.text))
        return response

    def _get_coredata(self, coredata_dict):
        """
        Given the coredata dict, this method will extract the document count from it

        :param coredata_dict: The coredata dict from the response dict
        :return: int
        """
        document_count = self._get_dict_item(coredata_dict, 'document-count', 0)
        return document_count

    def _get_affiliation_data(self, affiliation_dict):
        affiliation_id = self._get_dict_item(affiliation_dict, '@id', '')
        affiliation_country = self._get_dict_item(affiliation_dict, 'affiliation-country', '')
        affiliation_city = self._get_dict_item(affiliation_dict, 'affiliation-city', '')
        affiliation_institute = self._get_dict_item(affiliation_dict, 'affiliation-name', '')

        return affiliation_id, affiliation_country, affiliation_city, affiliation_institute

    def _get_name_data(self, name_dict):
        """
        Given the name dict of the response dict, returns first name and last name of author

        :param name_dict: The dict containing the name data from the response dict
        :return:
        """
        first_name = self._get_dict_item(name_dict, 'given-name', '')
        last_name = self._get_dict_item(name_dict, 'surname', '')

        return first_name, last_name

    def _extract_author_retrieval(self, response_dict):
        """
        extracts the response dict from the author retrieval and returns the coredata dict, the name dict, the
        affiliation dict and the h index of the author.

        :param response_dict: The response dict of the author retrieval request
        :return: dict, dict, dict, int
        """
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
            error_message = 'There is no item to the key "{}" for the author "{}"'.format(
                key,
                self.current_author_id,
            )
            self.logger.warning(error_message)
            # Returning the default value, so that the program can still run in case there was no item in the dict
            return default


class ScopusPublicationController(ScopusBaseController):

    def __init__(self):
        ScopusBaseController.__init__(self)

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
        print(url)

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
        self.logger.info('PUBLICATION REQUEST FOR "{}"'.format(scopus_id))
        # Setting the scopus id, that is being processed at the moment by the controller for the logging purpose
        self.current_scopus_id = scopus_id

        # Requesting the abstract retrieval for the scopus id and processing the response into a dictionary
        response = self.request_abstract_retrieval(scopus_id)
        response_dict = self._get_response_dict(response)

        publication = self._publication_from_response_dict(response_dict, scopus_id)
        return publication

    def _publication_from_response_dict(self, response_dict, scopus_id):
        # Extracting the main info from the response dict, which are the coredata dict, the
        (
            coredata_dict,
            authors_entry_list,
            keywords_entry_list,
            affiliation_entry_list
        ) = self._extract_abstract_retrieval(response_dict)

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
        publication = ScopusPublication(
            scopus_id,
            eid,
            doi,
            title,
            description,
            date,
            creator,
            author_list,
            citation_list,
            keyword_list,
            journal,
            volume
        )

        return publication

    def get_citation_publications(self, eid):
        # Requesting the citation search and processing the response into a dictionary
        response = self.request_citations_search(eid)
        pprint.pprint(json.loads(response.text))
        response_dict = self._get_response_dict(response)

        # Getting the list of scopus ids for the citing publications
        search_entry_list = self._extract_search_response_dict(response_dict)

        publication_list = []
        for search_entry_dict in search_entry_list:
            scopus_id = self._get_scopus_id(search_entry_dict)
            if scopus_id != '':
                publication = self._publication_from_response_dict(search_entry_dict, scopus_id)
                publication_list.append(publication)

        return publication_list

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
        date = self._get_dict_item(coredata_dict, 'prism:coverDate', '')

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
        author = ScopusAuthor(first_name, last_name, author_id, affiliation_list)
        return author

    def _extract_abstract_retrieval(self, response_dict):
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

        # Getting the list of author entry dicts from the response dict
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
            value = dictionary[key]
            if value is None:
                return default
            else:
                return dictionary[key]
        elif isinstance(dictionary, list) and key < len(dictionary):
            return dictionary[key]
        else:
            error_message = 'There is no item to the key "{}" in the publication "{}"'.format(
                key,
                self.current_scopus_id,
            )
            self.logger.warning(error_message)
            # Returning the default value, so that the program can still run in case there was no item in the dict
            return default


class ScopusController:
    """
    The top controller for everything that has to do with requesting from the scopus database
    """
    def __init__(self):

        self.publication_controller = ScopusPublicationController()
        self.author_controller = ScopusAuthorController()
        self.affiliation_controller = ScopusAffiliationController()

    def get_publication(self, scopus_id):
        """
        Gets the ScopusPublication object to the scopus id from the scopus database

        :param scopus_id: The int id of the publication
        :return: The ScopusPublication object, representing the publication
        """
        return self.publication_controller.get_publication(scopus_id)

    def get_multiple_publications(self, scopus_id_list):
        """
        Gets a list of publication objects to a list of scopus ids.

        :param scopus_id_list: The list of int scopus ids for which to retrieve the publication data
        :return: A list of ScopusPublication objects
        """
        publication_list = []
        for scopus_id in scopus_id_list:
            publication = self.get_publication(scopus_id)
            if publication.title != "":
                publication_list.append(publication)

        return publication_list

    def get_author_profile(self, author_id):
        """
        The AuthorProfile object for a given author id.

        :param author_id: The int id of the author
        :return: The ScopusAuthorProfile representing the author
        """
        return self.author_controller.get_author(author_id)

    def get_multiple_author_profiles(self, author_id_list):
        """
        A list of author profiles to a list of author ids.

        :param author_id_list: The list of int author ids for which to get the profiles
        :return: A list of ScopusAuthorProfile objects
        """
        author_profile_list = []
        for author_id in author_id_list:
            author_profile = self.get_author_profile(author_id)
            author_profile_list.append(author_profile)

        return author_profile_list

    def get_author_publications(self, author_profile):
        """
        A list of publication objects for the publications the given author has contributed to.

        :param author_profile: The ScopusAuthorProfile object representing the author
        :return: A list of ScopusPublication objects
        """
        return self.get_multiple_publications(author_profile.publications)

    def get_citation_publications(self, publication):
        """
        A list of publications, that have cited the publication given.

        :param publication: The publication of which the citing publications shall be gotten
        :return: A list of ScopusPublications
        """
        return self.publication_controller.get_citation_publications(publication.eid)

    def get_publication_author_profiles(self, publication):
        """
        Gets the author profiles of all the authors, that have contributed to the given publication.

        :param publication: ScopusPublication
        :return: A list of ScopusAuthorProfile objects
        """
        author_profile_list = []
        for author in publication.authors:
            author_id = int(author)
            author_profile = self.get_author_profile(author_id)
            author_profile_list.append(author_profile)
        return author_profile_list

    def get_affiliation(self, affiliation_id):
        """
        The ScopusAffiliation data structure to the given affiliation id.

        :param affiliation_id: the int id of the affiliation
        :return: The ScopusAffiliation object
        """
        return self.affiliation_controller.get_affiliation(affiliation_id)

    def get_multiple_affiliations(self, affiliation_id_list):
        """
        A list of affiliations to a list of affiliation ids.

        :param affiliation_id_list: A list of affiliation ids
        :return: A list of ScopusAffiliation objects
        """
        affiliation_list = []
        for affiliation_id in affiliation_id_list:
            affiliation = self.get_affiliation(affiliation_id)
            affiliation_list.append(affiliation)
        return affiliation_list

    def get_publication_affiliations(self, publication):
        """
        The list of ScopusAffiliations for a given publication.

        :param publication: The publication for which to get the affiliations
        :return: a list of ScopusAffiliation objects
        """
        return self.get_multiple_affiliations(publication.affiliations)


class ScopusAuthorPublicationFetcher:

    def __init__(self, author_id):
        self.author_id = author_id

        self.logger = logging.getLogger('SCOPUS')

        self.config = cfg.Config.get_instance()
        self.url_base = self.config['SCOPUS']['url']
        self.api_key = self.config['SCOPUS']['api_key']

        # Constructing the headers dict from the API key
        self.headers = {
            'Accept': 'application/json',
            'X-ELS-APIKey': self.api_key
        }

        print(self.headers)

    def fetch(self):
        entry_dict_list = []

        # Requesting the publication search
        start_index = 0
        requesting = True
        while requesting:

            response = self.request_publication_search(start_index)
            (
                _entry_dict_list,
                total_results,
                items_per_page
            ) = self._extract_publication_search_response(response)

            # Adding the temporary list of entry dicts from the current request to the total list of entry dicts
            entry_dict_list += _entry_dict_list

            # The loop continues requesting if the total amount of search results is greater
            # than the current start index plus the entries acquired in the current request
            requesting = int(total_results) > (start_index + len(_entry_dict_list))

            start_index += int(items_per_page)

        # Turning the list of entry dicts into a list of publication ids
        scopus_id_list = []
        for entry_dict in entry_dict_list:
            try:
                scopus_id = self.scopus_id_from_entry_dict(entry_dict)
            except (KeyError, ValueError):
                self.logger.error('Skipped publication for author "{}" due to missing scopus id entry'.format(
                    self.author_id
                ))
                continue
            scopus_id_list.append(scopus_id)

        return scopus_id_list

    @staticmethod
    def scopus_id_from_entry_dict(entry_dict):
        scopus_id_string = entry_dict['dc:identifier']
        if scopus_id_string == '':
            raise ValueError()
        scopus_id = int(scopus_id_string.replace('SCOPUS_ID:', ''))
        return scopus_id

    def request_publication_search(self, start_index):
        search_query_string = 'AU-ID({})'.format(self.author_id)

        query_dict = {
            'query': search_query_string,
            'view': 'STANDARD',
            'start': start_index
        }

        url_encoded_query_string = urlparse.urlencode(query_dict)

        url_base = os.path.join(self.url_base, 'search/scopus')
        url = '{}?{}'.format(
            url_base,
            url_encoded_query_string
        )

        print(url)
        response = requests.get(url, headers=self.headers)
        return response

    @staticmethod
    def _extract_publication_search_response(response):
        """
        This method will be used for the 
        :param response:
        :return:
        """
        # JSON Decoding the response text into a dict structure
        response_dict = json.loads(response.text)

        entry_dict_list = response_dict['search-results']['entry']

        total_results = response_dict['search-results']['opensearch:totalResults']
        items_per_page = response_dict['search-results']['opensearch:itemsPerPage']

        return entry_dict_list, total_results, items_per_page


class ScopusPublicationProcessor:

    def __init__(self):
        self.dict = None
        self.scopus_id = None
        self.logger = logging.getLogger('scopusProcessing')

    def process(self, publication_entry_dict):
        # Getting the id from the publication
        self.scopus_id = publication_entry_dict

    def _query_dict(self, key_query, default_value):
        key_list = key_query.split('/')

        try:
            current_level = self.dict
            for key_string in key_list:
                # Need a try except here
                current_level = current_level[key_string]
        except (TypeError, KeyError) as exception:
            self.logger.warning(
                'The publication entry "{}" does not have the value for "{}", exception: {}'.format(
                    self.scopus_id,
                    key_query,
                    str(exception)
                )
            )
            return default_value

        return current_level


if __name__ == '__main__':

    controller = ScopusController()
    author = controller.get_author_profile(57094104200)
    pubs = controller.get_author_publications(author)
    print(pubs)





