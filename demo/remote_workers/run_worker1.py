from eventdispatch import Properties

from client_helper import prep_client_app_settings
from demo.workers import Worker1
from eventcenter import start_event_router

prep_client_app_settings()

start_event_router()

Worker1()

print(f"Running 'Worker 1' on port: {Properties().get('EVENT_CENTER_CALLBACK_PORT')}")
