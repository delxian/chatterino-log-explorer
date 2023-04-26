"""Execution of log analysis."""
# pylint: disable=invalid-name,multiple-statements
from collections import defaultdict
import json
import os
import random
import re
import sys
from tkinter.filedialog import askdirectory
from typing import TypedDict

import matplotlib.pyplot as plt
import numpy

from patterns import check_msg


class Config(TypedDict):
    """Configuration data for default operation."""
    logs_folder: str
    utc_offset: int
    exclude_commands: bool
    exclude_bots: bool


def sort_dict(d: dict, use_value: bool = False, reverse: bool = False):
    """Shorthand for sorting dictionaries through list sorting."""
    if use_value:
        return dict(sorted(d.items(),key=lambda item: item[1],reverse=reverse))
    return dict(sorted(d.items(),reverse=reverse))

config: Config = {
    "logs_folder": "",
    "utc_offset": 0,
    "exclude_commands": False,
    "exclude_bots": False
    }
try:
    with open("config.json",'r',encoding="UTF-8") as file:
        config = json.loads(file.read())
except FileNotFoundError:
    print("Configuration file missing, starting first-time setup:")
    logs_folder = askdirectory(title='Select your Chatterino logs directory " \
                               "(see Chatterino Settings >> Moderation >> Logs)')
    utc_offset = input("Input +/- UTC offset (e.g. UTC-6 = -6): ").strip()
    utc_offset = int(utc_offset) if utc_offset.lstrip('-+').isnumeric() else 0
    exclude_commands = input(
        "Exclude !command messages? [unless checking commands specifically] (y/n): "
        ).strip() == 'y'
    exclude_bots = input(
        "Exclude bot messages? [doesn't apply if checking exact username] (y/n): "
        ).strip() == 'y'
    config = {
        "logs_folder": logs_folder,
        "utc_offset": utc_offset,
        "exclude_commands": exclude_commands,
        "exclude_bots": exclude_bots
        }
    with open("config.json",'w',encoding="UTF-8") as file:
        file.write(json.dumps(config,indent=4,separators=(',',': ')))
    print("Configuration saved:")
    print(f"    Logs directory: {logs_folder}")
    print(f"    UTC offset: {utc_offset}")
    print(f"    Commands excluded: {exclude_commands}")
    print(f"    Bots excluded: {exclude_bots}")
finally:
    logs_folder = config["logs_folder"]
    utc_offset = config["utc_offset"]
    exclude_commands = config["exclude_commands"]
    exclude_bots = config["exclude_bots"]

ttypes = ("bots","common_eng","strong_curse","mild_curse","sexual")
if any(not os.path.isfile(ttype+".txt") for ttype in ttypes):
    print("At least one term list was missing and has been created:")
    for ttype in ("bots","common_eng","strong_curse","mild_curse","sexual"):
        if not os.path.isfile(ttype+".txt"):
            print(f"    {ttype}.txt")
            with open(ttype+".txt",'w',encoding="UTF-8") as file:
                pass
    print("Please add terms as desired and restart the program (one lowercase term per line).")
    sys.exit()

with open("bots.txt",'r',encoding="UTF-8") as file:
    BOTS = set(file.read().splitlines())
with open("common_eng.txt",'r',encoding="UTF-8") as file:
    COMMON_ENG = tuple(file.read().splitlines())
with open("strong_curse.txt",'r',encoding="UTF-8") as file:
    STRONG_CURSE = set(file.read().splitlines())
with open("mild_curse.txt",'r',encoding="UTF-8") as file:
    MILD_CURSE = set(file.read().splitlines())
with open("sexual.txt",'r',encoding="UTF-8") as file:
    SEXUAL = set(file.read().splitlines())
PURITY_TERMS = STRONG_CURSE | MILD_CURSE | SEXUAL  # separate only for organization

print('\n'.join([line.center(50,'=') for line in ('',"Chatterino Chat Log Explorer",'')]))

