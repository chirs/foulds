#!/usr/local/bin/env python
# -*- coding: utf-8 -*-

import datetime
import re

from foulds.utils import scrape_soup, get_contents
from foulds.cache import data_cache, set_cache

date_re = re.compile("(.*?) (\d+) de (\w+) de (\d+)")
goal_re = re.compile("(.*?) al minuto (\d+)' (a pase de (.*?))?")


months = {
    'enero': 1,
    'febrero': 2,
    'marzo': 3,
    'abril': 4,
    'mayo': 5,
    'junio': 6,
    'julio': 7,
    'agosto': 8,
    'septiembre': 9,
    'septiempre': 9,
    'octubre': 10,
    'noviembre': 11,
    'diciembre': 12,
}    


def scrape_games(gids):
    gids = [e for e in gids if e > 0 and e < 70000]
    games = []
    goals = []
    for gid in gids:
        try:
            g = scrape_game(gid)
            if g is not None:
                games.append(g[0])
                goals.append(g[1])
        except KeyboardInterrupt:
            raise
        except:
            import pdb; pdb.set_trace()
            print("Uncaught error for %s" % gid)


    return games


@set_cache
def scrape_game(gid):


    url = 'http://msn.mediotiempo.com/ficha.php?id_partido=%s' % gid
    soup = scrape_soup(url, encoding='iso_8859_1', sleep=2)
    breadcrumbs = soup.find("div", {"id": "breadcrums"})
    try:
        competition, rest = [e for e in breadcrumbs.contents[1].childGenerator()]
        season, sround = [get_contents(e) for e in rest.findAll('a')]
        #country, competition, season, sround, matchup = [e for e in [get_contents(e) for e in breadcrumbs] if e.strip()]
    except:
        #import pdb; pdb.set_trace()
        print("Breadcrumbs Failure on %s" % gid)
        return None

    izquierdas = soup.findAll("div", 'cuadro_izquierda')
    derechas = soup.findAll("div", 'cuadro_derecha')
    if len(izquierdas) < 3:
        print("Failure on %s" % gid)
        return None

    team1, score, team2 = [e for e in [get_contents(e) for e in izquierdas[1]] if e]
    team1_score, team2_score = [int(e) for e in score.split('-')]
    context = [e for e in [get_contents(e) for e in izquierdas[2]] if e.strip()]
    date_s, stadium = context[:2]
    referees = [e.split('(')[0] for e in context[2:]]

    if referees:
        referee = referees[0]
        linesmen = referees[1:]
    else:
        referee = None
        linesmen = []

    try:
        _, day, month, year = date_re.search(date_s.lower()).groups()
    except:
        print("Date Failure on %s" % gid)
        return None

    if month not in months:
        import pdb; pdb.set_trace()


    game = {
        'competition': str(competition) , # throwing Pickle error when using bs4.NavigableString
        #'country': country,
        'season': season,
        'round': sround,
        'group': None,

        'date': datetime.datetime(int(year), months[month], int(day)),

        'team1': team1.title(),
        'team2': team2.title(),
        'team1_score': team1_score,
        'team2_score': team2_score,

        #'stadium': stadium,
        'location': stadium,

        'referee': referee,
        'linesmen': linesmen,

        'sources': [url],
        }


    #goals = [get_contents(e) for e in derechas.findAll("span", "mini_titulo")]
    goals = []

    return game, goals




if __name__ == "__main__":
    # Have downloaded 10000 to 11800
    print(scrape_games(range(10000, 11500)))
