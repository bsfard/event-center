import os
from typing import Callable, Any

import pytest
from eventdispatch import EventDispatch, Event, Properties
from eventdispatch.core import EventDispatchEvent, register_for_events, EventDispatchManager

from constants import EVENT_CENTER_PORT

default_event_dispatch: EventDispatch = EventDispatchManager().default_dispatch


class EventHandler:
    def __init__(self):
        self.received_events = {}

    def on_event(self, event: Event):
        if event.name in self.received_events:
            pytest.fail('Same event received again')

        self.received_events[event.name] = event


def prep_default_event_dispatch():
    global default_event_dispatch
    default_event_dispatch.toggle_event_logging(True)


def set_properties_for_event_center_interfacing():
    # Seed properties that components in tests will need.
    Properties().set('EVENT_CENTER_URL', f'http://localhost:{EVENT_CENTER_PORT}', is_skip_if_exists=True)
    Properties().set('EVENT_CENTER_CALLBACK_HOST', 'http://localhost', is_skip_if_exists=True)
    Properties().set('EVENT_CENTER_CALLBACK_PORT', 9000, is_skip_if_exists=True)
    Properties().set('RUN_AS_A_SERVER', True, is_skip_if_exists=True)


def register_handler_for_event(handler, event=None, event_dispatch: EventDispatch = None):
    event_dispatch = event_dispatch if event_dispatch else default_event_dispatch

    event_log_count = len(event_dispatch.event_log)
    handler_count = get_handler_count()

    events = [event] if event else []

    register_for_events(handler.on_event, events)
    validate_expected_handler_count(handler_count + 1)
    validate_event_log_count(event_log_count + 1)


def get_handler_count(event_dispatch: EventDispatch = None):
    event_dispatch = event_dispatch if event_dispatch else default_event_dispatch
    count = 0
    for event_name, handlers in event_dispatch.event_handlers.items():
        count += len(handlers)
    return count


def validate_event_log_count(expected_count: int, event_dispatch: EventDispatch = None):
    event_dispatch = event_dispatch if event_dispatch else default_event_dispatch
    assert len(event_dispatch.event_log) == expected_count


def validate_expected_handler_count(expected_count: int, event_dispatch: EventDispatch = None):
    assert get_handler_count(event_dispatch) == expected_count


def validate_handler_registered_for_all_events(handler: EventHandler):
    validate_test_handler_registered_for_event(handler, None)


def validate_test_handler_registered_for_event(handler: EventHandler, event: str = None):
    validate_handler_registered_for_event(handler.on_event, event)


def validate_handler_registered_for_event(handler: Callable, event: str = None, event_dispatch: EventDispatch = None):
    event_dispatch = event_dispatch if event_dispatch else default_event_dispatch

    # Check if validating for all events.
    if not event:
        handlers = event_dispatch.all_event_handlers
    else:
        handlers = event_dispatch.event_handlers.get(event, [])
    assert handler in handlers


def validate_received_events(handler: EventHandler, expected_events: [Any], is_ignore_registration_event=True):
    expected_events = EventDispatch.to_string_events(expected_events)
    registration_event = EventDispatch.to_string_event(EventDispatchEvent.HANDLER_REGISTERED)
    if is_ignore_registration_event:
        if registration_event in handler.received_events:
            handler.received_events.pop(registration_event)

    assert len(handler.received_events) == len(expected_events)

    validated_events = []
    for expected_event in expected_events:
        assert expected_event in handler.received_events
        validated_events.append(expected_event)

    # Remove received events that have been validated.
    for event in validated_events:
        handler.received_events.pop(event)


def validate_received_event(handler: EventHandler, expected_event: str, expected_payload: dict):
    for name, event in handler.received_events.items():
        if name == expected_event:
            if event.payload.keys() == expected_payload.keys():
                # if event.payload == expected_payload:
                return
    pytest.fail(f'Could not find expected event: {expected_event}')


def validate_file_exists(filepath):
    assert os.path.isfile(filepath)


def validate_file_not_exists(filepath):
    assert not os.path.isfile(filepath)


def validate_file_content(filepath, content):
    try:
        with open(filepath, 'r') as file:
            data = file.read()
        assert data == content
    except FileNotFoundError:
        pytest.fail(f"Could not find file '{filepath}'")
