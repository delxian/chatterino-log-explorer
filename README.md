# Chatterino Log Explorer
Scrapes and analyzes chat logs collected by Chatterino's logging feature.  
My first "real" Python project.
## Features
- First-time setup (logs directory, UTC offset, default exclusions)
- Specify channel, dates, usernames, and message contents
- Filter users below minimum message count threshold
- Show all/random messages from results
- Show most common words from results
  - Exclude most common English words (list from [Wikipedia](https://en.wikipedia.org/wiki/Most_common_words_in_English))
- Determine purity scores (how "innocent" a user's messages are)
  - term lists not included
- Count total/average per-user statistics (messages, words, characters)
- Count total/average matching messages (all, daily, hourly)
- Exclude known bots and command messages from results
## Requirements
- Python 3.8 or higher
- [matplotlib](https://pypi.org/project/matplotlib/), [numpy](https://pypi.org/project/numpy/)
## License
- [MIT](LICENSE)