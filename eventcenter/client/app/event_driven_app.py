import argparse
import json
import logging
import signal
import sys
from typing import Dict, Any

from eventdispatch import Properties, Event, unregister_from_events, register_for_events

from eventcenter.client.app.service import ServiceEvent, RUN_AS_A_SERVER
from eventcenter.client.event_center_adapter import EVENT_CENTER_URL, EVENT_CENTER_CALLBACK_HOST, \
    EVENT_CENTER_CALLBACK_PORT
from eventcenter.client.router import start_event_router, stop_event_router, ROUTER_NAME

# Event-Driven App properties
PRETTY_PRINT = 'PRETTY_PRINT'
MONITOR_EVENTS = 'MONITOR_EVENTS'

DEFAULT_EVENT_CENTER_URL = 'http://localhost:6000'
DEFAULT_CALLBACK_HOST = 'http://localhost'
DEFAULT_CALLBACK_PORT = 7000

logging.basicConfig(level=logging.INFO)


class AppInterface:
    def add_program_args(self, parser: argparse.ArgumentParser):
        pass

    def set_properties(self, args: Dict[str, Any]):
        pass


class EventDrivenApp(AppInterface):
    __logger = logging.getLogger(__name__)
    __is_pretty_print = False

    """
    PURPOSE:
    - Base class for common/reusable functionality for apps.
    - Enables event posting and receiving with remote event center.
    - Allows custom program arguments to be defined.
    - Allows custom properties to be set.
    """

    def __init__(self, name: str = 'EventDrivenApp'):
        # Get program arguments.
        parser = argparse.ArgumentParser()
        self.add_program_args(parser)
        index = 1 if '--' not in sys.argv else sys.argv.index('--') + 1
        args = vars(parser.parse_args(sys.argv[index:]))

        self.__set_initial_properties(name, args)

        start_event_router()

        # For local dev assistance only (register to receive all events).
        if Properties().get(MONITOR_EVENTS):
            EventDrivenApp.__is_pretty_print = Properties().get(PRETTY_PRINT)
            register_for_events(self.on_event, [])

        # Set any additional properties from subclasses.
        self.set_properties(args)

        # Shutdown this app gracefully, if service is shut down remotely (via API call).
        register_for_events(self.on_service_shutdown, [ServiceEvent.STOPPED])

        # Set up to listen for CTRL+C command to stop app.
        signal.signal(signal.SIGINT, self.handle_program_interrupt)

    def add_program_args(self, parser: argparse.ArgumentParser):
        parser.add_argument('-ec', '--event_center_url',
                            metavar='',
                            default=DEFAULT_EVENT_CENTER_URL,
                            help=f'Full URL to reach the remote Event Center (Default: {DEFAULT_EVENT_CENTER_URL})')

        parser.add_argument('-ch', '--callback_host',
                            metavar='',
                            default=DEFAULT_CALLBACK_HOST,
                            help=f'Your hostname, reachable by the remote Event Center to send you events (Default: {DEFAULT_CALLBACK_HOST})')

        parser.add_argument('-cp', '--callback_port',
                            metavar='',
                            default=DEFAULT_CALLBACK_PORT,
                            help=f'Your port, reachable by the remote Event Center to send you events (Default: {DEFAULT_CALLBACK_PORT})')

        parser.add_argument('-raas', '--router_as_a_server',
                            action='store_true', default=False,
                            help=f'Launch router as a server.  Use when launching as python or flask app. Do not use if launching as a daemon or via gunicorn')

        parser.add_argument('-me', '--monitor_events',
                            action='store_true', default=False,
                            help=f'Enable monitoring all events during app')

        parser.add_argument('-pp', '--pretty_print',
                            action='store_true', default=False,
                            help=f'Enable pretty print format for json payloads')

    @staticmethod
    def __set_initial_properties(name: str, args: Dict[str, Any]):
        # Set event center and routing properties.
        Properties().set(EVENT_CENTER_URL, args.get('event_center_url'))
        Properties().set(EVENT_CENTER_CALLBACK_HOST, args.get('callback_host'))
        Properties().set(EVENT_CENTER_CALLBACK_PORT, args.get('callback_port'))

        # Set app properties.
        Properties().set(ROUTER_NAME, name)
        Properties().set(PRETTY_PRINT, args.get('pretty_print'))
        Properties().set(MONITOR_EVENTS, args.get('monitor_events'))
        Properties().set(RUN_AS_A_SERVER, args.get('router_as_a_server'))

    @staticmethod
    def on_event(event: Event):
        header = f'[{event.time_formatted}][#{event.id}]: {event.name}'

        if EventDrivenApp.__is_pretty_print:
            payload = json.dumps(event.payload, indent=2)
        else:
            payload = event.payload
        EventDrivenApp.__logger.info(f" Got event:\n{header}\n{payload}\n")

    def on_service_shutdown(self, _):
        unregister_from_events(self.on_service_shutdown, [ServiceEvent.STOPPED])
        self.shutdown()

    @staticmethod
    def shutdown():
        unregister_from_events(EventDrivenApp.on_event, [])
        stop_event_router()

    @staticmethod
    def handle_program_interrupt(_1, _2):
        EventDrivenApp.__logger.info('Shutting down app')
        EventDrivenApp.shutdown()
        sys.exit(0)
