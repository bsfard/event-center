import json
import logging

from eventdispatch import Event, Properties, register_for_events
from flask import Flask

from demo.remote_workers.client_helper import prep_client_app_settings
from eventcenter import start_event_router, EventRouter
from eventcenter.client.router import ROUTER_NAME

app: Flask

logging.basicConfig(level=logging.DEBUG)

is_pretty_print = False


def main():
    global app, is_pretty_print

    prep_client_app_settings()

    is_pretty_print = Properties().get('PRETTY_PRINT')

    Properties().set(ROUTER_NAME, 'All_Event_Listener')

    start_event_router()

    er: EventRouter = Properties().get('EVENT_ROUTER')
    app = er.server

    register_for_events(on_event, [])
    print(f"Running 'All Event Listener' on port: {Properties().get('EVENT_CENTER_CALLBACK_PORT')}")


def on_event(event: Event):
    header = f'[{event.time_formatted}][#{event.id}]: {event.name}'
    if is_pretty_print:
        payload = json.dumps(event.payload, indent=2)
    else:
        payload = event.payload
    logging.info(f" Got event:\n{header}\n{payload}\n")


if __name__ == '__main__':
    main()
