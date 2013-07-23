#!/usr/local/bin/env python
# -*- coding: utf-8 -*-

# Errors:
# http://soccernet.espn.go.com/match?id=289678
# http://soccernet.espn.go.com/match?id=262155
# This one is missing match stats...

# Now defunct due to soccernet's move to espnfc.com
# Only use for old (pre-2011) scores.

# Need to set up a way of doing this better.


# 1. Scrape_all_league_scores
# scrape_scoreboard_urls
# for url in urls: scrape_league_scoreboard(url)

#  scrape_all_league_games
# scrape_all_league_scores
# for each url, scrape_live_game(url)



"""
Need to figure out a way to refresh failed results.
e.g. ran into a FC dallas game that couldn't be scraped.
Will silently fail for now, but eventually need to do something else.


How should a typical load go?

Cacheing sould happen on each level.

But there are essentially three levels.

Need to separate conceptually and cache different levels.

Need to make sure that new date urls are being loaded, but aren't taking too long.
Use a single objects that gets and parses urls in one go (for a given date/code),
and remembers those permanently. Don't cache the backwards searching thing.

1. Load game urls.
2. Load game data.
3. Load extended data.

1. Get scoreboard urls for each date. - 
2. Get game urls for each scoreboard.
3. Fetch game data from urls.
4. Use game data to fetch lineup, goal, and foul data.

"""


from collections import defaultdict
import datetime
import re

from foulds.utils import scrape_soup, get_contents
from foulds.cache import set_cache, data_cache

url_cache = data_cache
game_cache = set_cache
detail_cache = set_cache
everything_cache = set_cache

ROOT_URL = 'http://soccernet.espn.go.com'
STOP_DATE = datetime.date(2012, 1, 1)


SOCCERNET_ALIASES = {
    # CONCACAF Champions League...
    'Motagua': 'CD Motagua',
    'Olimpia (H)': 'CD Olimpia',
    'San Fco': 'San Francisco F.C.',
    'Santos FC': 'Santos Laguna',
    'Comunicacion': 'Comunicaciones',
    'C.D. Fas': 'C.D. FAS',
    'I. Metapán': 'Isidro Metapán',
    'San Francisco': 'San Francisco F.C.',

    'Chicago': 'Chicago Fire',
    'Colorado': 'Colorado Rapids',
    'Columbus': 'Columbus Crew',
    'Houston': 'Houston Dynamo',
    'Impact de Montreal': 'Montreal Impact',
    'Kansas City': 'Sporting Kansas City',
    'Los Angeles': 'Los Angeles Galaxy',
    'Montreal': 'Montreal Impact',
    'New England': 'New England Revolution',
    'Philadelphia': 'Philadelphia Union',
    'Portland': 'Portland Timbers',
    'Puerto Rico': 'Puerto Rico Islanders',
    'Salt Lake': 'Real Salt Lake',
    'San Jose': 'San Jose Earthquakes',

    'Seattle': 'Seattle Sounders',
    'Toronto': 'Toronto FC',
    'Vancouver': 'Vancouver Whitecaps',
    }



def code_to_competition(league_code):
    return {
        'usa.1': 'Major League Soccer',
        'concacaf.champions': 'CONCACAF Champions League',
        'mex.1': 'Liga MX',
        }[league_code]




# Don't cache this or else you don't get daily updates; won't save much time anyway.
def get_urls_for_league(league_code, stop_date):
    """
    Walk backwards in time, collecting game urls, until you hit the stop_date.
    """

    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    scoreboard_urls = get_scoreboard_urls(league_code, yesterday, stop_date)

    urls = []
    for url in scoreboard_urls:
        try:
            urls.extend(scrape_scoreboard(url))
        except:
            print(url)

    return [e for e in urls if e]



