import datetime
from functools import partial

class ReplaceFillers:
    today = datetime.datetime.today()

    def __init__(self, track: str) -> None:
        self.track = self.iterate_functions(track)

    def iterate_functions(self, track: str) -> str:
        mutable = copy(track)
        for filler, function in self.filler_functions.items():
            if filler in mutable:
                mutable = function(mutable, filler)

        return mutable

    @staticmethod
    def replace_fillers(mutable: str, filler: str, value: str) -> str:
        return mutable.replace(filler, copy(value))

    filler_functions = {
        '{now}'         : partial(replace_fillers, value = today.strftime('%y%m%d %H:%M')),
        '{weekday}'     : partial(replace_fillers, value = today.strftime('%A')),
        '{year}'        : partial(replace_fillers, value = today.strftime('%y')),
        '{month}'       : partial(replace_fillers, value = today.strftime('%m')),
        '{day}'         : partial(replace_fillers, value = today.strftime('%d')),
        '{week}'        : partial(replace_fillers, value = today.strftime('%V'))
    }
