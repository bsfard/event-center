import logging
import threading
from typing import Any, Dict

import requests
from eventdispatch import NotifiableError
from flask import Flask
from werkzeug.serving import make_server

HEADERS = {'Content-Type': 'application/json'}


class FlaskAppRunner(threading.Thread):
    def __init__(self, host: str, port: int, app: Flask):
        super().__init__()

        # Silence logging from flask and requests libraries.
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)

        self.logger = logging.getLogger(app.name)
        self.app = app

        self.server = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.logger.debug(f"Starting flask app '{self.app.name}'")
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
        self.logger.debug(f"Stopped flask app '{self.app.name}'")


class APICaller:
    @staticmethod
    def make_post_call(url: str, body: Dict[str, Any], headers: Dict[str, Any] = None,
                       session: requests.Session = None,
                       timeout_sec: float = None,
                       is_suppress_connection_error: bool = False) -> requests.Response:
        headers = headers if headers else HEADERS

        try:
            if session:
                if timeout_sec:
                    response = session.post(url, json=body, headers=headers, timeout=timeout_sec)
                else:
                    response = session.post(url, json=body, headers=headers)
            else:
                if timeout_sec:
                    response = requests.post(url, json=body, headers=headers, timeout=timeout_sec)
                else:
                    response = requests.post(url, json=body, headers=headers)

            APICaller.__validate_response_ok(url, response)
            return response

        except requests.exceptions.ConnectionError:
            if not is_suppress_connection_error:
                raise ApiConnectionError(url, body)

    @staticmethod
    def make_get_call(url: str, params: Dict[str, Any], headers: Dict[str, Any] = None,
                      session: requests.Session = None,
                      is_suppress_connection_error: bool = False) -> requests.Response:
        headers = headers if headers else HEADERS
        params = APICaller.__remove_empty_params(params)
        try:
            if session:
                response = session.get(url, params=params, headers=headers)
            else:
                response = requests.get(url, params=params, headers=headers)

            APICaller.__validate_response_ok(url, response)
            return response

        except requests.exceptions.ConnectionError:
            if not is_suppress_connection_error:
                raise ApiConnectionError(url, {})

    @staticmethod
    def __remove_empty_params(params):
        return {key: value for (key, value) in params.items() if value}

    @staticmethod
    def __validate_response_ok(url: str, response):
        if response.status_code != 200:
            raise BadResponseStatusError(url, response)


class ApiConnectionError(NotifiableError):
    """Raised when connection to API cannot be established"""

    def __init__(self, url: str, body: Dict[str, Any]):
        message = ''
        # message = f'\nURL: {url}\nBody: {body}'
        error = 'api_connection_error'
        payload = {
            'url': url,
            'body': body
        }
        super().__init__(message, error, payload)


class BadResponseStatusError(NotifiableError):
    """Raised when response code from an API call is not 200"""

    def __init__(self, url: str, response: requests.Response):
        message = f'\nURL: {url}'
        error = 'bad_response_error'
        payload = {
            'message': message,
            'url': url,
            'status_code': response.status_code,
            'response': response
        }
        super().__init__(message, error, payload)
