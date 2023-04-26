"""Message query matching logic."""
import re

modes = {
    "`U": lambda message:
        all(x.isalpha() or x.isspace() for x in message) and
        not re.match(r"^!\w+",message) and message.isupper(),
    "`L": lambda message:
        all(x.isalpha() or x.isspace() for x in message) and
        not re.match(r"^!\w+",message) and message.islower(),
    "`T": lambda message:
        len(message) >= 2 and all(x.isalpha() or x.isspace() for x in message) and
        not re.match(r"^!\w+",message) and message[0].isupper() and message[1].islower(),
    "`Ts": lambda message:
        len(message) >= 2 and all(x.isalpha() or x.isspace() for x in message) and
        not re.match(r"^!\w+",message) and message[0].isupper() and
        all(x.isalpha() and x.islower() or x.isspace() for x in message[1:]),
    "`C": lambda message:
        len(message) >= 2 and re.match(r"^!\w+",message) and
        '!' not in message.split(' ')[0][1:],
}

start = (
    lambda message, fix_query:
        message.lower().startswith(fix_query.lower()),
    lambda message, fix_query:
        bool(re.match(rf"^{fix_query.lower()}\b.*",message.lower())),
    lambda message, fix_query:
        message.startswith(fix_query),
    lambda message, fix_query:
        bool(re.match(rf"^{fix_query}\b.*",message))
)

end = (
    lambda message, fix_query:
        message.lower().endswith(fix_query.lower()),
    lambda message, fix_query:
        bool(re.match(rf".*\b{fix_query.lower()}$",message.lower())),
    lambda message, fix_query:
        message.endswith(fix_query),
    lambda message, fix_query:
        bool(re.match(rf".*\b{fix_query}$",message))
)

exclude = (
    lambda message, fix_query:
        fix_query.lower() not in message.lower(),
    lambda message, fix_query:
        not bool(re.match(rf".*\b{fix_query.lower()}\b.*",message.lower())),
    lambda message, fix_query:
        fix_query not in message,
    lambda message, fix_query:
        not bool(re.match(rf".*\b{fix_query}\b.*",message))
)

include = (
    lambda message, fix_query:
        fix_query.lower() in message.lower(),
    lambda message, fix_query:
        bool(re.match(rf".*\b{fix_query.lower()}\b.*",message.lower())),
    lambda message, fix_query:
        fix_query in message,
    lambda message, fix_query:
        bool(re.match(rf".*\b{fix_query}\b.*",message))
)

def check_msg(message: str, query: str, fix_query: str,
              check_case: bool, check_exact_word: bool) -> bool:
    """Test if a message matches a query pattern."""
    index = 2*int(check_case)+int(check_exact_word)
    # (none, exact word, case-sensitive, case-sensitive + exact word)
    if query in modes:
        return modes[query](message)
    if query.startswith('>'):
        return start[index](message,fix_query)
    if query.endswith('<'):
        return end[index](message,fix_query)
    if query.startswith('~'):
        return exclude[index](message,fix_query)
    return include[index](message,fix_query)
