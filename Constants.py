
#cbb_scoreboard_url = 'https://www.espn.com/mens-college-basketball/scoreboard/_/group/50/date/'
cbb_scoreboard_url = 'https://www.espn.com/mens-college-basketball/scoreboard'
nba_scoreboard_url = 'https://www.espn.com/nba/scoreboard'
espn_url = 'http://www.espn.com/college-football/boxscore?gameId='
espn_matchup_url = 'http://www.espn.com/college-football/matchup?gameId='
cbb_play_by_play = 'https://www.espn.com/mens-college-basketball/playbyplay?gameId='
nba_play_by_play = 'https://www.espn.com/nba/playbyplay?gameId='
nba_gamecast_url = 'https://www.espn.com/nba/game?gameId='
api_key = 'c06e566dfb583f3a48a89143106b6241'
nba_version = 'basketball_nba'
cbb_version = 'basketball_ncaab'
region = 'us'
live_columns = ['Game','Period','Away','Home','Current Total','Live Total','PPM Last N','PPM Game','Live Spread','Margin Last N']
player_columns = ['player','team','Pos','FG','3PT','Reb','Ast','PF','Pts']
play_by_play_columns = ['time_index', 'same_time_count', 'time' ,'period', 'adj_time', 'away', 'home', 'total', 'play', 'player', 'fg_makes', 'fg_misses', '3_makes', '3_misses', 'ft_makes', 'ft_misses', 'points','team']

fg_cols = ['1Q FG-FGA','1Q 3P-3PA','1Q FT-FTA',
          '2Q FG-FGA','2Q 3P-3PA','2Q FT-FTA',
          '3Q FG-FGA','3Q 3P-3PA','3Q FT-FTA',
          '4Q FG-FGA','4Q 3P-3PA','4Q FT-FTA' ]

score_by_quarter = ['player', 'team', 'points'] + fg_cols


period_points = {1: '1Q PTS', 2: '2Q PTS', 3:'3Q PTS', 4:'4Q PTS', 5:'OT PTS', 6:'2OT PTS', 7:'3OT', 8:'4OT'}

period_fg_makes = {1: '1Q FG', 2: '2Q FG', 3:'3Q FG', 4:'4Q FG', 5:'OT', 6:'2OT', 7:'3OT', 8:'4OT'}
period_fg_misses = {1: '1Q FGM', 2: '2Q FGM', 3:'3Q FGM', 4:'4Q FGM', 5:'OT', 6:'2OT', 7:'3OT', 8:'4OT'}

period_ft_makes = {1: '1Q FT', 2: '2Q FT', 3:'3Q FT', 4:'4Q FT', 5:'OT', 6:'2OT', 7:'3OT', 8:'4OT'}
period_ft_misses = {1: '1Q FTM', 2: '2Q FTM', 3:'3Q FTM', 4:'4Q FTM', 5:'OT', 6:'2OT', 7:'3OT', 8:'4OT'}

period_3_makes = {1: '1Q 3P', 2: '2Q 3P', 3:'3Q 3P', 4:'4Q 3P', 5:'OT', 6:'2OT', 7:'3OT', 8:'4OT'}
period_3_misses = {1: '1Q 3PM', 2: '2Q 3PM', 3:'3Q 3PM', 4:'4Q 3PM', 5:'OT', 6:'2OT', 7:'3OT', 8:'4OT'}


team_dict = {
    'Orlando': 'Magic',
    'Atlanta Hawks':'Hawks',
    'Boston Celtics':'Celtics',
    'Brooklyn Nets':'Nets',
    'New Jersey Nets':'Nets',
    'Charlotte Hornets':'Hornets',
    'Charlotte Bobcats':'Hornets',
    'Chicago Bulls':'Bulls',
    'Cleveland Cavaliers':'Cavaliers',
    'Dallas Mavericks':'Mavericks',
    'Denver Nuggets':'Nuggets',
    'Detroit Pistons':'Pistons',
    'Golden State Warriors':'Warriors',
    'Houston Rockets':'Rockets',
    'Indiana Pacers':'Pacers',
    'Los Angeles Clippers':'Clippers',
    'Los Angeles Lakers':'Lakers',
    'Memphis Grizzlies':'Grizzlies',
    'Vancouver Grizzlies':'Grizzlies',
    'Miami Heat':'Heat',
    'Milwaukee Bucks':'Bucks',
    'Minnesota Timberwolves':'Timberwolves',
    'New Orleans Pelicans':'Pelicans',
    'New Orleans Hornets':'Pelicans',
    'New York Knicks':'Knicks',
    'Oklahoma City Thunder':'Thunder',
    'Seattle Supersonics':'Thunder',
    'Orlando Magic':'Magic',
    'Philadelphia 76ers':'76ers',
    'Philadelphia 76Ers':'76ers',
    'Phoenix Suns':'Suns',
    'Portland Trail Blazers':'Blazers',
    'Sacramento Kings':'Kings',
    'San Antonio Spurs':'Spurs',
    'Toronto Raptors':'Raptors',
    'Utah Jazz':'Jazz',
    'Washington Wizards':'Wizards'
}


def format_team_names(team_name):
	formatted_team = team_dict.get(team_name)
	if formatted_team:
		return formatted_team
	else:
		return team_name


