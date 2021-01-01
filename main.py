from selenium import webdriver, common
from selenium.webdriver.common.keys import Keys
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
import GUI as g
import Game_Cast as gc
import queue
import re

class Live_Games_Tool:

	def __init__(self, version, n):
		self.version = version
		self.n = n
		self.time_fmt = '%M:%S'
		self.date_fmt = '%Y%m%d'
		self.options = Options()
		self.options.headless = True
		self.odds_df = None
		self.gui = g.GUI(version=version)
		self.ot = timedelta(minutes=5)


		if version == 'nba':
			self.odds_version = 'basketball_nba'
			self.period_minutes = timedelta(minutes=12)
			self.regulation = timedelta(minutes=48)
			self.num_periods = 4
		elif version == 'cbb':
			self.odds_version = 'basketball_ncaab'
			self.period_minutes = timedelta(minutes=20)
			self.regulation = timedelta(minutes=40)
			self.num_periods = 2


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
				if self.version == 'nba':

					driver.execute_script("window.open()")
					driver.switch_to.window(driver.window_handles[1])
					time.sleep(.75)
					driver.get(c.nba_gamecast_url + game_id)
					driver.switch_to.window(driver.window_handles[0])

			except common.exceptions.TimeoutException:
				continue
			break


		time.sleep(1)
		return driver

	def time_difference(self, lines, current_time):
		line, time_diff = None, None
		for li in lines:
			time_txt = li.find('td', {'class': 'time-stamp'}).text
			if '.' in time_txt:
				past_time = datetime.strptime('00:' + time_txt.split('.')[0], self.time_fmt)
			else:
				past_time = datetime.strptime(time_txt, self.time_fmt)
			line = li
			time_diff = past_time - current_time
			if time_diff > timedelta(minutes=self.n):
				break

		return  line, time_diff

	def play_by_play(self, game_id):
		driver = self.open_web_driver(game_id=game_id)
		last_minute = ''
		game = ''
		live_total = ''
		last_time = None
		already_half = False
		df = pd.DataFrame(columns=c.live_columns)#, index=['index'])
		pbp_df = pd.DataFrame(columns=c.play_by_play_columns)



		while True:
			try:
				page = driver.page_source
				break
			except common.exceptions.WebDriverException:
				continue

		soup = bs.BeautifulSoup(page, "html.parser")
		time.sleep(1)
		periods = soup.find_all('div',{'id': re.compile(r'^gp-quarter-')})
		for p in periods:
			period = int(p.attrs['id'][-1])
			#print(p.find('tbody'))
			#print(p.find_all('tr'))
			for line in p.find_all('tr')[1:]:
				time_txt = line.find('td', {'class': 'time-stamp'}).text
				if '.' in time_txt:
					past_time = datetime.strptime('00:' + time_txt.split('.')[0], self.time_fmt)
				else:
					past_time = datetime.strptime(time_txt, self.time_fmt)

				time_index = ' '.join([str(period), time_txt])
				pbp_df.at[time_index, 'time'] = past_time
				pbp_df.at[time_index, 'period'] = period

				pbp_df.at[time_index, 'adj_time'] = past_time
				past_score = line.find('td', {'class': 'combined-score'}).text
				past_road_score = int(past_score.split()[0])
				past_home_score = int(past_score.split()[2])
				#past_total = past_road_score + past_home_score
				pbp_df.at[time_index, 'away'] = past_road_score
				pbp_df.at[time_index, 'home'] = past_home_score
				#pbp_df.at[past_time, 'total'] = past_total


		pbp_df['total'] = pbp_df['home'] + pbp_df['away']

		#pbp_df['adj_time'] = pbp_df.apply(lambda row: self.period * row.period - row.time if row.period <= self.regulation else self.ot * row.period - row.time, axis = 1)])
		for i in pbp_df.index:

			if pbp_df.at[i,'period'] <= self.num_periods:
				pbp_df.at[i, 'adj_time'] = (datetime.strptime("00:00", "%H:%M") +self.period_minutes * pbp_df.at[i, 'period']) - pbp_df.at[i, 'time']
			else:
				print(pbp_df.at[i,'period'])
				ot_number = pbp_df.at[i,'period'] - self.num_periods
				pbp_df[i, 'adj_time'] = self.regulation + (datetime.strptime("00:00", "%H:%M") + self.ot * ot_number) - pbp_df[i, 'time']
		pbp_df.to_csv('test.csv')
		print('wrote test')
		return


		while True:
			try:
				team_a = soup.find('div', {'class': 'team away'})
				away = team_a.find('span', {'class': 'long-name'}).text + ' ' + team_a.find('span', {'class': 'short-name'}).text
				team_h = soup.find('div', {'class': 'team home'})
				home = team_h.find('span', {'class': 'long-name'}).text + ' ' + team_h.find('span', {'class': 'short-name'}).text
				game = ' '.join([away, 'vs', home])


				break
			except IndexError:
				time.sleep(.2)
				continue

		if self.version == 'nba':
			player_box = self.gui.create_player_box(columns=c.player_columns, game=game)
			#player_df = pd.DataFrame(columns=c.player_columns)
			player_queue = queue.Queue()
			t2 = threading.Thread(target=self.gui.process_players, args=[player_queue, player_box])
			t2.start()


		while True:
			try:
				page = driver.page_source
			except common.exceptions.WebDriverException:
				continue

			soup = bs.BeautifulSoup(page, "html.parser")

			try:
				#block = soup.find('table', {'class': 'plays-region'})
				lines = soup.find('div', {'id': 'gamepackage-play-by-play'})
			except AttributeError:
				continue

			try:
				if self.version == 'cbb':
					half = soup.find('span', {'class': 'status-detail'}).text.split()[-2]
				elif self.version == 'nba':
					half = soup.find('span', {'class': 'status-detail'}).text.split()[-1]
			except (IndexError, ValueError, AttributeError) as e:

				h = soup.find('span', {'class': 'status-detail'}).text
				if h == 'Halftime':# or h == '0.0':
					half = h
					if already_half:
						time.sleep(60)
						continue
				elif 'OT' in h:
					half = h
				else:
					print('End of Game')
					self.gui.df.drop(index=game, inplace=True)
					driver.close()
					return
			# try:
			# 	lines = block.find('tbody')
			# except AttributeError:
			# 	continue
			time_stamp = lines.find('td', {'class': 'time-stamp'}).text

			if '.' in time_stamp:
				current_time = datetime.strptime('00:'+time_stamp.split('.')[0], self.time_fmt)
			else:
				current_time = datetime.strptime(time_stamp, self.time_fmt)

			#current_minute = int(time_stamp.split(':')[0])
			#score = lines.find('td', {'class': 'combined-score'}).text

			#if current_minute != last_minute:
			if current_time != last_time:

				print(away, 'vs', home, time_stamp, half, 'quarter')

				# live_total = self.odds_df[(self.odds_df['home_team'].str.lower() == home.lower()) & (self.odds_df['away_team'].str.lower() == away.lower())]
				# if live_total.empty:
				# 	print('no live odds')
				# 	print()


				last_time = current_time
				road_score = int(score.split()[0])
				#home_score = int(score.split()[2])
				total_points = road_score + home_score
				line = None
				if already_half:
					already_half = False
					past_time = datetime.strptime('20:00', self.time_fmt)
					#line = lines
					time_diff = past_time - current_time
				else:
					#line, time_diff = self.time_difference(lines, current_time)
					for li in lines.find_all('tr'):
						try:
							time_txt = li.find('td', {'class': 'time-stamp'}).text
						except AttributeError:
							continue
						if '.' in time_txt:
							past_time = datetime.strptime('00:' + time_txt.split('.')[0], self.time_fmt)
						else:
							past_time = datetime.strptime(time_txt, self.time_fmt)
						line = li
						time_diff = past_time - current_time
						if time_diff > timedelta(minutes=self.n):
							break

				past_score = line.find('td', {'class': 'combined-score'}).text
				past_road_score = int(past_score.split()[0])
				past_home_score = int(past_score.split()[2])
				past_total = past_road_score + past_home_score
				#print(total_points, past_total)
				print('current total', total_points, 'live total')#,live_game['total'].values[0])
				try:
					ppm_n = round((total_points - past_total) / (time_diff.seconds / 60), 2)
				except ZeroDivisionError:
					continue
				#print('ppm last ' + str(self.n) + ' minutes', ppm_n)


				if self.version == 'cbb':
					game_time = 20
					if half == '1st' or half == 'Halftime':
						q = '20:00'
					elif half == '2nd':
						q = '40:00'
				elif self.version == 'nba':
					game_time = 40
					if half == '1st':
						q = '12:00'
					elif half == '2nd' or half == 'Halftime':
						q = '24:00'
					if half == '3rd':
						q = '36:00'
					elif half == '4th':
						q = '48:00'
				if 'OT' in  half:
					try:
						ot = int(half[0])
					except ValueError:
						ot = 1
					ot_minutes = game_time + ot * 5
					q = str(ot_minutes)+':00'

				t = datetime.strptime(q, self.time_fmt)
				seconds_played = (t - last_time).seconds
				ppm_game = round(total_points / (seconds_played / 60), 2)
				#print('ppm game', round(ppm_game, 2))
				# self.gui.df.at[game, 'Time'] = time_stamp
				# self.gui.df.at[game, 'Period'] = half
				# self.gui.df.at[game, 'Game'] = game
				# self.gui.df.at[game, 'Current Total'] = total_points
				# self.gui.df.at[game, 'Live Total'] = live_total
				# self.gui.df.at[game, 'PPM Last N'] = ppm_n
				# self.gui.df.at[game, 'PPM Game'] = ppm_game

				df.at[game, 'Time'] = time_stamp
				df.at[game, 'Period'] = half
				df.at[game, 'Game'] = game
				df.at[game, 'Current Total'] = total_points
				#df.at[game, 'Live Total'] = live_total['total'].values[0]
				df.at[game, 'PPM Last N'] = ppm_n
				df.at[game, 'PPM Game'] = ppm_game
				if not df.empty:
					self.gui.q.put(item=df)
					#self.gui.fill_box(self.gui.df)

				if self.version == 'nba':
					player_df = gc.current_lineups(driver)
					player_df[:5]['Team'] = away
					player_df[5:]['Team'] = home
					if not player_df.empty:
						player_queue.put(player_df)

				if half == 'Halftime':
					print('halftime')
					already_half = True
				print()

			time.sleep(3)
		driver.close()


def driver(version, n):
	lg = Live_Games_Tool(version=version, n=n)
	lg.gui.create_box(columns=c.live_columns)

	# t1 = threading.Thread(target=lg.update_odds)
	# t1.start()
	#
	# id_list = lg.get_game_urls()
	#
	# if not id_list: return
	#
	# for id in id_list:
	# 	thread = threading.Thread(target=lg.play_by_play, args=[id])
	# 	thread.start()
	# 	time.sleep(2)

	# t2 = threading.Thread(target=lg.gui.process_incoming)
	# t2.start()

	initial = True
	id_set = set()
	while True:
		id_list = lg.get_game_urls()
		if not id_list: return

		for id in id_list:
			if id not in id_set:
				id_set.add(id)
				thread = threading.Thread(target=lg.play_by_play, args=[id])
				try:
					thread.start()
				except KeyboardInterrupt:
					thread.join()
				time.sleep(2)
			break

		if initial:
			t2 = threading.Thread(target=lg.gui.process_incoming)
			t2.start()
			initial = False

		time.sleep(600)


if __name__ == '__main__':
	driver(version='cbb',n=5)
	f = {}
