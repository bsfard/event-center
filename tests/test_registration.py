from eventdispatch import EventDispatch, Event

from eventcenter.service import RESPONSE_OK, Registration, EventReceiver
from test_helper import validate_handler_registered_for_event, validate_expected_handler_count


def setup_module():
    pass


def setup_function():
    EventDispatch().clear_event_log()
    EventDispatch().clear_registered_handlers()


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
    mock_call = mocker.patch('eventcenter.service.APICaller.make_post_call', return_value=RESPONSE_OK)

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
    mock_call = mocker.patch('eventcenter.service.APICaller.make_post_call', return_value=RESPONSE_OK)
    reg = Registration(event_receiver)
    mock_call.assert_called()
    validate_expected_handler_count(1)

    # Test
    reg.cancel()

    # Verify
    validate_expected_handler_count(0)
    mock_call.assert_called()


def test_on_event(mocker):
    # Objective:
    # Remote handler's API is called, with event object.

    # Setup
    event_receiver = EventReceiver('', callback_url='url')
    mock_call = mocker.patch('eventcenter.service.APICaller.make_post_call', return_value=RESPONSE_OK)
    reg = Registration(event_receiver)
    validate_expected_handler_count(1)
    event = Event('test_event', {'name': 'Alice'})

    # Test
    reg.on_event(event)

    # Verify
    mock_call.assert_called_with(event_receiver.callback_url, event.raw)
