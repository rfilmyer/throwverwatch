from typing import List, Dict
import json
import unicodedata
import logging

import requests
import bs4

logger = logging.getLogger("throwverwatch")

HEROES = ["Genji", "McCree", "Pharah", "Reaper", "Soldier: 76", "Sombra", "Tracer", "Bastion", "Hanzo", "Junkrat",
          "Mei", "Torbjörn", "Widowmaker", "D.Va", "Orisa", "Reinhardt", "Roadhog", "Winston", "Zarya", "Ana", "Lúcio", "Mercy",
          "Symmetra", "Zenyatta"]

with open("page_layout.json") as f:
    PAGE_LAYOUT = json.load(f)

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


def get_page(url: str, session: requests.Session = None) -> bs4.BeautifulSoup:
    """
    Grabs a webpage and parses it with BeautifulSoup
    """
    session = session if session else requests
    response = session.get(url)

    return bs4.BeautifulSoup(response.text, 'html.parser')

def find_table(header: str, div: bs4.element.Tag) -> bs4.element.Tag:
    """
    Find the first table in a div with matching header text
    :param header:
    :param div:
    :return:
    """
    logger.debug(header)
    return next((table for table in div.find_all("table") if table.thead.tr.text == header), None)


def find_stat_in_table(stat:str, div: bs4.element.Tag, suffix:str = None) -> str:
    """
    Table rows are formatted like so...
    <tbody>
        <tr>
            <td>Melee Final Blow</td>
            <td>1</td>
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
    Annoying edge cases: In the English-language version of the page, stats with a value of 1 are singularized.
    Example: "Melee Final Blows: 167", but "Melee Final Blow: 1"
    Even better, they are singularized in stat averages as well.
    Example: "Objective Kills - Most In Game: 2,000", but "Objective Kill - Most In Game: 1"

    :param stat: The name of a statistic, in the singular. (Ex: "Melee Final Blow", "Medal")
    :param div: could also be a tbody in the future
    :param suffix: If the statistic has a suffix, put that suffix here, excluding the initial space
        (Ex: "Medals - Gold" -> stat="Medal", suffix="- Gold")
    :return:
    """
    for tr in div.find_all("tr"):
        if tr.td:
          row_label = tr.td.text
          row_value = tr.find_all("td")[1].text
            if suffix:
                if row_label.endswith(suffix) and row_label[:-len(suffix)].rstrip(' ').rstrip('s') == stat:
                    return row_value
            else:
                if row_label.rstrip('s') == stat:
                    return row_value


def normalize_string(string: str) -> str:
    normalized = ''.join(c for c in unicodedata.normalize('NFD', string) if unicodedata.category(c) != 'Mn')
    alnum_lower = ''.join(c for c in normalized.lower() if c.isalnum())
    return alnum_lower


HeroDict = Dict[str, str]


def get_heroes_from_selection_menu(soup: bs4.BeautifulSoup) -> List[HeroDict]:
    select_attrs = {"data-js": "career-select", "data-group-id": "stats"}
    hero_options = soup.find("select", attrs=select_attrs).find_all("option")
    heroes = []
    for option in hero_options:
        heroes.append({"name": option.text, "normalized_name": normalize_string(option.text), "id": option["value"]})
    heroes = heroes[1:] #first option is "All Heroes"
    return heroes



CareerStatDict = Dict[str, str]
CareerStatList = List[CareerStatDict]

def get_sr_and_rank(soup: bs4.BeautifulSoup) -> CareerStatList:
    """
    Finds the 2 main competitive stats on the page, Skill Rating (AKA SR) and Rank (from bronze to grandmaster).
    Top 500 players will appear to be in Grandmaster.

    :param soup: a webpage loaded through BeautifulSoup
    :return: Dict containing "skill_rating", the player's Skill Rating, and "rank", the player's rank
    """
    image_to_rank = {"7": "Grandmaster",
                     "6": "Master",
                     "5": "Diamond",
                     "4": "Platinum",
                     "3": "Gold",
                     "2": "Silver",
                     "1": "Bronze"}

    skill_rating = {"name": "Skill Rating", "key": "skill_rating", "value": soup.find(class_="competitive-rank").div.text}
    rank = {"name": "Rank", "key": "rank", "value": image_to_rank.get(soup.find(class_="competitive-rank").img["src"][-5])}
    return [skill_rating, rank]

# career stats
# hero stats




def get_career_stats(div: bs4.element.Tag) -> CareerStatList:
    """

    :param div: The innermost common <div> containing stats for a hero
    :return:
    """
    stats = []
    for section in PAGE_LAYOUT["career_stats"]:
        table = find_table(section["sectionName"], div)
        if section["sectionName"] == "Game":
            pass
        if table:
            for stat_layout in section["stats"]:
                stat = {"name": stat_layout["name"],
                        "key": stat_layout["key"],
                        "value": find_stat_in_table(stat_layout["name"],
                                                    table,
                                                    stat_layout.get("suffix"))}
                stats.append(stat)
    return stats


def parse_stats_page(soup: bs4.BeautifulSoup) -> CareerStatList:
    """
    Extracts player statistics from a web page parsed by BeautifulSoup.
    :param soup: A parsed copy of the PlayOverwatch.com stats page for a user.
    :return: dict
    """

    competitive_rank = get_sr_and_rank(soup)
    heroes = get_heroes_from_selection_menu(soup)
    logger.debug([hero["name"] for hero in heroes])

    all_game_stats = [] + competitive_rank
    for game_mode in ["competitive", "quickplay"]:
        section = soup.find(id=game_mode)
        overall_stats = get_career_stats(section.find("div", attrs={"data-category-id": "0x02E00000FFFFFFFF"}))
        all_hero_stats = [] + overall_stats
        for hero in heroes:
            logger.debug("Hero: {}".format(hero["name"]))
            hero_div = section.find("div", attrs={"data-category-id": hero["id"]})
            if hero_div:
                hero_stats = get_career_stats(hero_div)
                hero_stats_formatted = [{"name": "{stat} ({hero})".format(stat=stat["name"], hero=hero["name"]),
                                         "key": "{stat}_{hero}".format(stat=stat["key"], hero=hero["normalized_name"]),
                                         "value": stat["value"]} for stat in hero_stats]
                all_hero_stats += hero_stats_formatted
        for stat in all_hero_stats:
            game_mode_stat = {"name": "{stat} - {game_mode}".format(stat=stat["name"], game_mode=game_mode),
                              "key": "{stat}_{game_mode}".format(stat=stat["key"], game_mode=game_mode),
                              "value": stat["value"]}
            all_game_stats.append(game_mode_stat)

    return all_game_stats

def format_time_played(unparsed_time: str):
    if unparsed_time == '--':
        time = 0
    elif 'second' in unparsed_time:
        time = float(unparsed_time.split()[0]) / 60.0
    elif 'minute' in unparsed_time.split()[-1]:
        time = int(unparsed_time.split()[0])
    elif 'hour' in unparsed_time.split()[-1]:
        time = 60 * int(unparsed_time.split()[0])
    else:
        time = None
    return time

def get_statistics(battletag: str, device: str = 'pc', region: str = 'us', session: requests.Session = None) -> CareerStatList:
    return parse_stats_page(get_page(assemble_url(battletag, device=device, region=region), session=session))
