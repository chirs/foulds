import datetime
import hashlib
import os
import re
import urllib

from foulds.cache import data_cache, set_cache
from foulds.utils import scrape_soup, scrape_url, get_contents
from foulds.settings import IMAGE_DIR


team_abbreviations = [
    'chi',
    'clb',
    'col',
    #'dal',
    'dc',
    'kc',
    'la',
    'met',
    'ne',
    'sj',
]

make_absolute = lambda u: 'http://web.archive.org' + u


def scrape_2001_roster_bios(team_code):
    url = 'http://web.archive.org/web/20020208192848/http://www.mlsnet.com/teams/%s/roster.html' % team_code
    soup = scrape_soup(url)

    table = soup.find('p', 'navBody').parent.find('table')

    anchors = table.findAll('a')
    urls = [make_absolute(a['href']) for a in anchors]

    l = [scrape_2001_bio(url) for url in urls]
    return [e for e in l if e]


@data_cache
def scrape_2001_bio(url):
    try:
        soup = scrape_soup(url)
    except urllib.error.HTTPError:
        return None

    images = soup.findAll('img')

    hrefs = [(e['src'], e.get('alt')) for e in images]

    
    imgs = [e for e in hrefs if '/players/' in e[0]]

    if len(imgs) != 1:
        return None
    else:
        u = make_absolute(imgs[0][0])
        img_path = download_image(u)

        return {
            'name': imgs[0][1],
            'source': url,
            'img': img_path,
            }


# data_cache because of bad urls.
@data_cache
def scrape_2001_bios():
    l = []
    for team in team_abbreviations:
        images = scrape_2001_roster_bios(team)
        l.extend(images)
    return l


@set_cache
def scrape_2005_bio(url):
    try:
        soup = scrape_soup(url)
    except:
        return None

    main = soup.find('div', {'id': 'main'})

    if main is None:
        return None


    tables = main.findAll('table')
    player_img = tables[1].find('img')
    img_src = player_img['src']

    if img_src.endswith('gif'):
        return None

    bio_data = [e.next_sibling for e in main.findAll('span', 'bioGrey')]
    name, position, height, weight, bd, hometown, previous_team = bio_data
    birthdate = datetime.datetime.strptime(bd, "%B %d, %Y")

    abs_src = make_absolute(img_src)

    #img_path = download_image(abs_src)
    img_path = None

    print(name)
    print(hometown)

    return {
        #'name': name,
        #'hometown': hometown,
        'birthdate': birthdate,
        'img': img_path,

        'source': url,
        }




def scrape_2005_bios():
    url = 'http://web.archive.org/web/20050829135848/http://www.mlsnet.com/MLS/players/'
    soup = scrape_soup(url)

    hrefs = [e['href'] for e in soup.findAll('a')]

    player_urls = [e for e in hrefs if 'players/bio' in e]
    absolute_urls = [make_absolute(e) for e in player_urls]

    l = []
    for url in absolute_urls[:3]:
        l.append(scrape_2005_bio(url))

    return [e for e in l if e]


def download_image(url):
    if url.lower().endswith('.jpg') or url.lower().endswith('.jpeg'):
        fn = hashlib.md5(url.encode('utf-8')).hexdigest() + '.jpg'
        pth = os.path.join(IMAGE_DIR, fn)
        if os.path.exists(pth):
            return pth
        
        try:
            data = scrape_url(url, encoding=None)
        except urllib.error.HTTPError:
            return None

        with open(pth, 'wb') as fn:
            fn.write(data)
        return pth
    else:
        raise




if __name__ == "__main__":
    #scrape_2005_bios()
    print(scrape_2001_bios())
    #print(scrape_2001_bio('http://web.archive.org/web/20020208192848/http://www.mlsnet.com/bios/evan_whitfield.html'))

    
    