# Consider rewriting this. It's not pretty.
def get_scoreboard_urls(league_code, start, end=None):
    """Returns a list of scoreboard urls for a given league code."""

    date_code = start.strftime("%Y%m%d") # 20090515, e.g.
    base_url = 'http://soccernet.espn.go.com/scores?date=%s&league=%s&cc=5901&xhr=1' 
    search_url = base_url % (date_code, league_code)

    def keep_searching(url):
        if end is None:
            return True

        u = url.split("date=")[1]
        u = u.split("&league")[0]
        year, month, day = u[:4], u[4:6],  u[6:]
        try:
            d = datetime.date(int(year), int(month), int(day))
        except:
            print("scoreboard date fail on %s" % url)
            return False

        return d >= end


    # This is commented out because get_previous_url badly written so that
    # it doesn't update dates properly when this is cached.
    #@data_cache
    @set_cache
    def get_previous_url(url):
        """
        Given a scoreboard, scrape the url for the previous scoreboard.
        Returns an ajax url (unformatted)
        """
        soup = scrape_soup(url, encoding='iso_8859_1', sleep=10)
        urls = [a['href'] for a in soup.findAll("ul")[0].findAll("a")]
        full_url = "%s%s&xhr=1" % (ROOT_URL, urls[0])
        return full_url


    new_url = get_previous_url(search_url)
    urls = [new_url]
    while new_url:
        new_url = get_previous_url(new_url)

        # Check that the date is over.
        if not keep_searching(new_url):
            return urls

        # Will loop back if necessary.
        if new_url in urls:
            return urls

        urls.append(new_url)

    return urls


@url_cache
def scrape_scoreboard(url):
    """Retrieve game detail urls from a scoreboard."""
    
    def get_valid_url(game):
        """Fetch all urls that can be parsed from a scoreboard."""
        # Are all these checks necessary? What happens if we just skip them?

        data = [get_contents(e) for e in game.findAll("a")] 
        home_team, score, away_team = data[:3]

        urls = [e['href'] for e in game.findAll("a")]

        # Distiguish espnfc vs. soccernet urls.
        if 'http' in urls[1]:
            url = urls[1]
        else:
            url = ROOT_URL + urls[1]

        # Are any of these checks necessary?
        score = score.replace("&nbsp;", ' ')

        # Game postponed
        if score == "P - P":
            return {}

        # Unplayed
        if score == 'v':
            return {}

        # Make sure the score is parseable.

        try:
            home_score, away_score = [int(e) for e in  score.replace("&nbsp;", '').split("-")]
        except:
            import pdb; pdb.set_trace()
            return {}

        return url

    soup = scrape_soup(url, encoding='iso_8859_1', sleep=10)
    gameboxes = soup.findAll("div", 'gamebox')
    return [get_valid_url(game) for game in gameboxes]



def scrape_league(league_code):
    """
    """

    def make_match_stats_url(url):
        """Get the match url of a different link to a game."""
        #This is the match stats url which has subs, goals, etc.

        if 'espnfc' in url:
            return url

        regexen = ('id=(\d+)[&$]', "/_/id/(\d+)$")
        for regex in regexen:
            m = re.search(regex, url)
            if m:
                return '%s/match?id=%s' % (ROOT_URL, m.groups()[0])

        import pdb; pdb.set_trace()
        x = 5



    competition = code_to_competition(league_code)
    l = []
    for u in get_urls_for_league(league_code, STOP_DATE):
        url = make_match_stats_url(u)

        if 'espnfc' in url:
            l.append(scrape_espnfc_game(url, competition))
        else:
            l.append(scrape_soccernet_game(url, competition))

    games = [e['game'] for e in l if e.get('game')]
    goals = [e['goals'] for e in l if e.get('goals')]
    lineups = [e['lineups'] for e in l if e.get('lineups')]
    return games, goals, lineups


