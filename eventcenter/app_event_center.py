import logging
import os

from eventdispatch import Properties
from flask import Flask

from eventcenter import EventCenterService

app: Flask

# Check if port is specified in environment (otherwise use default).
port = int(os.environ.get('EC_PORT', 6000))

# Check desired log level from environment ('1' == DEBUG, otherwise INFO).
log_level = os.environ.get('EC_LOG_DEBUG', '1')

# Check flask run level from environment ('1' == DEBUG, otherwise INFO).
run_as_a_server = os.environ.get('RUN_AS_A_SERVER', '0')

logging.getLogger().setLevel(level=logging.DEBUG if log_level == '1' else logging.INFO)


def main():
    global app

    Properties().set('REGISTRANTS_FILE_PATH', 'server/registrants.json')
    Properties().set('EVENT_CENTER_PORT', port)
    Properties().set('CLIENT_CALLBACK_TIMEOUT_SEC', 20)
    Properties().set('RUN_AS_A_SERVER', True if run_as_a_server == '1' else False)
    Properties().set('PRETTY_PRINT', True)

    ecs = EventCenterService()
    app = ecs.app
    print(f"Event Center started on port: {Properties().get('EVENT_CENTER_PORT')}")


main()
