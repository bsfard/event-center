import logging
import threading
import traceback

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
    def make_post_api_call(url: str, body: dict):
        try:
            response = requests.post(url, json=body, headers=HEADERS)
            return response if response.status_code == 200 else {}
        except requests.exceptions.ConnectionError as e:
            raise ApiConnectionError(url, body, e)


class ApiConnectionError(NotifiableError):
    """Raised when connection to API cannot be established"""

    def __init__(self, url: str, body: dict, exception: traceback):
        message = f'\nURL: {url}\nBody: {body}'
        error = 'api_connection_error'
        payload = {
            'url': url,
            'body': body
        }
        super().__init__(message, error, payload, exception)
