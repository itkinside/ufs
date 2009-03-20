import re
import locale

CALLSIGN_RE = re.compile(r'^[A-Z]+[0-9][A-Z0-9]*[A-Z]$')

def callsign_sorted(objects):
    current_locale = locale.getlocale()
    locale.setlocale(locale.LC_COLLATE, ("nb_NO", 'UTF-8'))

    sorted_list = sorted(objects, callsign_cmp, callsign_key)

    locale.setlocale(locale.LC_COLLATE, current_locale)

    return sorted_list

def callsign_key(value):
    return (locale.strxfrm(value.name.lower().encode('utf-8')),
            value.short_name)

def callsign_cmp(x, y):
    '''
        ARK friendly sort method that should sort in the following order:

            1. LAxxxx signs
            2. LBxxxx signs
            3. xxxxxx signs
            4. Other names
    '''

    x_short_name = x[1] or ''
    y_short_name = y[1] or ''

    x_is_callsign = CALLSIGN_RE.match(x_short_name)
    y_is_callsign = CALLSIGN_RE.match(y_short_name)

    if x_is_callsign and y_is_callsign:
        x_is_la = x_short_name.startswith('LA')
        y_is_la = y_short_name.startswith('LA')

        if x_is_la and y_is_la:
            return cmp(x_short_name, y_short_name)
        elif x_is_la:
            return -1
        elif y_is_la:
            return 1

        x_is_lb = x_short_name.startswith('LB')
        y_is_lb = y_short_name.startswith('LB')

        if x_is_lb and y_is_lb:
            return cmp(x_short_name, y_short_name)
        elif x_is_lb:
            return -1
        elif y_is_lb:
            return 1

    elif x_is_callsign:
        return -1
    elif y_is_callsign:
        return 1

    return cmp(x[0], y[0])
