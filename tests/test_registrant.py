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
    global event_dispatch, registrant

    event_dispatch.clear_event_log()
    event_dispatch.clear_registered_handlers()

    registrant = Registrant('http://localhost')
    validate_expected_registration_count('', 0)


def teardown_function():
    pass


def teardown_module():
    pass


def test_register__when_not_registered__registering_for_event(mocker):
    # Objective:
    # Registration is created for event.

    # Setup
    global registrant
    channel = ''
    test_event = 'test_event'
    mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)

    # Test
    registrant.register(test_event, channel)

    # Verify
    validate_expected_registration_count(channel, 1)
    validate_registered_channel_and_event(channel, test_event)


def test_register__when_not_registered__registering_for_all_events(mocker):
    # Objective:
    # Registration is created for all events.

    # Setup
    global registrant
    channel = ''
    mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)

    # Test
    registrant.register(channel=channel)

    # Verify
    validate_expected_registration_count(channel, 1)
    validate_registered_channel_and_event(channel, None)


def test_register__when_already_registered_for_event():
    # Objective:
    # New registration is not created.

    # Setup
    global registrant
    channel = ''
    test_event = 'test_event'
    create_registration(channel, test_event, 1)

    # Test
    registrant.register(test_event, channel)

    # Verify
    validate_expected_registration_count(channel, 1)
    validate_registered_channel_and_event(channel, test_event)


def test_unregister__when_not_registered_for_event__registered_for_other_events():
    # Objective:
    # Other registrations are not cancelled, registration list remains the same.

    # Setup
    global registrant
    channel = ''
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'
    create_registration(channel, test_event1, 1)

    # Test
    registrant.unregister(test_event2, channel)

    # Verify
    validate_expected_registration_count(channel, 1)
    validate_registered_channel_and_event(channel, test_event1)


def test_unregister__when_registered_for_event_and_other_events():
    # Objective:
    # Specified registration is cancelled.
    # Other registrations are not cancelled.

    # Setup
    global registrant
    channel = ''
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'
    create_registration(channel, test_event1, 1)
    create_registration(channel, test_event2, 2)

    # Test
    registrant.unregister(test_event2, channel)

    # Verify
    validate_expected_registration_count(channel, 1)
    validate_registered_channel_and_event(channel, test_event1)


def test_unregister__when_registered_for_event():
    # Objective:
    # Registration is cancelled for event, registration object is removed from list.

    # Setup
    global registrant
    channel = ''
    test_event = 'test_event'
    create_registration(channel, test_event, 1)

    # Test
    registrant.unregister(test_event, channel)

    # Verify
    validate_expected_registration_count(channel, 0)
    assert channel not in registrant.registrations


def test_unregister__when_registered_for_all_events(mocker):
    # Objective:
    # Registration is cancelled for all events, registration object is removed from list.

    # Setup
    global registrant
    channel = ''
    mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)
    create_registration(channel, None, 1)

    # Test
    registrant.unregister()

    # Verify
    validate_expected_registration_count(channel, 0)
    assert channel not in registrant.registrations


def test_unregister_all__when_not_registered():
    # Objective:
    # No exception occurs.

    # Setup
    global registrant
    channel = ''
    validate_expected_registration_count(channel, 0)

    # Test
    registrant.unregister_all()

    # Verify
    validate_expected_registration_count(channel, 0)
    assert channel not in registrant.registrations


def test_unregister_all__when_registered_for_event():
    # Objective:
    # All registrations for registrant are deleted.

    # Setup
    global registrant
    channel = ''
    test_event = 'test_event'
    create_registration(channel, test_event, 1)

    # Test
    registrant.unregister_all()

    # Verify
    validate_expected_registration_count(channel, 0)
    assert channel not in registrant.registrations


def test_unregister_all__when_registered_for_all_events():
    # Objective:
    # All registrations for registrant are deleted.

    # Setup
    global registrant
    channel = ''
    create_registration(channel, None, 1)

    # Test
    registrant.unregister_all()

    # Verify
    validate_expected_registration_count(channel, 0)
    assert channel not in registrant.registrations


def test_unregister_all__when_registered_for_events_and_all_events(mocker):
    # Objective:
    # All registrations for registrant are deleted.

    # Setup
    global registrant
    channel = ''
    test_event = 'test_event'
    mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)
    create_registration(channel, test_event, 1)
    create_registration(channel, None, 2)

    registrant.register(None, channel)
    validate_expected_registration_count(channel, 2)
    validate_registered_channel_and_event(channel, None)

    # Test
    registrant.unregister_all()

    # Verify
    validate_expected_registration_count(channel, 0)
    assert channel not in registrant.registrations


def create_registration(channel: str, event: str = None, expected_count: int = 0):
    global registrant

    registrant.register(event, channel)
    validate_expected_registration_count(channel, expected_count)
    validate_registered_channel_and_event(channel, event)


def validate_registered_channel_and_event(channel: str = '', event: str = None):
    global registrant

    event = event if event else ''

    assert channel in registrant.registrations
    events = registrant.registrations[channel]
    assert event in events
    reg = events[event]

    if event:
        assert reg.event == event
    else:
        assert reg.event is None


def validate_expected_registration_count(channel: str, expected_count):
    global registrant
    assert len(registrant.registrations.get(channel, [])) == expected_count
