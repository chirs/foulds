#!/usr/local/bin/env python
# -*- coding: utf-8 -*-

import datetime
import re

from foulds.utils import scrape_soup, get_contents
from foulds.cache import data_cache, set_cache

# Want to scrape next round / previous round urls.
# Actually definitely want to do this. Some rounds aren't even in order.


def scrape_aleague():
    # Looks like we've got some metadata that we're not really handling.
    # Need to investigate.
    l = []
    for season, sid in season_ids:
        l.extend(scrape_scoreboard(sid, season))

    games = []
    for season, gid in l:
        games.append(scrape_aleague_game(gid, season))

    goals = []
    for season, gid in l:
        goals.append(scrape_aleague_goals(gid, season))

    lineups = []
    #for season, gid in l:
    #    lineups.append(scrape_aleague_lineups(gid, season))

    #game_stats = []
    #for season, gid in l:
    #    game_stats.append(scrape_aleague_game_stats(gid, season))


    games = [e for e in games if e]
    goals = [e for e in goals if e]
    #lineups = [e for e in lineups if e]
        
    return (games, goals, lineups)



def scrape_scoreboard(sid, season):
    url = 'http://www.footballaustralia.com.au/aleague/results/%s/all-rounds/%s/0' % (season, sid)
    soup = scrape_soup(url)
    results = soup.find('div', 'fixtures-results')
    urls = [e['href'] for e in results.findAll('a',href=True)]
    match_urls = [url for url in urls if 'matchcentre' in url]
    gids = sorted(set([e.split('/')[-1] for e in match_urls]))
    return [(season, gid) for gid in gids]


season_ids = [
    ('2005-2006', 2),
    ('2006-2007', 31),
    ('2007-2008', 97),
    ('2008-2009', 135),
    ('2009-2010', 155),
    ('2010-2011', 173),
    ('2011-2012', 223),
    ('2012-2013', 261),
    ('2013-2014', 286),
]


@data_cache
def scrape_aleague_game(gid, season):


    game_url = 'http://www.footballaustralia.com.au/aleague/matchcentre/matchstats/filler/%s' % gid
    soup = scrape_soup(game_url)

    home_team = get_contents(soup.find('a', {'id': 'ctl11_hlHeaderHomeClub'}))
    away_team = get_contents(soup.find('a', {'id': 'ctl11_hlHeaderAwayClub'}))
    location = get_contents(soup.find('span', {'id': 'headervenue' }))

    try:
        home_score, away_score = [int(e) for e in get_contents(soup.find('span', {'id': 'headerscore' })).split('-')]
    except ValueError:
        return {}

    date_string = get_contents(soup.find('span', {'id': 'headerdatetime' }))

    try:
        dt = datetime.datetime.strptime(date_string, "%d %B %Y")
    except ValueError:
        print("Date parsing error.")
        return {}

    return {
        'team1': home_team,
        'team2': away_team,
        'team1_score': home_score,
        'team2_score': away_score,
        'home_team': home_team,
        'competition': 'Hyundai A-League',
        'season': season,
        'date': dt,
        'location': location,
        #'referee': referee,
        #'attendance': attendance,
        'sources': [game_url],
        }    


@data_cache
def scrape_aleague_goals(gid, season):

    game_url = 'http://www.footballaustralia.com.au/aleague/matchcentre/matchstats/filler/%s' % gid
    game_data = scrape_aleague_game(gid, season)

    soup = scrape_soup(game_url)
    

    goal_scorers = [get_contents(e) for e in soup.findAll('div', 'goal_scorer')]
    goal_times = [get_contents(e) for e in soup.findAll('div', 'goal_time')]
    goals = zip(goal_times, goal_scorers)

    l = []
    for i, g in enumerate(goals, start=1):
        time, player = g
        minute = int(time.replace('\'', '').replace(':', ''))

        # site doesn't explicitly state team.
        # so figure it out.
        if i <= game_data['team1_score']:
            team = game_data['team1']
        else:
            team = game_data['team2']
        

        l.append({
                'team': '',
                'competition': 'Hyundai A-League',
                'date': game_data['date'],
                'team': team,
                'goal': player,
                'minute': minute,
                'assists': [],
                'season': season,
                })
                
    return l



@set_cache
def scrape_aleague_game_stats(gid, season):

    game_url = 'http://www.footballaustralia.com.au/aleague/matchcentre/matchstats/filler/%s' % gid
    game_data = scrape_aleague_game(gid, season)

    soup = scrape_soup(game_url)

    goal_scorers = [get_contents(e) for e in soup.findAll('div', 'goal_scorer')]
    goal_times = [get_contents(e) for e in soup.findAll('div', 'goal_time')]
    goals = zip(goal_times, goal_scorers)

    l = []
    for i, g in enumerate(goals, start=1):
        time, player = g
        minute = int(time.replace('\'', '').replace(':', ''))

        # site doesn't explicitly state team.
        # so figure it out.
        if i <= game_data['team1_score']:
            team = game_data['team1']
        else:
            team = game_data['team2']
        

        l.append({
                'team': '',
                'competition': 'Hyundai A-League',
                'date': game_data['date'],
                'team': team,
                'goal': player,
                'minute': minute,
                'assists': [],
                'season': season,
                })
                
    return l
    

@data_cache
def scrape_aleague_lineups(gid, season):


    def process_block(b, team, on, off):
        l = []
        names = [get_contents(e) for e in b.findAll('div', 'playername')]
        for name in names:
            l.append({
                    'name': name.title(),
                    'team': team,
                    'on': on,
                    'off': off,
                    })
        return l

    lineup_url = 'http://www.footballaustralia.com.au/aleague/matchcentre/lineup/filler/%s' % gid

    game_data = scrape_aleague_game(gid, season)
    if game_data == {}:
        return []


    soup = scrape_soup(lineup_url)

    home_starters, home_subs = soup.findAll('div', 'lineuphome')
    away_starters, away_subs = soup.findAll('div', 'lineuphome')

    base = {
        'competition': 'Hyundai A-League',
        'date': game_data['date'],
        'season': season,
        #'order': None,
        }

    appearances = []
    appearances.extend(process_block(home_starters, game_data['team1'], 0, None))
    appearances.extend(process_block(home_subs, game_data['team1'], None, None))
    appearances.extend(process_block(away_starters, game_data['team2'], 0, None))
    appearances.extend(process_block(away_subs, game_data['team2'], None, None))

    for e in appearances:
        e.update(base)

    return appearances






if __name__ == '__main__':
    #print(scrape_aleague_game(''))
    #print(scrape_aleague_goals(''))
    #print(scrape_scoreboard(31, '2006-2007'))
    print(scrape_aleague())

    #games, goals, lineups = scrape_aleague()

    #print(scrape_aleague_game_stats(340, 'A-League'))
