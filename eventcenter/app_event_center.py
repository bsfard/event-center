import argparse
import logging
import sys

from eventdispatch import Properties

from eventcenter import EventCenterService

DEFAULT_PORT = 5000
DEFAULT_REGISTRANTS_FILE_PATH = 'server/registrants.json'
DEFAULT_CALLBACK_TIMEOUT_SEC = 10

program_args = {}


def main():
    logging.basicConfig(level=logging.INFO)

    get_program_args()
    set_properties()
    EventCenterService()
    print(f"Event Center started on port: {Properties.get('EVENT_CENTER_PORT')}")


def get_program_args():
    global program_args
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p')
    parser.add_argument('--registrants_path', '-rp')
    parser.add_argument('--timeout_sec', '-t')
    parser.add_argument('--allow_cors', '-ac')
    program_args = vars(parser.parse_args(sys.argv[1:]))


def set_properties():
    Properties.set('EVENT_CENTER_PORT', program_args.get('port') or DEFAULT_PORT)
    Properties.set('REGISTRANTS_FILE_PATH', program_args.get('registrants_path') or DEFAULT_REGISTRANTS_FILE_PATH)
    Properties.set('CLIENT_CALLBACK_TIMEOUT_SEC', program_args.get('timeout_sec') or DEFAULT_CALLBACK_TIMEOUT_SEC)
    Properties.set('ALLOW_CORS', program_args.get('allow_cors') == '1')


if __name__ == '__main__':
    main()
