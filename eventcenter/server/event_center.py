import json
import logging
import threading
from typing import Dict, Any

from eventdispatch import Data, Event, Properties, NamespacedEnum, register_for_events, \
    EventDispatchManager, PropertyNotSetError
from eventdispatch import EventMapUtil
from requests.exceptions import InvalidSchema

from eventcenter.client.network import APICaller, ApiConnectionError


class RegistrationData(Data):
    def __init__(self, callback_url: str, events: [str], channel: str = ''):
        super().__init__({
            'callback_url': callback_url,
            'events': events,
            'channel': channel,
        })

        self.__callback_url = callback_url
        self.__events = events
        self.__channel = channel

    @property
    def callback_url(self) -> str:
        return self.__callback_url

    @property
    def events(self) -> [str]:
        return self.__events

    @property
    def channel(self) -> str:
        return self.__channel

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        callback_url = data.get('callback_url')
        events = data.get('events')
        channel = data.get('channel', '')
        return RegistrationData(callback_url, events, channel)


# -------------------------------------------------------------------------------------------------

class RemoteEventData(Data):
    def __init__(self, channel: str, event: Event):
        super().__init__({
            'channel': channel if channel else '',
            'event': event.dict
        })

        self.__channel = channel
        self.__event = event

    @property
    def channel(self) -> str:
        return self.__channel

    @property
    def event(self) -> Event:
        return self.__event

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        channel = data.get('channel')
        event = Event.from_dict(data.get('event'))
        return RemoteEventData(channel, event)


# -------------------------------------------------------------------------------------------------

class EventMappingData(Data):
    def __init__(self, channel: str, events_to_map: [Event], event_to_post: Event, ignore_if_exists: bool = False):
        super().__init__({
            'channel': channel if channel else '',
            'events_to_map': [event.dict for event in events_to_map],
            'event_to_post': event_to_post.dict,
            'ignore_if_exists': ignore_if_exists
        })

        self.__channel = channel
        self.__events_to_map = events_to_map
        self.__event_to_post = event_to_post
        self.__ignore_if_exists = ignore_if_exists

    @property
    def channel(self) -> str:
        return self.__channel

    @property
    def events_to_map(self) -> [Event]:
        return self.__events_to_map

    @property
    def event_to_post(self) -> Event:
        return self.__event_to_post

    @property
    def ignore_if_exists(self) -> bool:
        return self.__ignore_if_exists

    @property
    def json(self, pretty_print: bool = False) -> str:
        return json.dumps(self.__data, indent=4) if pretty_print else json.dumps(self.__data)

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        channel = data.get('channel')
        ignore_if_exists = data.get('ignore_if_exists', False)
        events_to_map = [Event.from_dict(event) for event in data.get('events_to_map')]
        event_to_post = Event.from_dict(data.get('event_to_post'))
        return EventMappingData(channel, events_to_map, event_to_post, ignore_if_exists)


# -------------------------------------------------------------------------------------------------

