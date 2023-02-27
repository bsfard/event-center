import argparse
import logging
import sys

from eventdispatch import Event, Properties, register_for_events
from flask import Flask

from demo.remote_workers.util import log_event
from eventcenter import start_event_router, EventRouter

DEFAULT_HOST = 'http://localhost'
DEFAULT_PORT = 7011
DEFAULT_EVENT_CENTER_URL = 'http://localhost:5000'

program_args = {}

is_flask_debug = False

app: Flask


def main():
    global app

    logging.basicConfig(level=logging.INFO)

    get_program_args()
    set_properties()
    start_event_router()

    er: EventRouter = Properties.get('EVENT_ROUTER')
    app = er.server

    register_for_events(on_event, [])
    print(f"Running 'Event Listener' on port: {Properties.get('EVENT_CENTER_CALLBACK_PORT')}")


def on_event(event: Event):
    log_event(on_event, event)


def get_program_args():
    global program_args
    parser = argparse.ArgumentParser()
    parser.add_argument('--callback_host')
    parser.add_argument('--callback_port', '-p')
    parser.add_argument('--event_center_url', '-e')
    program_args = parse_program_args(parser)


def parse_program_args(parser: argparse.ArgumentParser) -> dict:
    global is_flask_debug

    start_index = 1

    # Check if launching with "flask run" (local dev/debug mode).
    if sys.argv[1] == 'run':
        is_flask_debug = True
        start_index = 2
    return vars(parser.parse_args(sys.argv[start_index:]))


def set_properties():
    Properties.set('EVENT_CENTER_CALLBACK_HOST', program_args.get('callback_host') or DEFAULT_HOST)
    Properties.set('EVENT_CENTER_CALLBACK_PORT', program_args.get('callback_port') or DEFAULT_PORT)
    Properties.set('EVENT_CENTER_URL', program_args.get('event_center_url') or DEFAULT_EVENT_CENTER_URL)

    if is_flask_debug:
        Properties.set('FLASK_DEBUG', '1')


main()
