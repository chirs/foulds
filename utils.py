import gzip
import hashlib
import os
import random
import time
from urllib import urlencode
import urllib2
from BeautifulSoup import BeautifulSoup


from settings import USER_AGENT, PAGE_CACHE_FOLDER


if not os.path.exists(PAGE_CACHE_FOLDER):
    os.makedirs(PAGE_CACHE_FOLDER)


def to_hash(s):
    return hashlib.md5(s).hexdigest()


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



def scrape_url(url, refresh=False, encoding=None, sleep=5, fix_tags=False, url_data={}):
    """
    Scrape a url, or just use a version saved in mongodb.
    """
    # Might want to allow a list of encodings.
    if encoding is None:
        encoding = 'utf-8'

    # Should be connection.cache
    data = None
    if refresh is False:
        try:
            p = os.path.join(PAGE_CACHE_FOLDER, to_hash(url))
            if os.path.exists(p):
                data = gzip.open(p, 'rb').read()
            #raise KeyError()
            #data = db.Get(url)
            print("pulling %s from page cache" % url)
        except KeyError:
            pass

    if data is None:
        time.sleep(sleep)
        print("downloading %s" % url)

        # Requests is not returning correct data.
        # e.g. http://www.fifa.com/worldcup/archive/edition=84/results/matches/match=3051/report.html
        # gets trash back.
        #data = requests.get(url, headers=[('User-Agent', USER_AGENT)]).read()

        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', USER_AGENT)]
        if url_data:
            post = urlencode(url_data)
            import pdb; pdb.set_trace()
            data = opener.open(url, data=post).read()
        else:
            data = opener.open(url).read()


        p = os.path.join(PAGE_CACHE_FOLDER, to_hash(url))
        f = gzip.open(p, 'wb')
        f.write(data)
        f.close()

    # jesus christ.
    data = data.replace("</scr'+'ipt>", "</script>")
    data = data.replace("</scr' + 'ipt", "</script")
    data = data.replace("</scr'+'ipt>", "</script>")
    data = data.replace("</SCRI' + 'PT>", "</SCRIPT>")
    data = data.replace("</scri'+'pt>", "</script>")
    data = data.replace('"RowHeader""', '"RowHeader"')
    data = data.replace("<meta content=  </div>", "<meta></div>")
    data = data.replace("<meta charset=  </div>", "<meta></div>")
    data = data.replace("<p style=  </div>", "<p></div>")


    # Seeing this problem with mlssoccer.com for some reason.
    if fix_tags:
        data = data.replace("&lt;", '<')
        data = data.replace("&gt;", '>')


    # Missing quotation mark. (http://soccernet.espn.go.com/match?id=331193&cc=5901)
    data = data.replace('href=http', 'href="http')

    # Bad tag.
    data = data.replace("<font size=  </div>", "</div>")

    # Oh shit! There was some bad unicode data in eu-football.info
    # Couldn't find an encoding so I'm just killing it.
    # Looked to be involved with goolge analytics.
    data = data.replace("\xf1\xee\xe7\xe4\xe0\xed\xee", "")

    # http://www.mlssoccer.com/schedule?month=all&year=1996&club=all&competition_type=all
    data = data.replace('<img alt="" src="/sites/league/files/eljimador_300x100.gif" style="border: medium none; width: 300px; height: 100px;" <img', "<img")

    data = data.replace("""onclick="this.href=this.href+'?ref=espn_deportes&refkw=deportes+tickets'""", '')
    
    return data


def scrape_soup(*args, **kwargs):
    html = scrape_url(*args, **kwargs)
    return BeautifulSoup(html)



def scrape_post(url, options):
    # Scrape a post url.
    # This doesn't really make sense, but this is how
    # Mediotiempo does it.

    options_string = dict_to_str(options)

    opener = urllib2.build_opener()
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


