from eventdispatch import Properties

from demo.workers import Worker2
from eventcenter import start_event_router

worker_id = 2
worker = Worker2
port = 7002

# ----- COMMON SECTION ----------------------------------------------------------------------------
# Property for reaching remote Event Center.
Properties().set('EVENT_CENTER_URL', 'http://localhost:6000')

# Properties for setting your host name and port, for remote Event Center to send you events.
Properties().set('EVENT_CENTER_CALLBACK_HOST', 'http://localhost')
Properties().set('EVENT_CENTER_CALLBACK_PORT', port)

start_event_router()

worker()

print(f"Running 'Worker {worker_id}' on port: {Properties().get('EVENT_CENTER_CALLBACK_PORT')}")
# -------------------------------------------------------------------------------------------------
