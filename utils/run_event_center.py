from properties import Properties
from service import EventCenter
from utils.util import get_program_args

get_program_args(default_event_center_host='http://localhost', default_event_center_port=5000)

ec = EventCenter()

print(f"Event Center started on port: {Properties().get('EVENT_CENTER_PORT')}")
