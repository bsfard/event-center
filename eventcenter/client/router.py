import json
import logging

from eventdispatch import Event, EventDispatchEvent, register_for_events, Properties, post_event, \
    EventDispatchManager
from eventdispatch.core import EventMapper
from flask import Flask
from wrapt import synchronized

from eventcenter.client.event_center_adapter import EventCenterAdapter
from eventcenter.server.event_center import RemoteEventData


def start_event_router():
    ec = EventRouter()
    Properties().set('EVENT_ROUTER', ec)


def stop_event_router():
    ec = Properties().get('EVENT_ROUTER')
    ec.disconnect()


# Router properties.
ROUTER_CHANNEL = 'ROUTER_CHANNEL'
ROUTER_NAME = 'ROUTER_NAME'
PRETTY_PRINT = 'PRETTY_PRINT'


# -------------------------------------------------------------------------------------------------


class EventRouter(EventMapper):
    __EXTERNAL_EVENT_ID = 'external_event_id'
    __EXTERNAL_EVENT_TIME = 'external_event_time'
    __pretty_print = False

    __logger = logging.getLogger(__name__)

    def __init__(self):
        self.__event_service_adapter = EventCenterAdapter(self.on_external_event)
        self.__channel = '' if not Properties().has(ROUTER_CHANNEL) else Properties().get(ROUTER_CHANNEL)
        self.__name = '' if not Properties().has(ROUTER_NAME) else Properties().get(ROUTER_NAME)
        EventRouter.__pretty_print = Properties().has(PRETTY_PRINT) and Properties().get(PRETTY_PRINT)

        self.__event_service_adapter.unregister_all()

        # Register for all internal events, to propagate out.
        register_for_events(self.on_internal_event, [])

        # Set event center adapter as one to handle event mappings (destined for the remote event center).
        EventDispatchManager().default_dispatch.set_event_map_manager(self)

    @property
    def server(self) -> Flask:
        return self.__event_service_adapter.app

    def map_events(self, events_to_map: [Event], event_to_post: Event, ignore_if_exists: bool = False) -> str:
        return self.__event_service_adapter.map_events(events_to_map, event_to_post, ignore_if_exists, self.__channel)

    @synchronized
    def on_internal_event(self, event: Event):
        self.__log_message_got_internal_event(event)

        # Check if event originated from outside (if so, no need to propagate it out again).
        if EventRouter.__EXTERNAL_EVENT_ID in event.payload and EventRouter.__EXTERNAL_EVENT_TIME in event.payload:
            self.__log_message_not_propagating_event__originated_outside(event)
            return

        # Check if registration event.
        if event.name == EventDispatchEvent.HANDLER_REGISTERED.namespaced_value:
            # Check if it's from Event Router (if so, ignore it).
            if 'EventRouter.on_internal_event' in event.payload['handler'] or 'BoundFunctionWrapper' in event.payload[
                'handler']:
                self.__log_message_not_propagating_event__originated_from_router(event)
                return

            events = event.get('events', event.payload)
            self.__log_message_propagating_event(event)
            self.__event_service_adapter.register(events, self.__channel)
        elif event.name == EventDispatchEvent.HANDLER_UNREGISTERED.namespaced_value:
            # Check if it's from Event Router (if so, ignore it).
            if 'EventRouter.on_internal_event' in event.payload['handler']:
                self.__log_message_not_propagating_event__originated_from_router(event)
                return

            events = event.get('events', event.payload)
            self.__log_message_propagating_event(event)
            self.__event_service_adapter.unregister(events, self.__channel)
        else:
            # All other (non-registration) events that should be propagated to the outside.
            event.payload['metadata'] = {
                'original_event_id': event.id,
                'original_event_time': event.time,
                'router': self.__name
            }

            self.__log_message_propagating_event(event)
            self.__event_service_adapter.post_event(event, self.__channel)

    def on_external_event(self, remote_event: RemoteEventData):
        # Add external (original) event info to payload.
        metadata = {
            EventRouter.__EXTERNAL_EVENT_ID: remote_event.event.id,
            EventRouter.__EXTERNAL_EVENT_TIME: remote_event.event.time,
            'channel': remote_event.channel
        }

        try:
            remote_event.event.payload['metadata'].update(metadata)
        except KeyError:
            remote_event.event.payload['metadata'] = metadata

        EventRouter.__log_message_got_external_event(remote_event.event)

        # Propagate external event to local_clients event center
        post_event(remote_event.event.name, remote_event.event.payload, self.on_internal_event)

    def disconnect(self):
        self.__event_service_adapter.shutdown()

    @staticmethod
    def __log_message_got_internal_event(event: Event):
        payload = json.dumps(event.payload, indent=2) if EventRouter.__pretty_print else event.payload
        message = f"Got internal event '{event.name}'\n{payload}"
        log_level = logging.ERROR if event.name.endswith('_error') else logging.DEBUG
        EventRouter.__logger.log(log_level, message)

    @staticmethod
    def __log_message_got_external_event(event: Event):
        message = f"Got external event '{event.name}'"
        try:
            name = event.payload.get('metadata').get('router')
            message += f" from router '{name}'"
        except KeyError:
            pass
        EventRouter.__logger.debug(message)

    @staticmethod
    def __log_message_not_propagating_event__originated_outside(event: Event):
        message = f"Not propagating event '{event.name}'...originated from outside"
        EventRouter.__logger.debug(message)

    @staticmethod
    def __log_message_not_propagating_event__originated_from_router(event: Event):
        message = f"Not propagating event '{event.name}'...originated from router"
        EventRouter.__logger.debug(message)

    @staticmethod
    def __log_message_propagating_event(event: Event):
        message = f"Propagating event '{event.name}' to event center"
        EventRouter.__logger.debug(message)
