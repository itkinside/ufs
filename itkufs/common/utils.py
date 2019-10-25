import re
import locale

CALLSIGN_RE = re.compile(r"^[A-Z]+[0-9][A-Z0-9]*[A-Z]$")


def verify_account_number(num):
    """Check that account is has correct check digit.

       http://no.wikipedia.org/wiki/Kontonummer
       http://no.wikipedia.org/wiki/MOD11
    """
    num = re.sub("[ .-]", "", str(num))
    if len(num) != 11:
        return False

    crosssum = 0
    for a, b in zip(num[:10], "5432765432"):
        crosssum += int(a) * int(b)
    return num[10] == str(11 - crosssum % 11) or (
        crosssum % 11 == 0 and num[10] == "0"
    )


def callsign_sorted(objects):
    current_locale = locale.getlocale()

    try:
        locale.setlocale(locale.LC_COLLATE, ("nb_NO", "UTF-8"))
    except Exception:
        pass

    sorted_list = sorted(objects, callsign_cmp, callsign_key)

    locale.setlocale(locale.LC_COLLATE, current_locale)

    return sorted_list


def callsign_key(value):
    is_callsign = value.short_name and CALLSIGN_RE.match(value.short_name)

    return {
        "name": locale.strxfrm(value.name.lower().encode("utf-8")),
        "short_name": value.short_name or "",
        "is_callsign": is_callsign,
        "is_la": is_callsign and value.short_name.startswith("LA"),
        "is_lb": is_callsign and value.short_name.startswith("LB"),
    }


def callsign_cmp(x, y):
    """
        ARK friendly sort method that should sort in the following order:

            1. LAxxxx signs
            2. LBxxxx signs
            3. xxxxxx signs
            4. Other names
    """

    if x["is_callsign"] and y["is_callsign"]:
        if x["is_la"] and y["is_la"]:
            return cmp(x["short_name"], y["short_name"])
        elif x["is_la"]:
            return -1
        elif y["is_la"]:
            return 1

        if x["is_lb"] and y["is_lb"]:
            return cmp(x["short_name"], y["short_name"])
        elif x["is_lb"]:
            return -1
        elif y["is_lb"]:
            return 1

    elif x["is_callsign"]:
        return -1
    elif y["is_callsign"]:
        return 1

    return cmp(x["name"], y["name"])
