import re

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


def callsign_sorted(accounts):
    """
    ARK friendly sort method that should sort in the following order:

    1. LAxxxx signs
    2. LA0xxx signs
    3. LBxxxx signs
    4. LB0xxx signs
    5. xxxxxx signs
    6. Other names
    """
    return sorted(accounts, key=callsign_key)


def callsign_key(account):
    is_callsign = account.short_name and CALLSIGN_RE.match(account.short_name)
    is_la = is_callsign and account.short_name.startswith("LA")
    is_la0 = is_callsign and account.short_name.startswith("LA0")
    is_lb = is_callsign and account.short_name.startswith("LB")
    is_lb0 = is_callsign and account.short_name.startswith("LB0")

    if is_la0:
        index = 2
    elif is_la:
        index = 1
    elif is_lb0:
        index = 4
    elif is_lb:
        index = 3
    elif is_callsign:
        index = 5
    else:
        index = 6

    return (index, account.short_name if is_callsign else account.name)
