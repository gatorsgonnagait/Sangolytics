from selenium import webdriver, common
from selenium.webdriver.firefox.options import Options
import urllib.request
import bs4 as bs
from datetime import datetime, timedelta
import time
import pandas as pd
import Constants as c
import threading
import Tools as t
import requests
from datetime import datetime as dt
from Odds import get_odds

class Live_Games_Tool:

	def __init__(self, version, n):
		self.version = version
		self.n = n
		self.time_fmt = '%M:%S'
		self.date_fmt = '%Y%m%d'
		self.options = Options()
		self.options.headless = True
		self.odds_df = None
		if version == 'nba':
			self.odds_version = 'basketball_nba'
		elif version == 'cbb':
			self.odds_version = 'basketball_ncaab'

	def update_odds(self):
		while True:
			self.odds_df = get_odds(version=self.odds_version)
			time.sleep(60)

	def get_game_urls(self):
		d = ''
		if self.version == 'nba':
			scoreboard_url = c.nba_scoreboard_url
		elif self.version == 'cbb':
			scoreboard_url = c.cbb_scoreboard_url
			d = datetime.today().strftime(self.date_fmt)
		else:
			return

		driver = webdriver.Firefox(options=self.options)

		url = scoreboard_url + d
		driver.get(url)
		time.sleep(3)
		page = driver.page_source
		soup = bs.BeautifulSoup(page, 'html.parser')
		live_games = soup.find_all('article',{'class':'scoreboard basketball live js-show'})
		return [str(lg.attrs['id']) for lg in live_games]

	def open_web_driver(self, game_id):
		driver = webdriver.Firefox(options=self.options)
		if self.version == 'nba':
			play_by_play = c.nba_play_by_play
		elif self.version == 'cbb':
			play_by_play = c.cbb_play_by_play
		else:
			return

		url = play_by_play + game_id

		while True:
			try:
				driver.get(url)
			except common.exceptions.TimeoutException:
				continue
			break

		time.sleep(4)
		return driver

	def play_by_play(self, game_id):
		driver = self.open_web_driver(game_id=game_id)
		last_minute = ''
		already_half = False

		while True:
			try:
				page = driver.page_source
			except common.exceptions.WebDriverException:
				continue

			soup = bs.BeautifulSoup(page, "html.parser")

			try:
				block = soup.find('table', {'class': 'plays-region'})
			except AttributeError:
				continue

			try:
				if self.version == 'cbb':
					half = int(soup.find('span', {'class': 'status-detail'}).text.split()[-2][0])
				elif self.version == 'nba':
					half = int(soup.find('span', {'class': 'status-detail'}).text.split()[-1][0])
			except (IndexError, ValueError) as e:

				h = soup.find('span', {'class': 'status-detail'}).text
				if h == 'Halftime' or h == '0.0':
					half = 0
					if already_half:
						time.sleep(60)
						continue
				else:
					print('End of Game')
					driver.close()
					return
			try:
				lines = block.find('tbody')
			except AttributeError:
				continue

			time_stamp = lines.find('td', {'class': 'time-stamp'}).text

			if len(time_stamp) == 4:
				current_time = datetime.strptime('00:'+time_stamp.split(':')[0], self.time_fmt)
			else:
				current_time = datetime.strptime(time_stamp, self.time_fmt)

			current_minute = int(time_stamp.split(':')[0])
			score = lines.find('td', {'class': 'combined-score'}).text

			if current_minute != last_minute:
				while True:
					try:
						team_a = soup.find('div', {'class':'team away'})
						away = team_a.find('span', {'class': 'long-name'}).text + ' ' + team_a.find('span', {'class': 'short-name'}).text
						team_h = soup.find('div', {'class':'team home'})
						home = team_h.find('span', {'class': 'long-name'}).text + ' ' + team_h.find('span', {'class': 'short-name'}).text
						print(away, 'vs', home, time_stamp, half, 'quarter')
						live_game = self.odds_df[(self.odds_df['home_team'].str.lower() == home.lower()) & (self.odds_df['away_team'].str.lower() == away.lower())]
						if live_game.empty:
							print('no live odds')
							print()
							driver.close()
							return

						break
					except IndexError:
						time.sleep(.2)
						continue

				last_minute = current_minute
				last_time = current_time
				road_score = int(score.split()[0])
				home_score = int(score.split()[2])
				total_points = road_score + home_score
				if already_half:
					already_half = False
					past_time = datetime.strptime('20:00', self.time_fmt)
					line = lines[0]
					time_diff = past_time - current_time
				else:
					for li in lines:
						time_txt = li.find('td', {'class': 'time-stamp'}).text
						past_time = datetime.strptime(time_txt, self.time_fmt)
						line = li
						time_diff = past_time - current_time
						if time_diff > timedelta(minutes=self.n):
							break


				past_score = line.find('td', {'class': 'combined-score'}).text
				past_road_score = int(past_score.split()[0])
				past_home_score = int(past_score.split()[2])
				past_total = past_road_score + past_home_score
				print('current total', total_points, 'live total',live_game['total'].values[0])
				ppm_n = round((total_points - past_total) / (time_diff.seconds / 60), 2)
				print('ppm last ' + str(self.n) + ' minutes', ppm_n)

				if self.version == 'cbb':
					if half == 1 or half == 0:
						q = '20:00'
					elif half == 2:
						q = '40:00'
				elif self.version == 'nba':
					if half == 1:
						q = '12:00'
					elif half == 2 or half == 0:
						q = '24:00'
					if half == 3:
						q = '36:00'
					elif half == 4:
						q = '48:00'

				t = datetime.strptime(q, self.time_fmt)
				seconds_played = (t - last_time).seconds
				ppm_game = total_points / (seconds_played / 60)
				print('ppm game', round(ppm_game, 2))

				if half == 0:
					print('halftime')
					already_half = True
				print()

			time.sleep(3)



def driver(version, n):
	lg = Live_Games_Tool(version=version, n=n)
	id_list = lg.get_game_urls()
	t1 = threading.Thread(target=lg.update_odds)
	t1.start()

	if not id_list: return

	for id in id_list:
		thread = threading.Thread(target=lg.play_by_play, args=[id])
		thread.start()
		time.sleep(2)



if __name__ == '__main__':
	driver(version='cbb',n=5)