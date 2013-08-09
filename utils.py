import gzip
import hashlib
import os
import random
import time
from urllib.parse import urlencode
from urllib.request import build_opener
from bs4 import BeautifulSoup


from foulds.settings import USER_AGENT, PAGE_CACHE_FOLDER


if not os.path.exists(PAGE_CACHE_FOLDER):
    os.makedirs(PAGE_CACHE_FOLDER)


def to_hash(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def get_id():
    """Generate a random string based on the time when this is called."""
    return hashlib.md5(str(time.time()).encode('utf8')).hexdigest()


def get_contents(l, formatter=lambda s: s):
    """
    Fetch the contents from a soup object.
    """
    # seem to be losing some spaces with this function.
    # Would be nice to turn br's into newlines.

    if not hasattr(l, 'contents'):
        s = l
    else:
        s = ""

        for e in l.contents:
            s += get_contents(e)
    return formatter(s.strip())


def dict_to_str(d):
    """
    Parse url options, basically.
    """
    opts = ["%s=%s" % (str(k), str(v)) for (k, v) in d.items()]
    return "?" + "&".join(opts)


# Scrapers



def scrape_url(url, refresh=False, encoding='utf-8', sleep=5, fix_tags=False, url_data={}):
    """
    Scrape a url, or just use a version saved in mongodb.
    """

    # Should be connection.cache
    data = None
    if refresh is False:
        try:
            p = os.path.join(PAGE_CACHE_FOLDER, to_hash(url))
            if os.path.exists(p):
                data = gzip.open(p, 'rb').read()
            print("pulling %s from page cache" % url)
        except KeyError:
            pass

    if data is None:
        print("downloading %s" % url)
        time.sleep(sleep)

        opener = build_opener()
        opener.addheaders = [('User-agent', USER_AGENT)]
        if url_data:
            post = urlencode(url_data)
            #import pdb; pdb.set_trace()
            data = opener.open(url, data=post.encode('utf-8')).read()
        else:
            data = opener.open(url).read()


        p = os.path.join(PAGE_CACHE_FOLDER, to_hash(url))
        f = gzip.open(p, 'wb')
        f.write(data)
        f.close()


    if encoding:
        data = data.decode(encoding)

    return data


def scrape_soup(*args, **kwargs):
    html = scrape_url(*args, **kwargs)
    return BeautifulSoup(html)



def scrape_post(url, options):
    # Scrape a post url.
    # This doesn't really make sense, but this is how
    # Mediotiempo does it.

    options_string = dict_to_str(options)

    opener = build_opener()
    opener.addheaders = [('User-agent', USER_AGENT)]
    data = opener.open(url, options_string).read()

    # Oh no more shit.
    # This is from mediotiempo.com/ajax/ajax_jornadas.php?id_liga=1&id_torneo=229&jornada=5
    # Tired of struggling with mediotiempo so I'm skipping over it for now.
    # But definitely need to address these problems.
    data = data.replace("\xed", "")

    
    return data


def scrape_post_soup():
    data = scrape_post()
    return BeautifulSoup(data)


