import threading

from eventdispatch import Properties, NamespacedEnum, post_event
from flask import Flask, request

from eventcenter import FlaskAppRunner
from eventcenter.server.event_center import EventRegistrationManager, RegistrationData, RemoteEventData

RESPONSE_OK = {
    'success': 'true'
}

RESPONSE_ERROR = {
    'success': 'false'
}


# -------------------------------------------------------------------------------------------------

class ECEvent(NamespacedEnum):
    STARTED = 'started'
    STOPPED = 'stopped'

    def get_namespace(self) -> str:
        return 'event_center'


# -------------------------------------------------------------------------------------------------

class EventCenterService(FlaskAppRunner):
    def __init__(self):
        self.__event_registration_manager = EventRegistrationManager()

        self.app = Flask('EventCenter')
        port = Properties().get('EVENT_CENTER_PORT')
        super().__init__('0.0.0.0', port, self.app)

        if not self.is_flask_debug():
            self.start()

        post_event(ECEvent.STARTED, {})

        @self.app.route('/ping', methods=['GET'])
        def ping():
            return self.make_response(RESPONSE_OK)

        @self.app.route('/register', methods=['POST'])
        def register():
            registration_data = RegistrationData.from_dict(request.json)
            self.__event_registration_manager.register(registration_data)
            return self.make_response(RESPONSE_OK)

        @self.app.route('/unregister', methods=['POST'])
        def unregister():
            registration_data = RegistrationData.from_dict(request.json)
            self.__event_registration_manager.unregister(registration_data)
            return self.make_response(RESPONSE_OK)

        @self.app.route('/unregister_all', methods=['POST'])
        def unregister_all():
            callback_url = request.json.get('callback_url', '')
            if not callback_url:
                RESPONSE_ERROR['error'] = 'Missing callback url'
                return RESPONSE_ERROR

            self.__event_registration_manager.unregister_all(callback_url)
            return self.make_response(RESPONSE_OK)

        @self.app.route('/post_event', methods=['POST'])
        def post():
            remote_event_data = RemoteEventData.from_dict(request.json)
            self.__event_registration_manager.post(remote_event_data)
            return self.make_response(RESPONSE_OK)

        @self.app.route('/track_events', methods=['POST'])
        def watch():
            request.json

        # Admin APIs
        @self.app.route('/registrants', methods=['GET'])
        def get_registrants():
            response = self.__event_registration_manager.pack_registrants()
            response.update(RESPONSE_OK)
            return self.make_response(response)

        @self.app.route('/shutdown', methods=['GET'])
        def shutdown():
            threading.Thread(target=self.shutdown, args=[]).start()
            return RESPONSE_OK

    def shutdown(self):
        super().shutdown()
        post_event(ECEvent.STOPPED)
