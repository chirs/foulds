import datetime
import json
import re
import urllib

from foulds.utils import scrape_soup, get_contents, scrape_url
from foulds.cache import data_cache, set_cache



def scrape_player_slugs():
    template = 'http://www.premierleague.com/ajax/player/index/A_TO_Z/null/null/ALL/null/null/null/ALL/null/null/100/4/2/2/%s/null.json'

    l  = []
    
    for e in range(1, 60):
        url = template % e
        data = scrape_url(url)
        js = json.loads(data)

        index = js['playerIndexSection']['index']
        results = index['resultsList']
        
        slugs = [e['cmsAlias'] for e in results]
        slugs = [e[0] for e in slugs if e]
        l.extend(slugs)


    return l

        
def scrape_player_bios():
    slugs = scrape_player_slugs()

    bios = []
    stats = []

    for i, slug in enumerate(slugs[:2950]):
        #print(i)
        purl = 'http://www.premierleague.com/en-gb/players/profile.career-history.html/%s' % slug
        #bio = scrape_player_bio(purl)
        #bios.append(bio)
        sx = scrape_player_stats(purl)
        stats.append(sx)

    return [e for e in stats if e]


def scrape_player_bio(url):
    soup = scrape_soup(url)


    name = get_contents(soup.find('h1')).split('-', 1)[1]


    data = soup.find('ul', 'stats').findAll('p')
    dt = datetime.datetime.strptime(get_contents(data[0]), '%d/%m/%Y')

    nationality = get_contents(data[1]).title()

    return {
        'name': name,
        'birthdate': dt,
        'nationality': nationality,
        'source': url,
        }


@data_cache
def scrape_player_stats(url):
    try:
        soup = scrape_soup(url, sleep=5)
    except:
        return []

    try:
        name = get_contents(soup.find('h1')).split('-', 1)[1]
    except:
        print("no name")
        return []

    teams = [get_contents(e) for e in soup.findAll('p', 'clubName')]
    stat_tables = soup.findAll('table', 'stats')
    
    if len(teams) != len(stat_tables):
        print("inconsistent teams / stats tables for %s" % url)
        return []

    l = []

    for team, table in zip(teams, stat_tables):
        trs = table.findAll("tr")
        for e in trs[1:]:
            tds = e.findAll('td')
            
            if len(tds) == 0:
                continue


            season, gp, g, yc, rc, wins, draws, losses, gf, ga, pts = [get_contents(e) for e in tds]
            l.append({
                    'name': name,
                    'team': team,
                    'season': season,
                    'competition': 'Premier League',
                    'games_played': gp,
                    'goals': g,
                    'source': url,
                    })
                
    return l



def scrape_calendars():
    urls = []
    for e in range(1992, 2007):
        season = '%s-%s' % (e, e + 1)
        url = 'http://www.premierleague.com/content/premierleague/en-gb/matchday/results.html?paramSeason=%s&view=.dateSeason' % season
        games = scrape_calendar(url)
        games = [e for e in games if season in e]
        urls.extend(games)

    games = []
    for url in urls:
        gd = scrape_game_data(url)
        #print(gd)
        games.append(gd)

    return games
        

@data_cache
def scrape_game_data(url):

    soup = scrape_soup(url, sleep=5)
    teaminfo = soup.find('table', 'teaminfo')

    home_team = get_contents(teaminfo.find('td', 'home'))
    away_team = get_contents(teaminfo.find('td', 'away'))

    home_score = int(get_contents(teaminfo.find('span', 'homeScore')))
    away_score = int(get_contents(teaminfo.find('span', 'awayScore')))

    fixtureinfo = get_contents(soup.find('p', 'fixtureinfo'))

#<p class="fixtureinfo"><span widget="localeDate" timestamp="737145900000" format="dddd d MMMM yyyy">Tuesday 11 May 1993</span> | Highbury | Referee: <a href="/en-gb/matchday/matches/1992-1993/epl.match-report.html/">Keith Cooper</a> | Attendance 26,393</p>
    
    try:
        date, stadium, referee, attendance = fixtureinfo.split('|')
    except:
        import pdb; pdb.set_trace()

    referee = referee.split(':')[1]
    attendance = int(attendance.replace('Attendance', '').replace(',', ''))

    dt = datetime.datetime.strptime(date, '%A %d %B %Y')

    return {
        'date': dt,
        'team1': home_team,
        'team2': away_team,
        'team1_score': home_score,
        'team2_score': away_score,
        'home_team': home_team,
        'stadium': stadium,
        'referee': referee,
        'attendance': attendance
        }
    

def scrape_calendar(url):
    soup = scrape_soup(url)

    urls = [e.get('href') for e in soup.findAll('a')]
    match_urls = [e for e in urls if e and '/matches/' in e]

    return ['http://www.premierleague.com' + e for e in match_urls]


if __name__ == "__main__":
    #print(scrape_player_bio('http://www.premierleague.com/en-gb/players/profile.career-history.html/alan-shearer'))
    #print(scrape_player_stats('http://www.premierleague.com/en-gb/players/profile.career-history.html/alan-shearer'))
    #print(scrape_player_urls())
    #print(scrape_player_bios()[-1])
    scrape_calendars()
