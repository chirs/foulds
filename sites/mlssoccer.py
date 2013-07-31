import datetime

import re
import urllib

from foulds.utils import scrape_soup, get_contents
from foulds.cache import data_cache, set_cache


# Scraping for new style mls games.

team_dict = {
    'CHI': 'Chicago Fire',
    'CLB': 'Columbus Crew',
    'COL': 'Colorado Rapids',
    'DAL': 'FC Dallas',
    'DC': 'DC United',
    'HOU': 'Houston Dynamo',
    'KC': 'Sporting Kansas City',
    'LA': 'Los Angeles Galaxy',
    'MTL': 'Montreal Impact',
    'NE': 'New England Revolution',
    'NY': 'New York Red Bulls',
    'PHI': 'Philadelphia Union',
    'POR': 'Portland Timbers',
    'PTI': 'Portland Timbers',
    'RSL': 'Real Salt Lake',
    'SEA': 'Seattle Sounders',
    'SJ': 'San Jose Earthquakes',
    'TOR': 'Toronto FC',
    'VAN': 'Vancouver Whitecaps',
}    

d2 = {
    #'CSL': 'Santos Laguna',
}

@data_cache
def scrape_game_data(url, competition):
    u2 = '%s/stats' % url

    try:
        soup = scrape_soup(u2, fix_tags=True)#, refresh=True)
    except urllib.error.HTTPError:
        return {}

    home_team = get_contents(soup.find("div", 'home-team-title'))
    away_team = get_contents(soup.find("div", 'away-team-title'))

    score = get_contents(soup.find("div", 'score-box'))
    home_score, away_score = [int(e) for e in score.split('-')]

    date_string = get_contents(soup.find("div", 'game-data-date'))
    dt = datetime.datetime.strptime(date_string, "%B %d, %Y")
    # Add hour.

    location = get_contents(soup.find("div", 'game-data-location'))

    referee = get_contents(soup.find("div", id='referee')).split(':')[1]
    attendance = get_contents(soup.find("div", id='attendance')).split(':')[1]
    if attendance.strip():
        attendnace = int(attendance)
    else:
        attendance = None

    return {
        'team1': home_team,
        'team2': away_team,
        'team1_score': home_score,
        'team2_score': away_score,
        'home_team': home_team,
        'competition': competition,
        'season': str(dt.year),
        'date': dt,
        'location': location,
        'referee': referee,
        'attendance': attendance,
        'sources': [url],
        }    

@data_cache
def scrape_goals(url, competition):
    u2 = '%s/stats' % url
    game_data = scrape_game_data(url, competition)
    if game_data is None:
        return []

    try:
        soup = scrape_soup(u2, fix_tags=True)#, refresh=True)
    except urllib.error.HTTPError:
        return []
    

    goals = []
    goal_trs = soup.find("div", {'id': 'goals'}).findAll("tr")[1:] # Skip header.
    for tr in goal_trs:
        tds = tr.findAll('td')
        try:
            club, minute, player, assists = [get_contents(e) for e in tds]
        except:
            import pdb; pdb.set_trace()
        team = team_dict.get(club, club)

        if '+' in minute:
            minute = minute.split('+')[0]
            minute = int(minute.replace('\'', ''))
        else:
            minute = int(minute.replace('\'', ''))


        assists = assists.replace('(', '').replace(')', '').split(',')
        goals.append({
                'team': team,
                'competition': competition,
                'date': game_data['date'],
                'goal': player,
                'minute': minute,
                'assists': assists,
                'season': game_data['season'],
                })

    return goals

@data_cache
def scrape_lineups(url, competition):

    def process_tr(tr, team, starter):
        global previous_off

        data = [get_contents(e) for e in tr.findAll("td")]
        number, position, player, minute = data[:4]


        minutes = int(minute)

        starter = starter or player in starter_dict

        if starter:
            on = 0
            off = minutes
            previous_off = off
            if player in starter_dict: # Short circuit to avoid duplicates.
                return
            starter_dict[player] = off
        else:
            on = previous_off
            off = on + minutes
            previous_off = off

        d = {
            'name': player,
            'team': team,
            'on': on,
            'off': off,
            }
        d.update(base)
        return d

    u2 = '%s/rosters' % url

    game_data = scrape_game_data(url, competition)
    if game_data is None:
        return []

    try:
        soup = scrape_soup(u2, fix_tags=True)#, refresh=True)
    except urllib.error.HTTPError:
        return []

    base = {
        #'team': game_dteam,
        'competition': game_data['competition'],
        'date': game_data['date'],
        'season': game_data['season'],
        #'goals_for': goals_for,
        #'goals_against': goals_against,
        'order': None,
        }


    lineups = []
    starter_dict = {}
    previous_off = 0

    starters, gks, subs, unused = soup.findAll("div", 'stats-table')

    home_starters, away_starters = starters.findAll('tbody')

    for tr in home_starters.findAll('tr'):
        a = process_tr(tr, game_data['team1'], True)
        lineups.append(a)

    for tr in away_starters.findAll('tr'):
        a = process_tr(tr, game_data['team2'], True)
        lineups.append(a)

    home_gks, away_gks = gks.findAll('tbody')
    lineups.append(process_tr(home_gks.find('tr'), game_data['team1'], True))
    lineups.append(process_tr(away_gks.find('tr'), game_data['team2'], True))

    home_subs, away_subs = subs.findAll('tbody')

    # Need to add in subs. Sort of difficult.
    for tr in home_subs.findAll('tr'):
        a = process_tr(tr, game_data['team1'], False)
        lineups.append(a)

    for tr in away_subs.findAll('tr'):
        a = process_tr(tr, game_data['team2'], False)
        lineups.append(a)

    return lineups


@data_cache
def scrape_schedule(url):
    soup = scrape_soup(url, fix_tags=True)#, refresh=True)
    schedule_table = soup.find("div", 'schedule-page')
    links = schedule_table.findAll("a")
    hrefs = [e['href'] for e in links]
    match_hrefs = [e for e in hrefs if 'matchcenter' in e]
    return ['http://www.mlssoccer.com/%s' % e for e in match_hrefs]


def extract_date(url):
    year, month, day = [int(e) for e in re.search('(\d+)-(\d+)-(\d+)', url).groups()]
    return datetime.date(year, month, day)

def scrape_competition(url, competition):
    urls = [url for url in scrape_schedule(url) if extract_date(url) < datetime.date.today()]

    games = [scrape_game_data(url, competition) for url in urls]
    goals = [scrape_goals(url, competition) for url in urls]
    lineups = [scrape_lineups(url, competition) for url in urls]

    g2 = []
    l2 = []
    for gx in goals:
        g2.extend(gx)

    for lx in lineups:
        l2.extend(lx)

    return games, g2, l2


if __name__ == "__main__":
    #scrape_competition("http://www.mlssoccer.com/schedule?month=all&year=2012&club=all&competition_type=45&broadcast_type=all&op=Search&form_id=mls_schedule_form",
    #                   "MLS Cup Playoffs")
    #print(scrape_competition("http://www.mlssoccer.com/schedule?month=all&year=2012&club=all&competition_type=44&broadcast_type=all&op=Search&form_id=mls_schedule_form",
    #                          "MLS Cup"))

    print(scrape_competition("http://www.mlssoccer.com/schedule?month=all&year=2011&club=all&competition_type=46&broadcast_type=all&op=Search&form_id=mls_schedule_form",
                              "Major League Soccer"))
