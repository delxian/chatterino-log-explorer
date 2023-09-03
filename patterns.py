"""Message query matching logic."""
import re

def mode(query: str, message: str) -> bool:
    """Handle query modes."""
    if query in {"`T", "`Ts", "`C"} and len(message) < 2:
        return False
    if query == "`C":
        return bool(re.match(r"^!\w+", message)) and '!' not in message.split(' ')[0][1:]
    if (bool(re.match(r"^!\w+", message)) or
            not all(x.isalpha() or x.isspace() for x in message)):
        return False
    modes = {
        "`U": message.isupper(),
        "`L": message.islower(),
        "`T": message[0].isupper() and message[1].isalpha() and message[1].islower(),
        "`Ts": (message[0].isupper() and
                all(x.islower() for x in message[1:] if x.isalpha()))
        }
    return modes[query]

def start(message: str, fix_query: str, check_exact_word: bool) -> bool:
    """Handle startswith query."""
    return (bool(re.match(rf"^{fix_query}\b.*", message))
            if check_exact_word else message.startswith(fix_query))

def end(message: str, fix_query: str, check_exact_word: bool) -> bool:
    """Handle endswith query."""
    return (bool(re.match(rf".*\b{fix_query}$", message))
            if check_exact_word else message.endswith(fix_query))

def exclude(message: str, fix_query: str, check_exact_word: bool) -> bool:
    """Handle exclusion query."""
    return (bool(re.match(rf".*\b{fix_query}\b.*", message))
            if check_exact_word else fix_query not in message)

def include(message: str, fix_query: str, check_exact_word: bool) -> bool:
    """Handle inclusion query."""
    return (bool(re.match(rf".*\b{fix_query}\b.*", message))
            if check_exact_word else fix_query in message)

def check_msg(message: str, query: str, fix_query: str,
              check_case: bool, check_exact_word: bool) -> bool:
    """Test if a message matches a query pattern."""
    if query in {"`U", "`L", "`T", "`Ts", "`C"}:
        return mode(query, message)
    if not check_case:
        message, fix_query = message.lower(), fix_query.lower()
    args = (message, fix_query, check_exact_word)
    if query.startswith('>'):
        return start(*args)
    if query.endswith('<'):
        return end(*args)
    return exclude(*args) if query.startswith('~') else include(*args)
