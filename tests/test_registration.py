import time

from eventdispatch import EventDispatch, Properties, EventDispatchManager, Event

from eventcenter.server.event_center import Registration, RemoteEventData, RegistrationEvent
from eventcenter.server.service import RESPONSE_OK
from helper import validate_handler_registered_for_event, validate_expected_handler_count, \
    EventHandler, validate_received_events

SOME_CHANNEL = 'some_channel'

event_dispatch: EventDispatch
handler: EventHandler


def setup_module():
    global event_dispatch

    event_dispatch = EventDispatchManager().default_dispatch
    event_dispatch.toggle_event_logging(True)

    Properties.set('CLIENT_CALLBACK_TIMEOUT_SEC', 10.0, is_skip_if_exists=True)


def setup_function():
    global handler, event_dispatch

    event_dispatch.clear_event_log()
    event_dispatch.clear_registered_handlers()

    handler = EventHandler()


def teardown_function():
    try:
        dispatcher = EventDispatchManager().event_dispatchers[SOME_CHANNEL]
        dispatcher.clear_event_log()
        dispatcher.clear_registered_handlers()
    except KeyError:
        pass

    EventDispatchManager().remove_event_dispatch(SOME_CHANNEL)


def teardown_module():
    pass


def test_init__when_registering_for_event():
    # Objective:
    # Registration's handler is registered with default event dispatch.

    # Test
    run_test_init__when_registering_for_event('')


def test_init__when_registering_for_event__with_channel():
    # Objective:
    # Registration's handler is registered with channel event dispatch.

    # Test
    run_test_init__when_registering_for_event(SOME_CHANNEL)


def run_test_init__when_registering_for_event(channel: str = ''):
    # Objective:
    # Registration's handler is registered with event dispatch.

    # Setup
    global event_dispatch
    callback_url = 'url'
    test_event = 'test_event'

    # Test
    reg = Registration(callback_url, test_event, channel)

    # Verify
    if channel:
        channel_event_dispatch = EventDispatchManager().event_dispatchers.get(channel)
    else:
        channel_event_dispatch = event_dispatch

    validate_expected_handler_count(1, channel_event_dispatch)
    validate_handler_registered_for_event(reg.on_event, test_event, channel_event_dispatch)
    assert reg.event == test_event


def test_init__when_registering_for_all_events(mocker):
    # Objective:
    # Registration's handler is registered with default event dispatch.

    # Test
    run_test_init__when_registering_for_all_events(mocker, '')


def test_init__when_registering_for_all_events__with_channel(mocker):
    # Objective:
    # Registration's handler is registered with channel event dispatch.

    # Test
    run_test_init__when_registering_for_all_events(mocker, SOME_CHANNEL)


def run_test_init__when_registering_for_all_events(mocker, channel: str = ''):
    # Objective:
    # Registration's handler is registered with event dispatch.

    # Setup
    global event_dispatch
    callback_url = 'url'
    mock_call = mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)

    # Test
    reg = Registration(callback_url, channel=channel)

    # Verify
    time.sleep(0.1)
    if channel:
        channel_event_dispatch = EventDispatchManager().event_dispatchers.get(channel)
    else:
        channel_event_dispatch = event_dispatch
    validate_expected_handler_count(1, channel_event_dispatch)
    validate_handler_registered_for_event(reg.on_event, event_dispatch=channel_event_dispatch)
    mock_call.assert_called()


def test_cancel__when_registered_for_event():
    # Objective:
    # Registration's handler is unregistered with default event dispatch.

    # Test
    run_test_cancel__when_registered_for_event('')


def test_cancel__when_registered_for_event__with_channel():
    # Objective:
    # Registration's handler is unregistered with channel event dispatch.

    # Test
    run_test_cancel__when_registered_for_event(SOME_CHANNEL)


def run_test_cancel__when_registered_for_event(channel: str = ''):
    # Objective:
    # Registration's handler is unregistered with event dispatch.

    # Setup
    global event_dispatch
    callback_url = 'url'
    test_event = 'test_event'
    reg = Registration(callback_url, test_event, channel)

    if channel:
        channel_event_dispatch = EventDispatchManager().event_dispatchers.get(channel)
    else:
        channel_event_dispatch = event_dispatch

    validate_expected_handler_count(1, channel_event_dispatch)

    # Test
    reg.cancel()

    # Verify
    validate_expected_handler_count(0, channel_event_dispatch)


