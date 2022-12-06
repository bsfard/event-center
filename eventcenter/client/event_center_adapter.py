from typing import Callable

from eventdispatch import Event, Properties
from flask import Flask, request

from eventcenter import FlaskAppRunner, APICaller
from eventcenter.server.event_center import RegistrationData

CALLBACK_ENDPOINT = '/on_event'


class EventCenterAdapter(FlaskAppRunner):
    def __init__(self, event_handler: Callable):
        self.event_handler = event_handler
        self.event_center_url = Properties.get('EVENT_CENTER_URL')
        host = Properties.get('EVENT_CENTER_CALLBACK_HOST')
        port = Properties.get('EVENT_CENTER_CALLBACK_PORT')

        self.url = f'{host}:{port}'
        self.callback_url = f'{self.url}{CALLBACK_ENDPOINT}'

        app = Flask('EventCenterAdapter')

        super().__init__('0.0.0.0', port, app)
        self.start()

        @app.route(CALLBACK_ENDPOINT, methods=['POST'])
        def on_event():
            self.event_handler(request.json)
            return {}

    def register(self, events: [str]):
        self.__register(events, is_register=True)

    def unregister(self, events: [str]):
        self.__register(events, is_register=False)

    def post_event(self, event: Event):
        url = self.event_center_url + '/post_event'
        event.payload['sender_url'] = f'{self.url}'
        APICaller.make_post_call(url, event.dict, is_suppress_connection_error=True)

    def __register(self, events: [str], is_register: bool = True):
        endpoint = '/register' if is_register else '/unregister'
        url = self.event_center_url + endpoint
        data = RegistrationData(self.callback_url, events)
        APICaller.make_post_call(url, data.dict, is_suppress_connection_error=True)