def scrape_espnfc_game(url, competition):

    try:
        # Loading soup here for speed.
        soup = scrape_soup(url, encoding='iso_8859_1', sleep=10)#, refresh=True)
    except:
        print("Failed for game at %s" % url)
        return {}


    try:
        game_data = scrape_espnfc_game_data(soup, competition, url)
    except:
        import pdb; pdb.set_trace()
    
    goal_data = scrape_espnfc_goals(soup, competition, game_data, url)
    lineup_data = scrape_espnfc_lineups(soup, competition, game_data, url)

    return {
        'game': game_data,
        'goals': goal_data,
        'lineups': lineup_data
        }



#@everything_cache
def scrape_soccernet_game(url, competition):
    try:
        # Loading soup here for speed.
        soup = scrape_soup(url, encoding='iso_8859_1', sleep=10)#, refresh=True)
    except:
        print("Failed for game at %s" % url)
        return {}


    game_data = scrape_soccernet_game_data(soup, competition, url)
    goal_data = scrape_soccernet_goals(soup, competition, game_data, url)
    lineup_data = scrape_soccernet_lineups(soup, competition, game_data, url)

    return {
        'game': game_data,
        'goals': goal_data,
        'lineups': lineup_data
        }



def scrape_espnfc_game_data(soup, competition, url):

    match_details = soup.find("div", "match-details")

    # Soccernet uses a javascript variable to display location-specific game time data.
    # Find the Date object and use it to construct a datetime.
    date_p = get_contents(match_details.findAll('p')[0])
    milliseconds_from_epoch = int(re.search("Date\((\d+)\)", date_p).groups()[0])
    dt = datetime.datetime.fromtimestamp(milliseconds_from_epoch / 1000)

    location = get_contents(match_details.findAll('p')[1])

    matchup = soup.find("div", 'matchup')

    attendance = int(get_contents(matchup.find('span')).replace("Attendance:", ''))

    home_team, away_team = [get_contents(e) for e in matchup.findAll("p", 'team-name')]

    score = get_contents(matchup.find("p", 'score'))
    home_score, away_score = [int(e) for e in score.split('-')]

    home_team = SOCCERNET_ALIASES.get(home_team, home_team)
    away_team = SOCCERNET_ALIASES.get(away_team, away_team)



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
        'referee': None,
        'attendance': attendance,
        'sources': [url],
        }    


@detail_cache
def scrape_espnfc_goals(soup, competition, game_data, url):
    """
    Get goal data from a game page.
    """
    
    goal_scorers = soup.findAll("ul", 'goal-scorers')
    home_goals = [get_contents(e) for e in goal_scorers[0].findAll('li')]
    away_goals = [get_contents(e) for e in goal_scorers[1].findAll('li')]

    def process_goal(s, team):

        # Need to check this for own goals?

        goal_type = 'normal'

        s = s.replace('\t', '').replace('\r', '').replace('\n', '').replace('&bull;', '').replace('\'', '').strip()

        if not s:
            return {}

        m = re.match('(.*?)(\d+)', s)
        if m:
            player, minute = m.groups()

        else:
            import pdb; pdb.set_trace()

        """
        m = re.match("(.*?)\(og (\d+)'\)", s)
        if m:
            player, minute = m.groups()
            goal_type = 'own goal'

        m = re.match("(.*?)\(pen (\d+)'\)", s)
        if m:
            player, minute = m.groups()
            goal_type = 'own goal'


        if player == 'player':
            import pdb; pdb.set_trace()
        """

            
        return {
            'goal': player,
            'minute': minute,
            'team': team,
            'type': goal_type,
            'season': unicode(game_data['date'].year),
            'date': game_data['date'],
            'competition': game_data['competition'],
            'assists': [],
            'sources': [url],
            }

    # Not the best way to handle this now that we've switched away from home/away designations.
    goals = []
    for goal in home_goals:
        gd = process_goal(goal, game_data['team1'])
        if gd:
            goals.append(gd)

    for goal in away_goals:
        gd = process_goal(goal, game_data['team2'])
        if gd:
            goals.append(gd)
        
    return goals



