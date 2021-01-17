from selenium import webdriver, common
from selenium.webdriver.firefox.options import Options
import bs4 as bs
from datetime import datetime, timedelta
import time
import pandas as pd
import Constants as c
import threading
from Odds import get_odds
import GUI as g
import Game_Cast as gc
import queue
import re


class Live_Games_Tool:

	def __init__(self, version):
		self.version = version
		self.time_fmt = '%M:%S'
		self.date_fmt = '%Y%m%d'
		self.options = Options()
		self.options.headless = True
		self.odds_df = None
		self.gui = g.GUI(version=version)
		self.ot = timedelta(minutes=5)
		self.web_driver_urls = None
		self.web_driver_dict = {}
		if version == 'cbb':
			self.max = 25
		else:
			self.max = 15

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

		self.web_driver_urls = webdriver.Firefox(options=self.options)

		url = scoreboard_url + d
		self.web_driver_urls.get(url)
		time.sleep(.5)
		page = self.web_driver_urls.page_source
		soup = bs.BeautifulSoup(page, 'html.parser')
		live_games = soup.find_all('article',{'class':'scoreboard basketball live js-show'})
		self.web_driver_urls.quit()
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
					time.sleep(.25)
					driver.get(c.nba_gamecast_url + game_id)
					driver.switch_to.window(driver.window_handles[0])

			except common.exceptions.TimeoutException:
				continue
			break

		self.web_driver_dict[game_id] = driver
		time.sleep(.5)
		return driver


	def get_play_lines(self, soup, initial):

		pbp_df = pd.DataFrame(columns=c.play_by_play_columns)
		pbp_df.index.name = 'time_stamp'

		periods = soup.find_all('div', {'id': re.compile(r'^gp-quarter-')})#[0]

		for p in periods:

			period = int(p.attrs['id'][-1])

			for line in p.find_all('tr')[1:]:
				time_txt = line.find('td', {'class': 'time-stamp'}).text
				if '.' in time_txt:
					past_time = datetime.strptime('00:' + time_txt.split('.')[0], self.time_fmt)
				else:
					past_time = datetime.strptime(time_txt, self.time_fmt)

				past_score = line.find('td', {'class': 'combined-score'}).text
				past_road_score = past_score.split()[0]
				past_home_score = past_score.split()[2]
				time_index = ' '.join([str(period), time_txt, past_road_score, past_home_score])
				pbp_df.at[time_index, 'time'] = past_time
				pbp_df.at[time_index, 'period'] = period

				pbp_df.at[time_index, 'adj_time'] = past_time
				pbp_df.at[time_index, 'away'] = int(past_road_score)
				pbp_df.at[time_index, 'home'] = int(past_home_score)
				if not initial: break
			if not initial: break

		pbp_df['total'] = pbp_df['home'] + pbp_df['away']

		for i in pbp_df.index:

			if pbp_df.at[i, 'period'] <= self.num_periods:
				pbp_df.at[i, 'adj_time'] = (datetime.strptime("00:00", "%H:%M") + self.period_minutes * pbp_df.at[i, 'period']) - pbp_df.at[i, 'time']
			else:
				ot_number = pbp_df.at[i, 'period'] - self.num_periods
				pbp_df.at[i, 'adj_time'] = self.regulation + (datetime.strptime("00:00", "%H:%M") + self.ot * ot_number) - pbp_df.at[i, 'time']


		return pbp_df


	def play_by_play(self, game_id):
		driver = self.open_web_driver(game_id=game_id)
		game = ''
		past_total = None
		time_diff = None
		df = pd.DataFrame(columns=c.live_columns)#, index=['index'])
		pbp_df = pd.DataFrame(columns=c.play_by_play_columns)
		pbp_df.index.name = 'time_stamp'
		initial = True
		self.gui.force_continue[game_id] = False
		if self.version == 'nba':
			self.gui.players_on[game_id] = False
			self.gui.player_queue_dict[game_id] = queue.Queue()

		while self.gui.is_alive():
			try:
				page = driver.page_source
				soup = bs.BeautifulSoup(page, "html.parser")
				time.sleep(.2)
				break
			except common.exceptions.WebDriverException:
				continue


		while self.gui.is_alive():
			try:
				team_a = soup.find('div', {'class': 'team away'})
				away = team_a.find('span', {'class': 'long-name'}).text + ' ' + team_a.find('span', {'class': 'short-name'}).text
				team_h = soup.find('div', {'class': 'team home'})
				home = team_h.find('span', {'class': 'long-name'}).text + ' ' + team_h.find('span', {'class': 'short-name'}).text
				game = ' '.join([away, 'vs', home])
				self.gui.id_to_names[game_id] = game
				self.gui.names_to_ids[game] = game_id
				self.gui.combo_box['values'] = list(self.gui.id_to_names.values())
				break
			except IndexError:
				time.sleep(.2)
				continue


		# if self.gui.is_alive() and self.version == 'nba':
		# 	player_box = self.gui.create_player_box(columns=c.player_columns, game=game)
		# 	player_queue = queue.Queue()
		# 	t2 = threading.Thread(target=self.gui.process_players, args=[player_queue, player_box])
		# 	try:
		# 		t2.start()
		# 	except (KeyboardInterrupt, SystemExit):
		# 		t2.join()
		# 		sys.exit()



		while self.gui.is_alive():

			try:
				page = driver.page_source
			except common.exceptions.WebDriverException:
				continue

			soup = bs.BeautifulSoup(page, "html.parser")
			try:
				half = soup.find('span', {'class': 'status-detail'}).text
			except AttributeError:
				continue
			if half == 'Final':\
					#or (pbp_df['period'].iloc[0] == '4th' and pbp_df['time'].iloc[0] == '4th' and pbp_df['away'].iloc[0] != pbp_df['home'].iloc[0]):
				print('End of Game')
				time.sleep(60)
				self.gui.list_box.delete(game)
				self.gui.id_to_names.pop(game, None)

				driver.quit()
				break

			if initial:
				pbp_df = self.get_play_lines(soup, initial=True)
				initial = False

			else:
				new_pbp = self.get_play_lines(soup, initial=False)

				if not new_pbp.empty and new_pbp.first_valid_index() not in pbp_df.index:
					pbp_df = new_pbp.iloc[0].to_frame().T.append(pbp_df)
				elif self.gui.force_continue[game_id]:
					self.gui.force_continue[game_id] = False
					pass
				else:
					continue

			time_stamp = pbp_df['time'].iloc[0]
			print(away, 'vs', home, time_stamp)

			# live_total = self.odds_df[(self.odds_df['home_team'].str.lower() == home.lower()) & (self.odds_df['away_team'].str.lower() == away.lower())]
			# if live_total.empty:
			# 	print('no live odds')
			# 	print()

			current_time = pbp_df['adj_time'].iloc[0]
			for i in pbp_df[1:].index:

				past_time = pbp_df.at[i, 'adj_time']
				past_total = pbp_df.at[i, 'total']
				time_diff = current_time - past_time
				if time_diff > timedelta(minutes=self.gui.n):
					break

			total_points = pbp_df['total'].iloc[0]

			try:
				ppm_n = round((total_points - past_total) / (time_diff.seconds / 60), 2)
			except ZeroDivisionError:
				continue

			try:
				ppm_game = round(total_points / (current_time.seconds / 60), 2)
			except ZeroDivisionError:
				continue

			df.at[game, 'Period'] = half
			df.at[game, 'Game'] = game
			df.at[game, 'Current Total'] = total_points
			#df.at[game, 'Live Total'] = live_total['total'].values[0]
			df.at[game, 'Away'] = pbp_df['away'].values[0]
			df.at[game, 'Home'] = pbp_df['home'].values[0]
			df.at[game, 'PPM Last N'] = ppm_n
			df.at[game, 'PPM Game'] = ppm_game
			if not df.empty:
				self.gui.q.put(item=df)

			if self.version == 'nba' and self.gui.players_on[game_id]:
				print()
				player_df = gc.current_lineups(driver)
				player_df[:5]['Team'] = away
				player_df[5:]['Team'] = home
				if not player_df.empty:
					self.gui.player_queue_dict[game_id].put(player_df)
			print()

			time.sleep(2)



def launch_threads(lg, id_set, max=None):
	id_list = lg.get_game_urls()

	for id in id_list[:max]:
		if id not in id_set:
			id_set.append(id)
			thread = threading.Thread(target=lg.play_by_play, args=[id])
			thread.daemon = True
			try:
				thread.start()
			except (KeyboardInterrupt, SystemExit):
				lg.web_driver_dict[id].quit()
				thread.join()

		if not lg.gui.is_alive():
			break

def driver(version):

	lg = Live_Games_Tool(version=version)
	lg.gui.create_box()

	id_set = []

	launch_threads(lg, id_set, lg.max)

	t2 = threading.Thread(target=lg.gui.process_incoming)
	t2.start()


	start = time.time()
	while True:

		if time.time() - start > 420:
			start = time.time()
			launch_threads(lg, id_set, lg.max)
		if not lg.gui.is_alive():
			break

	t2.join()
	for id in id_set:
		try:
			lg.web_driver_dict[id].quit()
		except KeyError:
			pass


if __name__ == '__main__':
	driver(version='nba')

