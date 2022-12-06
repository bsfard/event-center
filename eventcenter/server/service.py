import threading

from eventdispatch import Properties, NamespacedEnum, post_event, Event
from flask import Flask, request

from eventcenter import FlaskAppRunner
from eventcenter.server.event_center import EventRegistrationManager, RegistrationData

RESPONSE_OK = {
    'success': 'true'
}


class ECEvent(NamespacedEnum):
    STARTED = 'started'
    STOPPED = 'stopped'

    def get_namespace(self) -> str:
        return 'event_center'


class EventCenterService(FlaskAppRunner):
    def __init__(self):
        self.__event_registration_manager = EventRegistrationManager()

        app = Flask('EventCenter')
        port = Properties.get('EVENT_CENTER_PORT')
        super().__init__('0.0.0.0', port, app)
        self.start()

        post_event(ECEvent.STARTED)

        @app.route('/register', methods=['POST'])
        def register():
            data = RegistrationData.from_dict(request.json)
            self.__event_registration_manager.register(data.callback_url, data.events)
            return RESPONSE_OK

        @app.route('/unregister', methods=['POST'])
        def unregister():
            data = RegistrationData.from_dict(request.json)
            self.__event_registration_manager.unregister(data.callback_url, data.events)
            return RESPONSE_OK

        @app.route('/post_event', methods=['POST'])
        def post():
            data = Event.from_dict(request.json)
            post_event(data.name, data.payload)
            return RESPONSE_OK

        @app.route('/shutdown', methods=['GET'])
        def shutdown():
            threading.Thread(target=self.shutdown, args=[]).start()
            return RESPONSE_OK

    def shutdown(self):
        super().shutdown()
        post_event(ECEvent.STOPPED)
