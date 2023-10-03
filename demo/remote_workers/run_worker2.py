from eventdispatch import Properties

from client_helper import prep_client_app_settings
from demo.workers import Worker2
from eventcenter import start_event_router
from eventcenter.client.router import ROUTER_NAME

prep_client_app_settings()

Properties().set(ROUTER_NAME, 'Worker2')

start_event_router()

Worker2()

print(f"Running 'Worker 2' on port: {Properties().get('EVENT_CENTER_CALLBACK_PORT')}")
