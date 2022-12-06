from eventdispatch import post_event

from demo.remote_workers.util import get_program_args
from demo.workers import WorkerEvent
from eventcenter import start_event_router, stop_event_router

get_program_args(default_callback_port=7020)
start_event_router()

post_event(WorkerEvent.APP_STARTED)

stop_event_router()
