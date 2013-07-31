import datetime

import re
import urllib

from foulds.utils import scrape_soup, get_contents
from foulds.cache import data_cache, set_cache


team_map = {
    'MIN': 'Minnesota United', 
    'CAR': 'Carolina RailHawks',
    'ATL': 'Atlanta Silverbacks', 
    'TBR': 'Tampa Bay Rowdies', 
    'PRI': 'Puerto Rico Islanders', 
    'MNU': 'Minnesota United', 
    'EDM': 'FC Edmonton', 
    'FCE': 'FC Edmonton', 
    'SAS': 'San Antonio Scorpions', 
    'FTL': 'Fort Lauderdale Strikers',
    }


def get_season(dt):
    if dt.year <= 2012:
        return str(dt.year)

    if dt.year == 2013 and dt.month <= 7:
        return '2013 Spring'

    if dt.year == 2013 and dt.month > 7:
        return '2012 Fall'

    return ''

        


def scrape_schedules():
    url = 'http://nasl.com/index.php?id=12'

    urls = []
    for year in 2012, 2013:
        post = {
            'sch_year': year,
            'sch_type': 1,
            }
        soup = scrape_soup(url, encoding='iso-8859-1', url_data=post, refresh=True)

        url_stubs = [e['href'] for e in soup.findAll('a', 'scheduleRecap')]
        urls.extend(['http://nasl.com/%s' % e for e in url_stubs])


    return urls


def scrape_all_games():
    return [scrape_game_data(url) for url in scrape_schedules()]

def scrape_all_goals():
    l = [scrape_goal_data(url) for url in scrape_schedules()]
    return [e for e in l if e]

def scrape_all_game_stats():
    return [scrape_game_stats(url) for url in scrape_schedules()]


@data_cache
def scrape_game_data(url):
    try:
        soup = scrape_soup(url, encoding='iso-8859-1')
    except urllib.error.HTTPError:
        return {}


    content = soup.find('div', 'pageContent')
    
    header = soup.find('table')
    team1, misc, team2 = header.findAll('td')
    team1 = get_contents(team1)
    team2 = get_contents(team2)

    score = get_contents(misc.findAll('br')[1]).split('FINAL')[0]
    mtext = get_contents(misc)
    date_string, remainder = [e.strip() for e in mtext.split('  ', 1)]

    team1_score, team2_score = [int(e) for e in score.split('-')]



    dt = datetime.datetime.strptime(date_string, "%B %d, %Y")


    return {
        'team1': team1,
        'team2': team2,
        'team1_score': team1_score,
        'team2_score': team2_score,
        'date': dt,
        'competition': 'North American Soccer League (2011-)',
        'season': get_season(dt),
        'sources': [url],
        }


@set_cache
def scrape_goal_data(url):
    game_data = scrape_game_data(url)

    try:
        soup = scrape_soup(url, encoding='iso-8859-1')
    except urllib.error.HTTPError:
        return {}

    goal_soup = soup.find('div', {'id': 'goals'})
    goals = []

    for tr in goal_soup.findAll('tr')[1:]:
        tds = tr.findAll('td')
        time, team, scorer, assist, description = [get_contents(e) for e in tds]

        #scorer = re.match("#\d+ (.*)", scorer).groups()[0]
        scorer = scorer.split(' ', 1)[1]
        minute = time.split(':')[0]

        if assist:
            assists = [assist,]
        else:
            assists = []
        
        goals.append({
                'goal': scorer,
                'assists': assists,
                'minute': int(minute),
                'team': team_map.get(team, team),
                'competition': game_data['competition'],
                'date': game_data['date'],
                'season': game_data['season'],
                'sources': [url],
                })
        
    return goals
                


def psf(e):
    # Process Stat Field

    if e is None:
        import pdb; pdb.set_trace()

    e = e.strip()
    if e in ('', '-'):
        e = None
    else:
        return int(e)


@data_cache
def scrape_game_stats(url):
    game_data = scrape_game_data(url)

    try:
        soup = scrape_soup(url, encoding='iso-8859-1')
    except urllib.error.HTTPError:
        return {}

    lineup_soup = soup.find('div', {'id': 'lineups'}).findAll('table')
    game_stats = []

    def process_game_stat(tr, team):
        tds = tr.findAll('td')

        if len(tds) == 10:
            position, number, name, shots, sog, g, a, yc, rc, minutes = [get_contents(e) for e in tds]

        elif len(tds) == 8:
            return {}

        else:
            return {}

        if name.strip().lower() in ('totals', 'team'):
            return {}

        return {
                'player': name,
                'shots': psf(shots),
                'shots_on_goal': psf(sog),
                'yellow_cards': psf(yc),
                'red_cards': psf(rc),
                'goals': psf(g),
                'assists': psf(a),
                'minutes': psf(minutes),
                'team': team,
                'games_played': 1,
                'competition': game_data['competition'],
                'season': game_data['season'],
                'date': game_data['date'],
                'sources': [url],
                }


    for tr in lineup_soup[2].findAll('tr')[1:]:
        game_stats.append(process_game_stat(tr, game_data['team1']))

    for tr in lineup_soup[4].findAll('tr')[1:]:
        game_stats.append(process_game_stat(tr, game_data['team2']))
        
    return [e for e in game_stats if e]
                
        



if __name__ == '__main__':
    #print(scrape_game_stats('http://nasl.com/index.php?id=488&getGameID=481'))
    #print(scrape_schedules())
    print(scrape_all_games())
