import argparse
import sys

from eventdispatch import Event, Properties, register_for_events

from demo.remote_workers.util import log_event, start_event_router

DEFAULT_HOST = 'http://localhost'
DEFAULT_PORT = 7010
DEFAULT_EVENT_CENTER_URL = 'http://localhost:5000'

program_args = {}


def main():
    get_program_args()
    set_properties()
    start_event_router()
    register_for_events(on_event, [])
    print(f"Running 'Event Listener' on port: {Properties.get('EVENT_CENTER_CALLBACK_PORT')}")


def on_event(event: Event):
    log_event(on_event, event)


def get_program_args():
    global program_args
    parser = argparse.ArgumentParser()
    parser.add_argument('--callback_host', '-ch')
    parser.add_argument('--callback_port', '-cp')
    parser.add_argument('--event_center_url', '-ecu')
    program_args = vars(parser.parse_args(sys.argv[1:]))


def set_properties():
    Properties.set('EVENT_CENTER_CALLBACK_HOST', program_args.get('callback_host') or DEFAULT_HOST)
    Properties.set('EVENT_CENTER_CALLBACK_PORT', program_args.get('callback_port') or DEFAULT_PORT)
    Properties.set('EVENT_CENTER_URL', program_args.get('event_center_url') or DEFAULT_EVENT_CENTER_URL)


if __name__ == '__main__':
    main()
