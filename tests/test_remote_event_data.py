from eventdispatch import Event, Data

from server.event_center import RemoteEventData


def setup_module():
    pass


def setup_function():
    pass


def teardown_function():
    pass


def teardown_module():
    pass


def test_x__when_x1():
    # Objective:
    # TODO

    # Setup
    event = Event('some_event', {
        'name': 'Bob',
        'age': 30,
        'obj': TempData()
    })

    # Test
    data = RemoteEventData('channel', event)
    try:
        x = data.json
    except TypeError:
        x = 'NO_JSON'
    y = data.dict

    # Verify
    print(x)
    print(y)


class Temp:
    def __init__(self):
        self.name = 'jane'


class TempData(Data):
    def __init__(self):
        super().__init__({
            'obj': Temp()
        })
