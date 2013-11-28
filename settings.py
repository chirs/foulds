import os
import socket

USER_AGENT = 'Mozilla/5.0 (Windows NT 5.1; rv:8.0; en_us) Gecko/20100101 Firefox/8.0'

host = socket.gethostname()

roots = {
    'agni.local': '/Users/chris/soccer',
    'bert': '/home/chris/www',
    }

ROOT_DIR = roots[host]


IMAGE_DIR = os.path.join(ROOT_DIR, 'foulds/images')

CACHE_FOLDER = os.path.join(ROOT_DIR, 'scraper-cache')
PAGE_CACHE_FOLDER = os.path.join(CACHE_FOLDER, 'page')
DATA_CACHE_FOLDER = os.path.join(CACHE_FOLDER, 'data')



