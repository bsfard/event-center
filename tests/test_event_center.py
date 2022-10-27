import logging
import time

from eventdispatch import Event, EventDispatch
from eventdispatch import Properties
from flask import Flask, request
from pytest import fail

from eventcenter import APICaller, FlaskAppRunner, EventCenter
from eventcenter.service import RegistrationData, EventReceiver, RESPONSE_OK
from test_constants import TEST_EVENT_RECEIVER_PORT, EVENT_CENTER_PORT

es: EventCenter
event_center_url: str

logging.getLogger().setLevel(logging.DEBUG)


class TestEventReceiver(FlaskAppRunner):
    def __init__(self, port):
        app = Flask('TestEventReceiver')

        super().__init__('0.0.0.0', port, app)
        self.url = 'http://localhost:' + str(port) + '/on_event'
        self.received_events: [dict] = []

        self.start()

        @app.route('/on_event', methods=['POST'])
        def on_event() -> dict:
            data = request.json
            self.received_events.append({
                "name": data['name'],
                "payload": data['payload']
            })
            return {}

    @property
    def id(self) -> EventReceiver:
        return EventReceiver('UnitTester', self.url)


test_event_receiver1: TestEventReceiver
test_event_receiver2: TestEventReceiver


def setup_module():
    global es, event_center_url

    # Seed properties that components in tests will need.
    Properties().set('EVENT_CENTER_PORT', EVENT_CENTER_PORT)

    event_center_url = 'http://localhost:' + str(EVENT_CENTER_PORT)

    # Start a local_clients event center for testing.
    es = EventCenter()


def setup_function():
    global test_event_receiver1, test_event_receiver2

    EventDispatch().clear_event_log()
    EventDispatch().clear_registered_handlers()

    test_event_receiver1 = TestEventReceiver(TEST_EVENT_RECEIVER_PORT)
    test_event_receiver2 = TestEventReceiver(TEST_EVENT_RECEIVER_PORT + 1)


def teardown_function():
    test_event_receiver1.shutdown()
    test_event_receiver2.shutdown()


def teardown_module():
    es.shutdown()


def test_register__when_not_registered__multiple_events():
    # Objective:
    # One registrant is created.
    # Registrant has one registration for each event registered.

    # Setup
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'
    data = RegistrationData(test_event_receiver1.id, [test_event1, test_event2])

    # Test
    register(data)

    # Verify
    validate_registrant_count(1)
    validate_registrant_registered_for_event(test_event_receiver1.id, [test_event1, test_event2])

    # Cleanup
    unregister_event_receiver(test_event_receiver1, [test_event1, test_event2])


def test_register__when_registered_for_different_event():
    # Objective:
    # No additional registrants is created.
    # Registrant's prior registration is intact.
    # Registrant has a new registration added.

    # Setup
    test_event1 = 'test_event1'
    register_event_receiver(test_event_receiver1, [test_event1])
    validate_registrant_count(1)
    validate_registrant_registered_for_event(test_event_receiver1.id, [test_event1])

    test_event2 = 'test_event2'
    data = RegistrationData(test_event_receiver1.id, [test_event2])

    # Test
    register(data)

    # Verify
    validate_registrant_count(1)
    validate_registrant_registered_for_event(test_event_receiver1.id, [test_event1, test_event2])

    # Cleanup
    unregister_event_receiver(test_event_receiver1, [test_event1, test_event2])


def test_register__when_already_registered_for_event():
    # Objective:
    # No additional registrants is created.
    # Registrant's prior registration is intact.
    # No additional registrations are created.

    # Setup
    test_event = 'test_event'
    register_event_receiver(test_event_receiver1, [test_event])
    validate_registrant_count(1)
    validate_registrant_registered_for_event(test_event_receiver1.id, [test_event])

    data = RegistrationData(test_event_receiver1.id, [test_event])

    # Test
    register(data)

    # Verify
    validate_registrant_count(1)
    validate_registrant_registered_for_event(test_event_receiver1.id, [test_event])

    # Cleanup
    unregister_event_receiver(test_event_receiver1, [test_event])


def test_register__when_already_registered_for_one_of_the_events():
    # Objective:
    # No additional registrants is created.
    # Registrant's prior registration is intact.
    # Registrant has a new registration added.

    # Setup
    test_event1 = 'test_event1'
    register_event_receiver(test_event_receiver1, [test_event1])
    validate_registrant_count(1)
    validate_registrant_registered_for_event(test_event_receiver1.id, [test_event1])

    test_event2 = 'test_event2'
    data = RegistrationData(test_event_receiver1.id, [test_event1, test_event2])

    # Test
    register(data)

    # Verify
    validate_registrant_count(1)
    validate_registrant_registered_for_event(test_event_receiver1.id, [test_event1, test_event2])

    # Cleanup
    unregister_event_receiver(test_event_receiver1, [test_event1, test_event2])


def test_unregister__when_not_registered():
    # Objective:
    # Registrant count is same after unregistration.

    # Setup
    validate_registrant_count(0)
    data = RegistrationData(test_event_receiver1.id, ['test_event'])

    # Test
    unregister(data)

    # Verify
    validate_registrant_count(0)


def test_unregister__when_registered__multiple_events():
    # Objective:
    # Registrations are removed.

    # Setup
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'
    test_event3 = 'test_event3'
    register_event_receiver(test_event_receiver1, [test_event1, test_event2, test_event3])

    data = RegistrationData(test_event_receiver1.id, [test_event1, test_event2])

    # Test
    unregister(data)

    # Verify
    validate_registrant_count(1)
    validate_registrant_registered_for_event(test_event_receiver1.id, [test_event3])

    # Cleanup
    unregister_event_receiver(test_event_receiver1, [test_event3])