while True:
    channels, channels_disp = [], []
    for _, directories, _ in os.walk(f"{logs_folder}/Twitch/Channels/",topdown=False):
        channels = list(directories)
        channels_disp = [f"{i} - {username}" for i,username in enumerate(directories,start=1)]
    print(f'\nValid channels:\n{", ".join(channels_disp)}')
    while True:
        channel = input("\nInput username/number from list: ").strip().lower()
        if channel.isnumeric() and 1 <= int(channel) <= len(channels):
            channel = channels[int(channel)-1]
            break
        if channel in channels: break
    print(f"    Selected channel: {channel}")
    rootpath = f"{logs_folder}/Twitch/Channels/{channel}"

    dates = input(
        "Input dates (YYYY-MM-DD) separated by spaces " \
        "[or >start and/or end<] (leave blank for all dates): "
        ).split()
    date_find, date_replace = r'-(?:(?P<digit>\d))\b', r'-0\g<digit>'
    dates = [re.sub(date_find,date_replace,date) for date in dates]  # YYYY-M-D -> YYYY-MM-DD
    date_type, date_disp, rewrite_dates = "list", "listed above", False
    startdate, enddate = None, None
    startdate_num, enddate_num = 0, 10**8
    if not dates:
        date_type, date_disp, rewrite_dates = "all", "all", True
    cdate_match = r"^(?:>(?P<start>[\d-]+))? ?(?:(?P<end>[\d-]+)<)?$"
    if (cdates := re.fullmatch(cdate_match,' '.join(dates))):
        startdate, enddate = cdates.group('start'), cdates.group('end')
        startdate_num = int(startdate.replace('-','')) if startdate else 0
        enddate_num = int(enddate.replace('-','')) if enddate else 10**8
        if startdate or enddate:
            date_type = 'both' if startdate and enddate else ('start' if startdate else enddate)
        fromdate = startdate if startdate else "earliest"
        todate = enddate if enddate else "latest"
        date_disp = f'{fromdate} -> {todate}'
        dates = []
        for filename in os.listdir(rootpath):
            if (filedate := re.fullmatch(r"^[a-z\d_]*-(.*)\.log$",filename)):
                filedate = filedate.group(1)
                if startdate_num <= int(filedate.replace('-','')) <= enddate_num:
                    dates.append(filedate)
    print(f"    Selected dates: {date_disp}")

    query = input(
        "`U - UPPER, `L - lower, `T - TiTLE, `Ts - Title, `C - !cmd, " \
        ">xyz - xyz..., xyz< - ...xyz, ~xyz - no 'xyz'" \
        "\nInput $user query and/or message query [$UQ MQ] (leave blank for everything): "
        ).strip()
    user_query, message_query, fix_query = '', '', ''
    search_type, query_disp, has_string = 'all', '', False
    check_exact_name, check_case, check_exact_word, min_msgs = False, False, False, 0
    cquery_match = r"^(?:\$(?P<user>\S+) ?)?(?P<message>.*)$"
    if query and (cquery := re.fullmatch(cquery_match,query)):
        user_query = cquery.group('user') if cquery.group('user') else ''
        message_query = cquery.group('message')
        search_type, user_query = 'user', user_query.lower()
        if user_query:
            if (check_exact_name := input("Check exact username? (y/n): ").strip() == 'y'):
                query_disp += f" from {user_query}"
            else:
                query_disp += f" from ??{user_query}??"
        if message_query:
            search_type, has_string = 'msg', True
            if message_query in ("`U","`L","`T","`Ts","`C"):
                query_disp += {
                    "`U": " [uppercase only]",
                    "`L": " [lowercase only]",
                    "`T": " [title only]",
                    "`Ts": " [title (strict) only]",
                    "`C": " [command only]"
                    }[message_query]
                has_string = False
            elif message_query.startswith('>'):
                fix_query = message_query[1:]
                query_disp += f' [starting with "{fix_query}"'
            elif message_query.endswith('<'):
                fix_query = message_query[:-1]
                query_disp += f' [ending with "{fix_query}"'
            elif message_query.startswith('~'):
                fix_query = message_query[1:]
                query_disp += f' [excluding "{fix_query}"'
            else:
                fix_query = message_query
                query_disp += f' [containing "{fix_query}"'
            if has_string:
                if (check_case := input("[MQ] Case-sensitive? (y/n): ").strip() == 'y'):
                    query_disp += " (case-sensitive)"
                if (check_exact_word := input(
                    "[MQ] Enforce exact word match? [disable if query contains symbols] (y/n): "
                    ).strip() == 'y'):
                    query_disp += " <exact word match>"
                query_disp += ']'
    else:
        has_string = False
    if user_query and message_query:
        search_type = 'hybrid'
    if search_type in ('msg','hybrid','all') and not check_exact_name:
        if (min_msgs := input(
            "Input minimum # of messages to include user (leave blank for none): "
            ).strip()).isnumeric():
            min_msgs = int(min_msgs)
            query_disp += f" (from users with >={min_msgs} messages)"
        else:
            min_msgs = 0

    picks = [False]*8
    show_msgs, count_words, check_purity, show_random = picks[:4]
    count_daily, count_per_user, count_hourly, show_hourly_graph = picks[4:]
    show_freq_stats = False
    options = (
        "show messages from logs",
        "show most common words",
        "calculate user purity scores",
        "show random messages",
        "count daily messages",
        "count per-user stats",
        "count hourly messages",
        "show hourly message graph"
        )
    for i,option in enumerate(options,start=1):
        print(f"{i} - {option}")
    print("Keep in mind these options only include matched messages.")
    pick_option = input("Input numbers for the options you want to enable [e.g. 125]: ").strip()
    for num in pick_option:
        picks[int(num)-1] = True
    show_msgs, count_words, check_purity, show_random = picks[:4]
    count_daily, count_per_user, count_hourly, show_hourly_graph = picks[4:]
    show_freq_stats = any((count_daily,count_per_user,count_hourly,show_hourly_graph))

    if not show_msgs and (date_type != 'all' or message_query):
        show_msgs = input("Show messages? (y/n): ").strip() == 'y'

    word_query, word_fix_query, word_query_disp, word_has_string = '', '', '', False
    word_check_case, exclude_queries, exclude_common, unique_only = False, False, set(), False
    if count_words:
        if (word_query := input(
            "`U - UPPER, `L - lower, `T - TiTLE, `Ts - Title, " \
            "`C - !cmd, >xyz - xyz..., xyz< - ...xyz, ~xyz - no 'xyz'" \
            "\nInput word query (leave blank for everything): "
            ).strip()):
            word_has_string = True
            if word_query in ("`U","`L","`T","`Ts","`C"):
                word_query_disp += {
                    "`U": " [uppercase only]",
                    "`L": " [lowercase only]",
                    "`T": " [title only]",
                    "`Ts": " [title (strict) only]",
                    "`C": " [command only]"
                    }[word_query]
                word_has_string = False
            elif word_query.startswith('>'):
                word_fix_query = word_query[1:]
                word_query_disp += f' [starting with "{word_fix_query}"'
            elif word_query.endswith('<'):
                word_fix_query = word_query[:-1]
                word_query_disp += f' [ending with "{word_fix_query}"'
            elif word_query.startswith('~'):
                word_fix_query = word_query[1:]
                word_query_disp += f' [excluding "{word_fix_query}"'
            else:
                word_fix_query = word_query
                word_query_disp += f' [containing "{word_query}"'
            if word_has_string:
                if (word_check_case := input("Case-sensitive? (y/n): ").strip() == 'y'):
                    word_query_disp += " (case-sensitive)"
                word_query_disp += ']'
        if has_string or word_has_string:
            exclude_queries = input(
                "Exclude the queries themselves from word results? (y/n): "
                ).strip() == 'y'
        if (exclude_common := input(
            'Input # of 100 most common English words to exclude (leave blank for none): '
            ).strip()).isnumeric():
            word_query_disp += f" <without top {exclude_common} English words>"
            exclude_common = set(COMMON_ENG[:int(exclude_common)-1])
        else:
            exclude_common = set()
        if (unique_only := input("Only show unique words (ignore case)? (y/n): ").strip() == 'y'):
            word_query_disp += " (unique only)"

    purity_order, purity_disp = '', ''
    if check_purity:
        if search_type in ('msg','hybrid','all'):
            purity_order = input("Order users by most pure or impure? (p/i): ").strip()
            purity_disp = {'p':"Highest",'i':"Lowest"}.get(purity_order,"Highest")
        else:
            purity_disp = "User"

    show_indiv_word, show_indiv_char, average_indiv = False, False, False
    user_limit, user_order, user_disp, average_time_count = 0, '', '', ''
    if show_freq_stats:
        if count_per_user:
            show_indiv_word = input("Count per-user words? (y/n): ").strip() == 'y'
            show_indiv_char = input("Count per-user characters? (y/n): ").strip() == 'y'
            if show_indiv_word or show_indiv_char:
                average_indiv = input(
                    "Count per-message average instead of total words/characters? (y/n): "
                    ).strip() == 'y'
            if search_type in ('msg','all'):
                user_limit = input(
                    "Input # of users to show (leave blank for default 10): "
                    ).strip()
                user_limit = int(user_limit) if user_limit.isnumeric() else 10
                user_order = input("Order users by most or least? (m/l): ").strip()
                user_disp = {'m':"Most",'l':"Least"}.get(user_order,"Most")
            else:
                user_disp = "User"
        if any((count_daily,count_per_user,count_hourly,show_hourly_graph)):
            average_time_count = input(
                "Count daily average instead of total messages? (y/n): "
                ).strip() == 'y'

    if not any(picks): break

    print("\nLoading results...\n")

    # LOG SCRAPING BLOCK

    total_count, daily_count, dates_disp = 0, {}, []
    times, names = defaultdict(int), defaultdict(int)
    msgs, msg_words = defaultdict(list), defaultdict(int)
    msg_chars, purity = defaultdict(int), defaultdict(lambda: {'pcount':0,'icount':0})

    dates_len = len(dates)
    for dates_i,date in enumerate(dates,start=1):
        if not show_msgs:
            print(f"Reading logs... ({dates_i}/{dates_len})",end='\r')
        if date_type == "list":
            dates_disp.append(date)
        day_count = 0
        with open(f"{rootpath}/{channel}-{date}.log",'r',encoding='UTF-8',errors='replace') as file:
            for line in file:
                line = line.strip()
                matched = False
                if (cmsg := re.fullmatch(r"^\[([\d:]*)\]  ([a-z\d_]*): (.*)$",line)):
                    time, user, message = cmsg.groups()
                    args = (message,message_query,fix_query,check_case,check_exact_word)
                    if exclude_commands and message_query != "`C" and word_query != "`C":
                        if re.match(r"^!\w+",message): continue
                    if exclude_bots and not (search_type == "user" and check_exact_name):
                        if user in BOTS: continue
                    if search_type == 'all':
                        matched = True
                    elif search_type == 'user':
                        if check_exact_name:
                            matched = user == user_query
                        else:
                            matched = user_query.lower() in user.lower()
                    elif search_type in ('msg','hybrid'):
                        if user_query:
                            if check_exact_name:
                                matched = user == user_query
                            else:
                                matched = user_query.lower() in user.lower()
                            if matched:
                                matched = check_msg(*args)
                        else:
                            matched = check_msg(*args)

                    if matched:
                        if show_msgs:
                            print(date+" "+line)
                        total_count += 1
                        day_count += 1
                        times[int(time.replace(':','')[:2])] += 1  # count only by hour ([HH]MMSS)
                        names[user] += 1
                        msgs[user].append(message)
                        if show_indiv_word:
                            msg_words[user] += len(message.split(' '))
                        if show_indiv_char:
                            msg_chars[user] += len(message.replace(' ',''))
                        if check_purity:
                            message_words = message.lower().split(' ')
                            if not PURITY_TERMS.isdisjoint(message_words):
                                purity[user]['icount'] += 1
                            else:
                                purity[user]['pcount'] += 1

            daily_count[date] = day_count

    if min_msgs and not check_exact_name:
        for data in (msgs,msg_words,msg_chars,purity):
            new = {name:value for name,value in data.items() if names[name] >= min_msgs}
            data.clear()
            data.update(new)
        names = {name:value for name,value in names.items() if value >= min_msgs}

    # order hourly data by hour, user data by frequency
    times = sort_dict(times)
    names = sort_dict(names,use_value=True,reverse=True)

    # RESULTS BLOCK

    if msgs:
        msgs_len = len(msgs)
        query_disp += {
            'list': " on "+", ".join(dates_disp),
            'start': f" starting at {startdate}",
            'end': f" ending at {enddate}",
            'both': f" from {startdate} to {enddate}"
            }.get(date_type,'')

        # calculate most common words
        if count_words:
            print("\n")
            total_words = defaultdict(int)
            for msgs_i,(user,messages) in enumerate(msgs.items(),start=1):
                print(f"Reading users... ({msgs_i}/{msgs_len})",end='\r')
                message: str
                for message in messages:
                    for word in message.split():
                        args = (word,word_query,word_fix_query,word_check_case,False)
                        word_matched = True
                        if word_query:
                            word_matched = check_msg(*args)
                        if exclude_queries:
                            if fix_query:
                                if word.lower() == fix_query.lower():
                                    word_matched = False
                            if word_fix_query:
                                if word.lower() == word_fix_query.lower():
                                    word_matched = False
                        if exclude_common:
                            if word.lower() in exclude_common:
                                word_matched = False
                        if word_matched:
                            if unique_only:
                                total_words[word.lower()] += 1
                            else:
                                total_words[word] += 1

            total_words = sort_dict(total_words,use_value=True,reverse=True)
            print(total_words)
            print(f"\n\nMost common words{word_query_disp} in messages{query_disp} in #{channel}:")
            for i,word in enumerate(total_words):
                if i == 20: break
                print(f"    {word}: {total_words[word]}")

        if check_purity and purity:
            purity_score = {}
            for user,score in purity.items():
                pure = float(score['pcount'])
                impure = float(score['icount'])
                mcount = float(names[user])
                # arbitrary formula, modify as desired
                purity_score[user] = int(100 * ((pure/(pure+impure))**(4.25 * (mcount**0.05))))
            print(f"{purity_disp} purity score in messages{query_disp} in #{channel}:")
            if search_type == 'user':
                user_purity = purity[user_query]
                icount = str(user_purity['icount'])
                tcount = str(user_purity['icount']+user_purity['pcount'])
                print(f"    {purity_score[user_query]:<10} {'['+icount+'/'+tcount+' impure]'}")
            else:
                purity_score = sort_dict(purity_score,use_value=True,reverse=purity_order!='i')
                for i,(key,value) in enumerate(purity_score.items()):
                    if i == 20: break
                    user_purity = purity[key]
                    icount = str(user_purity['icount'])
                    tcount = str(user_purity['icount']+user_purity['pcount'])
                    print(f"    {key+': '+str(value):<30} {'['+icount+'/'+tcount+' impure]'}")
                print("\n")
                while (purity_user := input("Input a username (leave blank to exit): ").strip()):
                    try:
                        placement = list(purity_score).index(purity_user)+1
                        score = purity_score[purity_user]
                        pure = purity[purity_user]['pcount']
                        impure = purity[purity_user]['icount']
                    except (ValueError, KeyError):
                        print(f'User "{purity_user}" not found in results!')
                    else:
                        print(f'{purity_disp} purity placement{query_disp} for "{purity_user}" ' \
                              f'in #{channel}: {placement}/{len(purity_score)}')
                        print(f"Purity for {purity_user} in #{channel}: " \
                              f"{score} [{impure}/{pure+impure} impure]")

        if show_random:
            key_picker = list(msgs)
            print("\n\nPress enter for a new random message, type anything to quit.",end=' ')
            while not (loop := input('')):
                rand_key = random.choice(key_picker)
                print(
                    f"\nRandom message from {rand_key} in #{channel}: " \
                    f"{msgs[rand_key][random.randint(0,len(msgs[rand_key])-1)]}",
                    end=' ')  # type: ignore

    else:
        print("\nNo results found!")

    if show_freq_stats:
        title_disp, words_disp, per_words_disp = "Total", "total", "total"

        # convert to averages if needed
        if average_indiv:
            msg_words = {key:int(value/names[key]) for key,value in msg_words.items()}
            msg_chars = {key:int(value/names[key]) for key,value in msg_chars.items()}
            per_words_disp = "per message"
        if average_time_count:
            times = {key:int(value/dates_len) for key,value in times.items()}
            names = {key:int(value/dates_len) for key,value in names.items()}
            total_count = int(total_count/dates_len)
            title_disp, words_disp = "Daily", "daily"

        if count_daily and times:
            print(f"\nMessages{query_disp} by day in #{channel}:")
            for date,count in daily_count.items():
                print(f"    {date}: {count}")
        else:
            print("\n")

        # show total message count
        if search_type in ('msg','hybrid','all') or (search_type == 'user' and not count_per_user):
            print(f"{title_disp} messages{query_disp} in #{channel}: {total_count}\n")

        # per-user statistics
        if count_per_user and names:
            rev = user_order != 'l'
            print(f"{user_disp} {words_disp} messages{query_disp} in #{channel}:")
            if search_type == 'user':
                if check_exact_name:
                    print(f"    {names[user_query]}")
                else:
                    for key,value in names.items():
                        print(f"    {key}: {value}")
            else:
                names = sort_dict(names,use_value=True,reverse=rev)
                for i,(key,value) in enumerate(names.items()):
                    if i == user_limit: break
                    print(f"    {key}: {value}")
            if show_indiv_word and msg_words:
                print(f"{user_disp} words {per_words_disp} in messages{query_disp} in #{channel}:")
                if search_type == 'user':
                    print(f"    {msg_words[user_query]}")
                else:
                    msg_words = sort_dict(msg_words,use_value=True,reverse=rev)
                    for i,(key,value) in enumerate(msg_words.items()):
                        if i == user_limit: break
                        print(f"    {key}: {value}")
            if show_indiv_char and msg_chars:
                print(f"{user_disp} characters {per_words_disp} " \
                      f"in messages{query_disp} in #{channel}:")
                if search_type == 'user':
                    print(f"    {msg_chars[user_query]}")
                else:
                    msg_chars = sort_dict(msg_chars,use_value=True,reverse=rev)
                    for i,(key,value) in enumerate(msg_chars.items()):
                        if i == user_limit: break
                        print(f"    {key}: {value}")

        # show hourly message count
        if count_hourly and times:
            print(f"{title_disp} message frequency{query_disp} by hour in #{channel}:")
            hours_i, last_key = 0, None
            utc = list(range(-utc_offset % 24,24))+list(range(0,-utc_offset % 24))
            for key,value in times.items():
                key = key % 24
                showkey = str(key % 12 if key % 12 else 12)+(" AM" if key < 12 else " PM")
                # sync utc and local if hours missing
                hours_i = key if last_key is None else hours_i+(key-last_key)
                print(f"    {str(showkey)} ({utc[hours_i]} UTC): {str(value)}")
                last_key = key

        if show_hourly_graph:
            array = numpy.array(list(times.items()),dtype=int).transpose()
            try:
                plt.bar(array[0],array[1])
            except IndexError:
                print(f'No frequency results for query "{query}"')
            else:
                plt.title(f"{title_disp} Messages per Hour")
                plt.xlabel("Hour")
                plt.ylabel("# of messages sent")
                plt.show()

    if input("\nNew query? (y/n): ").strip() == 'n': break
