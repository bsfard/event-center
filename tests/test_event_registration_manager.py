import json
import os

import pytest
from eventdispatch import Properties, Event, EventDispatch, EventDispatchManager

from eventcenter.server.event_center import EventRegistrationManager, RegistrationEvent, RegistrationData, \
    RemoteEventData
from eventcenter.server.service import RESPONSE_OK
from test_helper import validate_file_exists, validate_file_not_exists, validate_file_content, validate_event_log_count

SOME_CHANNEL = 'some_channel'

event_dispatch: EventDispatch
event_registration_manager: EventRegistrationManager
callback_url = 'url'


def setup_module():
    global event_dispatch

    event_dispatch = EventDispatchManager().default_dispatch
    event_dispatch.toggle_event_logging(True)

    Properties.set('REGISTRANTS_FILE_PATH', 'registrants.json', is_skip_if_exists=True)
    Properties.set('CLIENT_CALLBACK_TIMEOUT_SEC', 10.0, is_skip_if_exists=True)


def setup_function():
    global event_registration_manager

    event_dispatch.clear_event_log()
    event_dispatch.clear_registered_handlers()

    event_registration_manager = EventRegistrationManager()
    event_registration_manager.clear_registrants()


def teardown_function():
    pass


def teardown_module():
    pass


def test_init__no_registrants_file():
    # Objective:
    # No failure
    # Registrants file is created, and contains an empty dictionary of registrants
    # Manager has an empty list of registrants

    # Setup
    filepath = Properties.get('REGISTRANTS_FILE_PATH')
    os.remove(filepath)
    validate_file_not_exists(filepath)
    expected_content = '{"registrants": {}}'

    # Test
    er_manager = EventRegistrationManager()

    # Verify
    validate_file_exists(filepath)
    validate_file_content(filepath, expected_content)
    validate_expected_registrant_count(0, er_manager)


def test_init__registrants_file_is_empty():
    # Objective:
    # No failure
    # Registrants file has an empty dictionary of registrants
    # Manager has an empty list of registrants

    # Setup
    filepath = Properties.get('REGISTRANTS_FILE_PATH')
    os.remove(filepath)
    validate_file_not_exists(filepath)
    expected_content = '{"registrants": {}}'

    # Create an empty file.
    open(filepath, 'x')

    # Test
    er_manager = EventRegistrationManager()

    # Verify
    validate_file_exists(filepath)
    validate_file_content(filepath, expected_content)
    validate_expected_registrant_count(0, er_manager)


def test_init__when_no_prior_registrants():
    # Objective:
    # Manager has an empty dictionary of registrants

    # Setup
    filepath = Properties.get('REGISTRANTS_FILE_PATH')
    os.remove(filepath)
    validate_file_not_exists(filepath)
    expected_registrants = '{"registrants": {}}'

    # Create an empty file, and write registrants into it.
    with open(filepath, 'x') as file:
        file.write(expected_registrants)

    # Test
    er_manager = EventRegistrationManager()

    # Verify
    validate_file_exists(filepath)
    validate_file_content(filepath, expected_registrants)
    validate_expected_registrant_count(0, er_manager)


def test_init__when_have_prior_registrants():
    # Objective:
    # Manager has a dictionary of registrants, matching the ones from the registrant file.

    # Setup
    filepath = Properties().get('REGISTRANTS_FILE_PATH')
    os.remove(filepath)
    validate_file_not_exists(filepath)
    callback_url1 = "http://localhost:8000/on_event"
    callback_url2 = "http://localhost:9000/on_event"
    expected_registrants = {
        "registrants": {
            callback_url1: {
                "some_channel": ["test_event1", "test_event2"],
                "": ["test_event3"],
            },
            callback_url2: {
                "another_channel": ["test_event4"],
                "": ["test_event3"],
            }
        }
    }

    # Create an empty file, and write registrants into it.
    with open(filepath, 'x') as file:
        file.write(json.dumps(expected_registrants))

    # Test
    er_manager = EventRegistrationManager()

    # Verify
    validate_file_exists(filepath)
    validate_expected_registrant_count(2, er_manager)
    validate_have_registrant(callback_url1, er_manager)
    validate_have_registrant(callback_url2, er_manager)


def test_register__when_not_registered__registering_for_events():
    # Objective:
    # Registrations are made for all specified events.

    # Setup
    channel = ''
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'
    data = RegistrationData(callback_url, [test_event1, test_event2], channel)

    # Test
    event_registration_manager.register(data)

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)


