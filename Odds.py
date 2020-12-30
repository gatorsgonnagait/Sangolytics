from datetime import datetime as dt
import requests
import pandas as pd
import Tools as t
import Constants as c

def get_odds(version):
    api_key = c.api_key
    sport = version
    region = c.region
    market = c.market

    odds_response = requests.get('https://api.the-odds-api.com/v3/odds', params={
        'api_key': api_key,
        'sport': sport,
        'region': region,
        'mkt': market,
    }).json()

    df = pd.DataFrame.from_dict(odds_response['data'])

    df['date'] = df['commence_time'].apply(lambda x: dt.fromtimestamp(x).replace(hour=0, minute=0, tzinfo=None))
    df['left_home'] = df.apply(lambda row: 1 if row.teams[0] == row.home_team else 0, axis = 1)
    df['away_team'] = df.apply(lambda row: row.teams[1] if row.left_home == 1 else row.teams[0], axis = 1)
    df['game'] = df['date'].astype('str') + ' ' + df['away_team'] + ' ' + df['home_team']
    if market == 'spreads':
        bet = 'spread'
    else:
        bet = 'total'

    df[bet] = df.apply(lambda x:  t.most_frequent([i['odds'][market]['points'][1] for i in x.sites]) if ( x.home_team == 0) else t.most_frequent([i['odds'][market]['points'][0] for i in x.sites]), axis=1)
    df.drop(['left_home'], axis=1, inplace=True)
    return df

if __name__ == '__main__':
    df = get_odds(version='basketball_nba')
    live_total = df[(df['home_team'] == 'Denver Nuggets') & (df['away_team'] == 'Sacramento Kings')]
    print(live_total['total'].values[0])
