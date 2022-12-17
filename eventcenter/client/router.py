import logging

from eventdispatch import Event, EventDispatchEvent, register_for_events, Properties, PropertyNotSetError, post_event

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
    __EXTERNAL_EVENT_ID = 'external_event_id'
    __EXTERNAL_EVENT_TIME = 'external_event_time'

    __logger = logging.getLogger(__name__)

    def __init__(self):
        self.__event_service_adapter = EventCenterAdapter(self.on_external_event)
        try:
            self.__channel = Properties.get('ROUTER_CHANNEL')
        except PropertyNotSetError:
            self.__channel = ''
            
        self.__event_service_adapter.unregister_all()

        # Register for all internal events, to propagate out.
        register_for_events(self.on_internal_event, [])

    def on_internal_event(self, event: Event):
        self.__log_message_got_internal_event(event)

        # Check if event originated from outside (if so, no need to propagate it out again).
        if EventRouter.__EXTERNAL_EVENT_ID in event.payload and EventRouter.__EXTERNAL_EVENT_TIME in event.payload:
            self.__log_message_not_propagating_event__originated_outside(event)
            return

        # Check if registration event.
        if event.name == EventDispatchEvent.HANDLER_REGISTERED.namespaced_value:
            # Check if it's from Event Router (if so, ignore it).
            if 'EventRouter.on_internal_event' in event.payload['handler']:
                self.__log_message_not_propagating_event__originated_from_router(event)
                return

            events = event.get('events', event.payload)
            self.__event_service_adapter.register(events, self.__channel)
        elif event.name == EventDispatchEvent.HANDLER_UNREGISTERED.namespaced_value:
            # Check if it's from Event Router (if so, ignore it).
            if 'EventRouter.on_internal_event' in event.payload['handler']:
                self.__log_message_not_propagating_event__originated_from_router(event)
                return

            events = event.get('events', event.payload)
            self.__event_service_adapter.unregister(events, self.__channel)
        else:
            # All other (non-registration) events that should be propagated to the outside.
            self.__log_message_propagating_event(event)

            event.payload['original_event_id'] = event.id
            event.payload['original_event_time'] = event.time
            self.__event_service_adapter.post_event(event, self.__channel)

    def on_external_event(self, remote_event: RemoteEventData):
        EventRouter.__log_message_got_external_event(remote_event.event)

        # Add external (original) event info to payload.
        remote_event.event.payload[EventRouter.__EXTERNAL_EVENT_ID] = remote_event.event.id
        remote_event.event.payload[EventRouter.__EXTERNAL_EVENT_TIME] = remote_event.event.time
        remote_event.event.payload['channel'] = remote_event.channel

        # Propagate external event to local_clients event center
        post_event(remote_event.event.name, remote_event.event.payload, self.on_internal_event)

    def disconnect(self):
        self.__event_service_adapter.shutdown()

    @staticmethod
    def __log_message_got_internal_event(event: Event):
        message = f"Got internal event '{event.name}'"
        EventRouter.__logger.debug(message)

    @staticmethod
    def __log_message_got_external_event(event: Event):
        message = f"Got external event '{event.name}'"
        EventRouter.__logger.debug(message)

    @staticmethod
    def __log_message_not_propagating_event__originated_outside(event: Event):
        message = f"Not propagating event '{event.name}'...originated from outside"
        EventRouter.__logger.debug(message)

    @staticmethod
    def __log_message_not_propagating_event__originated_from_router(event: Event):
        message = f"Not propagating event '{event.name}'...originated from from router"
        EventRouter.__logger.debug(message)

    @staticmethod
    def __log_message_propagating_event(event: Event):
        message = f"Propagating event '{event.name}' to event center"
        EventRouter.__logger.debug(message)
