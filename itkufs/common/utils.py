import re

CALLSIGN_RE = re.compile(r'^[A-Z]+[0-9][A-Z0-9]*[A-Z]$')

def callsign_sorted(objects):
    return sorted(objects, callsign_cmp, callsign_key)

def callsign_key(object):
    return object.short_name or object.name

def callsign_cmp(x, y):
    '''
        ARK friendly sort method that should sort in the following order:

            1. LAxxxx signs
            2. LBxxxx signs
            3. xxxxxx signs
            4. Other names
    '''

    x_is_callsign = CALLSIGN_RE.match(x)
    y_is_callsign = CALLSIGN_RE.match(y)

    if x_is_callsign and y_is_callsign:
        x_is_la = x.startswith('LA')
        y_is_la = y.startswith('LA')

        if x_is_la and y_is_la:
            return cmp(x, y)
        elif x_is_la:
            return -1
        elif y_is_la:
            return 1

        x_is_lb = x.startswith('LB')
        y_is_lb = y.startswith('LB')

        if x_is_lb and y_is_lb:
            return cmp(x, y)
        elif x_is_lb:
            return -1
        elif y_is_lb:
            return 1

    elif x_is_callsign:
        return -1
    elif y_is_callsign:
        return 1

    return cmp(x, y)
