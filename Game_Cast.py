url = 'https://www.espn.com/nba/game?gameId=401265848'
from selenium import webdriver, common
import time
import bs4 as bs
from selenium.webdriver.firefox.options import Options
import pandas as pd
import Constants as c
import re


def open_web_driver(game_id):
    options = Options()
    options.headless = False
    driver = webdriver.Firefox(options=options)
    url = 'https://www.espn.com/nba/playbyplay?gameId=' + game_id
    while True:
        try:
            driver.get(url)
        except common.exceptions.TimeoutException:
            continue
        break

    time.sleep(1)
    return driver


def player_stats(players):
    otf = pd.DataFrame(columns=c.player_columns)
    otf.index.name = 'player'
    for player in players:
        p_stats = [p.text.strip() for p in player.find_all('td')]
        p_stats = [re.sub(r"[\n\t]", " ", p) for p in p_stats]
        line = p_stats[0].split()
        pos = line[-1]
        name = ' '.join(line[:-1])
        fg, tri, reb, ast, pf, pts = p_stats[1],p_stats[2],p_stats[3],p_stats[4],p_stats[5],p_stats[6]
        otf.at[name, 'player'] = name
        otf.at[name, 'Pos'] = pos
        otf.at[name, 'FG'] = fg
        otf.at[name, '3PT'] = tri
        otf.at[name, 'Reb'] = reb
        otf.at[name, 'Ast'] = ast
        otf.at[name, 'PF'] = pf
        otf.at[name, 'Pts'] = pts
    return otf


def current_lineups(driver):
    driver.switch_to.window(driver.window_handles[1])
    page = driver.page_source
    soup = bs.BeautifulSoup(page, 'html.parser')
    player_table = soup.find('div', {'class':'sub-module tabbedTable on_the_court basketball'})
    tables = player_table.find_all('table',{'class':'content-tab'})
    away, home = tables[0], tables[1]
    away_players = away.find_all('tr')[2:]
    home_players = home.find_all('tr')[2:]
    away_df = player_stats(players=away_players)
    home_df = player_stats(players=home_players)
    return away_df.append(home_df)
