import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger()

USERNAME = "Calvin#1337"
REGION = 'us'


def assemble_url(battletag, device='pc', region='us'):
    username = battletag.replace('#', '-')
    return "https://playoverwatch.com/en-us/career/{device}/{region}/{username}".format(device=device, region=region, username=username)

def get_page(battletag, device='pc', region='us'):
    logger.debug("Looking up player {player} on PlayOverwatch.com".format(player=battletag))
    response = requests.get(assemble_url(battletag, device='pc', region=region))
    logger.info("Found page for player {player}".format(player=battletag))

    return BeautifulSoup(response.text, 'html.parser')

soup = get_page(USERNAME)
season_rank = soup.find(class_="competitive-rank").div.text


print("Your SR is {0}, you embarrassment to society.".format(season_rank))
