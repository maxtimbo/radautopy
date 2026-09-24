SECRET_KEYS = {"password", "api_key"}
MASK = "********"


def redact(value):
    if isinstance(value, dict):
        return {k: (MASK if k in SECRET_KEYS else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value
