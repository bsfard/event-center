from eventdispatch import post_event

from client_helper import prep_client_app_settings
from demo.workers import WorkerEvent
from eventcenter import start_event_router, stop_event_router

prep_client_app_settings()

start_event_router()

post_event(WorkerEvent.APP_STARTED)

stop_event_router()
