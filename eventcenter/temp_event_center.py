import os

from eventdispatch import Properties
from flask import Flask

from eventcenter import EventCenterService

app: Flask

port = int(os.environ.get('EC_PORT', 6000))


def main():
    global app

    Properties().set('REGISTRANTS_FILE_PATH', 'server/registrants.json')
    Properties().set('EVENT_CENTER_PORT', port)
    Properties().set('FLASK_DEBUG', '1')

    ecs = EventCenterService()
    app = ecs.app
    print(f"Event Center started on port: {Properties().get('EVENT_CENTER_PORT')}")


main()