def test_cancel__when_registered_for_all_events(mocker):
    # Objective:
    # Registration's handler is unregistered with default event dispatch.

    # Test
    run_test_cancel__when_registered_for_all_events(mocker, '')


def test_cancel__when_registered_for_all_events__with_channel(mocker):
    # Objective:
    # Registration's handler is unregistered with channel event dispatch.

    # Test
    run_test_cancel__when_registered_for_all_events(mocker, SOME_CHANNEL)


def run_test_cancel__when_registered_for_all_events(mocker, channel: str = ''):
    # Objective:
    # Registration's handler is unregistered with event dispatch.

    # Setup
    global event_dispatch
    callback_url = 'url'
    mock_call = mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)
    reg = Registration(callback_url)
    time.sleep(0.1)
    mock_call.assert_called()

    if channel:
        channel_event_dispatch = EventDispatchManager().event_dispatchers.get(channel)
    else:
        channel_event_dispatch = event_dispatch

    validate_expected_handler_count(1, channel_event_dispatch)

    # Test
    reg.cancel()

    # Verify
    validate_expected_handler_count(0, channel_event_dispatch)
    mock_call.assert_called()


def test_on_event__when_reachable_client(mocker):
    # Objective:
    # Remote handler's API is called, with default event object.

    # Test
    run_test_on_event__when_reachable_client(mocker, '')


def test_on_event__when_reachable_client__with_channel(mocker):
    # Objective:
    # Remote handler's API is called, with channel event object.

    # Test
    run_test_on_event__when_reachable_client(mocker, SOME_CHANNEL)


def run_test_on_event__when_reachable_client(mocker, channel: str = ''):
    # Objective:
    # Remote handler's API is called, with event object.

    # Setup
    global event_dispatch
    callback_url = 'url'
    mock_call = mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)
    reg = Registration(callback_url, channel=channel)

    if channel:
        channel_event_dispatch = EventDispatchManager().event_dispatchers.get(channel)
    else:
        channel_event_dispatch = event_dispatch

    validate_expected_handler_count(1, channel_event_dispatch)

    event = Event('test_event', {'name': 'Alice'})
    remote_event = RemoteEventData(channel, event)

    # Test
    reg.on_event(event)

    # Verify
    mock_call.assert_called_with(callback_url, remote_event.dict, timeout_sec=10.0)


def test_on_event__when_unreachable_client():
    # Objective:
    # Unreachable client is unregistered with default event dispatch.
    # Event sent about unreachable client.

    # Test
    run_test_on_event__when_unreachable_client('')


def test_on_event__when_unreachable_client__with_channel():
    # Objective:
    # Unreachable client is unregistered with channel event dispatch.
    # Event sent about unreachable client.

    # Test
    run_test_on_event__when_unreachable_client(SOME_CHANNEL)


def run_test_on_event__when_unreachable_client(channel: str = ''):
    # Objective:
    # Unreachable client is unregistered with event dispatch.
    # Event sent about unreachable client.

    # Setup
    global event_dispatch, handler
    callback_url = 'http://localhost:9999/some/nonexisting/endpoint'
    test_event = 'test_event'
    reg = Registration(callback_url, test_event, channel=channel)

    if channel:
        channel_event_dispatch = EventDispatchManager().event_dispatchers.get(channel)
    else:
        channel_event_dispatch = event_dispatch

    validate_expected_handler_count(1, channel_event_dispatch)
    event = Event(test_event)

    # Register watcher for callback failure event.
    channel_event_dispatch.register(handler.on_event, [
        RegistrationEvent.CALLBACK_FAILED_EVENT.namespaced_value
    ])
    validate_expected_handler_count(2, channel_event_dispatch)

    # Test
    reg.on_event(event)

    # Verify
    time.sleep(0.1)
    validate_expected_handler_count(1, channel_event_dispatch)
    validate_received_events(handler, [RegistrationEvent.CALLBACK_FAILED_EVENT])