class EventRegistrationManager:
    __REGISTRANTS_KEY = 'registrants'

    def __init__(self):
        self.__registrants = {}
        self.__lock = threading.Lock()
        self.__registrants_file_path = Properties().get('REGISTRANTS_FILE_PATH')

        if Properties().has('PRETTY_PRINT') and Properties().get('PRETTY_PRINT'):
            EventDispatchManager(pretty_print=True)

        # Register to get notified if clients are unreachable, to take action.
        register_for_events(self.on_event, [RegistrationEvent.CALLBACK_FAILED_EVENT])

        self.__load_registrants()

    @property
    def registrants(self) -> dict:
        return self.__registrants

    def register(self, registration_data: RegistrationData, is_persist: bool = True):
        with self.__lock:
            try:
                registrant = self.__registrants[registration_data.callback_url]
            except KeyError:
                # New registrant, create and store.
                registrant = Registrant(registration_data.callback_url)
                self.__registrants[registration_data.callback_url] = registrant

            is_got_registered = False
            if registration_data.events:
                for event in registration_data.events:
                    if registrant.register(event, channel=registration_data.channel):
                        is_got_registered = True
            else:
                if registrant.register(channel=registration_data.channel):
                    is_got_registered = True

            if is_got_registered:
                registrant.log_message_registrations(registrant.callback_url)

                if is_persist:
                    self.__persist_registrants()

    def unregister(self, registration_data: RegistrationData):
        with self.__lock:
            try:
                registrant = self.__registrants[registration_data.callback_url]

                is_got_unregistered = False
                if registration_data.events:
                    for event in registration_data.events:
                        if registrant.unregister(event, channel=registration_data.channel):
                            is_got_unregistered = True
                else:
                    if registrant.unregister(channel=registration_data.channel):
                        is_got_unregistered = True
                if len(registrant.registrations) == 0:
                    del self.__registrants[registration_data.callback_url]

                if is_got_unregistered:
                    registrant.log_message_registrations(registrant.callback_url)
                    self.__persist_registrants()

            except KeyError:
                # No registrant, so nothing to do.
                return

    def unregister_all(self, callback_url: str):
        with self.__lock:
            try:
                registrant = self.__registrants[callback_url]
                if registrant.unregister_all():
                    del self.__registrants[callback_url]
                    self.__persist_registrants()
            except KeyError:
                # No registrant, so nothing to do.
                return

    @staticmethod
    def post(remote_event_data: RemoteEventData):
        if remote_event_data.channel not in EventDispatchManager().event_dispatchers:
            EventDispatchManager().add_event_dispatch(remote_event_data.channel)
        event_dispatch = EventDispatchManager().event_dispatchers.get(remote_event_data.channel)
        event_dispatch.post_event(remote_event_data.event.name, remote_event_data.event.payload)

    @staticmethod
    def map_events(event_mapping_data: EventMappingData):
        if event_mapping_data.channel not in EventDispatchManager().event_dispatchers:
            EventDispatchManager().add_event_dispatch(event_mapping_data.channel)
        event_dispatch = EventDispatchManager().event_dispatchers.get(event_mapping_data.channel)
        return event_dispatch.map_events(event_mapping_data.events_to_map, event_mapping_data.event_to_post,
                                         event_mapping_data.ignore_if_exists)

    @staticmethod
    def get_event_maps(channel: str = '') -> Dict[str, Any]:
        event_dispatch = EventDispatchManager().event_dispatchers.get(channel, None)
        return event_dispatch.get_event_maps() if event_dispatch else {}

    @staticmethod
    def pack_event_maps(event_maps: Dict[str, Any]) -> Dict[str, Any]:
        maps = {}
        for key, event_map in event_maps.items():
            maps[key] = EventMapUtil.build_event_mapping_payload(event_map.events_to_map, event_map.event_to_post)
        return maps

    def get_registrant(self, callback_url: str):
        try:
            return self.__registrants[callback_url]
        except KeyError:
            return None

    def clear_registrants(self):
        with self.__lock:
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
        for callback_url, channels in registrants_data.items():
            for channel, events in channels.items():
                self.register(RegistrationData(callback_url, events, channel), is_persist=False)

    def __persist_registrants(self):
        with open(self.__registrants_file_path, 'w') as file:
            json.dump(self.pack_registrants(), file)

    def pack_registrants(self) -> Dict[str, Any]:
        registrants = {}
        for callback_url, registrant in self.__registrants.items():
            registrants[callback_url] = {}
            for channel, registrations in registrant.registrations.items():
                events = [] if len(registrations) == 0 else [event for event in registrations]
                registrants[callback_url][channel] = events

        message = '\nCurrent Registrations:\n'
        if Properties().has('PRETTY_PRINT') and Properties().get('PRETTY_PRINT'):
            message += json.dumps(registrants, indent=2) + '\n'
        else:
            message += f"{registrants}'\n'"
        logging.getLogger().debug(message)

        return {self.__REGISTRANTS_KEY: registrants}

    def __handle_unreachable_client(self, event: Event):
        callback_url = event.payload.get('callback_url')
        self.unregister_all(callback_url)


# -------------------------------------------------------------------------------------------------


class RegistrationEvent(NamespacedEnum):
    CALLBACK_FAILED_EVENT = 'callback_failed'

    def get_namespace(self) -> str:
        return 'registration'


# -------------------------------------------------------------------------------------------------


