import logging

from eventdispatch import post_event

from demo.workers import Worker1, Worker2, APP_STARTED

logging.basicConfig(level=logging.INFO)

Worker1()
Worker2()

# Generate initial event to kick things off.
post_event(APP_STARTED)
