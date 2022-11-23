from eventdispatch import Properties

from eventcenter.server.event_center import Registrant, EventReceiver
from eventcenter.server.service import RESPONSE_OK

registrant: Registrant


def setup_module():
    Properties.set('CLIENT_CALLBACK_TIMEOUT_SEC', 10.0, is_skip_if_exists=True)


def setup_function():
    global registrant

    event_receiver = EventReceiver('Tester', 'url')
    registrant = Registrant(event_receiver)
    validate_expected_registration_count(0)


def teardown_function():
    pass


def teardown_module():
    pass


def test_register__when_not_registered__registering_for_event(mocker):
    # Objective:
    # Registration is created for event.

    # Setup
    test_event = 'test_event'
    mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)

    # Test
    registrant.register(test_event)

    # Verify
    validate_expected_registration_count(1)
    assert test_event in registrant.registrations
    reg = registrant.registrations[test_event]
    assert reg.event == test_event


def test_register__when_not_registered__registering_for_all_events(mocker):
    # Objective:
    # Registration is created for all events.

    # Setup
    all_event_key = ''
    mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)

    # Test
    registrant.register()

    # Verify
    validate_expected_registration_count(1)
    assert all_event_key in registrant.registrations
    reg = registrant.registrations[all_event_key]
    assert reg.event is None


def test_register__when_already_registered_for_event():
    # Objective:
    # New registration is not created.

    # Setup
    test_event = 'test_event'
    registrant.register(test_event)
    validate_expected_registration_count(1)
    assert test_event in registrant.registrations

    # Test
    registrant.register(test_event)

    # Verify
    validate_expected_registration_count(1)
    assert test_event in registrant.registrations


def test_unregister__when_registered_for_event():
    # Objective:
    # Registration is cancelled for event, registration object is removed from list.

    # Setup
    test_event = 'test_event'
    registrant.register(test_event)
    validate_expected_registration_count(1)
    assert test_event in registrant.registrations

    # Test
    registrant.unregister(test_event)

    # Verify
    validate_expected_registration_count(0)
    assert test_event not in registrant.registrations


def test_unregister__when_registered_for_all_events(mocker):
    # Objective:
    # Registration is cancelled for all events, registration object is removed from list.

    # Setup
    all_event_key = ''
    mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)
    registrant.register()
    validate_expected_registration_count(1)
    assert all_event_key in registrant.registrations

    # Test
    registrant.unregister()

    # Verify
    # mock_call.assert_called()
    validate_expected_registration_count(0)
    assert all_event_key not in registrant.registrations


def test_unregister__when_not_registered():
    # Objective:
    # Registration is not cancelled, registration list remains the same.

    # Setup
    test_event1 = 'test_event1'
    registrant.register(test_event1)
    validate_expected_registration_count(1)
    assert test_event1 in registrant.registrations

    test_event2 = 'test_event2'

    # Test
    registrant.unregister(test_event2)

    # Verify
    validate_expected_registration_count(1)
    assert test_event2 not in registrant.registrations
    assert test_event1 in registrant.registrations


def validate_expected_registration_count(expected_count):
    assert len(registrant.registrations) == expected_count
