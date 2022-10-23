from flask import Flask, request

from core import EventDispatch, Data, Event
from network import FlaskAppRunner, APICaller
from properties import Properties

RESPONSE_OK = {
    'status': 'OK'
}


class EventCenter(FlaskAppRunner):
    def __init__(self):
        self.__event_registration_manager = EventRegistrationManager()

        app = Flask('EventCenter')
        port = Properties().get('EVENT_CENTER_PORT')
        super().__init__('0.0.0.0', port, app)
        self.start()

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
        def post_event():
            data = Event.from_dict(request.json)
            EventDispatch().post_event(data.name, data.payload)
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
    def from_dict(data: dict):
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
    def from_dict(data: dict):
        event_receiver = EventReceiver.from_dict(data.get('event_receiver'))
        events = data.get('events')
        return RegistrationData(event_receiver, events)


class EventRegistrationManager:
    def __init__(self):
        self.__registrants: dict[str: Registrant] = {}

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

        if events:
            for event in events:
                registrant.register(event)
        else:
            registrant.register()

    def unregister(self, event_receiver: EventReceiver, events: [str]):
        key = self.__build_event_receiver_key(event_receiver)

        try:
            registrant = self.__registrants[key]

            if events:
                for event in events:
                    registrant.unregister(event)
            else:
                registrant.unregister()
            if len(registrant.registrations) == 0:
                del self.__registrants[key]
        except KeyError:
            # No registrant, so nothing to do.
            return

    def get_registrant(self, event_receiver: EventReceiver):
        key = self.__build_event_receiver_key(event_receiver)
        try:
            return self.__registrants[key]
        except KeyError:
            return None

    @staticmethod
    def __build_event_receiver_key(event_receiver: EventReceiver):
        return event_receiver.name + ',' + event_receiver.callback_url


class Registration:
    def __init__(self, callback_url: str, event: str = None):
        self.__callback_url = callback_url
        self.__event = event

        events = [self.__event] if self.__event else []
        EventDispatch().register(self.on_event, events)

    @property
    def event(self) -> str:
        return self.__event

    def cancel(self):
        events = [self.__event] if self.__event else []
        EventDispatch().unregister(self.on_event, events)

    def on_event(self, event: Event):
        # Don't propagate event if event originated from destination url.
        sender_url = event.payload.get('sender_url', '')
        if sender_url and sender_url in self.__callback_url:
            return

        APICaller.make_post_api_call(self.__callback_url, event.raw)


class Registrant:
    def __init__(self, event_receiver: EventReceiver):
        self.__event_receiver = event_receiver
        self.__registrations: dict[str: Registration] = {}

    @property
    def registrations(self) -> dict[str: Registration]:
        return self.__registrations

    @property
    def event_receiver(self) -> EventReceiver:
        return self.__event_receiver

    def register(self, event: str = None):
        key = event if event else ''

        # Skip registration if registrant is already registered for event.
        if key in self.__registrations:
            return

        self.__registrations[key] = Registration(self.__event_receiver.callback_url, event)

    def unregister(self, event: str = None):
        key = event if event else ''

        # Skip un-registration if registrant is not registered for event.
        if key not in self.__registrations:
            return

        registration = self.__registrations.get(key)
        registration.cancel()
        del self.__registrations[key]
