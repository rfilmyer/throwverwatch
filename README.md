# throwverwatch
Overwatch Stats Collector - bind to a hotkey and save your SR/winrate at a point in time!

Ever check your SR at the end of a season and wonder how you lost 1000 points? I can't do everything, but I can help show you when you started trending down! 

# How to Run...
* Download or `git clone` the repository
* Install the `requests` and `bs4` (AKA BeautifulSoup4) python packages via `pip`
** `pip install -U requests bs4`
* Run the script through the command line! Try doing `python3 . --help` to get more info about the command line options


# Project Status
After 2 nights of coding, It's working as a command line application!

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
