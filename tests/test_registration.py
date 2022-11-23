from eventdispatch import EventDispatch, Event, Properties, register_for_events

from eventcenter.server.event_center import Registration, EventReceiver, RegistrationEvent
from eventcenter.server.service import RESPONSE_OK
from test_helper import validate_handler_registered_for_event, validate_expected_handler_count, TestEventHandler, \
    validate_received_events

handler: TestEventHandler


def setup_module():
    Properties.set('CLIENT_CALLBACK_TIMEOUT_SEC', 10.0, is_skip_if_exists=True)


def setup_function():
    global handler

    EventDispatch().clear_event_log()
    EventDispatch().clear_registered_handlers()

    handler = TestEventHandler()


def teardown_function():
    pass


def teardown_module():
    pass


def test_init__when_registering_for_event():
    # Objective:
    # Registration's handler is registered with Event Dispatch.

    # Setup
    test_event = 'test_event'
    event_receiver = EventReceiver('', callback_url='url')

    # Test
    reg = Registration(event_receiver, test_event)

    # Verify
    validate_expected_handler_count(1)
    validate_handler_registered_for_event(reg.on_event, test_event)
    assert reg.event == test_event


def test_init__when_registering_for_all_events(mocker):
    # Objective:
    # Registration's handler is registered with Event Dispatch.

    # Setup
    callback_url = 'url'
    event_receiver = EventReceiver('', callback_url)
    mock_call = mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)

    # Test
    reg = Registration(event_receiver)

    # Verify
    validate_expected_handler_count(1)
    validate_handler_registered_for_event(reg.on_event)
    mock_call.assert_called()


def test_cancel__when_registered_for_event():
    # Objective:
    # Registration's handler is unregistered with Event Dispatch.

    # Setup
    test_event = 'test_event'
    event_receiver = EventReceiver('', callback_url='url')
    reg = Registration(event_receiver, test_event)
    validate_expected_handler_count(1)

    # Test
    reg.cancel()

    # Verify
    validate_expected_handler_count(0)


def test_cancel__when_registered_for_all_events(mocker):
    # Objective:
    # Registration's handler is unregistered with Event Dispatch.

    # Setup
    event_receiver = EventReceiver('', callback_url='url')
    mock_call = mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)
    reg = Registration(event_receiver)
    mock_call.assert_called()
    validate_expected_handler_count(1)

    # Test
    reg.cancel()

    # Verify
    validate_expected_handler_count(0)
    mock_call.assert_called()


def test_on_event__when_reachable_client(mocker):
    # Objective:
    # Remote handler's API is called, with event object.

    # Setup
    event_receiver = EventReceiver('', callback_url='url')
    mock_call = mocker.patch('eventcenter.server.event_center.APICaller.make_post_call', return_value=RESPONSE_OK)
    reg = Registration(event_receiver)
    validate_expected_handler_count(1)
    event = Event('test_event', {'name': 'Alice'})

    # Test
    reg.on_event(event)

    # Verify
    mock_call.assert_called_with(event_receiver.callback_url, event.raw, timeout_sec=10.0)


def test_on_event__when_unreachable_client():
    # Objective:
    # Unreachable client is unregistered.
    # Event sent about unreachable client.

    # Setup
    event_receiver = create_unreachable_event_receiver()

    test_event = 'test_event'
    reg = Registration(event_receiver, test_event)
    validate_expected_handler_count(1)
    event = Event(test_event)

    # Register watcher for callback failure event.
    register_for_events(handler.on_event, [
        RegistrationEvent.CALLBACK_FAILED_EVENT
    ])
    validate_expected_handler_count(2)

    # Test
    reg.on_event(event)

    # Verify
    validate_expected_handler_count(1)
    validate_received_events(handler, [RegistrationEvent.CALLBACK_FAILED_EVENT])


def create_unreachable_event_receiver() -> EventReceiver:
    return EventReceiver('', callback_url='http://localhost:9999/some/nonexisting/endpoint')