@detail_cache
def scrape_espnfc_lineups(soup, competition, game_data, url):
    """
    Scrape a lineup from a game url.
    """
    # Not checking for red cards currently.

    tables = soup.findAll("table", 'stat-table')
    home_lineup = tables[0].find('tbody').findAll('tr')
    away_lineup = tables[1].find('tbody').findAll('tr')
                

    def process_lineup(lineup, team):

        format_sub_time = lambda s: int(s.replace('\\', '').replace('-', '').replace('\'', ''))

        l = []

        for item in lineup:

            player_string = item.find('a')

            # This represents the break between starters and unused subs.
            # Just exit when we get here; we've gotten all the info about players who actually played.
            if player_string is None:
                return l

            player = get_contents(player_string)

            on = 0
            off = 90

            sub_out = item.find('div', 'soccer-icons-subout')
            if sub_out:
                off = format_sub_time(sub_out.contents[1])

            sub_in = item.find('div', 'soccer-icons-subin')
            if sub_in:
                on = format_sub_time(sub_in.contents[1])



            l.append({
                    'name': player,
                    'on': on,
                    'off': off,
                    'team': team,
                    'date': game_data['date'],
                    'season': unicode(game_data['date'].year),
                    'competition': game_data['competition'],
                    'sources': [url],
                    })

        return l



    la = process_lineup(home_lineup, game_data['team1'])
    lb = process_lineup(away_lineup, game_data['team2'])

    return la + lb





#@game_cache
def scrape_soccernet_game_data(soup, competition, url):
    """
    Get game data from a game page.
    """

    #if '336300' in url:
    #    import pdb; pdb.set_trace()
    
    home_team, away_team = [get_contents(e) for e in soup.findAll("div", "team-info")]
    game_data = soup.find("div", "game-time-location")

    score = get_contents(soup.find("p", "matchup-score"))
    home_score, away_score = [int(e) for e in score.replace("&nbsp;", " ").split("-")]

    data = [get_contents(e) for e in game_data]

    if len(data) == 3:
        season, datetime_string, location = data
        referee = None

    elif len(data) == 4:
        season, datetime_string, location, referee = data
        referee = referee.replace("Referee:", '').strip()

    elif len(data) == 5:
        # The second item is another referee (linesman?)
        season, datetime_string, location, referee, _ = data
        referee = referee.replace("Referee:", '').strip()

    else:
        import pdb; pdb.set_trace()


    minute, date_string = datetime_string.split(',', 1)
    date = datetime.datetime.strptime(date_string.strip(), "%B %d, %Y")

    home_team = SOCCERNET_ALIASES.get(home_team, home_team)
    away_team = SOCCERNET_ALIASES.get(away_team, away_team)

    return {
        'team1': home_team,
        'team2': away_team,
        'team1_score': home_score,
        'team2_score': away_score,
        'home_team': home_team,
        'competition': competition,
        'season': str(date.year),
        'date': date,
        'location': location,
        'referee': referee,
        'sources': [url],
        }


#@detail_cache
def scrape_soccernet_goals(soup, competition, game_data, url):
    """
    Get goal data from a game page.
    """
    
    container = soup.find("div", 'story-container').find("tbody")
    home_goals = [get_contents(e) for e in container.findAll("td", {"style": "text-align:left;"})]
    away_goals = [get_contents(e) for e in container.findAll("td", {"align": 'right'})]

    def process_goal(s, team):

        # Need to check this for own goals?

        goal_type = 'normal'

        s = s.replace("&nbsp;", '').strip()
        if not s:
            return {}

        m = re.match("(.*?)\((\d+)'\)", s)
        if m:
            player, minute = m.groups()


        # Need to fix this...
        m = re.match("(.*?)\(og (\d+)'\)", s)
        if m:
            player, minute = m.groups()
            goal_type = 'own goal'

        m = re.match("(.*?)\(pen (\d+)'\)", s)
        if m:
            player, minute = m.groups()
            goal_type = 'own goal'

        m = re.match("(.*?)\(pen miss (\d+)'\)", s)
        if m:
            return {}


        if player == 'player':
            import pdb; pdb.set_trace()

            
        return {
            'goal': player,
            'minute': minute,
            'team': team,
            'type': goal_type,
            'season': unicode(game_data['date'].year),
            'date': game_data['date'],
            'competition': game_data['competition'],
            'assists': [],
            'sources': [url],
            }

    # Not the best way to handle this now that we've switched away from home/away designations.
    goals = []
    for goal in home_goals:
        gd = process_goal(goal, game_data['team1'])
        if gd:
            goals.append(gd)

    for goal in away_goals:
        gd = process_goal(goal, game_data['team2'])
        if gd:
            goals.append(gd)
        
    return goals


