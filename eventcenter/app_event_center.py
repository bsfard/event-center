import logging
import os

from eventdispatch import Properties
from flask import Flask

from eventcenter import EventCenterService

app: Flask

# Check if port is specified in environment (otherwise use default).
port = int(os.environ.get('EC_PORT', 6000))

# Check desired log level from environment ('1' == DEBUG, otherwise INFO).
log_level = os.environ.get('EC_LOG_DEBUG', '0')

logging.basicConfig(level=logging.DEBUG if log_level == '1' else logging.INFO)


def main():
    global app

    Properties().set('REGISTRANTS_FILE_PATH', 'server/registrants.json')
    Properties().set('EVENT_CENTER_PORT', port)
    Properties().set('CLIENT_CALLBACK_TIMEOUT_SEC', 20)
    Properties().set('FLASK_DEBUG', '1')

    ecs = EventCenterService()
    app = ecs.app
    print(f"Event Center started on port: {Properties().get('EVENT_CENTER_PORT')}")


main()
