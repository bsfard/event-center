from eventdispatch import Event, Properties, register_for_events

from eventcenter.utils.util import log_event, get_program_args, start_event_router

get_program_args(default_callback_port=7010)
start_event_router()


def on_event(event: Event):
    log_event(on_event, event)


# Register for all events.
register_for_events(on_event, [])

print(f"Running 'Event Listener' on port: {Properties().get('EVENT_CENTER_CALLBACK_PORT')}")
