from eventdispatch import Event, Properties

from eventcenter.event_center_adapter import EventCenterAdapter
from eventcenter.service import RegistrationData, RESPONSE_OK
from test_constants import EVENT_CENTER_PORT
from test_helper import TestEventHandler

adapter: EventCenterAdapter
handler1: TestEventHandler


def setup_module():
    # Seed properties that components in tests will need.
    Properties().set('EVENT_CENTER_URL', f'http://localhost:{EVENT_CENTER_PORT}', is_skip_if_exists=True)
    Properties().set('EVENT_CENTER_CALLBACK_HOST', 'http://localhost', is_skip_if_exists=True)
    Properties().set('EVENT_CENTER_CALLBACK_PORT', 7000, is_skip_if_exists=True)


def setup_function():
    global adapter, handler1

    handler1 = TestEventHandler()
    adapter = EventCenterAdapter(handler1.on_event)


def teardown_function():
    adapter.shutdown()


def teardown_module():
    pass


def test_init():
    # Objective:
    # Adapter is created, no exceptions are raised.

    # Setup
    host = Properties().get('EVENT_CENTER_CALLBACK_HOST')
    port = str(Properties().get('EVENT_CENTER_CALLBACK_PORT'))

    # Test
    # (none...taken care of by setup function)

    # Verify
    # (got here, no exceptions raised).
    assert adapter.event_receiver is not None
    assert host in adapter.event_receiver.callback_url
    assert port in adapter.event_receiver.callback_url


def test_register__when_have_events(mocker):
    run_test__register(['test_event1', 'test_event2'], mocker)


def test_register__when_all_events(mocker):
    run_test__register([], mocker)


def run_test__register(events, mocker):
    # Objective:
    # /register API is called for specified events.

    # Setup
    mock_call = mocker.patch('eventcenter.network.APICaller.make_post_api_call', return_value=RESPONSE_OK)

    # Test
    adapter.register(events)

    # Verify
    url = adapter.event_center_url + '/register'
    body = RegistrationData(adapter.event_receiver, events)
    mock_call.assert_called_with(url, body.raw)


def test_unregister__when_have_events(mocker):
    run_test__unregister(['test_event1', 'test_event2'], mocker)


def test_unregister__when_all_events(mocker):
    run_test__unregister([], mocker)


def run_test__unregister(events, mocker):
    # Objective:
    # /unregister API is called for specified events.

    # Setup
    mock_call = mocker.patch('eventcenter.network.APICaller.make_post_api_call', return_value=RESPONSE_OK)

    # Test
    adapter.unregister(events)

    # Verify
    url = adapter.event_center_url + '/unregister'
    body = RegistrationData(adapter.event_receiver, events)
    mock_call.assert_called_with(url, body.raw)


def test_post_event(mocker):
    # Objective:
    # /post_event API is called for specified event.

    # Setup
    event = Event('test_event', {'name': 'Alice'})
    mock_call = mocker.patch('eventcenter.network.APICaller.make_post_api_call', return_value=RESPONSE_OK)

    # Test
    adapter.post_event(event)

    # Verify
    url = adapter.event_center_url + '/post_event'
    mock_call.assert_called_with(url, event.raw)
