import pickle
import datetime
import functools
import gzip
import hashlib

import json
import os


from foulds.settings import USER_AGENT, DATA_CACHE_FOLDER

if not os.path.exists(DATA_CACHE_FOLDER):
    os.makedirs(DATA_CACHE_FOLDER)



# This is how dates are formatted/unformatted, since leveldb can't store datetimes.
format_string = '%Y-%m-%dT%H:%M:%S'


def cache_format(el):
    """
    Format an item for insertion into leveldb.
    """

    def _inner(v):
        """
        Convert all datetimes inside an object into strings.
        """
        # What about tuples?
        if type(v) == type([]):
            l2 = []
            for e in v:
                l2.append(_inner(e))
            return l2

        elif type(v) == type({}):
            d2 = {}
            for key, value in v.items():
                d2[key] = _inner(value)
            return d2

        if isinstance(v, datetime.datetime):
            return v.strftime(format_string)
        
        return v

    return json.dumps(_inner(el))


def cache_unformat(el):
    """
    Unformat an item upon removal from leveldb.
    """

    def _inner(v):
        """
        Turn datetime strings back into datetimes.
        """
        if type(v) == type([]):
            l2 = []
            for e in v:
                l2.append(_inner(e))
            return l2

        elif type(v) == type({}):
            d2 = {}
            for key, value in v.items():
                d2[key] = _inner(value)
            return d2

        #elif type(v) in [type(''), type(u'')]:
        elif type(v) == type(''):
            try:
                return datetime.datetime.strptime(v, format_string)
            except:

                pass

        return v

    return _inner(json.loads(el))


def set_data_cache(cache_id, value):
    """
    Set a value in the cache.
    """

    p = os.path.join(DATA_CACHE_FOLDER, cache_id)
    f = gzip.open(p, 'wb')
    pickle.dump( value, f)
    f.close()


def get_data_cache(cache_id):
    """
    Get a value from cache.
    """

    p = os.path.join(DATA_CACHE_FOLDER, cache_id)
    f = gzip.open(p, 'rb')
    data = pickle.load(f)
    f.close()
    return data


class AbstractCache(object):
    """
    Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        raise NotImplementedError()

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)


class data_cache(AbstractCache):
    """
    A cache decorator that uses mongodb as a backend.
    """

    def __call__(self, *args):

        name = ('%s:%s' % (self.func.__name__, args)).encode('utf-8')
        key = hashlib.md5(name).hexdigest()

        # Try to retrieve from the cache.
        try:
            data = get_data_cache(key)
            #print("Returning %s%s from data cache." % (self.func.func_name, args))
            return data
        except IOError:
            # Data wasn't in the cache, so go get it.
            pass

        value = self.func(*args)
        set_data_cache(key, value)
        return value


class set_cache(AbstractCache):
    """
    A decorator that will set the cache without trying to access it.
    """

    def __call__(self, *args):
        # Should maybe fail rather than returning None?
        # Presumably need kwargs in here too?
        name = ('%s:%s' % (self.func.__name__, args)).encode('utf-8')
        key = hashlib.md5().hexdigest()
        value = self.func(*args)
        set_data_cache(key, value)
        return value

                                    
