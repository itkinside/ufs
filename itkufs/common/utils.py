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
    2. LBxxxx signs
    3. xxxxxx signs
    4. Other names
    """
    return sorted(accounts, key=callsign_key)


def callsign_key(account):
    is_callsign = account.short_name and CALLSIGN_RE.match(account.short_name)
    is_la = is_callsign and account.short_name.startswith("LA")
    is_lb = is_callsign and account.short_name.startswith("LB")

    if is_la:
        index = 1
    elif is_lb:
        index = 2
    elif is_callsign:
        index = 3
    else:
        index = 4

    return (index, account.name)
