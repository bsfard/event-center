from eventdispatch import EventDispatch, Event, Properties
from eventdispatch.core import EventDispatchEvent

from eventcenter import EventRouter
from eventcenter.service import RESPONSE_OK
from test_constants import EVENT_CENTER_PORT
from test_helper import validate_expected_handler_count, validate_handler_registered_for_event, \
    validate_event_log_count, TestEventHandler, validate_received_events, register_handler_for_event

event_router: EventRouter
handler1: TestEventHandler


def setup_module():
    EventDispatch().toggle_event_logging(True)

    # Seed properties that components in tests will need.
    Properties().set('EVENT_CENTER_URL', f'http://localhost:{EVENT_CENTER_PORT}', is_skip_if_exists=True)
    Properties().set('EVENT_CENTER_CALLBACK_HOST', 'http://localhost', is_skip_if_exists=True)
    Properties().set('EVENT_CENTER_CALLBACK_PORT', 7000, is_skip_if_exists=True)


def setup_function():
    global event_router, handler1

    EventDispatch().clear_event_log()
    EventDispatch().clear_registered_handlers()

    event_router = EventRouter()
    handler1 = TestEventHandler()


def teardown_function():
    event_router.disconnect()


def teardown_module():
    EventDispatch().toggle_event_logging(False)


def test_init(mocker):
    # Objective:
    # Event router is registered with Event Dispatch for all events.
    # Registration event for this registration is not propagated to Event Center.

    # Setup
    mock_call = mocker.patch('eventcenter.event_center_adapter.EventCenterAdapter.register', return_value=None)

    # Test
    # (none)

    # Verify (event router got registered with Event Dispatch for all events).
    validate_expected_handler_count(1)
    validate_handler_registered_for_event(event_router.on_internal_event)
    validate_event_log_count(1)

    # Verify registration event IS NOT propagated out.
    mock_call.assert_not_called()


def test_on_internal_event__when_registration_event(mocker):
    # Objective:
    # Event is registered with Event Center.

    # Setup
    test_event = 'test_event'
    event = Event(EventDispatchEvent.HANDLER_REGISTERED.namespaced_value, {
        'events': [test_event],
        'handler': repr(handler1.on_event)
    })
    mock_call = mocker.patch('eventcenter.event_center_adapter.EventCenterAdapter.register', return_value=None)

    # Test
    event_router.on_internal_event(event)

    # Verify registration event got propagated out.
    mock_call.assert_called_with(event.payload.get('events'))


def test_on_internal_event__when_unregistration_event(mocker):
    # Objective:
    # Event is unregistered with Event Center.

    # Setup
    test_event = 'test_event'
    event = Event(EventDispatchEvent.HANDLER_UNREGISTERED.namespaced_value, {
        'events': [test_event],
        'handler': repr(handler1.on_event)
    })
    mock_call = mocker.patch('eventcenter.event_center_adapter.EventCenterAdapter.unregister', return_value=None)

    # Test
    event_router.on_internal_event(event)

    # Verify unregistration event got propagated out.
    mock_call.assert_called_with(event.payload.get('events'))


def test_on_internal_event__when_non_registration_event(mocker):
    # Objective:
    # Event is posted to Event Center.

    # Setup
    event = Event('test_event', {
        'name': 'Alice'
    })
    mock_call = mocker.patch('eventcenter.event_center_adapter.EventCenterAdapter.post_event', return_value=None)

    # Test
    event_router.on_internal_event(event)

    # Verify
    mock_call.assert_called_with(event)


def test_on_external_event(mocker):
    # Objective:
    # Event is posted to local_clients Event Dispatch, and locally registered handler receives it.

    # Setup
    event = Event('test_event', {
        'name': 'Alice'
    })
    mocker.patch('eventcenter.service.APICaller.make_post_call', return_value=RESPONSE_OK)
    register_handler_for_event(handler1, event.name)

    # Test
    event_router.on_external_event(event.raw)

    # Verify
    validate_received_events(handler1, [event.name])
