from eventdispatch import Event, EventDispatchEvent, register_for_events, post_event, Properties, PropertyNotSetError

from eventcenter.client.event_center_adapter import EventCenterAdapter
from eventcenter.server.event_center import RemoteEventData


def start_event_router():
    ec = EventRouter()
    Properties.set('EVENT_ROUTER', ec)


def stop_event_router():
    ec = Properties.get('EVENT_ROUTER')
    ec.disconnect()


# -------------------------------------------------------------------------------------------------


class EventRouter:
    def __init__(self):
        self.__event_service_adapter = EventCenterAdapter(self.on_external_event)
        try:
            self.__channel = Properties.get('ROUTER_CHANNEL')
        except PropertyNotSetError:
            self.__channel = ''

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
            self.__event_service_adapter.register(events, self.__channel)
        elif event.name == EventDispatchEvent.HANDLER_UNREGISTERED.namespaced_value:
            # Check if it's for Event Router (if so, ignore it).
            if 'EventRouter.on_internal_event' in event.payload['handler']:
                return

            events = event.get('events', event.payload)
            self.__event_service_adapter.unregister(events, self.__channel)
        else:
            # All other (non-registration) events that should be propagated to the outside.
            event.payload['original_event_id'] = event.id
            event.payload['original_event_time'] = event.time
            self.__event_service_adapter.post_event(event, self.__channel)

    @staticmethod
    def on_external_event(remote_event: RemoteEventData):
        # Add external (original) event info to payload.
        remote_event.event.payload['external_event_id'] = remote_event.event.id
        remote_event.event.payload['external_event_time'] = remote_event.event.time
        remote_event.event.payload['channel'] = remote_event.channel

        # Propagate external event to local_clients event center
        post_event(remote_event.event.name, remote_event.event.payload)

    def disconnect(self):
        self.__event_service_adapter.shutdown()
