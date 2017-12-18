import ScopusWp.config as cfg

import logging


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

