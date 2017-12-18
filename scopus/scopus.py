from ScopusWp.scopus.data import ScopusPublication, ScopusAuthor, ScopusAffiliation, ScopusAuthorProfile

import ScopusWp.config as cfg

import logging
import urllib.parse as urlparse
import requests
import json
import os


class ScopusBaseController:
    """
    Abstract base class for all the specific scopus controllers.
    """
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
            error_message = 'There is no item to the key "{}" for the affiliation "{}" with the sub dict: {}'.format(
                key,
                self.current_affiliation_id,
                str(dictionary)
            )
            self.logger.warning(error_message)
            # Returning the default value, so that the program can still run in case there was no item in the dict
            return default

    def _log(self, string):
        pass

