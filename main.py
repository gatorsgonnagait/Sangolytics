from selenium import webdriver, common
from selenium.webdriver.firefox.options import Options
import urllib.request
import bs4 as bs
from datetime import datetime, timedelta
import time
import pandas as pd
import Constants as c
import threading


class Live_Games_Tool:

	def __init__(self, type, n):
		self.type = type
		self.n = n
		self.time_fmt = '%M:%S'
		self.date_fmt = '%Y%m%d'
		self.options = Options()
		self.options.headless = True

	def get_game_urls(self):
		d = ''
		if self.type == 'nba':
			scoreboard_url = c.nba_scoreboard_url
		elif self.type == 'cbb':
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
		return [lg.attrs['id'] for lg in live_games]

	def open_web_driver(self, game_id):
		driver = webdriver.Firefox()
		if self.type == 'nba':
			play_by_play = c.nba_play_by_play
		elif self.type == 'cbb':
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
				half = int(soup.find('span', {'class': 'status-detail'}).text.split()[-2][0])
			except IndexError:
				h = soup.find('span', {'class': 'status-detail'}).text
				if h == 'Halftime':
					half = 3
					if already_half:
						time.sleep(60)
						continue
				else:
					break
			try:
				lines = block.find('tbody')
			except AttributeError:
				continue

			time_stamp = lines.find('td', {'class': 'time-stamp'}).text
			current_time = datetime.strptime(time_stamp, self.time_fmt)
			current_minute = int(time_stamp.split(':')[0])
			score = lines.find('td', {'class': 'combined-score'}).text

			if current_minute != last_minute:
				try:
					team_a = soup.find('div', {'class':'team away'})
					away = team_a.find('span', {'class': 'long-name'}).text + ' ' + team_a.find('span', {'class': 'short-name'}).text
					team_h = soup.find('div', {'class':'team home'})
					home = team_h.find('span', {'class': 'long-name'}).text + ' ' + team_h.find('span', {'class': 'short-name'}).text
					print(away, 'vs', home)
				except IndexError:
					pass

				last_minute = current_minute
				last_time = current_time
				road_score = int(score.split()[0])
				home_score = int(score.split()[2])
				total_points = road_score + home_score
				if already_half:
					already_half = False
					past_time = datetime.strptime('20:00', self.time_fmt)
					line = lines[0]
				else:
					for li in lines:
						time_txt = li.find('td', {'class': 'time-stamp'}).text
						past_time = datetime.strptime(time_txt, self.time_fmt)
						line = li
						time_diff = past_time - current_time
						if time_diff > timedelta(minutes=self.n):
							break

				time_diff = past_time - current_time
				past_score = line.find('td', {'class': 'combined-score'}).text
				past_road_score = int(past_score.split()[0])
				past_home_score = int(past_score.split()[2])
				past_total = past_road_score + past_home_score
				print('current total', total_points)
				ppm_n = round((total_points - past_total) / (time_diff.seconds / 60), 2)
				print('ppm last ' + str(self.n) + ' minutes', ppm_n)


				if half == 1 or half == 3:
					t = datetime.strptime('20:00', self.time_fmt)
				elif half == 2:
					t = datetime.strptime('40:00', self.time_fmt)

				seconds_played = (t - last_time).seconds
				ppm_game = total_points / (seconds_played / 60)
				print('ppm game', round(ppm_game, 2))

				if half == 3:
					print('halftime')
					already_half = True
				print()

			time.sleep(5)


def driver(type, n):
	lg = Live_Games_Tool(type=type, n=n)
	id_list = lg.get_game_urls()
	print(id_list)
	if not id_list: return

	for id in id_list:

		thread = threading.Thread(target=lg.play_by_play, args=(id))
		thread.start()
		time.sleep(2)

	#play_by_play(n=5, game_ids=id_list)



if __name__ == '__main__':
	driver(type='cbb',n=5)