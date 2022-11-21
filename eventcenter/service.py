import json
from typing import Dict, Any

from eventdispatch import Data, Event, Properties, NamespacedEnum, post_event, register_for_events, \
    unregister_from_events
from flask import Flask, request

from eventcenter import FlaskAppRunner, APICaller, ApiConnectionError

RESPONSE_OK = {
    'status': 'OK'
}


class ECEvent(NamespacedEnum):
    STARTED = 'started'

    def get_namespace(self) -> str:
        return 'event_center'


class EventCenter(FlaskAppRunner):
    def __init__(self):
        self.__event_registration_manager = EventRegistrationManager()

        app = Flask('EventCenter')
        port = Properties().get('EVENT_CENTER_PORT')
        super().__init__('0.0.0.0', port, app)
        self.start()

        post_event(ECEvent.STARTED)

        @app.route('/register', methods=['POST'])
        def register():
            data = RegistrationData.from_dict(request.json)
            self.__event_registration_manager.register(data.event_receiver, data.events)
            return RESPONSE_OK

        @app.route('/unregister', methods=['POST'])
        def unregister():
            data = RegistrationData.from_dict(request.json)
            self.__event_registration_manager.unregister(data.event_receiver, data.events)
            return RESPONSE_OK

        @app.route('/post_event', methods=['POST'])
        def post():
            data = Event.from_dict(request.json)
            post_event(data.name, data.payload)
            return RESPONSE_OK

    # ----- For testing ---------------------------------------------------------------------------
    def get_registrants(self):
        return self.__event_registration_manager.registrants

    def get_registrant(self, event_receiver):
        return self.__event_registration_manager.get_registrant(event_receiver)

    # ---------------------------------------------------------------------------------------------


class EventReceiver(Data):
    def __init__(self, name: str, callback_url: str):
        super().__init__({
            'name': name,
            'callback_url': callback_url
        })

        self.__name = name
        self.__callback_url = callback_url

    @property
    def name(self) -> str:
        return self.get('name')

    @property
    def callback_url(self) -> str:
        return self.get('callback_url')

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        return EventReceiver(data.get('name'), data.get('callback_url'))

    def __eq__(self, other):
        return self.name == other.name and self.callback_url == other.callback_url


class RegistrationData(Data):
    def __init__(self, event_receiver: EventReceiver, events: [str]):
        super().__init__({
            'event_receiver': event_receiver.raw,
            'events': events
        })

        self.__event_receiver = event_receiver
        self.__events = events

    @property
    def event_receiver(self) -> EventReceiver:
        return self.__event_receiver

    @property
    def events(self) -> [str]:
        return self.__events

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        event_receiver = EventReceiver.from_dict(data.get('event_receiver'))
        events = data.get('events')
        return RegistrationData(event_receiver, events)


