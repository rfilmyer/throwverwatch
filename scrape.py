import requests
from bs4 import BeautifulSoup


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