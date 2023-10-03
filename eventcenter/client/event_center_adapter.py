import logging
import threading
from typing import Callable

from eventdispatch import Event, Properties
from eventdispatch.core import NotifiableError
from flask import Flask, request

from eventcenter import FlaskAppRunner, APICaller
from eventcenter.server.event_center import RegistrationData, RemoteEventData, EventMappingData

CALLBACK_ENDPOINT = '/on_event'

# Event Center properties
EVENT_CENTER_URL = 'EVENT_CENTER_URL'
EVENT_CENTER_CALLBACK_HOST = 'EVENT_CENTER_CALLBACK_HOST'
EVENT_CENTER_CALLBACK_PORT = 'EVENT_CENTER_CALLBACK_PORT'


class EventCenterAdapter(FlaskAppRunner):
    def __init__(self, event_handler: Callable):
        self.event_handler = event_handler
        self.event_center_url = Properties().get('EVENT_CENTER_URL')
        host = Properties().get('EVENT_CENTER_CALLBACK_HOST')
        port = Properties().get('EVENT_CENTER_CALLBACK_PORT')

        self.url = f'{host}:{port}'
        self.callback_url = f'{self.url}{CALLBACK_ENDPOINT}'

        self.app = Flask('EventCenterAdapter')

        super().__init__('0.0.0.0', port, self.app)

        if self.is_flask_debug():
            self.start()

        @self.app.route(CALLBACK_ENDPOINT, methods=['POST'])
        def on_event():
            remote_event = RemoteEventData.from_dict(request.json)
            threading.Thread(target=self.event_handler, args=[remote_event]).start()
            return {}

    def register(self, events: [str], channel: str = ''):
        self.__register(events, channel, is_register=True)

    def unregister(self, events: [str], channel: str = ''):
        self.__register(events, channel, is_register=False)

    def unregister_all(self):
        url = self.event_center_url + '/unregister_all'
        data = {
            'callback_url': self.callback_url
        }
        APICaller.make_post_call(url, json=data, is_suppress_connection_error=True)

    def post_event(self, event: Event, channel: str = ''):
        url = self.event_center_url + '/post_event'

        sender = f'{self.url}'
        try:
            metadata = event.payload['metadata']
            metadata['sender_url'] = sender
        except KeyError:
            event.payload['metadata'] = {'sender_url': sender}

        data = RemoteEventData(channel, event)
        APICaller.make_post_call(url, json=data.dict, is_suppress_connection_error=True)

    def map_events(self, events_to_map: [Event], event_to_post: Event, reset_if_exists: bool = False,
                   channel: str = ''):
        url = self.event_center_url + '/map_events'

        data = EventMappingData(channel, events_to_map, event_to_post, reset_if_exists)
        response = APICaller.make_post_call(url, json=data.dict, is_suppress_connection_error=True)
        response = response.json()

        if response.get('success', 'false') == 'true':
            EventCenterAdapter.__log_message_map_events_succeeded(data)
        else:
            error = response.get('error', '(no error message provided')
            raise EventMappingError(error)

    @staticmethod
    def __log_message_map_events_succeeded(event_mapping_data: EventMappingData):
        logging.getLogger().debug(f"Mapped events\n{event_mapping_data.dict}")

    def __register(self, events: [str], channel: str, is_register: bool = True):
        endpoint = '/register' if is_register else '/unregister'
        url = self.event_center_url + endpoint
        data = RegistrationData(self.callback_url, events, channel)
        APICaller.make_post_call(url, json=data.dict, is_suppress_connection_error=True)


class EventMappingError(NotifiableError):
    def __init__(self, reason: str):
        message = f"Could not map events, reason: {reason}"
        error = 'event_mapping_error'
        payload = {
            'reason': reason,
        }
        super().__init__(message, error, payload)
