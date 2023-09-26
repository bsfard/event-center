import json
import logging
import time

from eventdispatch import Event, Properties, register_for_events
from flask import Flask

from demo.remote_workers.client_helper import prep_client_app_settings
from eventcenter import start_event_router, EventRouter

app: Flask

logging.basicConfig(level=logging.DEBUG)

is_pretty_print = False


def main():
    global app, is_pretty_print

    prep_client_app_settings()

    is_pretty_print = Properties().get('CLIENT_LOGGING_PRETTY_PRINT')

    start_event_router()

    er: EventRouter = Properties().get('EVENT_ROUTER')
    app = er.server

    register_for_events(on_event, [])
    print(f"Running 'All Event Listener' on port: {Properties().get('EVENT_CENTER_CALLBACK_PORT')}")


def on_event(event: Event):
    if is_pretty_print:
        payload = json.dumps(event.dict, indent=2)
    else:
        payload = event.dict
    logging.info(f" Got event '{event.name}'\nPayload:\n{payload}\n")


if __name__ == '__main__':
    main()
