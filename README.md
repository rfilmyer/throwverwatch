# throwverwatch
Overwatch Stats Collector - bind to a hotkey and save your SR/winrate at a point in time!

Ever check your SR at the end of a season and wonder how you lost 1000 points? I can't do everything, but I can help show you when you started trending down! 

# How to Run...
* Download or `git clone` the repository
* Install the `requests` and `bs4` (AKA BeautifulSoup4) python packages via `pip`
** `pip install -U requests bs4`
* Run the script through the command line!


# Project Status
After a Friday night coding session, I got an MVP working! Doesn't listen for hotkeys yet, and doesn't save any data. #2 will be easy, #1 requires root on Linux, so more difficult to test.

# MVP Goals
A command-line application that...

1. Listens for a hotkey,
2. Grabs your overwatch stats at that moment in time, and
3. Saves them to a CSV file

# MVP dependencies:

* Python 3.5 or newer
* requests
* BeautifulSoup

# Future Goals:

* A GUI (tkinter?)
* Ability to automatically check when a match ends (Check for access to the end-of-match sound files?)
