from selenium import webdriver
import urllib.request
import bs4 as bs
from datetime import datetime, timedelta
import time
import pandas as pd
import Constants as c
time_fmt = '%M:%S'
date_fmt = '%Y%m%d'

def get_game_urls():
	driver = webdriver.Firefox()
	d = datetime.today().strftime(date_fmt)
	url = c.espn_scoreboard_url + d
	driver.get(url)
	time.sleep(3)
	page = driver.page_source
	soup = bs.BeautifulSoup(page, 'html.parser')
	live_games = soup.find_all('article',{'class':'scoreboard basketball live js-show'})
	print(live_games[0].attrs['id'])


def play_by_play(n):
	driver = webdriver.Firefox()
	url = 'https://www.espn.com/mens-college-basketball/playbyplay?gameId=401268090'
	driver.get(url)
	time.sleep(3)
	last_minute = ''
	n = 4

	while True:
		page = driver.page_source
		soup = bs.BeautifulSoup(page, "html.parser")
		block = soup.find('table', {'class': 'plays-region'})
		try:
			half = int(soup.find('span', {'class': 'status-detail'}).text.split()[-2][0])
		except IndexError:
			h = soup.find('span', {'class': 'status-detail'}).text
			if h == 'Halftime':
				half = 3
			else:
				break

		try:
			lines = block.find('tbody')
		except AttributeError:
			continue

		time_stamp = lines.find('td', {'class': 'time-stamp'}).text
		current_time = datetime.strptime(time_stamp, time_fmt)
		current_minute = int(time_stamp.split(':')[0])
		score = lines.find('td', {'class': 'combined-score'}).text

		if current_minute != last_minute:

			last_minute = current_minute
			last_time = current_time
			road_score = int(score.split()[0])
			home_score = int(score.split()[2])
			total_points = road_score + home_score

			for line in lines:
				time_txt = line.find('td', {'class': 'time-stamp'}).text
				past_minute = int(time_txt.split(':')[0])
				past_time = datetime.strptime(time_txt, time_fmt)
				time_diff = past_time - current_time
				if time_diff > timedelta(minutes=n):
					past_score = line.find('td', {'class': 'combined-score'}).text
					past_road_score = int(past_score.split()[0])
					past_home_score = int(past_score.split()[2])
					past_total = past_road_score + past_home_score
					print('current total', total_points)
					ppm_n = round((total_points - past_total) / (time_diff.seconds / 60), 2)
					print('ppm last ' + str(n) + ' minutes', ppm_n)
					break

			if half == 1 or half == 3:
				t = datetime.strptime('20:00', time_fmt)
			elif half == 2:
				t = datetime.strptime('40:00', time_fmt)

			seconds_played = (t - last_time).seconds
			ppm_game = total_points / (seconds_played / 60)
			print('ppm game', round(ppm_game, 2))
			print()

			if half == 3:
				print('halftime')
				time.sleep(720)

		time.sleep(5)


if __name__ == '__main__':

	get_game_urls()