def test_unregister__when_registered__no_more_registrations_for_registrant():
    # Objective:
    # Registrant is removed.

    # Setup
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'
    register_event_receiver(test_event_receiver1, [test_event1, test_event2])

    data = RegistrationData(test_event_receiver1.id, [test_event1, test_event2])

    # Test
    unregister(data)

    # Verify
    validate_registrant_count(0)


def test_unregister__when_registered_for_only_one_of_the_events():
    # Objective:
    # Registration that exists for event is removed.

    # Setup
    test_event1 = 'test_event1'
    test_event2 = 'test_event2'
    register_event_receiver(test_event_receiver1, [test_event1, test_event2])

    test_event3 = 'test_event3'
    data = RegistrationData(test_event_receiver1.id, [test_event2, test_event3])

    # Test
    unregister(data)

    # Verify
    validate_registrant_count(1)
    validate_registrant_registered_for_event(test_event_receiver1.id, [test_event1])

    # Cleanup
    unregister_event_receiver(test_event_receiver1, [test_event1])


def test_unregister__when_registered_for_different_event():
    # Objective:
    # Registration for the different event is intact.

    # Setup
    test_event1 = 'test_event1'
    register_event_receiver(test_event_receiver1, [test_event1])

    test_event2 = 'test_event2'
    data = RegistrationData(test_event_receiver1.id, [test_event2])

    # Test
    unregister(data)

    # Verify
    validate_registrant_count(1)
    validate_registrant_registered_for_event(test_event_receiver1.id, [test_event1])

    # Cleanup
    unregister_event_receiver(test_event_receiver1, [test_event1])


def test_post__when_no_registrants():
    # Objective:
    # No events are propagated

    # Setup
    # (nothing)

    # Test
    post('test_event')

    wait_for_event()

    # Verify
    validate_received_events(test_event_receiver1, [])


def test_post__when_no_registrants_for_event():
    # Objective:
    # No events are propagated

    # Setup
    test_event = 'test_event'
    register_event_receiver(test_event_receiver1, [test_event])

    # Test
    post('test_event_other')

    wait_for_event()

    # Verify
    validate_received_events(test_event_receiver1, [])

    # Cleanup
    unregister_event_receiver(test_event_receiver1, [test_event])


def test_post__when_have_registrant_for_event():
    # Objective:
    # Event is propagated to registrant.

    # Setup
    test_event = 'test_event'
    register_event_receiver(test_event_receiver1, [test_event])

    # Test
    post(test_event)

    wait_for_event()

    # Verify
    validate_received_events(test_event_receiver1, [test_event])

    # Cleanup
    unregister_event_receiver(test_event_receiver1, [test_event])


def test_post__when_have_multiple_registrants_for_event():
    # Objective:
    # Event is propagated to all registrant for event.

    # Setup
    test_event = 'test_event'
    register_event_receiver(test_event_receiver1, [test_event])
    register_event_receiver(test_event_receiver2, [test_event])

    # Test
    post(test_event)

    wait_for_event()

    # Verify
    validate_received_events(test_event_receiver1, [test_event])
    validate_received_events(test_event_receiver2, [test_event])

    # Cleanup
    unregister_event_receiver(test_event_receiver1, [test_event])
    unregister_event_receiver(test_event_receiver2, [test_event])


def test_post__when_registrants_for_event_and_different_event():
    # Objective:
    # Event is propagated to registrant for event.
    # No event is propagated to registrant not for event.

    # Setup
    test_event1 = 'test_event1'
    register_event_receiver(test_event_receiver1, [test_event1])

    test_event2 = 'test_event2'
    register_event_receiver(test_event_receiver2, [test_event2])

    # Test
    post(test_event1)

    wait_for_event()

    # Verify
    validate_received_events(test_event_receiver1, [test_event1])
    validate_received_events(test_event_receiver2, [])

    # Cleanup
    unregister_event_receiver(test_event_receiver1, [test_event1])
    unregister_event_receiver(test_event_receiver2, [test_event2])


def register_event_receiver(event_receiver: TestEventReceiver, events: [str]):
    data = RegistrationData(event_receiver.id, events)
    register(data)


def register(registration_data: RegistrationData):
    make_post_api_call('/register', registration_data.raw)


def unregister_event_receiver(event_receiver: TestEventReceiver, events: [str]):
    data = RegistrationData(event_receiver.id, events)
    unregister(data)


def unregister(registration_data: RegistrationData):
    make_post_api_call('/unregister', registration_data.raw)


def post(event: str, payload: dict = None):
    payload = payload if payload else {}
    data = Event(event, payload)
    make_post_api_call('/post_event', data.raw)


def make_post_api_call(endpoint: str, data: dict, expected_response: dict = RESPONSE_OK):
    response = APICaller.make_post_api_call(event_center_url + endpoint, data)
    assert response != {}
    assert response.status_code == 200
    validate_response(response, expected_response)
    return response


def validate_response(response, expected_response):
    assert response.json() == expected_response


def validate_registrant_count(expected_count):
    assert len(es.get_registrants()) == expected_count


def validate_registrant_registered_for_event(event_receiver: EventReceiver, events: [str]):
    registrant = es.get_registrant(event_receiver)
    assert registrant
    assert len(registrant.registrations) == len(events)

    for event in events:
        is_found = False
        for registration in registrant.registrations:
            if registration == event:
                is_found = True
                break
        if not is_found:
            fail('Could not registered event')


def validate_received_events(receiver: TestEventReceiver, events: [str]):
    assert len(receiver.received_events) == len(events)

    for event in receiver.received_events:
        assert event.get('name') in events


def wait_for_event():
    # Give time for event to be received.
    time.sleep(0.1)
