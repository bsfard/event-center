import json
import os

from eventdispatch import Properties, Event

from eventcenter.server.event_center import EventRegistrationManager, RegistrationEvent
from eventcenter.server.service import RESPONSE_OK
from test_helper import validate_file_exists, validate_file_not_exists, validate_file_content

event_registration_manager: EventRegistrationManager
callback_url = 'url'


def setup_module():
    Properties.set('REGISTRANTS_FILE_PATH', 'registrants.json', is_skip_if_exists=True)
    Properties.set('CLIENT_CALLBACK_TIMEOUT_SEC', 10.0, is_skip_if_exists=True)


def setup_function():
    global event_registration_manager

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
    callback_url2 = "http://localhost:9000/on_event"
    expected_registrants = {
        "registrants": {
            callback_url2: {
                "events": ["test_event1", "test_event2"]
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
    validate_expected_registrant_count(1, er_manager)
    validate_have_registrant(callback_url2, er_manager)


def test_register__when_not_registered__registering_for_events():
    # Objective:
    # Registrations are made for all specified events.

    # Setup
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'

    # Test
    event_registration_manager.register(callback_url, [test_event1, test_event2])

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)


def test_register__when_not_registered__registering_for_all_events(mocker):
    # Objective:
    # Registration is made for all events.

    # Setup
    mock_call = mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)

    # Test
    event_registration_manager.register(callback_url, [])

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)
    mock_call.assert_called()


def test_register__when_registered__registering_for_event():
    # Objective:
    # Existing registrant is used.

    # Setup
    test_event = 'test_event'
    event_registration_manager.register(callback_url, [test_event])
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)

    # Test
    event_registration_manager.register(callback_url, [test_event])

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)


def test_unregister__when_not_registered():
    # Objective:
    # Nothing is done.

    # Setup
    test_event = 'test_event'

    # Test
    event_registration_manager.unregister(callback_url, [test_event])

    # Verify
    validate_expected_registrant_count(0)


def test_unregister__when_registered_for_event__unregistering_for_event():
    # Objective:
    # Registrant is removed from list.

    # Setup
    test_event = 'test_event'
    event_registration_manager.register(callback_url, [test_event])
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)

    # Test
    event_registration_manager.unregister(callback_url, [test_event])

    # Verify
    validate_expected_registrant_count(0)


def test_unregister__when_registered_for_multiple_events__unregistering_for_some_events():
    # Objective:
    # Registrant is not removed from list.

    # Setup
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'
    event_registration_manager.register(callback_url, [test_event1, test_event2])
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)

    # Test
    event_registration_manager.unregister(callback_url, [test_event1])

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)


def test_unregister__when_registered_for_all_events():
    # Objective:
    # Registrant is removed from list.

    # Setup
    event_registration_manager.register(callback_url, [])
    validate_expected_registrant_count(1)
    validate_have_registrant(callback_url)

    # Test
    event_registration_manager.unregister(callback_url, [])

    # Verify
    validate_expected_registrant_count(0)


def test_on_event__when_callback_failed_with_max_retries():
    # Objective:
    # Unreachable client is unregistered from given event.

    # Setup
    test_event = 'test_event'
    event_registration_manager.register(callback_url, [test_event])
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
