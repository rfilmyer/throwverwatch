import logging
import argparse
import requests
#import keyboard
from bs4 import BeautifulSoup

logger = logging.getLogger("throwverwatch")

parser = argparse.ArgumentParser(description="Track Overwatch Stats")
parser.add_argument("battletag", nargs="?", default="Calvin#1337", help="Your Battle.net username in the format 'Calvin#1337'")
parser.add_argument("--region", dest="region", default="us", help="Overwatch Region (us, kr, eu)")
parser.add_argument("--platform", dest="platform", default="pc", help="Platform (pc, ps4, xbone)")
args = parser.parse_args()

HEROES = ["Genji", "McCree", "Pharah", "Reaper", "Soldier: 76", "Sombra", "Tracer", "Bastion", "Hanzo", "Junkrat",
          "Mei", "Torbjörn", "Widowmaker", "D.Va", "Reinhardt", "Roadhog", "Winston", "Zarya", "Ana", "Lúcio", "Mercy",
          "Symmetra", "Zenyatta"]

def assemble_url(battletag, device='pc', region='us'):
    username = battletag.replace('#', '-')
    return "https://playoverwatch.com/en-us/career/{device}/{region}/{username}".format(device=device, region=region, username=username)


def get_page(battletag, device='pc', region='us', session=None):
    logger.debug("Looking up player {player} on PlayOverwatch.com".format(player=battletag))
    session = session if session else requests
    response = session.get(assemble_url(battletag, device='pc', region=region))
    logger.info("Found page for player {player}".format(player=battletag))

    return BeautifulSoup(response.text, 'html.parser')

def find_stat_in_table(stat, div):
    for tr in div.find_all("tr"):
        if tr.td:
            if tr.td.text == stat:
                return tr.find_all("td")[1].text

def parse_stats_page(soup):
    stats = {}
    stats["season_rank"] = soup.find(class_="competitive-rank").div.text
    quick_play_stats = soup.find(id="quickplay").find(attrs={"data-category-id": "0x02E00000FFFFFFFF"}).find_all("div")
    quick_play_game_game_stats = next(div for div in quick_play_stats if div.table.thead.span.text == "Game")
    #stats["quick_play_games"] = find_stat_in_table("Games Played", quick_play_game_game_stats)
    stats["quick_play_wins"] = find_stat_in_table("Games Won", quick_play_game_game_stats)

    competitive_stats = soup.find(id="competitive").find(attrs={"data-category-id": "0x02E00000FFFFFFFF"}).find_all("div")
    competitive_game_stats = next(div for div in competitive_stats if div.table.thead.span.text == "Game")
    stats["competitive_games"] = find_stat_in_table("Games Played", competitive_game_stats)
    stats["competitive_wins"] = find_stat_in_table("Games Won", competitive_game_stats)

    # This is dead code for now, I'll add this when I add the other 6 metrics
    stats["heroes"] = {}
    for hero_bar in soup.find(id="competitive").find(attrs={"data-category-id": "overwatch.guid.0x0860000000000021"}).find_all(
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

def get_statistics(battletag, device='pc', region='us', session=None):
    return parse_stats_page(get_page(battletag))

while True:
    #keyboard.wait('ctrl')
    stats = get_statistics(args.battletag, device=args.platform, region=args.region)
    print("Your SR is {0}.".format(stats["season_rank"]))
    print("{wins} qp wins.".format(wins=stats["quick_play_wins"]))
    print("{wins} comp wins out of {games} games.".format(wins=stats["competitive_wins"], games=stats["competitive_games"]))
    for hero, minutes in stats["heroes"].items():
        print("{hero}: {time} Minutes Played".format(hero=hero, time=minutes))
    print("(press return to pull stats again)")
    input()

