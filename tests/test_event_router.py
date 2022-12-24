import time

from eventdispatch import Event
from eventdispatch.core import EventDispatchEvent

from eventcenter import EventRouter
from eventcenter.server.event_center import RemoteEventData
from helper import validate_expected_handler_count, validate_handler_registered_for_event, \
    validate_event_log_count, TestEventHandler, validate_received_events, register_handler_for_event, \
    prep_default_event_dispatch, set_properties_for_event_center_interfacing, default_event_dispatch

event_router: EventRouter
handler1: TestEventHandler


def setup_module():
    prep_default_event_dispatch()
    set_properties_for_event_center_interfacing()


def setup_function():
    global event_router, handler1

    default_event_dispatch.clear_event_log()
    default_event_dispatch.clear_registered_handlers()

    event_router = EventRouter()
    handler1 = TestEventHandler()


def teardown_function():
    event_router.disconnect()


def teardown_module():
    pass


def test_init(mocker):
    # Objective:
    # Event router is registered with Event Dispatch for all events.
    # Registration event for this registration is not propagated to Event Center.

    # Setup
    mock_call = mocker.patch('eventcenter.client.event_center_adapter.EventCenterAdapter.register', return_value=None)

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
    test_channel = ''
    event = Event(EventDispatchEvent.HANDLER_REGISTERED.namespaced_value, {
        'events': [test_event],
        'handler': repr(handler1.on_event)
    })
    mock_call = mocker.patch('eventcenter.client.event_center_adapter.EventCenterAdapter.register', return_value=None)

    # Test
    event_router.on_internal_event(event)

    # Verify registration event got propagated out.
    mock_call.assert_called_with(event.payload.get('events'), test_channel)


def test_on_internal_event__when_unregistration_event(mocker):
    # Objective:
    # Event is unregistered with Event Center.

    # Setup
    test_event = 'test_event'
    test_channel = ''
    event = Event(EventDispatchEvent.HANDLER_UNREGISTERED.namespaced_value, {
        'events': [test_event],
        'handler': repr(handler1.on_event)
    })
    mock_call = mocker.patch('eventcenter.client.event_center_adapter.EventCenterAdapter.unregister', return_value=None)

    # Test
    event_router.on_internal_event(event)

    # Verify unregistration event got propagated out.
    mock_call.assert_called_with(event.payload.get('events'), test_channel)


def test_on_internal_event__when_non_registration_event(mocker):
    # Objective:
    # Event is posted to Event Center.

    # Setup
    test_channel = ''
    event = Event('test_event', {
        'name': 'Alice'
    })
    mock_call = mocker.patch('eventcenter.client.event_center_adapter.EventCenterAdapter.post_event', return_value=None)

    # Test
    event_router.on_internal_event(event)

    # Verify
    mock_call.assert_called_with(event, test_channel)


def test_on_external_event():
    # Objective:
    # Event is posted to local_clients Event Dispatch, and locally registered handler receives it.

    # Setup
    test_channel = ''
    event = Event('test_event', {
        'name': 'Alice'
    })
    register_handler_for_event(handler1, event.name)

    remote_event = RemoteEventData(test_channel, event)

    # Test
    event_router.on_external_event(remote_event)

    # Verify
    time.sleep(0.1)
    validate_received_events(handler1, [event.name])
