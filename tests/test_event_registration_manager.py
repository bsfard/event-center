import json
import os
import time

import pytest
from eventdispatch import Properties, Event, EventDispatch, EventDispatchManager

from eventcenter.server.event_center import EventRegistrationManager, RegistrationEvent, RegistrationData, \
    RemoteEventData
from eventcenter.server.service import RESPONSE_OK
from test_helper import validate_file_exists, validate_file_not_exists, validate_file_content, validate_event_log_count

SOME_CHANNEL = 'some_channel'

event_dispatch: EventDispatch
event_registration_manager: EventRegistrationManager
callback_url = 'http://localhost'


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
    # Registrant, channel, and events are properly persisted.

    # Setup
    filepath = Properties.get('REGISTRANTS_FILE_PATH')
    channel = ''
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'
    data = RegistrationData(callback_url, [test_event1, test_event2], channel)

    expected_registrants = {
        "registrants": {
            callback_url: {
                channel: [test_event1, test_event2]
            }
        }
    }

    # Test
    event_registration_manager.register(data)

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)

    # Verify (registrant info got persisted correctly).
    validate_file_exists(filepath)
    validate_file_content(filepath, json.dumps(expected_registrants))


def test_register__when_not_registered__registering_for_all_events():
    # Objective:
    # Registration is made for all events.
    # Registrant, channel, and events are properly persisted.

    # Setup
    filepath = Properties.get('REGISTRANTS_FILE_PATH')
    channel = ''
    data = RegistrationData(callback_url, [], channel)

    expected_registrants = {
        "registrants": {
            callback_url: {
                channel: [
                    ""
                ]
            }
        }
    }

    # Test
    event_registration_manager.register(data)

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)

    # Verify (registrant info got persisted correctly).
    validate_file_exists(filepath)
    validate_file_content(filepath, json.dumps(expected_registrants))


def test_register__when_registered__registering_for_same_event():
    # Objective:
    # Existing registrant is unchanged.

    # Setup
    channel = ''
    test_event = 'test_event'
    data = RegistrationData(callback_url, [test_event], channel)
    create_registrant_with_data(data, callback_url, 1)

    # Test
    event_registration_manager.register(data)

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)


def test_register__when_registered__registering_for_different_event():
    # Objective:
    # Existing registrant is used and gets an additional event registered.

    # Setup
    channel = ''
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'
    create_registrant(callback_url, channel, 1, [test_event1])

    data = RegistrationData(callback_url, [test_event2], channel)

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
    create_registrant_with_data(data, callback_url, 1)

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
    create_registrant(callback_url, channel, 1, [test_event1, test_event2])

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
    create_registrant_with_data(data, callback_url, 1)
    event_registration_manager.register(data)

    # Test
    event_registration_manager.unregister(data)

    # Verify
    validate_expected_registrant_count(0)


def test_unregister_all__when_not_registered__no_other_registrants():
    # Objective:
    # Nothing happens, no registrants are in memory and persisted.

    # Setup
    filepath = Properties.get('REGISTRANTS_FILE_PATH')
    validate_expected_registrant_count(0)

    expected_registrants = {
        "registrants": {}
    }

    # Test
    event_registration_manager.unregister_all(callback_url)

    # Verify
    validate_expected_registrant_count(0)
    validate_file_exists(filepath)
    validate_file_content(filepath, json.dumps(expected_registrants))


def test_unregister_all__when_not_registered__have_other_registrants():
    # Objective:
    # Nothing happens, other registrants are still there in memory and persisted.

    # Setup
    filepath = Properties.get('REGISTRANTS_FILE_PATH')
    callback_url1 = 'some_other_url'

    channel = ''
    test_event = 'test_event'
    create_registrant(callback_url, channel, 1, [test_event])

    expected_registrants = {
        "registrants": {
            callback_url: {
                channel: [
                    test_event
                ]
            }
        }
    }

    # Test
    event_registration_manager.unregister_all(callback_url1)

    # Verify
    validate_expected_registrant_count(1)
    validate_file_exists(filepath)
    validate_file_content(filepath, json.dumps(expected_registrants))


def test_unregister_all__when_registered_for_event_and_all_events__on_same_channel__no_other_registrants(mocker):
    # Objective:
    # Registrant's registrations are not in memory nor persisted.

    # Setup
    filepath = Properties.get('REGISTRANTS_FILE_PATH')

    channel = ''
    test_event = 'test_event'
    mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)
    create_registrant(callback_url, channel, 1, [test_event])
    create_registrant(callback_url, channel, 1, [])

    expected_registrants = {
        "registrants": {}
    }

    # Test
    event_registration_manager.unregister_all(callback_url)

    # Verify
    time.sleep(0.1)
    validate_expected_registrant_count(0)
    validate_file_exists(filepath)
    validate_file_content(filepath, json.dumps(expected_registrants))


def test_unregister_all__when_registered_for_event_and_all_events__on_same_channel__have_other_registrants(mocker):
    # Objective:
    # Registrant's registrations are not in memory nor persisted.
    # Other registrants are still there in memory and persisted.

    # Setup
    filepath = Properties.get('REGISTRANTS_FILE_PATH')

    channel = ''
    test_event = 'test_event'
    mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)
    create_registrant(callback_url, channel, 1, [test_event])

    test_url = 'http://localhost:1000'
    create_registrant(test_url, channel, 2, [test_event])
    create_registrant(test_url, channel, 2, [])

    expected_registrants = {
        "registrants": {
            callback_url: {
                channel: [
                    test_event
                ]
            }
        }
    }

    # Test
    event_registration_manager.unregister_all(test_url)

    # Verify
    time.sleep(0.1)
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)
    validate_file_exists(filepath)
    validate_file_content(filepath, json.dumps(expected_registrants))


def test_unregister_all__when_registered_for_events__on_multiple_channels__no_other_registrants(mocker):
    # Objective:
    # Registrant's registrations are not in memory nor persisted.

    # Setup
    filepath = Properties.get('REGISTRANTS_FILE_PATH')

    channel = 'ch-1'
    channel2 = 'ch-2'
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'
    mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)
    create_registrant(callback_url, channel, 1, [test_event1])
    create_registrant(callback_url, channel, 1, [])
    create_registrant(callback_url, channel2, 1, [test_event1, test_event2])

    expected_registrants = {
        "registrants": {}
    }

    # Test
    event_registration_manager.unregister_all(callback_url)

    # Verify
    time.sleep(0.1)
    validate_expected_registrant_count(0)
    validate_file_exists(filepath)
    validate_file_content(filepath, json.dumps(expected_registrants))


def create_registrant(url: str, channel: str, expected_registrant_count: int, events: [str]):
    data = RegistrationData(url, events, channel)
    event_registration_manager.register(data)
    validate_expected_registrant_count(expected_registrant_count)
    validate_have_registrant(url)


def create_registrant_with_data(data: RegistrationData, url: str, expected_registrant_count: int):
    event_registration_manager.register(data)
    validate_expected_registrant_count(expected_registrant_count)
    validate_have_registrant(url)


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
