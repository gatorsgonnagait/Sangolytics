import requests
import pandas as pd

def call_api(market):
    api_key = 'c06e566dfb583f3a48a89143106b6241'
    sport = 'americanfootball_ncaaf'
    region = 'us'
    odds_response = requests.get('https://api.the-odds-api.com/v3/odds', params={
        'api_key': api_key,
        'sport': sport,
        'region': region,
        'mkt': market,
    }).json()

    df = pd.DataFrame.from_dict(odds_response['data'])
    df['Date'] = df['commence_time'].apply(lambda x: dt.datetime.fromtimestamp(x).replace(hour=0, minute=0, tzinfo=None))
    df['Home'] = df['home_team'].apply(lambda x: ft.format_team_names(x))
    df['left_home'] = df.apply(lambda row: 1 if ft.format_team_names(row.teams[0]) == row.Home else 0, axis = 1)
    df['Away'] = df.apply(lambda row: ft.format_team_names(row.teams[1]) if row.left_home == 1 else ft.format_team_names(row.teams[0]), axis = 1)
    df['Game'] = df['Date'].astype('str') + ' ' + df['Away'] + ' ' + df['Home']
    if market == 'spreads':
        bet = 'Current Spread Home'
    else:
        bet = 'Over Under'

    df[bet] = df.apply(lambda x:  ft.most_frequent([i['odds'][market]['points'][1] for i in x.sites]) if ( x.left_home == 0) else ft.most_frequent([i['odds'][market]['points'][0] for i in x.sites]), axis=1)
    df.drop(['left_home'], axis=1, inplace=True)
    return df

def odds_api(year, week):
    neutral_games = pd.read_csv('..' + path.sep + str(year) + path.sep + str(year) + '_neutral_games.csv')

    spreads = call_api('spreads')
    totals = call_api('totals')
    spreads.dropna(axis=0, inplace=True)
    totals.dropna(axis=0, inplace=True)

    schedule = pd.merge(spreads[['Game', 'Date', 'Away', 'Home', 'Current Spread Home']], totals[['Game', 'Over Under']], on='Game')
    first_date = schedule['Date'].iloc[0]
    neutral_games['Game Rev'] = schedule['Date'].astype('str') + ' ' + schedule['Home'] + ' ' + schedule['Away']
    schedule['Neutral Site'] = schedule['Game'].apply(lambda x: 1 if x in neutral_games['Game'] or x in neutral_games['Game Rev'] else 0)
    schedule['Week'] = schedule['Date'].apply(lambda date: week + 1 if (date - first_date).days > 5 else week )
    schedule.set_index('Game', inplace=True)
    schedule = schedule[['Date','Week','Away', 'Home', 'Current Spread Home','Over Under','Neutral Site']]
    return schedule


def get_odds(year, week, version):
    scraper = spread_scraper(year, week)
    odds = odds_api(year, week)
    scraper.reset_index(inplace=True)
    odds.reset_index(inplace=True)

    scraper['Date'] = pd.to_datetime(scraper['Date'])
    scraper['Date'] = scraper['Date'].apply(lambda x: x.replace(hour=0, minute=0, tzinfo=None))
    scraper['Neutral Site'] = scraper['Neutral Site'].astype('int')
    scraper['Current Spread Home'] = scraper['Current Spread Home'].astype('float')
    scraper.drop(['Spread Price', 'Over Under Price'], axis=1, inplace=True)
    odds['Current Spread Home'] = odds['Current Spread Home'].astype('float')
    scraper['Over Under'] = scraper['Over Under'].astype('float')
    games = odds.append(scraper, sort=False)
    games = games.drop_duplicates(keep='first', subset=['Game'])
    games.set_index('Game', inplace=True)
    games.sort_index(axis=0, inplace=True)

    print('returned odds')
    file_path = c.file_path(year, week, version='', folder='_spreads') + version + '.csv'
    if Path(file_path).is_file():
        print('file exists already')
    else:
        games.to_csv(file_path, index=True)