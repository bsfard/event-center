from eventdispatch import NamespacedEnum


class RouterEvent(NamespacedEnum):
    STARTED = 'started'
    FAILED_TO_REACH_EVENT_CENTER = 'failed_to_reach_event_center'
    READY = 'ready'
    GOT_INTERNAL_EVENT = 'got_internal_event'
    GOT_EXTERNAL_EVENT = 'got_external_event'
    PROPAGATING_INTERNAL_EVENT = 'propagating_internal_event'
    NOT_PROPAGATING_INTERNAL_EVENT = 'not_propagating_internal_event'
    NOT_PROPAGATING_EXTERNAL_EVENT = 'not_propagating_external_event'

    def get_namespace(self) -> str:
        return 'router'
