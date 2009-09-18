import re
import locale

CALLSIGN_RE = re.compile(r'^[A-Z]+[0-9][A-Z0-9]*[A-Z]$')

def callsign_sorted(objects):
    current_locale = locale.getlocale()

    try:
        locale.setlocale(locale.LC_COLLATE, ("nb_NO", 'UTF-8'))
    except:
        pass

    sorted_list = sorted(objects, callsign_cmp, callsign_key)

    locale.setlocale(locale.LC_COLLATE, current_locale)

    return sorted_list

def callsign_key(value):
    is_callsign = value.short_name and CALLSIGN_RE.match(value.short_name)

    return {
        'name': locale.strxfrm(value.name.lower().encode('utf-8')),
        'short_name': value.short_name or '',
        'is_callsign': is_callsign,
        'is_la': is_callsign and value.short_name.startswith('LA'),
        'is_lb': is_callsign and value.short_name.startswith('LB'),
    }

def callsign_cmp(x, y):
    '''
        ARK friendly sort method that should sort in the following order:

            1. LAxxxx signs
            2. LBxxxx signs
            3. xxxxxx signs
            4. Other names
    '''

    if x['is_callsign'] and y['is_callsign']:
        if x['is_la'] and y['is_la']:
            return cmp(x['short_name'], y['short_name'])
        elif x['is_la']:
            return -1
        elif y['is_la']:
            return 1

        if x['is_lb'] and y['is_lb']:
            return cmp(x['short_name'], y['short_name'])
        elif x['is_lb']:
            return -1
        elif y['is_lb']:
            return 1

    elif x['is_callsign']:
        return -1
    elif y['is_callsign']:
        return 1

    return cmp(x['name'], y['name'])
