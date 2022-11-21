import os
from typing import Callable, Any

import pytest
from eventdispatch import EventDispatch, Event
from eventdispatch.core import EventDispatchEvent, register_for_events


class TestEventHandler:
    def __init__(self):
        self.received_events = {}

    def on_event(self, event: Event):
        if event.name in self.received_events:
            pytest.fail('Same event received again')

        self.received_events[event.name] = event


def register_handler_for_event(handler, event=None):
    event_log_count = len(EventDispatch().event_log)
    handler_count = get_handler_count()

    events = [event] if event else []

    register_for_events(handler.on_event, events)
    validate_expected_handler_count(handler_count + 1)
    validate_event_log_count(event_log_count + 1)


def get_handler_count():
    count = 0
    for event_name, handlers in EventDispatch().event_handlers.items():
        count += len(handlers)
    return count


def validate_event_log_count(expected_count: int):
    assert len(EventDispatch().event_log) == expected_count


def validate_expected_handler_count(expected_count: int):
    assert get_handler_count() == expected_count


def validate_handler_registered_for_all_events(handler: TestEventHandler):
    validate_test_handler_registered_for_event(handler, None)


def validate_test_handler_registered_for_event(handler: TestEventHandler, event: str = None):
    validate_handler_registered_for_event(handler.on_event, event)


def validate_handler_registered_for_event(handler: Callable, event: str = None):
    # Check if validating for all events.
    if not event:
        handlers = EventDispatch().all_event_handlers
    else:
        handlers = EventDispatch().event_handlers.get(event, [])
    assert handler in handlers


def validate_received_events(handler: TestEventHandler, expected_events: [Any], is_ignore_registration_event=True):
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


def validate_received_event(handler: TestEventHandler, expected_event: str, expected_payload: dict):
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