def test_register__when_not_registered__registering_for_all_events(mocker):
    # Objective:
    # Registration is made for all events.

    # Setup
    channel = ''
    data = RegistrationData(callback_url, [], channel)
    mock_call = mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)

    # Test
    event_registration_manager.register(data)

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)
    mock_call.assert_called()


def test_register__when_registered__registering_for_event():
    # Objective:
    # Existing registrant is used.

    # Setup
    channel = ''
    test_event = 'test_event'
    data = RegistrationData(callback_url, [test_event], channel)
    event_registration_manager.register(data)
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)

    # Test
    event_registration_manager.register(data)

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)


def test_unregister__when_not_registered():
    # Objective:
    # Nothing is done.

    # Setup
    channel = ''
    test_event = 'test_event'
    data = RegistrationData(callback_url, [test_event], channel)

    # Test
    event_registration_manager.unregister(data)

    # Verify
    validate_expected_registrant_count(0)


def test_unregister__when_registered_for_event__unregistering_for_event():
    # Objective:
    # Registrant is removed from list.

    # Setup
    channel = ''
    test_event = 'test_event'
    data = RegistrationData(callback_url, [test_event], channel)
    event_registration_manager.register(data)
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)

    # Test
    event_registration_manager.unregister(data)

    # Verify
    validate_expected_registrant_count(0)


def test_unregister__when_registered_for_multiple_events__unregistering_for_some_events():
    # Objective:
    # Registrant is not removed from list.

    # Setup
    channel = ''
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'
    data = RegistrationData(callback_url, [test_event1, test_event2], channel)
    event_registration_manager.register(data)
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)

    data = RegistrationData(callback_url, [test_event1], channel)

    # Test
    event_registration_manager.unregister(data)

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)


def test_unregister__when_registered_for_all_events():
    # Objective:
    # Registrant is removed from list.

    # Setup
    channel = ''
    data = RegistrationData(callback_url, [], channel)
    event_registration_manager.register(data)
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)

    # Test
    event_registration_manager.unregister(data)

    # Verify
    validate_expected_registrant_count(0)


def test_post():
    # Objective:
    # The default event dispatch gets the event posted on it.

    # Test
    run_test_post('')


def test_post__when_have_channel():
    # Objective:
    # The specific channel event dispatch gets the event posted on it.

    # Test
    run_test_post(SOME_CHANNEL)


def run_test_post(channel: str = ''):
    # Setup
    event = Event('test_event')
    remote_event_data = RemoteEventData(channel, event)
    if channel:
        EventDispatchManager().add_event_dispatch(channel)
    channel_event_dispatch = EventDispatchManager().event_dispatchers.get(channel)
    channel_event_dispatch.toggle_event_logging(True)
    channel_event_dispatch.log_event_if_no_handlers = True

    # Test
    event_registration_manager.post(remote_event_data)

    # Verify
    channel_event_dispatch = EventDispatchManager().event_dispatchers.get(channel)
    validate_event_log_count(1, channel_event_dispatch)

    # Teardown
    channel_event_dispatch.toggle_event_logging(False)
    channel_event_dispatch.log_event_if_no_handlers = False


def test_post__when_channel_not_exist():
    # Objective:
    # No exception while posting event.
    # Event dispatch is created (exists now) for new channel

    # Setup
    channel = "none-existent-channel"
    event = Event('test_event')
    remote_event_data = RemoteEventData(channel, event)

    # Verify channel is not already being managed.  If so, this is a testing error.
    if channel in EventDispatchManager().event_dispatchers:
        pytest.fail('Expected channel not to exist')

    # Test
    event_registration_manager.post(remote_event_data)

    # Verify (channel was added)
    assert EventDispatchManager().event_dispatchers.get(channel)


def test_on_event__when_callback_failed():
    # Objective:
    # Unreachable client is unregistered from given event.

    # Setup
    channel = ''
    test_event = 'test_event'
    data = RegistrationData(callback_url, [test_event], channel)
    event_registration_manager.register(data)
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)

    event = Event(RegistrationEvent.CALLBACK_FAILED_EVENT.namespaced_value, {
        'callback_url': callback_url,
        'event': test_event
    })

    # Test
    event_registration_manager.on_event(event)

    # Verify
    validate_expected_registrant_count(0)


def validate_expected_registrant_count(expected_count: int, manager: EventRegistrationManager = None):
    manager = manager if manager else event_registration_manager
    assert len(manager.registrants) == expected_count


def validate_have_registrant(evt_receiver: str, manager: EventRegistrationManager = None):
    manager = manager if manager else event_registration_manager
    assert manager.get_registrant(evt_receiver)
