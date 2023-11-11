from eventdispatch import Properties
from eventdispatch.demo import Worker1

from client_helper import prep_client_app_settings
from eventcenter.client.router import start_event_router, ROUTER_NAME

prep_client_app_settings()

Properties().set(ROUTER_NAME, 'Worker1')

start_event_router()

Worker1()

print(f"Running 'Worker 1' on port: {Properties().get('EVENT_CENTER_CALLBACK_PORT')}")
