url = 'https://www.espn.com/nba/game?gameId=401265848'
from selenium import webdriver, common
import time
import bs4 as bs
from selenium.webdriver.firefox.options import Options
import pandas as pd

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

def current_lineups(id):
    driver = open_web_driver(game_id=id)
    time.sleep(3)
    page = driver.page_source
    soup = bs.BeautifulSoup(page, 'html.parser')
    player_table = soup.find('div', {'class':'sub-module tabbedTable on_the_court basketball'})

    tables = player_table.find_all('table',{'class':'content-tab'})

    away, home = tables[0], tables[1]
    away_players = away.find_all('tr')[2:]
    otf = pd.DataFrame(columns=['Name','Pos','FG','3PT','REB','AST','PF','PTS'])
    for player in away_players:

        p_stats = [p.text.strip() for p in player.find_all('td')]
        f, l, pos = p_stats[0].split()
        fg, tri, reb, ast, pf, pts = p_stats[1],p_stats[2],p_stats[3],p_stats[4],p_stats[5],p_stats[6]

        print(f, l, pos)
        print(fg, tri, reb, ast, pf, pts)
        print()


if __name__ == '__main__':

    current_lineups(id='401265849')