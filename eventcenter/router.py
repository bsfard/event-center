from typing import Dict, Any

from eventdispatch import Event, register_for_events, post_event
from eventdispatch.core import EventDispatchEvent

from .event_center_adapter import EventCenterAdapter


class EventRouter:
    def __init__(self):
        self.__event_service_adapter = EventCenterAdapter(self.on_external_event)

        # Register for all internal events, to propagate out.
        register_for_events(self.on_internal_event, [])

    def on_internal_event(self, event: Event):
        # Check if event originated from outside (if so, no need to propagate it out again).
        if 'external_id' in event.payload and 'external_time' in event.payload:
            return

        # Check if registration event.
        if event.name == EventDispatchEvent.HANDLER_REGISTERED.namespaced_value:
            # Check if it's for Event Router (if so, ignore it).
            if 'EventRouter.on_internal_event' in event.payload['handler']:
                return

            events = event.get('events', event.payload)
            self.__event_service_adapter.register(events)
        elif event.name == EventDispatchEvent.HANDLER_UNREGISTERED.namespaced_value:
            # Check if it's for Event Router (if so, ignore it).
            if 'EventRouter.on_internal_event' in event.payload['handler']:
                return

            events = event.get('events', event.payload)
            self.__event_service_adapter.unregister(events)
        else:
            # All other (non-registration) events that should be propagated to the outside.
            self.__event_service_adapter.post_event(event)

    @staticmethod
    def on_external_event(event: Dict[str, Any]):
        # Add external (original) event ID and time to payload.
        payload = event.get('payload')
        payload['external_id'] = event.get('id')
        payload['external_time'] = event.get('time')

        # Propagate external event to local_clients event center.
        post_event(event.get('name'), payload)

    def disconnect(self):
        self.__event_service_adapter.shutdown()
