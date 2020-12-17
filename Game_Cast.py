url = 'https://www.espn.com/nba/game?gameId=401265848'
from selenium import webdriver, common
import time
import bs4 as bs
from selenium.webdriver.firefox.options import Options
import pandas as pd
import urllib.request
import Constants as c

def open_web_driver(game_id):
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)

    url = 'https://www.espn.com/nba/game?gameId=' + game_id

    while True:
        try:
            driver.get(url)
        except common.exceptions.TimeoutException:
            continue
        break

    time.sleep(1)
    return driver

def player_stats(players):
    otf = pd.DataFrame(columns=['POS', 'FG', '3PT', 'REB', 'AST', 'PF', 'PTS'])
    otf.index.name = 'NAME'
    for player in players:
        p_stats = [p.text.strip() for p in player.find_all('td')]
        f, l, pos = p_stats[0].split()
        name = f + ' ' + l
        fg, tri, reb, ast, pf, pts = p_stats[1],p_stats[2],p_stats[3],p_stats[4],p_stats[5],p_stats[6]
        otf.at[name, 'POS'] = pos
        otf.at[name, 'FG'] = fg
        otf.at[name, '3PT'] = tri
        otf.at[name, 'REB'] = reb
        otf.at[name, 'AST'] = ast
        otf.at[name, 'PF'] = pf
        otf.at[name, 'PTS'] = pts
    return otf

def current_lineups(id, driver):
    driver.find_element_by_tag_name('body').send_keys(common.Keys.COMMAND + 't')
    while True:
        try:
            driver.get(c.nba_gamecast_url+id)
        except common.exceptions.TimeoutException:
            continue
        break
    time.sleep(.2)
    page = driver.page_source
    soup = bs.BeautifulSoup(page, 'html.parser')
    player_table = soup.find('div', {'class':'sub-module tabbedTable on_the_court basketball'})
    tables = player_table.find_all('table',{'class':'content-tab'})
    away, home = tables[0], tables[1]
    away_players = away.find_all('tr')[2:]
    home_players = home.find_all('tr')[2:]

    away_df = player_stats(players=away_players)
    home_df = player_stats(players=home_players)
    return away_df, home_df


if __name__ == '__main__':

    current_lineups(id='401265854')