from eventdispatch import Event, Properties

from eventcenter.client.event_center_adapter import EventCenterAdapter
from eventcenter.server.event_center import RegistrationData, RemoteEventData
from eventcenter.server.service import RESPONSE_OK
from helper import EventHandler, prep_default_event_dispatch, set_properties_for_event_center_interfacing, \
    default_event_dispatch

SOME_CHANNEL = 'some_channel'

adapter: EventCenterAdapter
handler1: EventHandler


def setup_module():
    prep_default_event_dispatch()
    set_properties_for_event_center_interfacing()


def setup_function():
    global adapter, handler1

    default_event_dispatch.clear_event_log()
    default_event_dispatch.clear_registered_handlers()

    handler1 = EventHandler()
    adapter = EventCenterAdapter(handler1.on_event)


def teardown_function():
    global adapter
    adapter.shutdown()


def teardown_module():
    pass


def test_init():
    # Objective:
    # Adapter is created, no exceptions are raised.

    # Setup
    global adapter
    host = Properties.get('EVENT_CENTER_CALLBACK_HOST')
    port = str(Properties.get('EVENT_CENTER_CALLBACK_PORT'))

    # Test
    # (none...taken care of by setup function)

    # Verify
    # (got here, no exceptions raised).
    assert adapter.callback_url is not None
    assert host in adapter.callback_url
    assert port in adapter.callback_url


def test_register__when_have_events(mocker):
    # Objective:
    # /register API is called for specified events.

    # Test
    run_test__register(mocker, ['test_event1', 'test_event2'], '')


def test_register__when_have_events__with_channel(mocker):
    # Objective:
    # /register API is called for specified events, with channel.

    # Test
    run_test__register(mocker, ['test_event1', 'test_event2'], SOME_CHANNEL)


def test_register__when_all_events(mocker):
    # Objective:
    # /register API is called for all events.

    # Test
    run_test__register(mocker, [], '')


def test_register__when_all_events__with_channels(mocker):
    # Objective:
    # /register API is called for all events, with channel.

    # Test
    run_test__register(mocker, [], SOME_CHANNEL)


def run_test__register(mocker, events: [str], channel: str = ''):
    # Setup
    global adapter
    mock_call = mocker.patch('eventcenter.client.event_center_adapter.APICaller.make_post_call',
                             return_value=RESPONSE_OK)

    # Test
    adapter.register(events, channel)

    # Verify
    url = adapter.event_center_url + '/register'
    body = RegistrationData(adapter.callback_url, events, channel)
    mock_call.assert_called_with(url, body.dict, is_suppress_connection_error=True)


def test_unregister__when_have_events(mocker):
    # Objective:
    # /unregister API is called for specified events.

    # Test
    run_test__unregister(mocker, ['test_event1', 'test_event2'], '')


def test_unregister__when_have_events__with_channel(mocker):
    # Objective:
    # /unregister API is called for specified events, with channel.

    # Test
    run_test__unregister(mocker, ['test_event1', 'test_event2'], SOME_CHANNEL)


def test_unregister__when_all_events(mocker):
    # Objective:
    # /unregister API is called for all events.

    # Test
    run_test__unregister(mocker, [], '')


def test_unregister__when_all_events__with_events(mocker):
    # Objective:
    # /unregister API is called for all events, with channel.

    # Test
    run_test__unregister(mocker, [], SOME_CHANNEL)


def run_test__unregister(mocker, events: [str], channel: str = ''):
    # Setup
    global adapter
    mock_call = mocker.patch('eventcenter.client.event_center_adapter.APICaller.make_post_call',
                             return_value=RESPONSE_OK)

    # Test
    adapter.unregister(events, channel)

    # Verify
    url = adapter.event_center_url + '/unregister'
    body = RegistrationData(adapter.callback_url, events, channel)
    mock_call.assert_called_with(url, body.dict, is_suppress_connection_error=True)


def test_post_event(mocker):
    # Objective:
    # /post_event API is called for specified event.

    # Test
    run_test_post_event(mocker, '')


def test_post_event__with_channel(mocker):
    # Objective:
    # /post_event API is called for specified event, with channel.

    # Test
    run_test_post_event(mocker, SOME_CHANNEL)


def run_test_post_event(mocker, channel: str = ''):
    # Setup
    global adapter
    event = Event('test_event', {'name': 'Alice'})
    remote_event = RemoteEventData(channel, event)
    mock_call = mocker.patch('eventcenter.client.event_center_adapter.APICaller.make_post_call',
                             return_value=RESPONSE_OK)

    # Test
    adapter.post_event(event, channel)

    # Verify
    url = adapter.event_center_url + '/post_event'
    mock_call.assert_called_with(url, remote_event.dict, is_suppress_connection_error=True)