class Registration:
    def __init__(self, callback_url: str, event: str = None, channel: str = ''):
        self.__channel = channel if channel else ''
        self.__callback_url = callback_url
        self.__event = event or ''
        self.__client_callback_timeout_sec = Properties().get('CLIENT_CALLBACK_TIMEOUT_SEC')
        self.__is_cancelled = False

        # if first registration for channel, add event dispatch for channel.
        if self.__channel not in EventDispatchManager().event_dispatchers:
            EventDispatchManager().add_event_dispatch(self.__channel)

        self.__event_dispatch = EventDispatchManager().event_dispatchers.get(self.__channel)
        self.__event_dispatch.register(self.on_event, self.__get_event_as_list())

    @property
    def event(self) -> str:
        return self.__event

    def cancel(self):
        if self.__is_cancelled:
            return

        self.__is_cancelled = True
        self.__event_dispatch.unregister(self.on_event, self.__get_event_as_list())

    def on_event(self, event: Event):
        if self.__is_cancelled:
            self.__log_message_skipping_post(event, 'registration_cancelled')
            return

        # Don't propagate event if event originated from destination url.
        if event.payload:
            metadata = event.payload.get('metadata', {})
            if metadata:
                sender_url = metadata.get('sender_url', '')
                if sender_url and sender_url in self.__callback_url:
                    self.__log_message_skipping_post(event, 'destination is originator')
                    return

        remote_event = RemoteEventData(self.__channel, event)

        try:
            APICaller.make_post_call(self.__callback_url, json=remote_event.dict,
                                     timeout_sec=self.__client_callback_timeout_sec)
            self.__log_message_posted_event(event)
        except (ApiConnectionError, InvalidSchema):
            self.__handle_unreachable_client()

    def __log_message_posted_event(self, event: Event):
        logging.getLogger().debug(f"Posted '{event.name}' to '{self.__callback_url}'")

    def __log_message_skipping_post(self, event: Event, reason: str):
        logging.getLogger().debug(
            f"Skipping posting '{event.name}' to '{self.__callback_url}'...{reason}")

    def __get_event_as_list(self) -> [str]:
        return [self.__event] if self.__event else []

    def __handle_unreachable_client(self):
        self.cancel()

        self.__event_dispatch.post_event(RegistrationEvent.CALLBACK_FAILED_EVENT.namespaced_value, {
            'channel': self.__channel,
            'callback_url': self.__callback_url,
            'event': self.__event
        })

    def dict(self) -> Dict[str, Any]:
        return {
            'channel': self.__channel,
            'callback_url': self.__callback_url,
            'event': self.__event
        }

    @staticmethod
    def to_dict_list(registrations) -> [Dict[str, Any]]:
        return [v.dict() for _, v in registrations.items()]


# -------------------------------------------------------------------------------------------------


class Registrant:
    __ALL_EVENT = ''

    def __init__(self, callback_url: str):
        self.__callback_url = callback_url
        self.__registrations: Dict[str, Dict[str, Registration]] = {}

        try:
            self.__pretty_print = Properties().get('PRETTY_PRINT')
        except PropertyNotSetError:
            self.__pretty_print = False

    @property
    def registrations(self) -> Dict[str, Dict[str, Registration]]:
        return self.__registrations

    @property
    def callback_url(self) -> str:
        return self.__callback_url

    def register(self, event: str = None, channel: str = '') -> bool:
        if channel not in self.__registrations:
            self.__registrations[channel] = {}

        registrations = self.__registrations[channel]

        key = event if event else self.__ALL_EVENT

        # Skip registration if registrant is already registered for event.
        if key in registrations:
            return False

        registrations[key] = Registration(self.__callback_url, event, channel)

        # self.__log_message_registrations()
        return True

    def unregister(self, event: str = None, channel: str = '') -> bool:
        # Skip un-registration if channel is not in list.
        if channel not in self.__registrations:
            return False

        registrations = self.__registrations[channel]

        key = event if event else self.__ALL_EVENT

        # Skip un-registration if registrant is not registered for event.
        if key not in registrations:
            return False

        registration = registrations.get(key)
        registration.cancel()
        del self.__registrations[channel][key]

        # Delete channel if no more events.
        if len(self.__registrations[channel]) == 0:
            del self.__registrations[channel]

        # self.log_message_registrations()
        return True

    def unregister_all(self) -> bool:
        is_unregistered = False
        for channel, registrations in self.__registrations.items():
            for event, registration in registrations.items():
                registration.cancel()
                is_unregistered = True

        self.__registrations = {}

        self.log_message_registrations(self.__callback_url)
        return is_unregistered

    def log_message_registrations(self, registrant_name: str):
        message = f'Registrations for: {registrant_name}\n'
        regs = []
        for channel, registrations in self.__registrations.items():
            for event, registration in registrations.items():
                if self.__pretty_print:
                    regs.append(registration.dict())
                else:
                    message += f'{registration.dict()}'

        if self.__pretty_print:
            message += json.dumps(regs, indent=2)

        logging.getLogger().debug(message)

    def dict(self) -> Dict[str, Any]:
        return {
            'callback_url': self.__callback_url,
            'registrations': Registration.to_dict_list(self.__registrations)
        }
