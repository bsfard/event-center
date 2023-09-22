import argparse
import logging
import sys

from eventdispatch import Properties
from flask import Flask

from eventcenter import EventCenterService

DEFAULT_PORT = 6000
DEFAULT_REGISTRANTS_FILE_PATH = 'server/registrants.json'
DEFAULT_CALLBACK_TIMEOUT_SEC = 10

program_args = {}

is_flask_debug = False

app: Flask


def main():
    global app

    logging.basicConfig(level=logging.DEBUG)

    get_program_args()
    set_properties()
    ecs = EventCenterService()
    app = ecs.app
    print(f"Event Center started on port: {Properties().get('EVENT_CENTER_PORT')}")


def get_program_args():
    global program_args
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p')
    parser.add_argument('--registrants_path', '-r')
    parser.add_argument('--timeout_sec', '-t')
    parser.add_argument('--allow_cors', '-c')
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
    Properties().set('EVENT_CENTER_PORT', program_args.get('port') or DEFAULT_PORT)
    Properties().set('REGISTRANTS_FILE_PATH', program_args.get('registrants_path') or DEFAULT_REGISTRANTS_FILE_PATH)
    Properties().set('CLIENT_CALLBACK_TIMEOUT_SEC', program_args.get('timeout_sec') or DEFAULT_CALLBACK_TIMEOUT_SEC)
    Properties().set('ALLOW_CORS', program_args.get('allow_cors') == '1')

    if is_flask_debug:
        Properties().set('FLASK_DEBUG', '1')


main()
