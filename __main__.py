import logging
import argparse
import csv
import os
from datetime import datetime
from contextlib import contextmanager

import requests
import keyboard
from bs4 import BeautifulSoup

logger = logging.getLogger("throwverwatch")

parser = argparse.ArgumentParser(description="Track Overwatch Stats")
parser.add_argument("battletag", nargs="?", default="Calvin#1337",
                    help="Your Battle.net username in the format 'Calvin#1337'")
parser.add_argument("output_file", nargs="?", default=None, help="The CSV file in which to save stats.")
parser.add_argument("--region", dest="region", default="us",
                    help="Overwatch Region (us, kr, eu)")
parser.add_argument("--platform", dest="platform", default="pc",
                    help="Platform (pc, ps4, xbone)")
parser.add_argument("--hotkey", dest="hotkey", default="home", help="Specify a hotkey/key combo (ex: 'home', 'ctrl+f')")
args = parser.parse_args()

HEROES = ["Genji", "McCree", "Pharah", "Reaper", "Soldier: 76", "Sombra", "Tracer", "Bastion", "Hanzo", "Junkrat",
          "Mei", "Torbjörn", "Widowmaker", "D.Va", "Reinhardt", "Roadhog", "Winston", "Zarya", "Ana", "Lúcio", "Mercy",
          "Symmetra", "Zenyatta"]


def assemble_url(battletag: str, device: str = 'pc', region: str = 'us') -> str:
    """
    Returns the URL to a user's stats page on PlayOverwatch.com
    :rtype: str
    :param battletag: A Battle.net battletag, including character code. (Ex: "Calvin#1337", "짬내#3905")
    :param device: pc or any of the console platforms (I've only tested PC)
    :param region: us, kr, or eu, corresponding to the battletag's account in the given region.
    :return:
    """
    username = battletag.replace('#', '-')
    return "https://playoverwatch.com/en-us/career/{device}/{region}/{username}".format(device=device,
                                                                                        region=region,
                                                                                        username=username)


def get_page(url: str, session: requests.Session = None) -> BeautifulSoup:
    """
    Grabs a webpage and parses it with BeautifulSoup
    """
    session = session if session else requests
    response = session.get(url)

    return BeautifulSoup(response.text, 'html.parser')


def find_stat_in_table(stat, div):
    """
    Table rows are formatted like so...
    <tbody>
        <tr>
            <td>Melee Final Blows</td>
            <td>167</td>
        </tr>
        <tr>
            <td>Solo Kills</td>
            <td>5,124</td>
        </tr>
        <tr>
            <td>Objective Kills</td>
            <td>5,762</td>
        </tr>
    </tbody>

    This is a convenient function to extract a statistic, given its name.

    :param stat: The name of a statistic (Ex: "Melee Final Blows", "Medals - Gold")
    :param div: could also be a tbody in the future
    :return:
    """
    for tr in div.find_all("tr"):
        if tr.td:
            if tr.td.text == stat:
                return tr.find_all("td")[1].text


def parse_stats_page(soup: BeautifulSoup) -> dict:
    """
    Extracts player statistics from a web page parsed by BeautifulSoup.
    :param soup: A parsed copy of the PlayOverwatch.com stats page for a user.
    :return: dict
    """

    image_to_rank = {"7": "Grandmaster",
                     "6": "Master",
                     "5": "Diamond",
                     "4": "Platinum",
                     "3": "Gold",
                     "2": "Silver",
                     "1": "Bronze"}

    stats = {"skill_rating": soup.find(class_="competitive-rank").div.text,
             "rank": image_to_rank.get(soup.find(class_="competitive-rank").img["src"][-5])}


    all_heroes_attr = {"data-category-id": "0x02E00000FFFFFFFF"}
    quick_play_stats = soup.find(id="quickplay").find(attrs=all_heroes_attr).find_all("div")
    quick_play_game_game_stats = next(div for div in quick_play_stats if div.table.thead.span.text == "Game")
    # stats["quick_play_games"] = find_stat_in_table("Games Played", quick_play_game_game_stats)
    stats["quick_play_wins"] = find_stat_in_table("Games Won", quick_play_game_game_stats)

    competitive_stats = soup.find(id="competitive").find(attrs=all_heroes_attr).find_all("div")
    competitive_game_stats = next(div for div in competitive_stats if div.table.thead.span.text == "Game")
    stats["competitive_games"] = find_stat_in_table("Games Played", competitive_game_stats)
    stats["competitive_wins"] = find_stat_in_table("Games Won", competitive_game_stats)

    # This is dead code for now, I'll add this when I add the other 6 metrics
    stats["heroes"] = {}
    for hero_bar in soup.find(id="competitive").find(
            attrs={"data-category-id": "overwatch.guid.0x0860000000000021"}).find_all(
                class_="bar-text"):
        hero = hero_bar.find(class_="title").text
        unparsed_time = hero_bar.find(class_="description").text
        if unparsed_time == '--':
            time = 0
        elif 'minute' in unparsed_time.split()[-1]:
            time = int(unparsed_time.split()[0])
        elif 'hour' in unparsed_time.split()[-1]:
            time = 60 * int(unparsed_time.split()[0])
        else:
            time = None
        stats["heroes"][hero] = time
    return stats


