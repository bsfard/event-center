from eventdispatch import Properties

from demo.remote_workers.util import get_program_args, start_event_router
from demo.workers import Worker1

get_program_args(default_callback_port=7001)
start_event_router()

Worker1()

print(f"Running 'Worker 1' on port: {Properties().get('EVENT_CENTER_CALLBACK_PORT')}")
