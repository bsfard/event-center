from eventdispatch import Properties, EventDispatchManager, EventDispatch

from eventcenter.server.event_center import Registrant
from eventcenter.server.service import RESPONSE_OK

event_dispatch: EventDispatch
registrant: Registrant


def setup_module():
    global event_dispatch

    event_dispatch = EventDispatchManager().default_dispatch
    event_dispatch.toggle_event_logging(True)

    Properties.set('CLIENT_CALLBACK_TIMEOUT_SEC', 10.0, is_skip_if_exists=True)


def setup_function():
    global registrant

    event_dispatch.clear_event_log()
    event_dispatch.clear_registered_handlers()

    registrant = Registrant('url')
    validate_expected_registration_count(0)


def teardown_function():
    pass


def teardown_module():
    pass


def test_register__when_not_registered__registering_for_event(mocker):
    # Objective:
    # Registration is created for event.

    # Setup
    channel = ''
    test_event = 'test_event'
    expected_key = f'{channel}:{test_event}'
    mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)

    # Test
    registrant.register(test_event, channel)

    # Verify
    validate_expected_registration_count(1)
    assert expected_key in registrant.registrations
    reg = registrant.registrations[expected_key]
    assert reg.event == test_event


def test_register__when_not_registered__registering_for_all_events(mocker):
    # Objective:
    # Registration is created for all events.

    # Setup
    channel = ''
    all_event_key = ''
    expected_key = f'{channel}:{all_event_key}'
    mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)

    # Test
    registrant.register(channel=channel)

    # Verify
    validate_expected_registration_count(1)
    assert expected_key in registrant.registrations
    reg = registrant.registrations[expected_key]
    assert reg.event is None


def test_register__when_already_registered_for_event():
    # Objective:
    # New registration is not created.

    # Setup
    channel = ''
    test_event = 'test_event'
    expected_key = f'{channel}:{test_event}'
    registrant.register(test_event, channel)
    validate_expected_registration_count(1)
    assert expected_key in registrant.registrations

    # Test
    registrant.register(test_event, channel)

    # Verify
    validate_expected_registration_count(1)
    assert expected_key in registrant.registrations


def test_unregister__when_registered_for_event():
    # Objective:
    # Registration is cancelled for event, registration object is removed from list.

    # Setup
    channel = ''
    test_event = 'test_event'
    expected_key = f'{channel}:{test_event}'
    registrant.register(test_event, channel)
    validate_expected_registration_count(1)
    assert expected_key in registrant.registrations

    # Test
    registrant.unregister(test_event, channel)

    # Verify
    validate_expected_registration_count(0)
    assert expected_key not in registrant.registrations


def test_unregister__when_registered_for_all_events(mocker):
    # Objective:
    # Registration is cancelled for all events, registration object is removed from list.

    # Setup
    channel = ''
    all_event_key = ''
    expected_key = f'{channel}:{all_event_key}'
    mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)
    registrant.register(channel=channel)
    validate_expected_registration_count(1)
    assert expected_key in registrant.registrations

    # Test
    registrant.unregister()

    # Verify
    validate_expected_registration_count(0)
    assert expected_key not in registrant.registrations


def test_unregister__when_not_registered():
    # Objective:
    # Registration is not cancelled, registration list remains the same.

    # Setup
    channel = ''
    test_event1 = 'test_event1'
    expected_key1 = f'{channel}:{test_event1}'
    registrant.register(test_event1, channel)
    validate_expected_registration_count(1)
    assert expected_key1 in registrant.registrations

    test_event2 = 'test_event2'
    expected_key2 = f'{channel}:{test_event2}'

    # Test
    registrant.unregister(test_event2, channel)

    # Verify
    validate_expected_registration_count(1)
    assert expected_key2 not in registrant.registrations
    assert expected_key1 in registrant.registrations


def validate_expected_registration_count(expected_count):
    assert len(registrant.registrations) == expected_count
