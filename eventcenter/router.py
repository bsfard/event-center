from eventdispatch import EventDispatch, Event

from .event_center_adapter import EventCenterAdapter


class EventRouter:
    def __init__(self):
        self.__event_service_adapter = EventCenterAdapter(self.on_external_event)

        # Register for all internal events, to propagate out.
        EventDispatch().register(self.on_internal_event, [])

    def on_internal_event(self, event: Event):
        # Check if event originated from outside (if so, no need to propagate it out again).
        if 'external_id' in event.payload and 'external_time' in event.payload:
            return

        # Check if registration event.
        if event.name == EventDispatch.REGISTRATION_EVENT:
            # Check if it's for Event Router (if so, ignore it).
            if 'EventRouter.on_internal_event' in event.payload['handler']:
                return

            events = event.get('events', event.payload)
            self.__event_service_adapter.register(events)
        elif event.name == EventDispatch.UNREGISTRATION_EVENT:
            # Check if it's for Event Router (if so, ignore it).
            if 'EventRouter.on_internal_event' in event.payload['handler']:
                return

            events = event.get('events', event.payload)
            self.__event_service_adapter.unregister(events)
        else:
            # All other (non-registration) events that should be propagated to the outside.
            self.__event_service_adapter.post_event(event)

    @staticmethod
    def on_external_event(event: dict):
        # Add external (original) event ID and time to payload.
        payload = event.get('payload')
        payload['external_id'] = event.get('id')
        payload['external_time'] = event.get('time')

        # Propagate external event to local_clients event center.
        EventDispatch().post_event(event.get('name'), payload)

    def disconnect(self):
        self.__event_service_adapter.shutdown()
