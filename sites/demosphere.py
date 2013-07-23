import datetime

from foulds.utils import scrape_soup, get_contents
from foulds.cache import data_cache, set_cache


# USSF D-2 2010
x = 'http://ussf.demosphere.com/stats/2010/2072059.html'

# Developmental academy data.
y = 'http://ussda.demosphere.com/standings/index_E.html'

# Going to have to scrape demosphere and assemble the data myself.
# Not really!



def clean_nbsp(s, r=''):
    return s.replace("&nbsp;", r).strip()

def scrape_ussf_d2_games():
    urls = get_game_urls('http://ussf.demosphere.com/Schedules/2010/20952154.html', 'http://ussf.demosphere.com')

    l = []
    for url in urls:
        l.append(scrape_game_stats(url))

    return l
    
    

def get_game_urls(url, absolute_template):
    soup = scrape_soup(url, encoding='ISO-8859-1', refresh=True)

    table = soup.find("table", "NAVBoxBlue")
    months = [e['href'] for e in table.findAll("a")]
    month_urls = ["%s%s" % (absolute_template, month) for month in months]

    game_urls = []
    for e in month_urls:
        s = scrape_soup(e, encoding='ISO-8859-1', refresh=True)
        anchors = s.findAll("a")
        anchors = [e['href'] for e in anchors if "/stats/" in e['href'] or "/MatchReport/" in e['href']]
        game_urls.extend(anchors)


    game_urls = sorted(set(game_urls))
    return ["%s%s" % (absolute_template, u) for u in game_urls]



def scrape_game_data(url):
    # Need to do attendance, weather.

    soup = scrape_soup(url, encoding='ISO-8859-1', refresh=True)

    tm = soup.find("table", "MainContent")

    first_table = tm.findAll("table")[0]
    home_team, away_team = [get_contents(e) for e in first_table.findAll("a")]
    
    scores = clean_nbsp(get_contents(first_table), '\n').split('\n')[3]
    home_score, away_score = [int(e) for e in scores.split(":")]

    stadium, date, time = [clean_nbsp(get_contents(e)) for e in tm.findAll("table")[1].findAll("td")]

    dt = datetime.datetime.strptime(date,  "%A, %B %d, %Y")

    return {
        'home_team': home_team,
        'away_team': away_team,
        'home_score': home_score,
        'away_score': away_score,
        'stadium': stadium,
        'date': date,
        'source': url
        }


def scrape_game_stats(url):
    game_data = scrape_game_data(url)
    
    soup = scrape_soup(url, encoding='ISO-8859-1')
    import pdb; pdb.set_trace()

    x = 5



if __name__ == "__main__":
    print(scrape_ussf_d2_games())

