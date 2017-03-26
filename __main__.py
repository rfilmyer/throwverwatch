import argparse
import csv
import logging
import os
from contextlib import contextmanager
from datetime import datetime

import keyboard
from bs4 import BeautifulSoup

import scrape

logger = logging.getLogger("throwverwatch")

parser = argparse.ArgumentParser(description="Track Overwatch Stats")
parser.add_argument("--from", dest="source", default=None,
                    help="Scrape a downloaded copy of the webpage, then quit. "
                         "Ignores battletag, region, platform arguments if set.")
parser.add_argument("--date", dest="date", default='',
                    help="If using --from, use this date/time instead of today's.")
parser.add_argument("--battletag", nargs="?", default="Calvin#1337",
                    help="Your Battle.net username in the format 'Calvin#1337'")
parser.add_argument("output_file", nargs="?", default=None, help="The CSV file in which to save stats.")
parser.add_argument("--region", dest="region", default="us",
                    help="Overwatch Region (us, kr, eu)")
parser.add_argument("--platform", dest="platform", default="pc",
                    help="Platform (pc, ps4, xbone)")
parser.add_argument("--hotkey", dest="hotkey", default="home", help="Specify a hotkey/key combo (ex: 'home', 'ctrl+f')")
args = parser.parse_args()


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
            logger.warning("You must be root in order to register hotkeys on linux. "
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

needs_header = False

@contextmanager
def get_writer(filename: str):
    """
    Yields a CSV writer for a file. If the file doesn't exist yet, it initializes it with a header row.
    :param filename:
    :return:
    """
    global needs_header

    if os.path.exists(filename):
        needs_header = False
        csvfile = open(filename, 'a')
        yield csv.writer(csvfile)
        csvfile.close()
    else:
        needs_header = True
        csvfile = open(filename, 'w')
        writer = csv.writer(csvfile)
        yield writer
        csvfile.close()

def write_header(stats: scrape.CareerStatList, writer: csv.writer):
    row = ["date"] + [stat["key"] for stat in stats]
    writer.writerow(row)

def save_statistics(stats: scrape.CareerStatList, writer: csv.writer, date: str = ''):
        row = [date if date else datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + [stat["value"] for stat in stats]
        writer.writerow(row)

warned_linux = False
csv_filename = check_filename(args.output_file)

if not args.source:
    print("Collecting stats for battletag {bt} in region {reg} and platform {plat}".format(bt=args.battletag,
                                                                                       reg=args.region,
                                                                                       plat=args.platform))
with get_writer(csv_filename) as csv_writer:
    if args.source:
        with open(args.source, 'r') as html_file:
            page = BeautifulSoup(html_file.read(), "html.parser")
            player_statistics = scrape.parse_stats_page(page)
            if needs_header:
                write_header(player_statistics, csv_writer)
            save_statistics(player_statistics, csv_writer, date=args.date)
    else:
        while True:
            player_statistics = scrape.get_statistics(args.battletag, device=args.platform, region=args.region)
            print("Your SR is {0}.".format(player_statistics["skill_rating"]))
            print("{wins} qp wins.".format(wins=player_statistics["quick_play_wins"]))
            print("{wins} comp wins out of {games} games.".format(wins=player_statistics["competitive_wins"],
                                                                  games=player_statistics["competitive_games"]))
            save_statistics(player_statistics, csv_writer)
            warned_linux = retrigger(hotkey=args.hotkey, linux_warning=warned_linux)
