from enum import Enum, unique, auto
from typing import Iterable


@unique
class CBUStateBase(Enum):
    def in_state(self, states):
        if type(states) is type(self):
            return self is states
        elif not isinstance(states, Iterable):
            states = (states,)
        return self in states