def get_statistics(battletag: str, device: str = 'pc', region: str = 'us', session: requests.Session = None) -> dict:
    return parse_stats_page(get_page(assemble_url(battletag, device=device, region=region), session=session))


def retrigger(hotkey: str = 'home', linux_warning: bool = False):
    """
    Blocks waiting for a hotkey (or enter) to be pressed.
    :param hotkey: The hotkey/key combination to listen for. See the `keyboard` library for documentation.
    :param linux_warning: Hotkeys do not work on linux.
            If this parameter is False, it will send a warning on a Linux machine.
    :return: Whether the user has been warned at some point.
    """
    try:
        keyboard.wait(hotkey)
    except ImportError:
        just_warned = False
        if not linux_warning:
            logging.warning("You must be root in order to register hotkeys on linux. "
                            "Press enter instead to refresh stats")
            just_warned = True
        input()
        return linux_warning or just_warned


def check_filename(filename: str = None) -> str:
    """
    If a filename is supplied, check if that file exists. Otherwise, returns a new filename
    :param filename:
    :return: A validated filename
    """
    if filename:
        if os.path.exists(filename):
            return filename

    # make a new file with a specific filename
    def make_default_filename():
        return "throwverwatch-{datetime}.csv".format(datetime=datetime.now().strftime("%Y%m%d-%H%M%S"))

    def make_filename_with_fudge(fudge_factor):
        return "throwverwatch-{datetime}-{fudge}.csv".format(datetime=datetime.now().strftime("%Y%m%d-%H%M%S"),
                                                             fudge=fudge_factor)

    if not os.path.exists(make_default_filename()):
        filename = make_default_filename()
    while os.path.exists(make_default_filename()):
        fudge = 1
        while os.path.exists(make_filename_with_fudge(fudge)):
            fudge += 1
            if fudge > 1000:
                raise IOError("Tried creating a new CSV, "
                              "but too many files named like {}".format(make_filename_with_fudge(fudge)))
        if not os.path.exists(make_filename_with_fudge(fudge)):
            filename = make_filename_with_fudge(fudge)
            break
    return filename


@contextmanager
def get_writer(filename: str):
    """
    Yields a CSV writer for a file. If the file doesn't exist yet, it initializes it with a header row.
    :param filename:
    :return:
    """
    if os.path.exists(filename):
        csvfile = open(filename, 'a')
        yield csv.writer(csvfile)
        csvfile.close()
    else:
        csvfile = open(filename, 'w')
        writer = csv.writer(csvfile)
        writer.writerow(["Time", "SR", "Rank", "Competitive Wins", "Competitive Games", "Quick Play Wins"])
        yield writer
        csvfile.close()


def save_statistics(stats: dict, writer: csv.writer):
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        stats["skill_rating"],
                        stats["rank"],
                        stats["competitive_wins"],
                        stats["competitive_games"],
                        stats["quick_play_wins"]])

warned_linux = False
csv_filename = check_filename(args.output_file)
print("Collecting stats for battletag {bt} in region {reg} and platform {plat}".format(bt=args.battletag,
                                                                                       reg=args.region,
                                                                                       plat=args.platform))
with get_writer(csv_filename) as csv_writer:
    while True:
        player_statistics = get_statistics(args.battletag, device=args.platform, region=args.region)
        print("Your SR is {0}.".format(player_statistics["skill_rating"]))
        print("{wins} qp wins.".format(wins=player_statistics["quick_play_wins"]))
        print("{wins} comp wins out of {games} games.".format(wins=player_statistics["competitive_wins"],
                                                              games=player_statistics["competitive_games"]))
        save_statistics(player_statistics, csv_writer)
        warned_linux = retrigger(hotkey=args.hotkey, linux_warning=warned_linux)
