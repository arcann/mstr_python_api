from enum import Enum


class BitSet(set):
    def combine(self):
        result = 0
        for entry in self:
            if isinstance(entry, Enum):
                result |= entry.value
            else:
                result |= entry
        return result
