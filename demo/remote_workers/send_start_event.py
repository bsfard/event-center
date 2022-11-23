from eventdispatch import post_event

from demo.remote_workers.util import get_program_args, start_event_router, stop_event_router

get_program_args(default_callback_port=7020)
start_event_router()

post_event('started')

stop_event_router()
