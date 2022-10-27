from unittest.mock import call

from eventcenter.service import EventRegistrationManager, EventReceiver

event_registration_manager: EventRegistrationManager
event_receiver: EventReceiver


def setup_module():
    pass


def setup_function():
    global event_receiver, event_registration_manager

    event_receiver = EventReceiver('Tester', 'url')

    event_registration_manager = EventRegistrationManager()
    validate_expected_registrant_count(0)


def teardown_function():
    pass


def teardown_module():
    pass


def test_register__when_not_registered__registering_for_events(mocker):
    # Objective:
    # Registrations are made for all specified events.

    # Setup
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'
    mock_call = mocker.patch('eventcenter.service.Registrant.register', return_value=None)

    # Test
    event_registration_manager.register(event_receiver, [test_event1, test_event2])

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(event_receiver)
    assert mock_call.call_count == 2
    assert mock_call.call_args_list == [call(test_event1), call(test_event2)]


def test_register__when_not_registered__registering_for_all_events(mocker):
    # Objective:
    # Registration is made for all events.

    # Setup
    mock_call = mocker.patch('eventcenter.service.Registrant.register', return_value=None)

    # Test
    event_registration_manager.register(event_receiver, [])

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(event_receiver)
    mock_call.assert_called_once_with()


def test_register__when_registered__registering_for_event(mocker):
    # Objective:
    # Existing registrant is used.

    # Setup
    test_event = 'test_event'
    event_registration_manager.register(event_receiver, [test_event])
    validate_expected_registrant_count(1)
    validate_have_registrant(event_receiver)

    mock_call = mocker.patch('eventcenter.service.Registrant.register', return_value=None)

    # Test
    event_registration_manager.register(event_receiver, [test_event])

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(event_receiver)
    mock_call.assert_called_once_with(test_event)


def test_unregister__when_not_registered():
    # Objective:
    # Nothing is done.

    # Setup
    test_event = 'test_event'

    # Test
    event_registration_manager.unregister(event_receiver, [test_event])

    # Verify
    validate_expected_registrant_count(0)


def test_unregister__when_registered_for_event__unregistering_for_event(mocker):
    # Objective:
    # Registrant is removed from list.

    # Setup
    test_event = 'test_event'
    event_registration_manager.register(event_receiver, [test_event])
    validate_expected_registrant_count(1)
    validate_have_registrant(event_receiver)

    mocker.patch('eventcenter.service.Registration.cancel', return_value=None)

    # Test
    event_registration_manager.unregister(event_receiver, [test_event])

    # Verify
    validate_expected_registrant_count(0)


def test_unregister__when_registered_for_multiple_events__unregistering_for_some_events(mocker):
    # Objective:
    # Registrant is not removed from list.

    # Setup
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'
    event_registration_manager.register(event_receiver, [test_event1, test_event2])
    validate_expected_registrant_count(1)
    validate_have_registrant(event_receiver)

    mocker.patch('eventcenter.service.Registration.cancel', return_value=None)

    # Test
    event_registration_manager.unregister(event_receiver, [test_event1])

    # Verify
    validate_expected_registrant_count(1)
    validate_have_registrant(event_receiver)


def test_unregister__when_registered_for_all_events(mocker):
    # Objective:
    # Registrant is removed from list.

    # Setup
    event_registration_manager.register(event_receiver, [])
    validate_expected_registrant_count(1)
    validate_have_registrant(event_receiver)

    mocker.patch('eventcenter.service.Registration.cancel', return_value=None)

    # Test
    event_registration_manager.unregister(event_receiver, [])

    # Verify
    validate_expected_registrant_count(0)


def validate_expected_registrant_count(expected_count):
    assert len(event_registration_manager.registrants) == expected_count


def validate_have_registrant(evt_receiver: EventReceiver):
    assert event_registration_manager.get_registrant(evt_receiver)
