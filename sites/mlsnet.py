import datetime

import re
import urllib

from foulds.utils import scrape_soup, get_contents
from foulds.cache import data_cache, set_cache


team_abbreviations = [
    'chi',
    'clb',
    'dc',
    'met',
    'ne',
    'col',
    #'dal',
    'kc',
    'la',
    'sj',
]

make_absolute = lambda u: 'http://web.archive.org' + u


def scrape_2001_roster_bios(team_code):
    url = 'http://web.archive.org/web/20020208192848/http://www.mlsnet.com/teams/%s/roster.html' % team_code
    soup = scrape_soup(url)

    table = soup.find('p', 'navBody').parent.find('table')

    anchors = table.findAll('a')
    urls = [make_absolute(a['href']) for a in anchors]

    l = [scrape_bio_image(url) for url in urls]
    return [e for e in l if e]


@data_cache
def scrape_bio_image(url):
    try:
        soup = scrape_soup(url)
    except urllib.error.HTTPError:
        return None

    images = soup.findAll('img')

    hrefs = [(e['src'], e.get('alt')) for e in images]

    
    imgs = [e for e in hrefs if '/players/' in e[0]]
    if len(imgs) == 0:
        return None
    elif len(imgs) == 1:
        bi = imgs[0]
        return (bi[1], make_absolute(bi[0]))
    else:
        import pdb; pdb.set_trace()
        x = 5



def scrape_2001_images():
    l = []
    for team in team_abbreviations:
        images = scrape_2001_roster_bios(team)
        l.extend(images)

    return l
        

if __name__ == "__main__":
    print(scrape_2001_images())
    #print(scrape_bio_image('http://web.archive.org/web/20020208192848/http://www.mlsnet.com/bios/evan_whitfield.html'))

    
    
