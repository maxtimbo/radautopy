from datetime import datetime, timedelta

from apscheduler.triggers.cron import CronTrigger
from cron_descriptor import Options, get_description

DOW_NAMES = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]


def _dow_number(value: str) -> int:
    value = value.lower()
    if value[:3] in DOW_NAMES:
        return DOW_NAMES.index(value[:3])
    number = int(value)
    if not 0 <= number <= 7:
        raise ValueError(f"day of week {value} is out of range (0-7)")
    return number


def _standard_dow_to_names(field: str) -> str:
    # APScheduler numbers weekdays from Monday=0; crontab uses Sunday=0 (or 7)
    if field in ("*", "?"):
        return "*"
    days = set()
    for part in field.split(","):
        base, _, step = part.partition("/")
        step = int(step) if step else 1
        if base == "*":
            low, high = 0, 6
        elif "-" in base:
            low, high = (_dow_number(v) for v in base.split("-", 1))
        else:
            low = _dow_number(base)
            high = 7 if step > 1 else low
        if low > high:
            raise ValueError(f"invalid day of week range {base}")
        days.update(d % 7 for d in range(low, high + 1, step))
    return ",".join(DOW_NAMES[d] for d in sorted(days))


def trigger_from_crontab(expression: str, timezone=None) -> CronTrigger:
    fields = expression.split()
    if len(fields) != 5:
        raise ValueError(f"expected 5 fields, got {len(fields)}")
    minute, hour, day, month, dow = fields
    return CronTrigger(minute=minute, hour=hour, day=day, month=month,
                       day_of_week=_standard_dow_to_names(dow), timezone=timezone)


def describe(expression: str) -> str:
    options = Options()
    options.use_24hour_time_format = True
    return get_description(expression, options)


def next_runs(expression: str, count: int = 5) -> list[datetime]:
    trigger = trigger_from_crontab(expression)
    runs = []
    previous = None
    after = datetime.now(trigger.timezone)
    for _ in range(count):
        fire = trigger.get_next_fire_time(previous, after)
        if fire is None:
            break
        runs.append(fire)
        previous = fire
        after = fire + timedelta(seconds=1)
    return runs