class EventRegistrationManager:
    __REGISTRANTS_KEY = 'registrants'
    __registrants = {}

    def __init__(self):
        self.__registrants_file_path = Properties().get('REGISTRANTS_FILE_PATH')

        # Register to get notified if clients are unreachable, to take action.
        register_for_events(self.on_event, [RegistrationEvent.CALLBACK_FAILED_EVENT])

        self.__load_registrants()

    @property
    def registrants(self) -> dict:
        return self.__registrants

    def register(self, event_receiver: EventReceiver, events: [str]):
        key = self.__build_event_receiver_key(event_receiver)

        try:
            registrant = self.__registrants[key]
        except KeyError:
            # New registrant, create and store.
            registrant = Registrant(event_receiver)
            self.__registrants[key] = registrant

        is_got_registered = False
        if events:
            for event in events:
                if registrant.register(event):
                    is_got_registered = True
        else:
            if registrant.register():
                is_got_registered = True

        if is_got_registered:
            self.__persist_registrants()

    def unregister(self, event_receiver: EventReceiver, events: [str]):
        key = self.__build_event_receiver_key(event_receiver)

        try:
            registrant = self.__registrants[key]

            is_got_unregistered = False
            if events:
                for event in events:
                    if registrant.unregister(event):
                        is_got_unregistered = True
            else:
                if registrant.unregister():
                    is_got_unregistered = True
            if len(registrant.registrations) == 0:
                del self.__registrants[key]

            if is_got_unregistered:
                self.__persist_registrants()

        except KeyError:
            # No registrant, so nothing to do.
            return

    def get_registrant(self, event_receiver: EventReceiver):
        key = self.__build_event_receiver_key(event_receiver)
        try:
            return self.__registrants[key]
        except KeyError:
            return None

    def clear_registrants(self):
        self.__registrants: Dict[str, Registrant] = {}
        self.__persist_registrants()

    def on_event(self, event: Event):
        if event.name == RegistrationEvent.CALLBACK_FAILED_EVENT.namespaced_value:
            self.__handle_unreachable_client(event)

    def __load_registrants(self):
        try:
            with open(self.__registrants_file_path, 'r') as file:
                data = json.load(file)
                if data:
                    self.__reprocess_registrations(data.get(self.__REGISTRANTS_KEY))
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # If file doesn't exist, or json data in file is invalid, assume clean start.
            self.clear_registrants()

    def __reprocess_registrations(self, registrants_data: Dict[str, Any]) -> [registrants]:
        for key, registrant_data in registrants_data.items():
            event_receiver = EventReceiver.from_dict(registrant_data['event_receiver'])
            events = registrant_data['events']
            # events = [data['event'] for data in registrant_data['registrations']]

            self.register(event_receiver, events)

    def __persist_registrants(self):
        with open(self.__registrants_file_path, 'w') as file:
            registrants = {}
            for registrant_key, registrant in self.__registrants.items():
                registrants[registrant_key] = {
                    'event_receiver': registrant.event_receiver.raw,
                    'events': [registration_key for registration_key in registrant.registrations]
                }
            json.dump({
                self.__REGISTRANTS_KEY: registrants
            }, file)

    def __handle_unreachable_client(self, event: Event):
        event_receiver = event.payload.get('event_receiver')
        event_receiver = EventReceiver.from_dict(event_receiver)
        event = event.payload.get('event')
        events = [event] if event else []
        self.unregister(event_receiver, events)

    @staticmethod
    def __build_event_receiver_key(event_receiver: EventReceiver):
        return event_receiver.name + ',' + event_receiver.callback_url


class RegistrationEvent(NamespacedEnum):
    CALLBACK_FAILED_EVENT = 'callback_failed'

    def get_namespace(self) -> str:
        return 'registration'


class Registration:
    def __init__(self, event_receiver: EventReceiver, event: str = None):
        self.__event_receiver = event_receiver
        self.__event = event
        self.__client_callback_timeout_sec = Properties().get('CLIENT_CALLBACK_TIMEOUT_SEC')

        events = [self.__event] if self.__event else []
        register_for_events(self.on_event, events)

    @property
    def event(self) -> str:
        return self.__event

    def cancel(self):
        events = [self.__event] if self.__event else []
        unregister_from_events(self.on_event, events)

    def on_event(self, event: Event):
        # Don't propagate event if event originated from destination url.
        sender_url = event.payload.get('sender_url', '')
        if sender_url and sender_url in self.__event_receiver.callback_url:
            return

        try:
            APICaller.make_post_call(self.__event_receiver.callback_url, event.raw,
                                     timeout_sec=self.__client_callback_timeout_sec)
        except ApiConnectionError:
            self.__handle_unreachable_client()

    def __handle_unreachable_client(self):
        self.cancel()

        post_event(RegistrationEvent.CALLBACK_FAILED_EVENT, {
            'event_receiver': self.__event_receiver.raw,
            'event': self.__event
        })

    def raw(self) -> Dict[str, Any]:
        return {
            'event_receiver': self.__event_receiver.raw,
            'event': self.__event
        }

    @staticmethod
    def to_raw_list(registrations) -> [Dict[str, Any]]:
        return [v.raw() for _, v in registrations.items()]


class Registrant:
    def __init__(self, event_receiver: EventReceiver):
        self.__event_receiver = event_receiver
        self.__registrations: Dict[str, Registration] = {}

    @property
    def registrations(self) -> Dict[str, Registration]:
        return self.__registrations

    @property
    def event_receiver(self) -> EventReceiver:
        return self.__event_receiver

    def register(self, event: str = None) -> bool:
        key = event if event else ''

        # Skip registration if registrant is already registered for event.
        if key in self.__registrations:
            return False

        self.__registrations[key] = Registration(self.__event_receiver, event)
        return True

    def unregister(self, event: str = None) -> bool:
        key = event if event else ''

        # Skip un-registration if registrant is not registered for event.
        if key not in self.__registrations:
            return False

        registration = self.__registrations.get(key)
        registration.cancel()
        del self.__registrations[key]
        return True

    def raw(self) -> Dict[str, Any]:
        return {
            'event_receiver': self.__event_receiver.raw,
            'registrations': Registration.to_raw_list(self.__registrations)
        }
