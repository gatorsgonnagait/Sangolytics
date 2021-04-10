
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
player_columns = ['Player','Team','Pos','FG','3PT','Reb','Ast','PF','Pts']
play_by_play_columns = ['time_index', 'same_time_count', 'time' ,'period', 'adj_time', 'away', 'home', 'total', 'play', 'player', 'fg_makes', 'fg_misses', '3_makes', '3_misses', 'ft_makes', 'ft_misses', 'points','team']
score_by_quarter = ['player', 'team', 'points', '1st', '2nd', '3rd', '4th']
score_by_quarter = ['player', 'team', 'points',
                    '1 FG', '1 FGA','1 FG', '1 3PT','1 3PTA', '1 FT','1 FTA',
                    '2 FG', '2 FGA','2 FG', '2 3PT','2 3PTA', '2 FT','2 FTA',
                    '3 FG', '3 FGA','3 FG', '3 3PT','3 3PTA', '3 FT','3 FTA',
                    '4 FG', '4 FGA','4 FG', '4 3PT','4 3PTA', '4 FT','4 FTA',]

period_points = {1: '1Q PTS', 2: '2Q PTS', 3:'3Q PTS', 4:'4Q PTS', 5:'OT PTS', 6:'2OT PTS', 7:'3OT', 8:'4OT'}

period_fg_makes = {1: '1Q FG', 2: '2Q FG', 3:'3Q FG', 4:'4Q FG', 5:'OT', 6:'2OT', 7:'3OT', 8:'4OT'}
period_fg_misses = {1: '1Q FGM', 2: '2Q FGM', 3:'3Q FGM', 4:'4Q FGM', 5:'OT', 6:'2OT', 7:'3OT', 8:'4OT'}

period_ft_makes = {1: '1Q FT', 2: '2Q FT', 3:'3Q FT', 4:'4Q FT', 5:'OT', 6:'2OT', 7:'3OT', 8:'4OT'}
period_ft_misses = {1: '1Q FGT', 2: '2Q FGT', 3:'3Q FGT', 4:'4Q FGT', 5:'OT', 6:'2OT', 7:'3OT', 8:'4OT'}