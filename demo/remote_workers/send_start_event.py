from eventdispatch import post_event, Properties
from eventdispatch.demo.workers import WorkerEvent

from client_helper import prep_client_app_settings
from eventcenter import start_event_router, stop_event_router
from eventcenter.client.router import ROUTER_NAME

prep_client_app_settings()

Properties().set(ROUTER_NAME, 'Send_Start_Event')

start_event_router()

post_event(WorkerEvent.APP_STARTED)

stop_event_router()
