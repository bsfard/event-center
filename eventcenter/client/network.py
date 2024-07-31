import logging
import threading
from typing import Any, Dict

import requests
from eventdispatch import NotifiableError, PropertyNotSetError, Properties
from flask import Flask, make_response
from werkzeug.serving import make_server

HEADERS = {'Content-Type': 'application/json'}


class FlaskAppRunner(threading.Thread):
    def __init__(self, host: str, port: int, app: Flask, run_as_a_server: bool = False):
        super().__init__()
        self.server = None

        self.is_allow_cors = False
        try:
            if Properties().has('ALLOW_CORS'):
                self.is_allow_cors = Properties().get('ALLOW_CORS') == True
        except PropertyNotSetError:
            pass

        # Silence logging from flask and requests libraries.
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)

        self.logger = logging.getLogger(app.name)
        self.app = app

        if run_as_a_server:
            self.server = make_server(host, port, app)

        self.ctx = app.app_context()
        self.ctx.push()

    @staticmethod
    def is_flask_debug() -> bool:
        if Properties().has('RUN_AS_A_SERVER'):
            return Properties().get('RUN_AS_A_SERVER')
        return False

    def make_response(self, response: Any):
        if self.is_allow_cors:
            response = make_response(response)
            response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    def run(self):
        if self.server:
            self.logger.debug(f"Starting flask app '{self.app.name}'")
            self.server.serve_forever()

    def shutdown(self):
        if self.server:
            self.server.shutdown()
            self.logger.debug(f"Stopped flask app '{self.app.name}'")


class APICaller:
    @staticmethod
    def make_post_call(url: str, data: Dict[str, Any] = None, json: Any = None,
                       headers: Dict[str, Any] = None,
                       session: requests.Session = None,
                       timeout_sec: float = None,
                       is_suppress_connection_error: bool = False) -> requests.Response:
        headers = headers if headers else HEADERS

        try:
            if session:
                if timeout_sec:
                    return session.post(url, data=data, json=json, headers=headers, timeout=timeout_sec)
                else:
                    return session.post(url, data=data, json=json, headers=headers)
            else:
                if timeout_sec:
                    return requests.post(url, data=data, json=json, headers=headers, timeout=timeout_sec)
                else:
                    return requests.post(url, data=data, json=json, headers=headers)

        except requests.exceptions.ConnectionError:
            if not is_suppress_connection_error:
                raise ApiConnectionError(url, data, json)

    @staticmethod
    def make_patch_call(url: str, data: Dict[str, Any] = None, json: Any = None,
                        headers: Dict[str, Any] = None,
                        session: requests.Session = None,
                        timeout_sec: float = None,
                        is_suppress_connection_error: bool = False) -> requests.Response:
        headers = headers if headers else HEADERS

        try:
            if session:
                if timeout_sec:
                    return session.patch(url, data=data, json=json, headers=headers, timeout=timeout_sec)
                else:
                    return session.patch(url, data=data, json=json, headers=headers)
            else:
                if timeout_sec:
                    return requests.patch(url, data=data, json=json, headers=headers, timeout=timeout_sec)
                else:
                    return requests.patch(url, data=data, json=json, headers=headers)

        except requests.exceptions.ConnectionError:
            if not is_suppress_connection_error:
                raise ApiConnectionError(url, data, json)

    @staticmethod
    def make_get_call(url: str, params: Dict[str, Any], headers: Dict[str, Any] = None,
                      session: requests.Session = None,
                      is_suppress_connection_error: bool = False) -> requests.Response:
        headers = headers if headers else HEADERS
        params = APICaller.__remove_empty_params(params)
        try:
            if session:
                return session.get(url, params=params, headers=headers)
            else:
                return requests.get(url, params=params, headers=headers)

        except requests.exceptions.ConnectionError:
            if not is_suppress_connection_error:
                raise ApiConnectionError(url, {}, {})

    @staticmethod
    def make_delete_call(url: str, data: Dict[str, Any] = None, json: Any = None,
                         headers: Dict[str, Any] = None,
                         session: requests.Session = None,
                         timeout_sec: float = None,
                         is_suppress_connection_error: bool = False) -> requests.Response:
        headers = headers if headers else HEADERS

        try:
            if session:
                if timeout_sec:
                    return session.delete(url, data=data, json=json, headers=headers, timeout=timeout_sec)
                else:
                    return session.delete(url, data=data, json=json, headers=headers)
            else:
                if timeout_sec:
                    return requests.delete(url, data=data, json=json, headers=headers, timeout=timeout_sec)
                else:
                    return requests.delete(url, data=data, json=json, headers=headers)

        except requests.exceptions.ConnectionError:
            if not is_suppress_connection_error:
                raise ApiConnectionError(url, data, json)

    @staticmethod
    def __remove_empty_params(params):
        return {key: value for (key, value) in params.items() if value}


def validate_response(url: str, response: requests.Response, expected_status_code: int):
    if response.status_code != expected_status_code:
        raise BadResponseStatusError(url, response)


class ApiConnectionError(NotifiableError):
    """Raised when connection to API cannot be established"""

    def __init__(self, url: str, data: Dict[str, Any], json: Dict[str, Any]):
        message = ''
        error = 'api_connection_error'
        payload = {
            'url': url,
            'data': data,
            'json': json
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
