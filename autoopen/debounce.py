from time import time


class Debounce:
    def __init__(self, debounce_time: float):
        self.debounce_time = debounce_time

        self._state_changed = False
        self._state_unstable = False
        self._state_debounced = False

        self._last_time = 0

    def is_rising(self):
        return self._state_debounced and self._state_changed

    @property
    def value(self):
        return self._state_debounced

    def update(self, new_value):
        self._state_changed = False
        cur_time = time()
        if new_value != self._state_unstable:
            self._last_time = cur_time
            self._state_unstable = not self._state_unstable
        else:
            if cur_time - self._last_time >= self.debounce_time:
                if new_value != self._state_debounced:
                    self._last_time = cur_time
                    self._state_debounced = not self._state_debounced
                    self._state_changed = True
