subscribers = dict()


def post(event_type: str, data):
    if not event_type in subscribers:
        return

    for fn in subscribers[event_type]:
        fn(data)


def subscribe(event_type: str, fn):
    if not event_type in subscribers:
        subscribers[event_type] = []

    subscribers[event_type] = fn


def unsubscribe(event_type: str, funct):
    if not event_type in subscribers:
        return

    for fn in subscribers[event_type]:
        if fn == funct:
            subscribers[event_type].remove(funct)
