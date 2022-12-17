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

        app = Flask('EventCenter')
        port = Properties.get('EVENT_CENTER_PORT')
        super().__init__('0.0.0.0', port, app)
        self.start()

        post_event(ECEvent.STARTED, {})

        @app.route('/register', methods=['POST'])
        def register():
            registration_data = RegistrationData.from_dict(request.json)
            self.__event_registration_manager.register(registration_data)
            return RESPONSE_OK

        @app.route('/unregister', methods=['POST'])
        def unregister():
            registration_data = RegistrationData.from_dict(request.json)
            self.__event_registration_manager.unregister(registration_data)
            return RESPONSE_OK

        @app.route('/unregister_all', methods=['POST'])
        def unregister_all():
            callback_url = request.json.get('callback_url', '')
            if not callback_url:
                RESPONSE_ERROR['error'] = 'Missing callback url'
                return RESPONSE_ERROR

            self.__event_registration_manager.unregister_all(callback_url)
            return RESPONSE_OK

        @app.route('/post_event', methods=['POST'])
        def post():
            remote_event_data = RemoteEventData.from_dict(request.json)
            self.__event_registration_manager.post(remote_event_data)
            return RESPONSE_OK

        @app.route('/shutdown', methods=['GET'])
        def shutdown():
            threading.Thread(target=self.shutdown, args=[]).start()
            return RESPONSE_OK

    def shutdown(self):
        super().shutdown()
        post_event(ECEvent.STOPPED)
