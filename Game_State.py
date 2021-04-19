from selenium import webdriver, common
from selenium.webdriver.firefox.options import Options
import bs4 as bs
from datetime import datetime, timedelta
import time
import pandas as pd
import Constants as c
import threading
from Odds import get_odds
import Game_Cast as gc
import queue
import re
import Tools as tools
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from multiprocessing import Process
from matplotlib.ticker import MaxNLocator


class MGA_Version:

	def __init__(self, version):
		self.version = version
		self.time_fmt = '%M:%S'
		self.date_fmt = '%Y%m%d'
		self.options = Options()
		self.options.headless = True
		self.totals_df = None
		self.spreads_df = None
		self.ot = timedelta(minutes=5)
		self.web_driver_urls = None
		self.web_driver_dict = {}
		self.score_by_quarter_on = {}
		self.use_live_total = False
		self.use_live_spread = False
		self.id_list = []
		self.players_on = {}
		self.player_queue_dict = {}
		self.score_by_quarter_on = {}
		self.n = 3



		if self.version == 'cbb':
			self.max = 1
		else:
			self.max = 1

		if self.version == 'nba':
			self.odds_version = 'basketball_nba'
			self.period_minutes = timedelta(minutes=12)
			self.regulation = timedelta(minutes=48)
			self.num_periods = 4
		elif self.version == 'cbb':
			self.odds_version = 'basketball_ncaab'
			self.period_minutes = timedelta(minutes=20)
			self.regulation = timedelta(minutes=40)
			self.num_periods = 2


	def update_odds(self):
		self.updating_odds = True
		while self.id_list:
			self.totals_df = get_odds(sport=self.odds_version, market='totals')
			self.spreads_df = get_odds(sport=self.odds_version, market='spreads')
			time.sleep(60)
		self.totals_df = None
		self.spreads_df = None
		self.updating_odds = False


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

		url = scoreboard_url# + d
		while True:
			try:
				self.web_driver_urls.get(url)
			except common.exceptions.TimeoutException:
				continue
			break

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
		limit = 10
		ct = 0
		periods = soup.find_all('div', {'id': re.compile(r'^gp-quarter-')})
		# click to open each element here
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
				pbp_df.at[time_index, 'play'] = line.find('td', {'class': 'game-details'}).text
				ct += 1
				if not initial and ct >= limit: break


			if not initial and ct >= limit: break


		pbp_df['total'] = pbp_df['home'] + pbp_df['away']

		for i in pbp_df.index:
			if pbp_df.at[i, 'period'] <= self.num_periods:
				pbp_df.at[i, 'adj_time'] = (datetime.strptime("00:00", "%H:%M") + self.period_minutes * pbp_df.at[i, 'period']) - pbp_df.at[i, 'time']
			else:
				ot_number = pbp_df.at[i, 'period'] - self.num_periods
				pbp_df.at[i, 'adj_time'] = self.regulation + (datetime.strptime("00:00", "%H:%M") + self.ot * ot_number) - pbp_df.at[i, 'time']

		return pbp_df

	def score_by_quarter(self, df, away, home):
		for i in range(len(df) - 1):
			m = ''
			if 'makes' in df['play'].iloc[i]:
				m = 'makes'
			elif 'made' in df['play'].iloc[i]:
				m = 'made'
			if m:
				player = df['play'].iloc[i].split(m)[0].strip()
				df['player'].iloc[i] = player
				# look back at last 5 and find least difference to account for bad sorted scores
				last_highest_score_away = df['away'].iloc[i+1:i+15].astype(int).max()
				last_highest_score_home = df['home'].iloc[i+1:i+15].astype(int).max()
				away_diff = int(df['away'].iloc[i]) - last_highest_score_away
				home_diff = int(df['home'].iloc[i]) - last_highest_score_home
				points = max(away_diff, home_diff)
				# accounts for mistake if player gets 0 points in the play
				if points == 0:
					last_highest_score_away = df['away'].iloc[i-15:i-1].astype(int).min()
					last_highest_score_home = df['home'].iloc[i-5:i-1].astype(int).min()
					away_diff = last_highest_score_away - int(df['away'].iloc[i])
					home_diff = last_highest_score_home - int(df['home'].iloc[i])
					points = min(away_diff, home_diff)

				if away_diff > 0:
					df['team'].iloc[i] = away
				else:
					df['team'].iloc[i] = home

				if 'free' in df['play'].iloc[i]:
					points = 1
				df['points'].iloc[i] = points

		score_by_q = df[df['player'].notnull()]
		current_period = df['period'].iloc[0]
		if self.version == 'nba':
			if current_period < 4:
				current_period = 4
		else:
			if current_period < 2:
				current_period = 2

		one_hot = pd.get_dummies(score_by_q['period'])
		one_hot = one_hot.T.reindex(list(range(1, current_period + 1))).T.fillna(0)
		one_hot = one_hot[list(range(1, current_period + 1))].multiply(score_by_q['points'], axis='index')
		one_hot = one_hot.rename(index=str, columns=c.period_dict)

		score_by_q = score_by_q[['player', 'points', 'team']]
		score_by_q = pd.concat([score_by_q, one_hot], axis=1)
		grouped_score = score_by_q.groupby(['player', 'team'], as_index=False).sum()

		order = pd.CategoricalDtype([away, home], ordered=True)
		grouped_score['team'] = grouped_score['team'].astype(order)
		grouped_score.sort_values('team', inplace=True)
		grouped_score['site'] = grouped_score['team'].apply(lambda x: 1 if x == home else (0 if x == away else x))
		grouped_score.reset_index(inplace=True)

		grouped_score.drop(grouped_score.columns[0], axis=1, inplace=True)
		grouped_score = grouped_score.astype({'points': 'int', '1st': 'int', '2nd': 'int', '3rd': 'int', '4th': 'int'})
		return grouped_score



	def play_by_play(self, game_id):
		limit = 600
		plt.ion()
		xar = []
		yar = []
		k = 0


		driver = self.open_web_driver(game_id=game_id)
		game = ''
		past_total = None
		past_home, past_away = None, None
		live_total = ''
		live_spread = ''
		away, home = '', ''
		time_diff = None
		df = pd.DataFrame(columns=c.live_columns)
		pbp_df = pd.DataFrame(columns=c.play_by_play_columns)
		last_player_df = pd.DataFrame(c.player_columns)
		pbp_df.index.name = 'time_stamp'
		initial = True
		self.score_by_quarter_on[game_id] = False
		self.players_on[game_id] = False
		self.player_queue_dict[game_id] = queue.Queue()

		while True:
			try:
				page = driver.page_source
				soup = bs.BeautifulSoup(page, "html.parser")
				time.sleep(.2)
				break
			except common.exceptions.WebDriverException:
				print('error', game_id)
				continue

		elements = driver.find_elements_by_class_name('accordion-header')
		for e in elements:
			try:
				period_accordion = e.find_element_by_class_name('collapsed')
				if period_accordion.get_attribute('aria-expanded') == 'false':
					period_accordion.click()
			except common.exceptions.NoSuchElementException:
				pass

		while True:
			try:
				team_a = soup.find('div', {'class': 'team away'})
				team_a_city = team_a.find('span', {'class': 'long-name'}).text
				team_a_mascot = team_a.find('span', {'class': 'short-name'}).text
				away = ' '.join([team_a_city, team_a_mascot])

				team_h = soup.find('div', {'class': 'team home'})
				team_h_city = team_h.find('span', {'class': 'long-name'}).text
				team_h_mascot = team_h.find('span', {'class': 'short-name'}).text
				home = ' '.join([team_h_city, team_h_mascot])

				game = ' '.join([away, 'vs', home])
				print(game)
				break

			except IndexError:
				time.sleep(.2)
				continue

		while True:#self.gui.is_alive():

			try:
				page = driver.page_source
			except common.exceptions.WebDriverException:
				continue

			soup = bs.BeautifulSoup(page, "html.parser")
			try:
				half = soup.find('span', {'class': 'status-detail'}).text
			except AttributeError:
				continue
			if half.startswith('Final'):
				print('End of', game)
				time.sleep(60)

				self.id_list.remove(game_id)
				driver.quit()
				break

			if initial:
				pbp_df = self.get_play_lines(soup, initial=True)
			else:
				new_pbp = self.get_play_lines(soup, initial=False)
				if not new_pbp.empty and new_pbp.first_valid_index() not in pbp_df.index:

					pbp_df = new_pbp.iloc[0].to_frame().T.append(pbp_df)
					pbp_df.index.name = 'time_stamp'
					pbp_df = tools.handle_duplicates(df=pbp_df, index='time_stamp')

				else:
					continue
			if pbp_df.empty: continue


			if self.use_live_total:
				try:
					live_total_df = self.totals_df[(self.totals_df['home_team'].str.lower() == home.lower()) & (self.totals_df['away_team'].str.lower() == away.lower())]
					live_total = live_total_df['total'].values[0]
				except (TypeError, IndexError) as e:
					live_total = ''
			if self.use_live_spread:
				try:
					live_spread_df = self.spreads_df[(self.spreads_df['home_team'].str.lower() == home.lower()) & (self.spreads_df['away_team'].str.lower() == away.lower())]
					live_spread = float(live_spread_df['spread'].values[0]) * -1
					if live_spread > 0:
						live_spread = ''.join(['+',str(live_spread)])
				except (TypeError, IndexError) as e:
					live_spread = ''


			current_time = pbp_df['adj_time'].iloc[0]
			current_home = pbp_df['home'].iloc[0]
			current_away = pbp_df['away'].iloc[0]

			for i in pbp_df[1:].index:
				past_time = pbp_df.at[i, 'adj_time']
				past_total = pbp_df.at[i, 'total']
				past_home = pbp_df.at[i, 'home']
				past_away = pbp_df.at[i, 'away']
				time_diff = current_time - past_time
				if time_diff > timedelta(minutes=self.n):
					break

			total_points = pbp_df['total'].iloc[0]
			home_margin = (current_home - past_home) - (current_away - past_away)
			pbp_df['adj_time'] = pd.to_timedelta(pbp_df['adj_time'])

			# yar = (pbp_df['home'] -  pbp_df['away']).tolist()
			# xar = pbp_df['adj_time'].dt.total_seconds().tolist()
			#
			# x = int(current_time.seconds)
			# print(x, home_margin)
			# xar.append(x)
			# yar.append(home_margin)
			#
			# if initial:
			# 	figure, ax = plt.subplots(figsize=(8, 6))
			# 	line1, = ax.plot(xar, yar)
			# 	ax.yaxis.set_major_locator(MaxNLocator(integer=True))
			# 	last_min = min(yar) - 4
			# 	last_max = max(yar) + 4
			# 	plt.axis([xar[0], xar[-1] + limit, last_min, last_max])
			#
			# line1.set_xdata(xar)
			# line1.set_ydata(yar)
			# figure.canvas.flush_events()
			# figure.canvas.draw()
			# ax.clear()
			# ax.plot(xar, yar)


			k += 1

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
			df.at[game, 'Live Total'] = live_total
			df.at[game, 'Away'] = pbp_df['away'].values[0]
			df.at[game, 'Home'] = pbp_df['home'].values[0]
			df.at[game, 'PPM Last N'] = ppm_n
			df.at[game, 'PPM Game'] = ppm_game
			df.at[game, 'Live Spread'] = live_spread
			df.at[game, 'Margin Last N'] = home_margin

			if not df.empty:
				# do something here

				print(df)
				quit()
				pass

			if self.version == 'nba':
				if self.players_on[game_id]:
					player_df = gc.current_lineups(driver)

					player_df['team'].iloc[0:5] = away
					player_df['team'].iloc[5:10] = home


			if self.score_by_quarter_on[game_id]:
				score_by_q = self.score_by_quarter(pbp_df, away, home)
				# pass to website here
			initial = False
			time.sleep(2)



def launch_threads(lg, id_list, max=None):
	ids = lg.get_game_urls()
	print(ids)
	for id in ids[:max]:
		if id not in id_list:
			id_list.append(id)
			thread = threading.Thread(target=lg.play_by_play, args=[id])
			thread.daemon = True
			try:
				thread.start()
			except (KeyboardInterrupt, SystemExit):
				lg.web_driver_dict[id].quit()
				thread.join()





def driver():

	lg = MGA_Version(version='cbb')

	launch_threads(lg, lg.id_list, lg.max)

	if lg.use_live_total or lg.use_live_spread:
		lg.update_odds()

	start = time.time()
	try:
		while True:

			if time.time() - start > 180:
				start = time.time()
				launch_threads(lg, lg.id_list, lg.max)
				if lg.id_list and (lg.use_live_total or lg.use_live_spread):
					lg.update_odds()

	except KeyboardInterrupt:
		pass


	for id in lg.id_list:
		try:
			lg.web_driver_dict[id].quit()
		except KeyError:
			pass


if __name__ == '__main__':
	driver()

# return the game state without all the gui stuff