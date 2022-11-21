import logging
import time
from typing import Any

from eventdispatch import Event, register_for_events, unregister_from_events, post_event

STEP_SIM_WORK_SEC = 1

APP_STARTED = 'started'
STEP1_COMPLETED = 'step_1_completed'
STEP2_COMPLETED = 'step_2_completed'
STEP3_COMPLETED = 'step_3_completed'
STEP4_COMPLETED = 'step_4_completed'


class Worker1:
    events = [
        APP_STARTED,
        STEP2_COMPLETED,
        STEP3_COMPLETED
    ]

    def __init__(self):
        register_for_events(self.on_event, Worker1.events)

    def on_event(self, event: Event):
        log_event(self, event)

        # Map events that occurred to action to perform.
        if event.name == APP_STARTED:
            self.do_step1()

        elif event.name == STEP2_COMPLETED:
            self.do_step3()

        elif event.name == STEP3_COMPLETED:
            # Done (cleanup).
            unregister_from_events(self.on_event, Worker1.events)

    def do_step1(self):
        log_task(self, 'step 1')
        wait(STEP_SIM_WORK_SEC)
        post_event(STEP1_COMPLETED)

    def do_step3(self):
        log_task(self, 'step 3')
        wait(STEP_SIM_WORK_SEC)
        post_event(STEP3_COMPLETED)


class Worker2:
    events = [
        STEP1_COMPLETED,
        STEP3_COMPLETED,
        STEP4_COMPLETED
    ]

    def __init__(self):
        register_for_events(self.on_event, Worker2.events)

    def on_event(self, event: Event):
        log_event(self, event)

        # Map events that occurred to action to perform.
        if event.name == STEP1_COMPLETED:
            self.do_step2()

        elif event.name == STEP3_COMPLETED:
            self.do_step4()

        elif event.name == STEP4_COMPLETED:
            # Done (cleanup).
            unregister_from_events(self.on_event, Worker2.events)

    def do_step2(self):
        log_task(self, 'step 2')
        wait(STEP_SIM_WORK_SEC)
        post_event(STEP2_COMPLETED)

    def do_step4(self):
        log_task(self, 'step 4')
        wait(STEP_SIM_WORK_SEC)
        post_event(STEP4_COMPLETED)


def wait(amount: float):
    time.sleep(amount)


def log_task(for_class: Any, task_name: str):
    get_logger(for_class).info(f' Doing: {task_name}\n')


def log_event(for_class: Any, event: Event):
    get_logger(for_class).info(f" Got event '{event.name}'\n{event.raw}\n")


def get_logger(cls: Any):
    return logging.getLogger(cls.__class__.__name__)
