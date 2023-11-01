import logging
import threading
from typing import Dict, Any

from eventcenter import FlaskAppRunner
from eventdispatch import Properties, NamespacedEnum, post_event
from flask import Flask

# Service properties.
SERVICE_PORT = 'SERVICE_PORT'
RUN_AS_A_SERVER = 'RUN_AS_A_SERVER'

RESPONSE_OK = {
    'success': 'true'
}

RESPONSE_ERROR = {
    'success': 'false'
}


class ServiceEvent(NamespacedEnum):
    STARTED = 'started'
    STOPPED = 'stopped'

    def get_namespace(self) -> str:
        return 'service'


class Service(FlaskAppRunner):
    __logger = logging.getLogger(__name__)

    """
    PURPOSE:
    - Creates and starts a service, with endpoints to:
        - ping
        - shutdown
    """

    def __init__(self, name: str = 'Service', run_as_a_server: bool = False):
        self.app = Flask(name)
        raas = run_as_a_server or Properties().get(RUN_AS_A_SERVER)
        port = Properties().get(SERVICE_PORT)
        super().__init__('0.0.0.0', port, self.app, raas)

        self.start()

        post_event(ServiceEvent.STARTED, {'service': self.app.name})

        self.__logger.info(f"{name} started on port: {port}")

        @self.app.route('/ping')
        def ping():
            return self.make_response(RESPONSE_OK)

        @self.app.route('/api/v1/shutdown', methods=['GET'])
        def shutdown():
            threading.Thread(target=self.shutdown, args=[]).start()
            return {
                'success': 'true'
            }

    @staticmethod
    def _success(results: Any) -> Dict[str, Any]:
        return {
            'success': 'true',
            'results': results
        }

    @staticmethod
    def _error(reason: Any) -> Dict[str, Any]:
        return {
            'success': 'false',
            'reasons': reason
        }

    def shutdown(self):
        super().shutdown()
        post_event(ServiceEvent.STOPPED, {'service': self.app.name})
