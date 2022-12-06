import json
from typing import Dict, Any

from eventdispatch import Data, Event, Properties, NamespacedEnum, post_event, register_for_events, \
    unregister_from_events

from eventcenter import APICaller, ApiConnectionError


class RegistrationData(Data):
    def __init__(self, callback_url: str, events: [str]):
        super().__init__({
            'callback_url': callback_url,
            'events': events
        })

        self.__callback_url = callback_url
        self.__events = events

    @property
    def callback_url(self) -> str:
        return self.__callback_url

    @property
    def events(self) -> [str]:
        return self.__events

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        callback_url = data.get('callback_url')
        events = data.get('events')
        return RegistrationData(callback_url, events)


class EventRegistrationManager:
    __REGISTRANTS_KEY = 'registrants'
    __registrants = {}

    def __init__(self):
        self.__registrants_file_path = Properties.get('REGISTRANTS_FILE_PATH')

        # Register to get notified if clients are unreachable, to take action.
        register_for_events(self.on_event, [RegistrationEvent.CALLBACK_FAILED_EVENT])

        self.__load_registrants()

    @property
    def registrants(self) -> dict:
        return self.__registrants

    def register(self, callback_url: str, events: [str]):
        try:
            registrant = self.__registrants[callback_url]
        except KeyError:
            # New registrant, create and store.
            registrant = Registrant(callback_url)
            self.__registrants[callback_url] = registrant

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

    def unregister(self, callback_url: str, events: [str]):
        try:
            registrant = self.__registrants[callback_url]

            is_got_unregistered = False
            if events:
                for event in events:
                    if registrant.unregister(event):
                        is_got_unregistered = True
            else:
                if registrant.unregister():
                    is_got_unregistered = True
            if len(registrant.registrations) == 0:
                del self.__registrants[callback_url]

            if is_got_unregistered:
                self.__persist_registrants()

        except KeyError:
            # No registrant, so nothing to do.
            return

    def get_registrant(self, callback_url: str):
        try:
            return self.__registrants[callback_url]
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
        for callback_url, events in registrants_data.items():
            self.register(callback_url, events)

    def __persist_registrants(self):
        with open(self.__registrants_file_path, 'w') as file:
            registrants = {}
            for callback_url, registrant in self.__registrants.items():
                registrants[callback_url] = {
                    'events': [event for event in registrant.registrations]
                }
            json.dump({
                self.__REGISTRANTS_KEY: registrants
            }, file)

    def __handle_unreachable_client(self, event: Event):
        callback_url = event.payload.get('callback_url')
        event = event.payload.get('event')
        events = [event] if event else []
        self.unregister(callback_url, events)


class RegistrationEvent(NamespacedEnum):
    CALLBACK_FAILED_EVENT = 'callback_failed'

    def get_namespace(self) -> str:
        return 'registration'


class Registration:
    def __init__(self, callback_url: str, event: str = None):
        self.__callback_url = callback_url
        self.__event = event
        self.__client_callback_timeout_sec = Properties.get('CLIENT_CALLBACK_TIMEOUT_SEC')

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
        if sender_url and sender_url in self.__callback_url:
            return

        try:
            APICaller.make_post_call(self.__callback_url, event.dict,
                                     timeout_sec=self.__client_callback_timeout_sec)
        except ApiConnectionError:
            self.__handle_unreachable_client()

    def __handle_unreachable_client(self):
        self.cancel()

        post_event(RegistrationEvent.CALLBACK_FAILED_EVENT, {
            'callback_url': self.__callback_url,
            'event': self.__event
        })

    def dict(self) -> Dict[str, Any]:
        return {
            'callback_url': self.__callback_url,
            'event': self.__event
        }

    @staticmethod
    def to_dict_list(registrations) -> [Dict[str, Any]]:
        return [v.dict() for _, v in registrations.items()]


class Registrant:
    def __init__(self, callback_url: str):
        self.__callback_url = callback_url
        self.__registrations: Dict[str, Registration] = {}

    @property
    def registrations(self) -> Dict[str, Registration]:
        return self.__registrations

    @property
    def callback_url(self) -> str:
        return self.__callback_url

    def register(self, event: str = None) -> bool:
        key = event if event else ''

        # Skip registration if registrant is already registered for event.
        if key in self.__registrations:
            return False

        self.__registrations[key] = Registration(self.__callback_url, event)
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

    def dict(self) -> Dict[str, Any]:
        return {
            'callback_url': self.__callback_url,
            'registrations': Registration.to_dict_list(self.__registrations)
        }
