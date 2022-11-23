from eventdispatch import Properties

from demo.remote_workers.util import get_program_args, start_event_router
from demo.workers import Worker2

get_program_args(default_callback_port=7002)
start_event_router()

Worker2()

print(f"Running 'Worker 2' on port: {Properties().get('EVENT_CENTER_CALLBACK_PORT')}")
