import argparse
import sys
from typing import Dict, Any

from eventdispatch import Properties

DEFAULT_EVENT_CENTER_URL = 'http://localhost:6000'
DEFAULT_CALLBACK_HOST = 'http://localhost'


def prep_client_app_settings(override_port: int = None):
    args = get_program_args()

    if override_port:
        args['callback_port'] = override_port

    set_properties(args)


def get_program_args() -> Dict[str, Any]:
    parser = argparse.ArgumentParser()
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
                        help=f'Your port, reachable by the remote Event Center to send you events')

    parser.add_argument('-raas', '--router_as_a_server',
                        action='store_true', default=False,
                        help=f'Launch router as a server.  Use when launching as python or flask app. Do not use if launching as a daemon or via gunicorn')

    # This argument is only for demo client apps.
    parser.add_argument('-pp', '--pretty_print',
                        action='store_true', default=False,
                        help=f'Enable pretty print format for json payloads')

    return vars(parser.parse_args(sys.argv[1:]))


def set_properties(args: Dict[str, Any]):
    # Property for reaching remote Event Center.
    Properties().set('EVENT_CENTER_URL', args.get('event_center_url'))

    # Properties for setting your host name and port, for remote Event Center to send you events.
    Properties().set('EVENT_CENTER_CALLBACK_HOST', args.get('callback_host'))
    Properties().set('EVENT_CENTER_CALLBACK_PORT', args.get('callback_port'))
    Properties().set('RUN_AS_A_SERVER', args.get('router_as_a_server'))
    Properties().set('CLIENT_LOGGING_PRETTY_PRINT', args.get('pretty_print'))