#@detail_cache
def scrape_soccernet_lineups(soup, competition, game_data, url):
    """
    Scrape a lineup from a game url.
    """
    # Not checking for red cards currently.

    tables = soup.findAll("table")
    

    if len(tables) == 11:
        home_lineup, _, home_subs = tables[1:4]
        away_lineup, _, away_subs = tables[6:9]

    elif len(tables) == 12:
        home_lineup, _, home_subs = tables[2:5]
        away_lineup, _, away_subs = tables[7:10]

    else:
        # Bad game listing.
        # Seems all 2006 New York lineups are missing.
        # e.g. http://soccernet.espn.go.com/match?id=207065&cc=5901
        print("Bad soccernet listing")
        return []



    def process_substitutions(subs):
        """
        Returns a dict like {"David Beckham": {"off": 45}, "Ryan Giggs": {"on": 45} }
        """

        d = defaultdict(dict)

        for sub in subs.findAll("tr"):
            tds = sub.findAll("td")
            if tds:
                if get_contents(tds[0]) == 'No Substitutions':
                    return {}

                minute = int(get_contents(tds[0]).replace("'", ''))

                l = [get_contents(e) for e in tds[1].findAll("a")]
                if len(l) == 2:
                    on, off = l
                    
                elif len(l) < 2:
                    s = get_contents(tds[1])
                    on, off = [e.strip() for e in s.split('for', 1)]

                else:
                    import pdb; pdb.set_trace()    
                    

                d[off]['off'] = d[on]['on'] = minute

        return d
            

    def process_lineup(lineup, subs, team):
        players = [get_contents(e) for e in lineup.findAll("a")]
        sub_dict = process_substitutions(subs)

        lineup = []

        for player in players:

            if player in sub_dict:
                sub_data = sub_dict[player]
                on = sub_data.get('on', 0)
                off = sub_data.get('off', 90)
            else:
                on = 0
                off = 90

            lineup.append({
                    'name': player,
                    'on': on,
                    'off': off,
                    'team': team,
                    'date': game_data['date'],
                    'season': unicode(game_data['date'].year),
                    'competition': game_data['competition'],
                    'sources': [url],
                    })

        return lineup

    la = process_lineup(home_lineup, home_subs, game_data['team1'])
    lb = process_lineup(away_lineup, away_subs, game_data['team2'])

    return la + lb






if __name__ == "__main__":

    leagues = [
        'conmebol.libertadores',
        'uefa.champions',
        'usa.1',
        'uefa.europa',
        'eng.1',
        'bra.1',
        'mex.1',
        'arg.1',
        ]

    #print(scrape_all_league_games('concacaf.champions'))
    #print(scrape_all_league_games('usa.1'))
    print(scrape_league('usa.1'))
    #print(scrape_all_league_goals('usa.1'))
    #print(scrape_all_league_lineups('usa.1'))
    #print(scrape_all_league_games('uefa.champions'))
    #print(scrape_all_league_games('usa.1'))
    #print(scrape_all_league_games('mex.1'))
    #print(scrape_bio())
