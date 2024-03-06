"""Core Shared Functions of Sodium"""
from datetime import timedelta
from re import compile as regex_compile

def timecode_parser(timecode: str, retvalid: bool = True) -> tuple[str]:
    """Parses timecode into h, m, s, and ms, optionally return if parsed timecode is valid"""
    has_ms = False
    tc = timecode
    h = "0"
    m = "0"
    s = "0"
    ms = "0"

    # If a timecode has a . split timecode into everything else and the ms
    count_ms = timecode.count(".")
    if count_ms == 1:
        has_ms = True
    if has_ms:
        tc, ms = timecode.split(".")

    # Split the timecode into h, m, and s
    count_split = tc.count(":")
    if count_split == 1:
        m, s = tc.split(":")
    elif count_split == 2:
        h, m, s = tc.split(":")

    if retvalid:
        valid = timecode_validate(timecode)
        return h, m, s, ms, valid
    return h, m, s, ms

def timecode_validate(timecode: str) -> str | bool:
    """Validates timecode"""
    has_ms = False
    tc = timecode
    h = ""
    m = ""
    s = ""
    ms = ""

    regex = regex_compile("^[0-9:.]+$")
    if not regex.match(timecode):
        return "Timecode can only contain 0-9, :, and ."

    # Counts number of .
    count_ms = timecode.count(".")
    # If it is one, then there are ms, if it is >1, then invalid
    if count_ms == 1:
        has_ms = True
    if count_ms > 1:
        return "Multiple . detected"

    # If it has ms, put the timecode without ms into tc
    if has_ms:
        tc, ms = timecode.split(".")
        # If # of digits in ms >3, invalid
        if len(ms) > 3:
            return "Milliseconds greater than 3 digits"
        if len(ms) == 0:
            return "Specified milliseconds but none provided"

    # Count number of : in tc
    count_split = tc.count(":")

    # If 0 or more than 2, invalid
    if (count_split == 0) or (count_split > 2):
        return "Format: [HH:]MM:SS.mmm"

    # If 1, then it only has minutes and second
    if count_split == 1:
        m, s = tc.split(":")
    # If it is 2, then it has hr, min, and sec
    elif count_split == 2:
        h, m, s = tc.split(":")

    if (len(h) > 2) or (len(m) < 1) or (len(m) > 2) or (not len(s) == 2):
        return "Format: [HH:]MM:SS[.mmm]"

    if int(m) >= 60:
        return "Minutes greater than 59"
    if int(s) >= 60:
        return "Seconds greater than 59"

    return True

def timecode_calculate(len_seconds: float) -> str:
    """Calculates timecode from given length in seconds"""
    return str(timedelta(seconds=len_seconds)).split("000",maxsplit=1)[0]

def timecode_compare(time1: tuple[int], time2: tuple[int]) -> int:
    """1 for time1 being larger than time2, 0 if they are the same, -1 if time2 is larger than time1"""
    h1, m1, s1, ms1 = time1
    h2, m2, s2, ms2 = time2

    # Compare h1 and h2, if they are the same fall through to next check
    if h1>h2:
        return 1
    if h1<h2:
        return -1
    # Compare m1 and m2, if they are the same fall through to next check
    if m1>m2:
        return 1
    if m1<m2:
        return -1
    # Compare s1 and s2, if they are the same fall through to next check
    if s1>s2:
        return 1
    if s1<s2:
        return -1
    # Compare ms1 and ms2, if they are the same return 0
    if ms1>ms2:
        return 1
    if ms1<ms2:
        return -1
    return 0