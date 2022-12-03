from enum import Enum, auto
from datetime import datetime, timedelta

from base_error import BaseError


class TaskType(Enum):
    CYCLIC = auto()
    ONCE = auto()


class Task:

    INVALID_TASK_TYPE = "Invalid task type"
    INVALID_TASK_NAME = "Invalid task name"
    TASK_TIME_MUST_BE_AN_INTERVAL_FOR_CYCLIC_TASKS = "Task time must be an interval for cyclic tasks"
    TASK_TIME_MUST_BE_AN_AWARE_TIME_FOR_ONCE_TASKS = "Task time must be an aware time for once tasks"
    EXCEPTION_DURING_TASK_EXECUTION = "Exception (type '{}', message '{}') during task execution"

    def __init__(self, name, task_type, task_time, command, arguments):
        if not isinstance(name, str):
            raise TaskError(Task.INVALID_TASK_NAME)
        self._name = name
        if not isinstance(task_type, TaskType):
            if isinstance(task_type, str):
                try:
                    task_type = TaskType[task_type]
                except KeyError:
                    raise TaskError(Task.INVALID_TASK_TYPE)
            else:
                raise TaskError(Task.INVALID_TASK_TYPE)
        self._task_type = task_type
        if self._task_type is TaskType.CYCLIC:
            if not isinstance(task_time, timedelta):
                raise TaskError(Task.TASK_TIME_MUST_BE_AN_INTERVAL_FOR_CYCLIC_TASKS)
            self._next_run = datetime.now().astimezone()
            self._task_time = task_time
        elif self._task_type is TaskType.ONCE:
            if not isinstance(task_time, datetime) or task_time.tzinfo is None or task_time.tzinfo.utcoffset(task_time) is None:
                raise TaskError(Task.TASK_TIME_MUST_BE_AN_AWARE_TIME_FOR_ONCE_TASKS)
            self._next_run = task_time
            self._task_time = None
        self._command = command
        self._arguments = arguments if arguments is not None else {}
        self._expired = False

    @property
    def name(self):
        return self._name

    @property
    def expired(self):
        return self._expired

    def run(self):
        if datetime.now().astimezone() > self._next_run and not self._expired:
            try:
                self._command(**self._arguments)
            except Exception as e:
                raise TaskError(Task.EXCEPTION_DURING_TASK_EXECUTION.format(type(e), str(e)))
            if self._task_type is TaskType.CYCLIC:
                self._next_run += self._task_time
            elif self._task_type is TaskType.ONCE:
                self._expired = True

    @property
    def info(self):
        return {
            'name': self._name,
            'type': self._task_type.name,
            'next_run': self._next_run,
            'time': self._task_time,
            'command': self._command.__name__,
            'arguments': self._arguments
        }


class TaskError(BaseError):
    _reference_class = Task
