r"""
This module provides set of classes for working with WildApricot public API v2.
Public API documentation can be found here: http://help.wildapricot.com/display/DOC/API+Version+2

"""

__author__ = 'dsmirnov@wildapricot.com'

import datetime
import urllib.request
import urllib.response
import urllib.error
import urllib.parse
import json
import base64


class WaApiClient(object):
    """Wild apricot API client."""
    auth_endpoint = "https://oauth.wildapricot.org/auth/token"
    api_endpoint = "https://api.wildapricot.org"
    client_id = None
    client_secret = None

    def __init__(self, api_key=None, client_id=None, client_secret=None):
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = {}

    def authenticate_with_apikey(self, scope=None):
        """perform authentication by api key and store result for execute_request method

        scope -- optional scope of authentication request. If None full list of API scopes will be used.
        """
        scope = "auto" if scope is None else scope
        data = {
            "grant_type": "client_credentials",
            "scope": scope
        }
        encoded_data = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(self.auth_endpoint, encoded_data, method="POST")
        request.add_header("ContentType", "application/x-www-form-urlencoded")
        request.add_header("Authorization", 'Basic ' + base64.standard_b64encode(('APIKEY:' + self.api_key).encode()).decode())

        response = urllib.request.urlopen(request)
        self._token = WaApiClient._parse_response(response)
        self._token['retrieved_at'] = datetime.datetime.now()

    def authenticate_with_contact_credentials(self, username, password, scope=None):
        """perform authentication by contact credentials and store result for execute_request method

        username -- typically a contact email
        password -- contact password
        scope -- optional scope of authentication request. If None full list of API scopes will be used.
        """
        scope = "auto" if scope is None else scope
        data = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "scope": scope
        }
        encoded_data = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(self.auth_endpoint, encoded_data, method="POST")
        request.add_header("ContentType", "application/x-www-form-urlencoded")
        auth_header = base64.standard_b64encode((self.client_id + ':' + self.client_secret).encode()).decode()

        request.add_header("Authorization", 'Basic ' + auth_header)
        response = urllib.request.urlopen(request)
        self._token = WaApiClient._parse_response(response)
        self._token['retrieved_at'] = datetime.datetime.now()

    def execute_request(self, api_url, api_request_object=None, method=None):
        """
        perform api request and return result as a dict

        api_url -- absolute or relative api resource url
        api_request -- any json serializable object to send to API
        method -- HTTP method of api request. Default: GET if api_request_object is None else POST
        """
        if self._token is None:
            raise ApiException("Access token is not abtained. "
                               "Call authenticate_with_apikey or authenticate_with_contact_credentials first.")

        if not api_url.startswith("http"):
            api_url = self.api_endpoint + api_url

        if method is None:
            if api_request_object is None:
                method = "GET"
            else:
                method = "POST"

        request = urllib.request.Request(api_url, method=method)
        if api_request_object is not None:
            request.data = json.dumps(api_request_object).encode()

        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")
        request.add_header("Authorization", "Bearer " + self._get_access_token())

        try:
            response = urllib.request.urlopen(request)
            return WaApiClient._parse_response(response)
        except urllib.error.HTTPError as httpErr:
            if httpErr.code == 400:
                raise ApiException(httpErr.read())
            else:
                raise

    def _get_access_token(self):
        expires_at = self._token['retrieved_at'] + datetime.timedelta(seconds=self._token['expires_in'] - 100)
        if datetime.datetime.utcnow() > expires_at:
            self._refresh_auth_token()
        return self._token['access_token']

    def _refresh_auth_token(self):
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._token['refresh_token']
        }
        encoded_data = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(self.auth_endpoint, encoded_data, method="POST")
        request.add_header("ContentType", "application/x-www-form-urlencoded")
        if self.api_key:
            auth_header = base64.standard_b64encode(('APIKEY:' + self.api_key).encode()).decode()
        else:
            auth_header = base64.standard_b64encode((self.client_id + ':' + self.client_secret).encode()).decode()

        # auth_header = base64.standard_b64encode((self.client_id + ':' + self.client_secret).encode()).decode()
        request.add_header("Authorization", 'Basic ' + auth_header)
        response = urllib.request.urlopen(request)
        self._token = WaApiClient._parse_response(response)
        self._token['retrieved_at'] = datetime.datetime.now()

    @staticmethod
    def _parse_response(http_response):
        return json.loads(http_response.read().decode())


class ApiException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
