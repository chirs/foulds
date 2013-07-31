import datetime
import json
import re
import urllib

from foulds.utils import scrape_soup, scrape_url, get_contents
from foulds.cache import data_cache, set_cache


def unreverse_name(s):

    # For some stupid reason, USLSoccer.com puts a large break between
    # nicknames and middle name abbreviations.
    if '\r\n' in s:
        s = s.split('\r\n')[0].strip()
    
    #s = s.replace('\r\n', '').strip()

    #if '"' in s:
    #    name, nickname = [e.strip() for e in s.split('"', 1)]
    #    s = "%s %s" % (name, nickname)
        
    #if 'Noone' in s:
    #    import pdb; pdb.set_trace()


    if ',' in s:
        last, first = [e.strip() for e in s.split(',', 1)]
        return '%s %s' % (first, last)

    return s



def scrape_schedule(url):
    data = scrape_url(url)
    data = data.replace('\r\n', '').split('=')[1].rsplit(';')[0]

    jsdata = json.loads(data)

    base_url = 'http://www.uslsoccer.com/scripts/runisa.dll?M2:gp::72013+Elements/Display+E+47107+Stats/+'
    urls = []

    for k in jsdata.keys():
        v = jsdata[k]
        dt = datetime.datetime.strptime(v['dt'], "%d-%b-%Y")
        d = datetime.date.fromordinal(dt.toordinal())
        if d < datetime.date.today():
            urls.append(base_url + k)

    return sorted(set(urls))


def scrape_2013_games():
    return [scrape_game_data(e) for e in scrape_schedule('http://uslpro.uslsoccer.com/schedules/2013/58092651.js?8778')]

def scrape_2013_game_stats():
    l = [scrape_game_stats(e) for e in scrape_schedule('http://uslpro.uslsoccer.com/schedules/2013/58092651.js?8778')]
    return [e for e in l if e]


@set_cache
def scrape_game_data(url):
    try:
        soup = scrape_soup(url, encoding='iso-8859-1')
    except urllib.error.HTTPError:
        return {}

    content = soup.find('table', 'MainContent')

    header = content.find('table')
    team1, team2 = [get_contents(e) for e in header.findAll('a')]

    header2 = content.findAll('table')[1]
    location, date_string, time = [get_contents(e) for e in header2.findAll('td')]

    score = get_contents(header).split(team2)[1].split(location)[0]
    team1_score, team2_score = [int(e) for e in score.split(':')]

    dt = datetime.datetime.strptime(date_string, "%A, %B %d, %Y")

    

    return {
        'team1': team1,
        'team2': team2,
        'team1_score': team1_score,
        'team2_score': team2_score,
        'date': dt,
        'competition': 'USL Pro',
        'season': str(dt.year),
        'sources': [url],
        }



def scrape_goal_data(url):
    try:
        soup = scrape_soup(url, encoding='iso-8859-1')
    except urllib.error.HTTPError:
        return {}

    section = soup.find('div', {'id': 'stats-1-mr' })


def psf(e):
    # Process Stat Field

    if e is None:
        import pdb; pdb.set_trace()

    e = e.strip()
    if e in ('', '-'):
        e = None
    else:
        return int(e)

    
@set_cache
def scrape_game_stats(url):
    game_data = scrape_game_data(url)

    try:
        soup = scrape_soup(url, encoding='iso-8859-1')
    except urllib.error.HTTPError:
        return {}

    lineup_soup = soup.find('table', 'statsPL').find('tbody')

    try:
        team1_lineups = lineup_soup.findAll('tbody')[0]
        team2_lineups = lineup_soup.findAll('tbody')[1]
    except:
        return []


    def process_game_stat(tr, team):
        tds = tr.findAll('td')

        position, number, name, minutes, goals, assists, shots, fouls = [get_contents(e) for e in tds]

        return {
                'player': unreverse_name(name),
                'shots': psf(shots),
                'fouls': psf(fouls),
                'goals': psf(goals),
                'assists': psf(assists),
                'minutes': psf(minutes),
                'team': team,
                'games_played': 1,
                'competition': game_data['competition'],
                'season': game_data['season'],
                'date': game_data['date'],
                'sources': [url],
                }


    game_stats = []

    for e in team1_lineups.findAll('tr', 'pl-a-row'):
        game_stats.append(process_game_stat(e, game_data['team1']))

    for e in team2_lineups.findAll('tr', 'pl-a-row'):
        game_stats.append(process_game_stat(e, game_data['team2']))

    return game_stats



if __name__ == "__main__":
    #print(scrape_game_data('http://www.uslsoccer.com/scripts/runisa.dll?M2:gp::72013+Elements/Display+E+47107+Stats/+3684775'))
    #print(scrape_game_stats('http://www.uslsoccer.com/scripts/runisa.dll?M2:gp::72013+Elements/Display+E+47107+Stats/+3684775'))
    pass
