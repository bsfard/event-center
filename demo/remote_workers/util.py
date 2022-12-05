import argparse
import logging
import sys
from typing import Any

from eventdispatch import Event, Properties

logging.basicConfig(level=logging.INFO)


def get_program_args(default_callback_host: str = 'http://localhost',
                     default_callback_port: int = 0,
                     default_event_center_host: str = 'http://localhost',
                     default_event_center_port: int = 5000,
                     default_registrants_filepath: str = 'registrants.json',
                     default_client_callback_timeout_sec: float = 10.0):
    parser = argparse.ArgumentParser()
    parser.add_argument('--callback_host', '-ch')
    parser.add_argument('--callback_port', '-cp')
    parser.add_argument('--event_center_host', '-ech')
    parser.add_argument('--event_center_port', '-ecp')
    parser.add_argument('--registrants_file_path', '-rfp')
    parser.add_argument('--client_callback_timeout_sec', '-ccts')
    parsed_args = vars(parser.parse_args(sys.argv[1:]))

    # Set up properties.
    ec_host = parsed_args.get('event_center_host') or default_event_center_host
    ec_port = parsed_args.get('event_center_port') or default_event_center_port
    Properties.set('EVENT_CENTER_PORT', ec_port)
    Properties.set('EVENT_CENTER_URL', f'{ec_host}:{ec_port}')

    Properties.set('EVENT_CENTER_CALLBACK_HOST', parsed_args.get('callback_host') or default_callback_host)

    port = parsed_args.get('callback_port') or default_callback_port
    if type(port) == str:
        port = int(port)
    Properties.set('EVENT_CENTER_CALLBACK_PORT', port)

    registrants_filepath = parsed_args.get('registrants_file_path') or default_registrants_filepath
    Properties.set('REGISTRANTS_FILE_PATH', registrants_filepath)

    client_callback_timeout_sec = parsed_args.get('client_callback_timeout_sec') or default_client_callback_timeout_sec
    Properties.set('CLIENT_CALLBACK_TIMEOUT_SEC', client_callback_timeout_sec)


def log_event(for_class: Any, event: Event):
    get_logger(for_class).info(f" Got event '{event.name}'\n{event.raw}\n")


def get_logger(cls: Any):
    return logging.getLogger(cls.__class__.__name__)
